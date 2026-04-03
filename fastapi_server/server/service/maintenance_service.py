import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from server.service.data_collector import GitHubCollector

scheduler = BackgroundScheduler()
collector = GitHubCollector()
logger = logging.getLogger(__name__)

def start_scheduler():
    """
    定时调度器 凌晨两点同步所有仓库
    """

    #在app启动时收集一次
    collector.sync_all_repositories()
    scheduler.add_job(
        collector.sync_all_repositories,
        trigger=CronTrigger(
            hour=2,minute=0
        ),
        id = "sync_repos",
        replace_existing=True
    )
    scheduler.start()
    logger.info("调度器已启动，每天凌晨两点进行仓库爬取任务")


def shutdown_scheduler():
    """关闭调度器"""
    scheduler.shutdown()
    logger.info("调度器已关闭")