"""
多模型漏洞严重性审查模块
使用硅基流动平台的国产模型对DeepSeek初判结果进行投票复核
模型：DeepSeek-V3.2、Qwen3.5-397B、GLM-5、Hunyuan
权重分配：DeepSeek-V3.2 0.30, Qwen3.5-397B 0.30, GLM-5 0.25, Hunyuan 0.15
"""

import json
import logging
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum

from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger(__name__)
load_dotenv()


class SeverityLevel(Enum):
    """严重性等级枚举"""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    NONE = "None"


@dataclass
class ModelReviewResult:
    """单个模型的审查结果"""
    model_name: str
    severity: str
    confidence: float  # 置信度 0-1
    reasoning: str  # 判断理由
    key_factors: List[str]  # 关键判断因素
    raw_response: str


@dataclass
class FinalReviewResult:
    """最终审查结果"""
    original_severity: str  # DeepSeek原始判断
    final_severity: str  # 投票后最终判断
    weighted_score: float  # 加权分数 0-4 (Critical=4, High=3, Medium=2, Low=1, None=0)
    consensus_rate: float  # 一致性比率
    model_results: Dict[str, ModelReviewResult]  # 各模型详细结果
    voting_breakdown: Dict[str, float]  # 投票分布
    review_summary: str  # 综合评审意见


class SeverityMapper:
    """严重性等级映射工具"""
    SEVERITY_SCORES = {
        "Critical": 4,
        "High": 3,
        "Medium": 2,
        "Low": 1,
        "None": 0,
        "null": 0,
        None: 0
    }

    # 模型权重配置（基于模型能力和可靠性）
    # 选用硅基流动平台支持的国产顶级模型
    SEVERITY_WEIGHTS = {
        "deepseek_v32": 0.30,   # DeepSeek-V3.2 代码理解最强
        "qwen35_397b": 0.30,    # Qwen3.5-397B 综合能力最强
        "glm5": 0.25,           # GLM-5 推理能力优秀
        "hunyuan": 0.15         # Hunyuan 补充视角
    }

    @classmethod
    def to_score(cls, severity: Optional[str]) -> int:
        """将严重性字符串转换为分数"""
        if not severity:
            return 0
        severity = severity.strip() if isinstance(severity, str) else severity
        return cls.SEVERITY_SCORES.get(severity, 0)

    @classmethod
    def from_score(cls, score: float) -> str:
        """将分数转换为严重性等级（加权平均后）"""
        if score >= 3.5:
            return "Critical"
        elif score >= 2.5:
            return "High"
        elif score >= 1.5:
            return "Medium"
        elif score >= 0.5:
            return "Low"
        else:
            return "None"


