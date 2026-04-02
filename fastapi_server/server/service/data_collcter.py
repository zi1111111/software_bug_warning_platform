import logging
import os


from github import Auth
from github import Github
from server.service.models import GithubCommit
logger = logging.getLogger(__name__)


class GitHubCollector:
    def __init__(self):
        """
        初始化 GitHub 采集器
        """
        logger.info("正从.env中读取github_token")
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token:
            auth = Auth.Token(github_token)
            self.g = Github(auth=auth)
            logger.info("使用 GitHub Token 进行认证")
        else:
            self.g = Github()
            logger.warning("使用匿名 GitHub API，每小时限制 60 次请求")

    def sync_repository(self, repo_model):
     """
        同步单个仓库的最新提交
     """
     try:
         logger.info(f"开始同步仓库：{repo_model.reponame}")

     except Exception as e:
         logger.error(f"同步仓库 {repo_model.repo_name} 时发生错误: {e}")
         raise




