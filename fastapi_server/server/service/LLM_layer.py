import json
import logging
import os
import re
from datetime import datetime, timedelta
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


# ================= 批量分析和缓存工具函数 =================

def get_date_range(time_range: str):
    """计算日期范围"""
    end_date = datetime.now()
    if time_range == '7d':
        start_date = end_date - timedelta(days=7)
    elif time_range == '30d':
        start_date = end_date - timedelta(days=30)
    elif time_range == '90d':
        start_date = end_date - timedelta(days=90)
    else:  # year
        start_date = end_date - timedelta(days=365)
    return start_date, end_date


def get_insights_commits(db, repo_id: int, time_range: str, max_total: int = 50):
    """
    智能获取用于AI洞察分析的commits
    策略：按严重程度分层取样 + 时间倒序
    """
    from server.service.models import LLMAnalyse, GithubCommit

    start_date, end_date = get_date_range(time_range)

    severity_limits = {
        'Critical': int(max_total * 0.3),
        'High': int(max_total * 0.3),
        'Medium': int(max_total * 0.25),
        'Low': int(max_total * 0.15)
    }

    all_commits = []
    used_commit_ids = set()

    for severity, limit in severity_limits.items():
        if limit <= 0:
            continue

        commits = db.query(GithubCommit, LLMAnalyse).join(
            LLMAnalyse, GithubCommit.id == LLMAnalyse.commit_id
        ).filter(
            GithubCommit.repo_id == repo_id,
            LLMAnalyse.is_security_related == True,
            LLMAnalyse.severity == severity,
            GithubCommit.commit_date >= start_date,
            GithubCommit.commit_date <= end_date
        ).order_by(GithubCommit.commit_date.desc()).limit(limit).all()

        for commit, analysis in commits:
            if commit.id not in used_commit_ids and commit.message:
                all_commits.append(commit.message)
                used_commit_ids.add(commit.id)

    # 补充不足的部分
    if len(all_commits) < max_total:
        remaining = max_total - len(all_commits)
        additional = db.query(GithubCommit, LLMAnalyse).join(
            LLMAnalyse, GithubCommit.id == LLMAnalyse.commit_id
        ).filter(
            GithubCommit.repo_id == repo_id,
            LLMAnalyse.is_security_related == True,
            ~GithubCommit.id.in_(list(used_commit_ids)) if used_commit_ids else True,
            GithubCommit.commit_date >= start_date,
            GithubCommit.commit_date <= end_date
        ).order_by(GithubCommit.commit_date.desc()).limit(remaining).all()

        for commit, _ in additional:
            if commit.message:
                all_commits.append(commit.message)

    return all_commits


def analyze_and_cache_insights(db, repo_id: int, time_range: str) -> bool:
    """
    分析指定仓库和时间范围的AI洞察，并缓存结果
    返回是否成功
    """
    from server.service.models import AIInsightsCache
    from datetime import datetime
    import json

    try:
        logger.info(f"开始AI洞察分析: repo_id={repo_id}, time_range={time_range}")

        # 获取commits
        commit_messages = get_insights_commits(db, repo_id, time_range, max_total=50)

        # 获取或创建缓存记录
        cache_record = db.query(AIInsightsCache).filter(
            AIInsightsCache.repo_id == repo_id,
            AIInsightsCache.time_range == time_range
        ).first()

        if not cache_record:
            cache_record = AIInsightsCache(repo_id=repo_id, time_range=time_range)
            db.add(cache_record)

        if not commit_messages:
            cache_record.insights = json.dumps([])
            cache_record.common_vuln_types = json.dumps([])
            cache_record.recommendations = "该时间段内暂无安全相关提交"
            cache_record.llm_identified_count = 0
            cache_record.summary = "暂无数据"
            cache_record.analyzed_at = datetime.now()
            cache_record.commit_count = 0
            db.commit()
            logger.info(f"仓库 {repo_id} 无数据，已创建空缓存")
            return True

        # 调用LLM分析
        analyzer = LLMAnalyzer()
        result = analyzer.analyze_commits_insights(commit_messages)

        # 更新缓存
        cache_record.insights = json.dumps(result.get("insights", []))
        cache_record.common_vuln_types = json.dumps(result.get("common_vuln_types", []))
        cache_record.recommendations = result.get("recommendations", "")
        cache_record.llm_identified_count = result.get("llm_identified_count", 0)
        cache_record.summary = result.get("summary", "")
        cache_record.analyzed_at = datetime.now()
        cache_record.analysis_cost = result.get("analysis_cost", 0)
        cache_record.commit_count = len(commit_messages)

        db.commit()
        logger.info(f"AI洞察分析完成: repo_id={repo_id}, time_range={time_range}")
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"AI洞察分析失败: {e}")
        return False