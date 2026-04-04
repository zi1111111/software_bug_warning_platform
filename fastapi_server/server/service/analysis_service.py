import logging
from sqlalchemy.orm import Session
from server.service.models import GithubCommit, LLMAnalyse
from server.service.LLM_layer import LLMAnalyzer
from server.db.database import SessionLocal

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self, model_type: str = "deepseek"):
        self.analyzer = LLMAnalyzer(model_type)

    def analyze_commit_sync(self, commit_id: int, commit_hash: str, message: str, diff: str, db: Session) -> bool:
        """
        分析单个 commit 并存储结果，返回是否成功
        """
        # 预过滤
        if not self.analyzer.should_analyze(message, diff):
            logger.info(f"Commit {commit_hash[:7]} 预过滤跳过（无安全关键词）")
            return False

        logger.info(f"分析 Commit {commit_hash[:7]} ...")
        result = self.analyzer.analyze_commit(commit_hash, message, diff)

        # 存储分析结果
        analyse = LLMAnalyse(
            commit_id=commit_id,
            is_security_related=result.get("is_security_related"),
            vulnerability_type=result.get("vulnerability_type"),
            affected_subsystem=result.get("affected_subsystem"),
            severity=result.get("severity"),
            cve_id=result.get("cve_id"),
            summary=result.get("summary"),
            model_name=result.get("model_name"),
            analysis_cost=result.get("analysis_cost"),
            raw_response=result.get("raw_response")
        )
        db.add(analyse)
        db.commit()
        logger.info(f"Commit {commit_hash[:7]} 分析完成，安全相关: {result.get('is_security_related')}")
        return True

    def analyze_unanalyzed_commits(self):
        """批量分析未分析过的 commits"""
        db = SessionLocal()
        try:
            # 查询未分析过的 commit（没有关联的 LLMAnalyse 记录）
            unanalyzed = db.query(GithubCommit).outerjoin(
                LLMAnalyse, GithubCommit.id == LLMAnalyse.commit_id
            ).filter(LLMAnalyse.id is None).all()

            logger.info(f"发现 {len(unanalyzed)} 个未分析的 commits")
            for commit in unanalyzed:
                try:
                    self.analyze_commit_sync(commit.id, commit.commit_hash, commit.message, commit.diff or "", db)
                except Exception as e:
                    logger.error(f"分析 commit {commit.commit_hash[:7]} 失败: {e}")
                    db.rollback()
                    continue
        finally:
            db.close()