class LLMCensorship:
    """多模型漏洞严重性审查器"""

    def __init__(self):
        self.clients = {}
        self._init_clients()

    def _init_clients(self):
        """初始化各个模型的API客户端"""
        # 硅基流动平台（国产模型）
        siliconflow_key = os.getenv("SILICONFLOW_API_KEY")
        if siliconflow_key:
            # DeepSeek-V3.2 (通过硅基流动)
            self.clients["deepseek_v32"] = OpenAI(
                api_key=siliconflow_key,
                base_url="https://api.siliconflow.cn/v1"
            )
            logger.info("DeepSeek-V3.2 客户端初始化成功")

            # Qwen3.5-397B
            self.clients["qwen35_397b"] = OpenAI(
                api_key=siliconflow_key,
                base_url="https://api.siliconflow.cn/v1"
            )
            logger.info("Qwen3.5-397B 客户端初始化成功")

            # GLM-5
            self.clients["glm5"] = OpenAI(
                api_key=siliconflow_key,
                base_url="https://api.siliconflow.cn/v1"
            )
            logger.info("GLM-5 客户端初始化成功")

            # Hunyuan
            self.clients["hunyuan"] = OpenAI(
                api_key=siliconflow_key,
                base_url="https://api.siliconflow.cn/v1"
            )
            logger.info("Hunyuan 客户端初始化成功")

        if not self.clients:
            logger.warning("没有可用的LLM客户端，审查功能将不可用")

    def _build_severity_review_prompt(
        self,
        commit_message: str,
        diff: str,
        original_analysis: Dict,
        model_name: str
    ) -> str:
        """
        构建严重性审查的严谨鉴定Prompt

        评估维度：
        1. 漏洞类型危害程度 (30%)
        2. 影响范围与权限 (25%)
        3. 利用难度与条件 (25%)
        4. 修复紧迫性 (20%)
        """
        return f"""你是一位资深网络安全专家，负责对漏洞严重性进行独立、严谨的评估。

【待审查的 Commit 信息】
Commit Message: {commit_message}
代码变更 (diff): {diff[:3000] if diff else "无代码变更"}

【DeepSeek 初始分析结果】
- 安全相关: {original_analysis.get('is_security_related', 'Unknown')}
- 漏洞类型: {original_analysis.get('vulnerability_type', 'Unknown')}
- 影响子系统: {original_analysis.get('affected_subsystem', 'Unknown')}
- 初始严重性判断: {original_analysis.get('severity', 'Unknown')}
- CVE ID: {original_analysis.get('cve_id', 'None')}
- 分析摘要: {original_analysis.get('summary', 'None')}
- 分析思路: {original_analysis.get('thinking', 'None')[:500]}...

【你的任务】
请独立评估此漏洞的严重性等级，**不要受DeepSeek初始判断的影响**。从以下四个维度进行专业分析：

1. **漏洞类型危害程度** (权重30%)
   - 内存破坏类 (UAF、溢出): 通常 Critical/High
   - 权限提升类: 根据影响范围评估
   - 信息泄露类: 根据泄露数据敏感度评估
   - 拒绝服务类: 根据可利用性评估

2. **影响范围与权限** (权重25%)
   - 是否影响内核核心组件
   - 是否可远程利用
   - 是否需要特殊权限
   - 影响的用户/系统范围

3. **利用难度与条件** (权重25%)
   - 是否需要复杂的利用条件
   - 是否有公开的利用代码 (Exploit)
   - 是否需要竞争条件或特定时序
   - 是否需要本地/物理接触

4. **修复紧迫性** (权重20%)
   - 是否已有在野利用 (In-the-wild)
   - 是否影响关键基础设施
   - CVSS 预估评分范围

【严重程度定义】
- **Critical**: 可远程代码执行、内核提权、无用户交互即可利用
- **High**: 本地提权、重要信息泄露、复杂的远程攻击
- **Medium**: 有限条件下的信息泄露、局部拒绝服务
- **Low**: 难以利用、影响极小、需要管理员权限
- **None**: 非安全问题、误报

【输出要求】
请严格按照以下JSON格式输出，不要包含任何其他内容：
{{
    "severity": "Critical/High/Medium/Low/None",
    "confidence": 0.0-1.0,  // 你的判断置信度
    "reasoning": "详细解释你的判断逻辑，包括上述四个维度的具体分析",
    "key_factors": [
        "关键因素1: 具体说明",
        "关键因素2: 具体说明",
        "关键因素3: 具体说明"
    ],
    "disagreement_with_original": "如果你与DeepSeek初始判断不同，说明理由；如果相同，写'一致'"
}}

请确保你的评估是独立的、专业的，不受初始分析结果的影响。"""

    def _call_model(
        self,
        model_key: str,
        prompt: str,
        max_retries: int = 3
    ) -> Optional[ModelReviewResult]:
        """调用单个模型进行审查"""
        client = self.clients.get(model_key)
        if not client:
            logger.warning(f"{model_key} 客户端未初始化")
            return None

        # 模型配置 - 硅基流动平台模型ID
        # 选用国产顶级模型：DeepSeek-V3.2、Qwen3.5-397B、GLM-5、Hunyuan
        model_configs = {
            "deepseek_v32": "Pro/deepseek-ai/DeepSeek-V3.2",
            "qwen35_397b": "Qwen/Qwen3.5-397B-A17B",
            "glm5": "Pro/zai-org/GLM-5",
            "hunyuan": "tencent/Hunyuan-A13B-Instruct"
        }

        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=model_configs[model_key],
                    messages=[
                        {"role": "system", "content": "你是一位严谨的网络安全专家，负责独立评估漏洞严重性。请提供客观、专业的判断。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,  # 低温度确保一致性
                    max_tokens=2000
                )

                raw_content = response.choices[0].message.content

                # 解析JSON响应
                try:
                    # 提取JSON块
                    import re
                    json_match = re.search(r'\{{.*\}}', raw_content, re.DOTALL)
                    if json_match:
                        raw_content = json_match.group(0)

                    data = json.loads(raw_content)
                    return ModelReviewResult(
                        model_name=model_key,
                        severity=data.get("severity", "None"),
                        confidence=float(data.get("confidence", 0.5)),
                        reasoning=data.get("reasoning", ""),
                        key_factors=data.get("key_factors", []),
                        raw_response=raw_content
                    )
                except json.JSONDecodeError as e:
                    logger.warning(f"{model_key} 响应解析失败: {e}, 原始内容: {raw_content[:200]}")
                    if attempt == max_retries - 1:
                        return None
                    continue

            except Exception as e:
                logger.error(f"{model_key} API调用失败 (尝试 {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return None

        return None

    def review_severity(
        self,
        commit_message: str,
        diff: str,
        original_analysis: Dict,
        use_parallel: bool = True
    ) -> FinalReviewResult:
        """
        执行多模型严重性审查投票

        Args:
            commit_message: Commit消息
            diff: 代码差异
            original_analysis: DeepSeek初始分析结果
            use_parallel: 是否并行调用模型

        Returns:
            FinalReviewResult: 最终审查结果
        """
        logger.info(f"开始多模型严重性审查: {original_analysis.get('cve_id', 'N/A')}")

        model_results = {}
        available_models = list(self.clients.keys())

        if use_parallel and len(available_models) > 1:
            # 并行调用
            with ThreadPoolExecutor(max_workers=len(available_models)) as executor:
                future_to_model = {}
                for model_key in available_models:
                    prompt = self._build_severity_review_prompt(
                        commit_message, diff, original_analysis, model_key
                    )
                    future = executor.submit(self._call_model, model_key, prompt)
                    future_to_model[future] = model_key

                for future in as_completed(future_to_model):
                    model_key = future_to_model[future]
                    try:
                        result = future.result(timeout=60)
                        if result:
                            model_results[model_key] = result
                            logger.info(f"{model_key} 审查完成: {result.severity} (置信度: {result.confidence:.2f})")
                        else:
                            logger.warning(f"{model_key} 审查返回空结果")
                    except Exception as e:
                        logger.error(f"{model_key} 审查异常: {e}")
        else:
            # 串行调用
            for model_key in available_models:
                prompt = self._build_severity_review_prompt(
                    commit_message, diff, original_analysis, model_key
                )
                result = self._call_model(model_key, prompt)
                if result:
                    model_results[model_key] = result
                    logger.info(f"{model_key} 审查完成: {result.severity}")

        # 如果没有获得任何结果，返回原始判断
        if not model_results:
            logger.error("所有模型审查失败，返回原始判断")
            original_severity = original_analysis.get("severity", "None")
            return FinalReviewResult(
                original_severity=original_severity,
                final_severity=original_severity,
                weighted_score=SeverityMapper.to_score(original_severity),
                consensus_rate=0.0,
                model_results={},
                voting_breakdown={},
                review_summary="多模型审查失败，使用原始判断"
            )

        # 计算加权投票结果
        weighted_score = 0.0
        total_weight = 0.0
        voting_breakdown = {}

        for model_key, result in model_results.items():
            weight = SeverityMapper.SEVERITY_WEIGHTS.get(model_key, 0.33)
            severity_score = SeverityMapper.to_score(result.severity)

            # 考虑置信度调整权重
            adjusted_weight = weight * result.confidence
            weighted_score += severity_score * adjusted_weight
            total_weight += adjusted_weight

            # 统计投票分布
            voting_breakdown[result.severity] = voting_breakdown.get(result.severity, 0) + weight

        if total_weight > 0:
            weighted_score = weighted_score / total_weight

        final_severity = SeverityMapper.from_score(weighted_score)
        original_severity = original_analysis.get("severity", "None")

        # 计算一致性
        unique_severities = set(r.severity for r in model_results.values())
        consensus_rate = 1.0 if len(unique_severities) == 1 else (
            0.67 if len(unique_severities) == 2 else 0.33
        )

        # 生成综合评审意见
        review_summary = self._generate_review_summary(
            model_results, final_severity, original_severity, consensus_rate
        )

        logger.info(f"多模型审查完成: 原始={original_severity}, 最终={final_severity}, 加权分数={weighted_score:.2f}")

        return FinalReviewResult(
            original_severity=original_severity,
            final_severity=final_severity,
            weighted_score=weighted_score,
            consensus_rate=consensus_rate,
            model_results=model_results,
            voting_breakdown=voting_breakdown,
            review_summary=review_summary
        )

    def _generate_review_summary(
        self,
        model_results: Dict[str, ModelReviewResult],
        final_severity: str,
        original_severity: str,
        consensus_rate: float
    ) -> str:
        """生成综合评审意见摘要"""
        parts = []

        # 一致性描述
        if consensus_rate >= 0.9:
            parts.append("各模型高度一致")
        elif consensus_rate >= 0.6:
            parts.append("各模型基本达成一致")
        else:
            parts.append("各模型存在分歧")

        # 与原始判断对比
        if final_severity == original_severity:
            parts.append(f"复核结果与初始判断一致 ({original_severity})")
        else:
            parts.append(f"复核调整: {original_severity} → {final_severity}")

        # 各模型简要意见
        model_opinions = []
        for name, result in model_results.items():
            model_opinions.append(f"{name}: {result.severity}")
        parts.append("；".join(model_opinions))

        return "。".join(parts)

    def to_dict(self, result: FinalReviewResult) -> Dict:
        """将审查结果转换为可序列化的字典（用于数据库存储）"""
        return {
            "original_severity": result.original_severity,
            "final_severity": result.final_severity,
            "weighted_score": result.weighted_score,
            "consensus_rate": result.consensus_rate,
            "review_summary": result.review_summary,
            "voting_breakdown": result.voting_breakdown,
            "model_results": {
                name: {
                    "model_name": r.model_name,
                    "severity": r.severity,
                    "confidence": r.confidence,
                    "reasoning": r.reasoning,
                    "key_factors": r.key_factors
                }
                for name, r in result.model_results.items()
            }
        }
