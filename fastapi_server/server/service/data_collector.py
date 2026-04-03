import datetime
import logging
import os

import pytz
from github import Auth
from github import Github


from server.db.database import SessionLocal
from server.service.models import GithubCommit,Repository
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

    def sync_repository(self, repo_model: Repository):
        db = SessionLocal()  # 直接创建会话
        try:
            logger.info(f"开始同步仓库：{repo_model.name}")
            repo_path = repo_model.repo_url.replace("https://github.com/", "").strip("/")
            github_repo = self.g.get_repo(repo_path)
            branch_name = repo_model.default_branch
            branch = github_repo.get_branch(branch_name)
            since_param = None
            if repo_model.last_fetched_at:
                since_param = repo_model.last_fetched_at.replace(tzinfo=datetime.timezone.utc)
            # 获取最近 200 个提交
            commits = list(github_repo.get_commits(sha=branch.commit.sha,since=since_param))[:200]
            new_commits = []
            for item in commits:
                exists = db.query(GithubCommit).filter(
                    GithubCommit.commit_hash == item.sha
                ).first()
                if exists:
                    continue

                # 获取完整的 commit 信息（含 files）
                full_commit = github_repo.get_commit(item.sha)
                diff_parts = []
                if full_commit.files:
                    for file in full_commit.files:
                        if file.patch:
                            diff_parts.append(f"--- a/{file.filename}\n+++ b/{file.filename}\n{file.patch}")
                diff_text = "\n".join(diff_parts)

                gm = GithubCommit(
                    commit_hash=item.sha,
                    author=full_commit.commit.author.name or "Unknown",
                    author_email=full_commit.commit.author.email or "",
                    commit_date=full_commit.commit.author.date,
                    message=full_commit.commit.message or "",
                    diff=diff_text,
                    repo_url=repo_model.repo_url,
                    branch=branch_name,
                )
                new_commits.append(gm)

            if new_commits:
                db.add_all(new_commits)
                repo = db.query(Repository).filter(Repository.id == repo_model.id).first()
                repo.last_fetched_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
                db.add(repo)
                db.commit()
                logger.info(f"仓库 {repo_model.name} 新增 {len(new_commits)} 个提交")
            else:
                logger.info(f"仓库 {repo_model.name} 没有新的提交")
        except Exception as e:
            db.rollback()
            logger.error(f"同步仓库 {repo_model.name} 时发生错误: {e}")
            raise
        finally:
            db.close()

    def sync_all_repositories(self):
        db = SessionLocal()
        try:
            repos = db.query(Repository).filter(Repository.is_active ==True).all()
            logger.info(f"开始同步{len(repos)} 个活跃仓库")
            for repo in repos:
                try:
                    self.sync_repository(repo)
                except Exception as e:
                    logger.info(f"同步仓库{repo.name}失败：{e}",exc_info=True)
        finally:
            db.close()

