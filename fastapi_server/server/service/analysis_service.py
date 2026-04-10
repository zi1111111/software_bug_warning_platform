import json
import logging
from sqlalchemy.orm import Session
from server.service.models import GithubCommit, LLMAnalyse
from server.service.LLM_layer import LLMAnalyzer
from server.service.LLM_censorship import LLMCensorship
from server.db.database import SessionLocal

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self, model_type: str = "deepseek", enable_censorship: bool = True):
        self.analyzer = LLMAnalyzer(model_type)
        self.enable_censorship = enable_censorship
        self.censorship = LLMCensorship() if enable_censorship else None

    def analyze_commit_sync(self, commit_id: int, commit_hash: str, message: str, diff: str, db: Session) -> bool:
        """
        分析单个 commit 并存储结果，返回是否成功
        """
        # 预过滤

        if not self.analyzer.should_analyze(message, diff):
            logger.info(f"Commit {commit_hash[:7]} 预过滤跳过（无安全关键词）")
            commit = db.query(GithubCommit).filter(GithubCommit.id == commit_id).first()
            commit.is_analysed = True
            db.add(commit)
            db.commit()
            return False

        logger.info(f"分析 Commit {commit_hash[:7]} ...")
        result = self.analyzer.analyze_commit(message, diff)

        # 多模型审查（仅对安全相关问题）
        review_data = None
        final_severity = result.get("severity")
        review_status = "skipped"

        if self.enable_censorship and self.censorship and result.get("is_security_related"):
            try:
                logger.info(f"Commit {commit_hash[:7]} 开始多模型严重性审查...")
                review_result = self.censorship.review_severity(
                    commit_message=message,
                    diff=diff,
                    original_analysis=result,
                    use_parallel=True
                )

                # 将审查结果转换为字典
                review_data = self.censorship.to_dict(review_result)
                final_severity = review_result.final_severity
                review_status = "completed"

                logger.info(f"Commit {commit_hash[:7]} 审查完成: {review_result.original_severity} -> {review_result.final_severity}")
            except Exception as e:
                logger.error(f"Commit {commit_hash[:7]} 多模型审查失败: {e}")
                review_status = "failed"
                final_severity = result.get("severity")  # 使用原始判断

        # 存储分析结果
        analyse = LLMAnalyse(
            commit_id=commit_id,
            is_security_related=result.get("is_security_related"),
            vulnerability_type=result.get("vulnerability_type"),
            affected_subsystem=result.get("affected_subsystem"),
            severity=result.get("severity"),
            cve_id=result.get("cve_id"),
            summary=result.get("summary"),
            thinking=result.get("thinking"),
            model_name=result.get("model_name"),
            analysis_cost=result.get("analysis_cost"),
            raw_response=result.get("raw_response"),
            review_status=review_status,
            review_result=json.dumps(review_data, ensure_ascii=False) if review_data else None,
            final_severity=final_severity
        )
        commit = db.query(GithubCommit).filter(GithubCommit.id == commit_id).first()
        commit.is_analysed = True
        db.add(commit)
        db.add(analyse)
        db.commit()
        logger.info(f"Commit {commit_hash[:7]} 分析完成，安全相关: {result.get('is_security_related')}, 最终严重性: {final_severity}")
        return True

    def analyze_unanalyzed_commits(self):
        """批量分析未分析过的 commits"""
        db = SessionLocal()
        try:
            # 查询未分析过的 commit（没有关联的 LLMAnalyse 记录）
            unanalyzed = db.query(GithubCommit).filter(GithubCommit.is_analysed == False).all()

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

    def analyze_unanalyzed_repo_commits(self,repo_id:int):
        """批量分析未分析过的 commits"""
        db = SessionLocal()
        try:
            # 查询未分析过的 commit（没有关联的 LLMAnalyse 记录）
            unanalyzed = db.query(GithubCommit).filter(GithubCommit.is_analysed == False,
                                                       GithubCommit.repo_id==repo_id).all()

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

