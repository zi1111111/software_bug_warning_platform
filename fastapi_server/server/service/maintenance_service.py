import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from server.service.data_collector import GitHubCollector

scheduler = BackgroundScheduler()

logger = logging.getLogger(__name__)

from server.service.analysis_service import AnalysisService


def start_scheduler():
    """
    定时调度器 凌晨两点同步所有仓库
    """
    # 在app启动时收集一次并交给模型分析一次
    collector = GitHubCollector()
    collector.sync_all_repositories()
    analysis_service = AnalysisService(model_type="deepseek")
    analysis_service.analyze_unanalyzed_commits()
    scheduler.add_job(
        collector.sync_all_repositories,
        trigger=CronTrigger(
            hour=2,minute=0
        ),
        id = "sync_repos",
        replace_existing=True
    )
    scheduler.add_job(
        analysis_service.analyze_unanalyzed_commits,
        trigger=CronTrigger(
            hour=2, minute=0
        ),
        id="sync_repos",
        replace_existing=True
    )
    scheduler.start()
    logger.info("调度器已启动，每天凌晨两点进行仓库爬取任务和模型分析任务")


def shutdown_scheduler():
    """关闭调度器"""
    scheduler.shutdown()
    logger.info("调度器已关闭")