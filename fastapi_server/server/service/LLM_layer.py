import json
import logging
import os
import re
from typing import Dict

from click import prompt
from django.db.models.functions import JSONObject
from openai import OpenAI
from openai.types import ResponseFormatJSONObject

logger = logging.getLogger(__name__)
class LLMAnalyzer:

    # 安全关键词预过滤（正则匹配）
    SECURITY_KEYWORDS = re.compile(
        r'(?i)\b(cve-\d+|security|vulnerabilit(y|ies)|exploit|'
        r'use-after-free|buffer[- ]overflow|race[- ]condition|'
        r'out[- ]of[- ]bounds|null[- ]pointer[- ]dereference|'
        r'denial[- ]of[- ]service|privilege[- ]escalation|'
        r'information[- ]leak|memory[- ]corruption)\b'
    )

    def __init__(self, model_type: str = "deepseek"):
        """
        初始化大模型分析器
        :param model_type: "deepseek" 或 "openai"
        """
        self.model_type = model_type
        self.client = None
        self.model_name = None

        if model_type == "deepseek":
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if not api_key:
                raise ValueError("未找到 DEEPSEEK_API_KEY 环境变量")
            self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            self.model_name = "deepseek-chat"
            logger.info("DeepSeek 分析器初始化成功")
        elif model_type == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("未找到 OPENAI_API_KEY 环境变量")
            self.client = OpenAI(api_key=api_key)
            self.model_name = "gpt-4o-mini"
            logger.info("OpenAI 分析器初始化成功")
        elif model_type == "grok":
            api_key = os.getenv("GROK_API_KEY")
            if not api_key:
                raise ValueError("未找到 GROK_API_KEY 环境变量")
            self.client = OpenAI(api_key=api_key)
            self.model_name = "GROK"
            logger.info("GROK 分析器初始化成功")
        else:
            raise ValueError(f"不支持的模型类型: {model_type}")


    def should_analyze(self,commit_message:str,diff:str="") -> bool:
        """
        预过滤 判断是否与安全相关
        """
        text = f"{commit_message}\n{diff}"
        return bool(self.SECURITY_KEYWORDS.search(text))

    def _build_prompt(self,message:str,diff:str) -> str:
        """
        构建分析prompt
        :param message:
        :param diff:
        :return:
        """
        return (f"""请分析以下GIT commit是否与内核安全更新有关，若果有请提取相关信息。"
                "Commit Message:{message}"
                "代码变更(diff):{diff if diff else "无代码变更"}"
                "请严格按照如下JSON格式输出，不要输出任何其他内容:"
                "{{
                "is_security_related": true/false,
                "vulnerability_type": "漏洞类型，如 use-after-free / buffer overflow / race condition / 其他，若不相关则为 null",
                "affected_subsystem": "影响的子系统，如 netfilter / bpf / ext4 / kernel core / 其他，若不相关则为 null",
                "severity": "Critical / High / Medium / Low，若不相关则为 null",
                "cve_id": "关联的 CVE 编号，如 CVE-2024-1234，若无则为 null",
                "summary": "一句话总结此 commit 的安全影响或修复内容（中文，不超过 50 字）"
                 }}"""
                )

    def _parse_response(self, raw: str) -> Dict:
        """解析大模型返回的 JSON，处理可能的格式错误"""
        try:
            # 尝试提取 JSON 块（部分模型会输出 markdown 代码块）
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if json_match:
                raw = json_match.group(0)
            data = json.loads(raw)

            # 确保字段存在
            return {
                "is_security_related": data.get("is_security_related", None),
                "vulnerability_type": data.get("vulnerability_type"),
                "affected_subsystem": data.get("affected_subsystem"),
                "severity": data.get("severity"),
                "cve_id": data.get("cve_id"),
                "summary": data.get("summary", "分析完成"),
                "raw_response": raw,
                "analysis_cost": 0,
                "model_name": self.model_name
            }
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 解析失败: {e}, 原始内容: {raw[:200]}")
            return {
                "is_security_related": None,
                "vulnerability_type": None,
                "affected_subsystem": None,
                "severity": None,
                "cve_id": None,
                "summary": "解析失败",
                "raw_response": raw,
                "analysis_cost": 0,
                "model_name": self.model_name
            }

    def analyze_commit(self,commit_hash,message:str,diff:str):
        """
        调用LLM分析commit，返回结构化json
        :param commit_hash:
        :param message:
        :param diff:
        :return:
        """
        truncated_diff = diff[:4000] if diff else ""
        prompt = self._build_prompt(message,truncated_diff)
        try:
                response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "你是一位资深网络安全专家，专门分析 Linux 内核及开源软件的安全补丁。"},
                    {"role": "user", "content": prompt}],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
                raw = response.choices[0].message.content
                token_usage = response.usage.total_tokens if response.usage else 0

                # 解析 JSON
                result = self._parse_response(raw)
                result["raw_response"] = raw
                result["analysis_cost"] = token_usage
                result["model_name"] = self.model_name

                return result
        except Exception as e:
            logger.info(f"LLM调用失败：{e}")
            return {
                "is_security_related": None,
                "vulnerability_type": None,
                "affected_subsystem": None,
                "severity": None,
                "cve_id": None,
                "summary": f"分析失败: {str(e)[:100]}",
                "raw_response": "",
                "analysis_cost": 0,
                "model_name": self.model_name
            }