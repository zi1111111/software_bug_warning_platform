import logging
from github import Auth
from github import Github

logger = logging.getLogger(__name__)


class GitHubCollector:
    def __init__(self, github_token=None):
        """
        初始化 GitHub 采集器
        """
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
        from django.utils import timezone
        from data_collection_layer.models import Commit, FileChange

        try:
            logger.info(f"开始同步仓库: {repo_model.repo_name}")

            # 解析 GitHub URL
            repo_path = repo_model.repo_url.replace("https://github.com/", "").strip("/")

            # 获取 GitHub 仓库对象
            github_repo = self.g.get_repo(repo_path)

            # 获取分支
            branch = github_repo.get_branch(repo_model.branch)

            # 获取最新提交
            new_commits = []

            # 如果已经有最后同步的 commit，则从该 commit 开始获取新提交
            if repo_model.last_sync_commit:
                try:
                    last_commit = github_repo.get_commit(repo_model.last_sync_commit)
                    commits = github_repo.get_commits(sha=branch.commit.sha, since=last_commit.commit.committer.date)
                except Exception as e:
                    logger.warning(f"无法获取最后提交 {repo_model.last_sync_commit}，将获取最新提交: {e}")
                    commits = github_repo.get_commits(sha=branch.commit.sha)
            else:
                commits = github_repo.get_commits(sha=branch.commit.sha)[:50]

            # 遍历所有提交
            for commit in commits:
                # 检查是否已存在该提交
                if Commit.objects.filter(repository=repo_model, commit_hash=commit.sha).exists():
                    continue

                # 处理提交者信息
                author_name = commit.commit.author.name if commit.commit.author else "Unknown"
                author_email = commit.commit.author.email if commit.commit.author else ""

                # 获取文件列表并计算数量
                files_list = list(commit.files)  # 转换为列表
                files_changed = len(files_list) if files_list else 0

                # 创建并保存 Commit 记录
                commit_model = Commit.objects.create(
                    repository=repo_model,
                    commit_hash=commit.sha,
                    author_name=author_name[:200],
                    author_email=author_email,
                    commit_date=commit.commit.author.date if commit.commit.author else timezone.now(),
                    commit_message=commit.commit.message[:5000] if commit.commit.message else "",
                    files_changed=files_changed,
                    lines_added=commit.stats.additions,
                    lines_deleted=commit.stats.deletions,
                    github_url=commit.html_url,
                    is_analyzed=False
                )

                new_commits.append(commit_model)

                # 保存文件变更信息
                file_changes_to_create = []
                for file in files_list:
                    # 确定变更类型
                    if file.status == "added":
                        change_type = "ADD"
                    elif file.status == "modified":
                        change_type = "MODIFY"
                    elif file.status == "removed":
                        change_type = "DELETE"
                    else:
                        change_type = "MODIFY"

                    # 创建 FileChange 对象
                    file_change = FileChange(
                        commit=commit_model,
                        file_path=file.filename[:500],
                        change_type=change_type,
                        lines_added=file.additions,
                        lines_deleted=file.deletions
                    )
                    file_changes_to_create.append(file_change)

                # 批量保存 FileChange 记录
                if file_changes_to_create:
                    FileChange.objects.bulk_create(file_changes_to_create)

            # 更新仓库的最后同步信息
            if new_commits:
                repo_model.last_sync_commit = new_commits[0].commit_hash
                repo_model.lasy_sync_time = timezone.now()
                repo_model.save()

                logger.info(f"仓库 {repo_model.repo_name} 新增 {len(new_commits)} 个提交")
                return len(new_commits)
            else:
                logger.info(f"仓库 {repo_model.repo_name} 没有新的提交")
                return 0

        except Exception as e:
            logger.error(f"同步仓库 {repo_model.repo_name} 时发生错误: {e}")
            raise

    def sync_all_repositories(self):
        """同步所有活跃的仓库"""
        from data_collection_layer.models import Repository, SyncLog

        repositories = Repository.objects.filter(is_active=True)

        if not repositories:
            logger.warning("没有活跃的仓库需要同步")
            return

        logger.info("开始同步所有仓库...")

        for repo in repositories:
            try:
                # 创建同步日志记录
                sync_log = SyncLog(
                    repository=repo,
                    success=True
                )

                # 执行同步
                new_commits_count = self.sync_repository(repo)
                sync_log.new_commits_count = new_commits_count
                sync_log.save()

                logger.info(f"仓库 {repo.repo_name} 同步完成，新增 {new_commits_count} 个提交")

            except Exception as e:
                logger.error(f"同步仓库 {repo.repo_name} 失败: {e}")
                sync_log = SyncLog(
                    repository=repo,
                    success=False,
                    error_message=str(e)[:500]
                )
                sync_log.save()

        logger.info("所有仓库同步完成")