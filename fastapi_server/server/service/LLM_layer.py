import json
import logging
import os
import re
from typing import Dict


from dotenv import load_dotenv
from openai import OpenAI


logger = logging.getLogger(__name__)
class LLMAnalyzer:

    # 安全关键词预过滤（正则匹配）
    SECURITY_KEYWORDS = re.compile(
        r'(?i)\b(cve-\d+|security|vulnerabilit(y|ies)|exploit|'
        r'use-after-free|buffer[- ]overflow|race[- ]condition|'
        r'out[- ]of[- ]bounds|null[- ]pointer[- ]dereference|'
        r'denial[- ]of[- ]service|privilege[- ]escalation|'
        r'information[- ]leak|memory[- ]corruption|'
        r'fix(es|ed)?|patch(es|ed)?|resolve([sd])?|repair(s|ed)?|'
        r'mitigate([sd])?|remediate([sd])?|address(es|ed)?|correct(s|ed)?|'
        r'rectif(y|ies|ied)?|amend(s|ed)?)\b'
    )

    def __init__(self, model_type: str = "deepseek"):
        """
        初始化大模型分析器
        :param model_type: "deepseek" 或 "openai"
        """
        self.model_type = model_type
        self.client = None
        self.model_name = None
        load_dotenv()
        if model_type == "deepseek":
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if not api_key:
                raise ValueError("未找到 DEEPSEEK_API_KEY 环境变量")
            self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            self.model_name = "deepseek-chat"
            logger.info("DeepSeek 分析器初始化成功")


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
        return (f"""请分析以下GIT commit是否与内核安全更新有关，如果有请提取相关信息。
                Commit Message:{message}
                代码变更(diff):{diff if diff else "无代码变更"}
                请严格按照如下JSON格式输出，不要输出任何其他内容:
                {{
                "is_security_related": true/false,
                "vulnerability_type": "漏洞类型，如 use-after-free / buffer overflow / race condition / 若为文档修改等也按分类分开，若属于多种类型，则选择最严重的类型，不要写其他若不相关则为 null",
                "affected_subsystem": "影响的子系统，如 netfilter / bpf / ext4 / kernel core / 其他，若不相关则为 null",
                "severity": "Critical / High / Medium / Low，若不相关则为 null",
                "cve_id": "关联的 CVE 编号，如 CVE-2024-1234，若无则为 null",如有多个只保留一个
                "summary": "一句话总结此 commit 的安全影响或修复内容（中文，不超过 50 字）",
                "thinking": "请用中文详细描述你的分析思考过程，包括：1) 为什么认为这个commit与安全相关/不相关；2) 如何判断漏洞类型和严重程度；3) 对代码变更的关键分析点"
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
                "thinking": data.get("thinking", ""),
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
                "thinking": "",
                "raw_response": raw,
                "analysis_cost": 0,
                "model_name": self.model_name
            }

    def analyze_commit(self,message:str,diff:str):
        """
        调用LLM分析commit，返回结构化json
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
                "thinking": "",
                "raw_response": "",
                "analysis_cost": 0,
                "model_name": self.model_name
            }

    def _build_insights_prompt(self, commit_messages: list) -> str:
        """
        构建分析commits洞察的prompt
        :param commit_messages: commit消息列表
        :return: prompt字符串
        """
        messages_text = "\n---\n".join([f"[{i+1}] {msg}" for i, msg in enumerate(commit_messages)])
        return f"""请分析以下Git commit messages，提取出关于安全漏洞修复的有趣洞察和模式。

Commit Messages:
{messages_text}

请分析这些commits，提取以下信息并以JSON格式输出：
{{
    "insights": [
        "洞察1: 具体描述发现的有趣模式或趋势",
        "洞察2: 例如：某个bug是由LLM识别出来的",
        "洞察3: 例如：最近项目经常出现某种类型的错误"
    ],
    "common_vuln_types": ["最常见的漏洞类型1", "类型2"],
    "recommendations": "基于这些commits，给项目的安全改进建议（中文，100字以内）",
    "llm_identified_count": 5,
    "summary": "整体总结这段时期的安全修复趋势（中文，50字以内）"
}}

注意：
1. insights数组应包含3-5条具体、有意义的洞察
2. 如果commit中有提到LLM/AI识别的bug，请特别指出
3. 如果发现某种漏洞类型频繁出现，请指出可能需要改进的地方
4. 如果没有足够数据，请返回空数组和"数据不足"的提示"""

    def analyze_commits_insights(self, commit_messages: list) -> Dict:
        """
        分析多个commit messages，提取洞察和趋势
        :param commit_messages: commit消息列表
        :return: 分析结果字典
        """
        if not commit_messages:
            return {
                "insights": [],
                "common_vuln_types": [],
                "recommendations": "暂无数据",
                "llm_identified_count": 0,
                "summary": "没有可分析的commits",
                "analysis_cost": 0,
                "model_name": self.model_name
            }

        # 限制分析的commits数量，避免token过多
        truncated_messages = commit_messages[:50]
        prompt = self._build_insights_prompt(truncated_messages)

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "你是一位资深网络安全分析师，擅长从代码提交中发现安全趋势和模式。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            raw = response.choices[0].message.content
            token_usage = response.usage.total_tokens if response.usage else 0

            # 解析JSON
            try:
                data = json.loads(raw)
                return {
                    "insights": data.get("insights", []),
                    "common_vuln_types": data.get("common_vuln_types", []),
                    "recommendations": data.get("recommendations", ""),
                    "llm_identified_count": data.get("llm_identified_count", 0),
                    "summary": data.get("summary", ""),
                    "analysis_cost": token_usage,
                    "model_name": self.model_name
                }
            except json.JSONDecodeError:
                logger.warning(f"洞察分析JSON解析失败: {raw[:200]}")
                return {
                    "insights": [],
                    "common_vuln_types": [],
                    "recommendations": "解析失败",
                    "llm_identified_count": 0,
                    "summary": "分析结果解析失败",
                    "analysis_cost": token_usage,
                    "model_name": self.model_name
                }

        except Exception as e:
            logger.error(f"洞察分析LLM调用失败: {e}")
            return {
                "insights": [],
                "common_vuln_types": [],
                "recommendations": f"分析失败: {str(e)[:100]}",
                "llm_identified_count": 0,
                "summary": "分析失败",
                "analysis_cost": 0,
                "model_name": self.model_name
            }