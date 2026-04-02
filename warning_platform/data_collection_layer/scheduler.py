
import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util

logger = logging.getLogger(__name__)


def start_collector():
    """启动 GitHub 数据采集任务"""
    from .git_collector import GitHubCollector
    from dotenv import load_dotenv

    load_dotenv()
    github_token = os.getenv("GITHUB_TOKEN")

    collector = GitHubCollector(github_token)
    collector.sync_all_repositories()


@util.close_old_connections
def delete_old_job_executions(max_age=604800):
    """删除超过7天的任务执行记录"""
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


def start_scheduler():
    """启动定时任务调度器"""
    scheduler = BackgroundScheduler()

    # 使用 DjangoJobStore 存储任务到数据库
    scheduler.add_jobstore(DjangoJobStore(), "default")

    # 添加每日凌晨1点执行的任务
    scheduler.add_job(
        start_collector,
        trigger=CronTrigger(hour=1, minute=0),  # 每天凌晨1点
        id="daily_git_collection",
        max_instances=1,
        replace_existing=True,
    )
    logger.info("已添加每日凌晨1点的数据采集任务")

    # 添加每周清理任务
    scheduler.add_job(
        delete_old_job_executions,
        trigger=CronTrigger(day_of_week="mon", hour=0, minute=0),  # 每周一凌晨
        id="delete_old_job_executions",
        max_instances=1,
        replace_existing=True,
    )

    try:
        logger.info("启动定时任务调度器...")
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("停止定时任务调度器...")
        scheduler.shutdown()