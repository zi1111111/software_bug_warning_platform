import logging
import json
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from server.service.data_collector import GitHubCollector
from server.db.database import SessionLocal
from server.service.models import Repository, LLMAnalyse, GithubCommit, AIInsightsCache
from server.service.LLM_layer import LLMAnalyzer

scheduler = BackgroundScheduler()

logger = logging.getLogger(__name__)

from server.service.analysis_service import AnalysisService


# 支持的时间范围
AI_INSIGHTS_TIME_RANGES = ['7d', '30d', '90d', 'year']


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


def analyze_and_cache_insights_for_repo(db, repo_id: int, time_range: str):
    """分析指定仓库和时间范围的AI洞察，并缓存结果"""
    logger.info(f"开始分析仓库 {repo_id}, 时间范围 {time_range}")

    try:
        start_date, end_date = get_date_range(time_range)

        # 获取时间范围内的commit messages
        commit_messages_query = db.query(GithubCommit.message).join(
            LLMAnalyse, GithubCommit.id == LLMAnalyse.commit_id
        ).filter(
            GithubCommit.repo_id == repo_id,
            LLMAnalyse.is_security_related == True,
            GithubCommit.commit_date >= start_date,
            GithubCommit.commit_date <= end_date
        ).limit(50).all()

        commit_messages = [msg[0] for msg in commit_messages_query if msg[0]]

        if not commit_messages:
            logger.info(f"仓库 {repo_id} 在 {time_range} 范围内没有安全相关的commits")
            # 创建空缓存记录
            cache_record = db.query(AIInsightsCache).filter(
                AIInsightsCache.repo_id == repo_id,
                AIInsightsCache.time_range == time_range
            ).first()

            if cache_record:
                cache_record.insights = json.dumps([])
                cache_record.common_vuln_types = json.dumps([])
                cache_record.recommendations = "该时间段内暂无安全相关提交"
                cache_record.llm_identified_count = 0
                cache_record.summary = "暂无数据"
                cache_record.analyzed_at = datetime.now()
                cache_record.commit_count = 0
            else:
                cache_record = AIInsightsCache(
                    repo_id=repo_id,
                    time_range=time_range,
                    insights=json.dumps([]),
                    common_vuln_types=json.dumps([]),
                    recommendations="该时间段内暂无安全相关提交",
                    llm_identified_count=0,
                    summary="暂无数据",
                    commit_count=0
                )
                db.add(cache_record)

            db.commit()
            return True

        # 使用LLM分析洞察
        logger.info(f"调用LLM分析 {len(commit_messages)} 条commits...")
        analyzer = LLMAnalyzer()
        insights_result = analyzer.analyze_commits_insights(commit_messages)

        # 检查是否已有缓存记录
        cache_record = db.query(AIInsightsCache).filter(
            AIInsightsCache.repo_id == repo_id,
            AIInsightsCache.time_range == time_range
        ).first()

        if cache_record:
            # 更新现有记录
            cache_record.insights = json.dumps(insights_result.get("insights", []))
            cache_record.common_vuln_types = json.dumps(insights_result.get("common_vuln_types", []))
            cache_record.recommendations = insights_result.get("recommendations", "")
            cache_record.llm_identified_count = insights_result.get("llm_identified_count", 0)
            cache_record.summary = insights_result.get("summary", "")
            cache_record.analyzed_at = datetime.now()
            cache_record.analysis_cost = insights_result.get("analysis_cost", 0)
            cache_record.commit_count = len(commit_messages)
        else:
            # 创建新记录
            cache_record = AIInsightsCache(
                repo_id=repo_id,
                time_range=time_range,
                insights=json.dumps(insights_result.get("insights", [])),
                common_vuln_types=json.dumps(insights_result.get("common_vuln_types", [])),
                recommendations=insights_result.get("recommendations", ""),
                llm_identified_count=insights_result.get("llm_identified_count", 0),
                summary=insights_result.get("summary", ""),
                analysis_cost=insights_result.get("analysis_cost", 0),
                commit_count=len(commit_messages)
            )
            db.add(cache_record)

        db.commit()
        logger.info(f"仓库 {repo_id} {time_range} 的AI洞察分析完成并缓存")
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"分析仓库 {repo_id} {time_range} 时出错: {e}")
        return False


def update_all_ai_insights():
    """更新所有活跃仓库的AI洞察分析"""
    logger.info("=" * 60)
    logger.info("开始执行AI洞察分析定时任务")
    logger.info(f"执行时间: {datetime.now()}")
    logger.info("=" * 60)

    db = SessionLocal()
    try:
        # 获取所有活跃的仓库
        repositories = db.query(Repository).filter(Repository.is_active == True).all()
        logger.info(f"找到 {len(repositories)} 个活跃仓库")

        total_success = 0
        total_failed = 0

        for repo in repositories:
            logger.info(f"\n处理仓库: {repo.name} (ID: {repo.id})")

            for time_range in AI_INSIGHTS_TIME_RANGES:
                success = analyze_and_cache_insights_for_repo(db, repo.id, time_range)
                if success:
                    total_success += 1
                else:
                    total_failed += 1

        logger.info("\n" + "=" * 60)
        logger.info("AI洞察分析定时任务完成")
        logger.info(f"成功: {total_success}, 失败: {total_failed}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"AI洞察定时任务执行出错: {e}")
    finally:
        db.close()


def start_scheduler():
    """
    定时调度器 凌晨两点同步所有仓库
    """
    # 在app启动时收集一次并交给模型分析一次
    collector = GitHubCollector()
    collector.sync_all_repositories()
    analysis_service = AnalysisService(model_type="deepseek")
    analysis_service.analyze_unanalyzed_commits()

    # 启动时执行一次AI洞察分析
    update_all_ai_insights()

    # 添加定时任务：仓库同步
    scheduler.add_job(
        collector.sync_all_repositories,
        trigger=CronTrigger(
            hour=2,minute=0
        ),
        id = "sync_repos",
        replace_existing=True
    )

    # 添加定时任务：模型分析
    scheduler.add_job(
        analysis_service.analyze_unanalyzed_commits,
        trigger=CronTrigger(
            hour=2, minute=0
        ),
        id="analyze_commits",
        replace_existing=True
    )

    # 添加定时任务：AI洞察分析（凌晨2:30执行，确保在数据同步和分析完成后）
    scheduler.add_job(
        update_all_ai_insights,
        trigger=CronTrigger(
            hour=2, minute=30
        ),
        id="ai_insights_analysis",
        replace_existing=True
    )

    scheduler.start()
    logger.info("调度器已启动，每天凌晨2:00进行仓库爬取和模型分析，2:30进行AI洞察分析")


def shutdown_scheduler():
    """关闭调度器"""
    scheduler.shutdown()
    logger.info("调度器已关闭")