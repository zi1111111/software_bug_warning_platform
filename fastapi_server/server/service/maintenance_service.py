import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from server.service.data_collector import GitHubCollector
from server.db.database import SessionLocal
from server.service.models import Repository
from server.service.LLM_layer import analyze_and_cache_insights

scheduler = BackgroundScheduler()
logger = logging.getLogger(__name__)

from server.service.analysis_service import AnalysisService

# 支持的时间范围
AI_INSIGHTS_TIME_RANGES = ['7d', '30d', '90d', 'year']


def update_all_ai_insights():
    """更新所有活跃仓库的AI洞察分析"""
    logger.info("开始执行AI洞察分析定时任务")

    db = SessionLocal()
    try:
        repositories = db.query(Repository).filter(Repository.is_active == True).all()
        logger.info(f"找到 {len(repositories)} 个活跃仓库")

        total_success = 0
        total_failed = 0

        for repo in repositories:
            for time_range in AI_INSIGHTS_TIME_RANGES:
                success = analyze_and_cache_insights(db, repo.id, time_range)
                if success:
                    total_success += 1
                else:
                    total_failed += 1

        logger.info(f"AI洞察分析完成: 成功{total_success}, 失败{total_failed}")

    except Exception as e:
        logger.error(f"AI洞察定时任务出错: {e}")
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