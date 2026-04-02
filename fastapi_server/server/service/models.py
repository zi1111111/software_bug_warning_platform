#这里是数据模型
#项目相关类别定义

from sqlalchemy import Column, Integer, String, DateTime, Text, func, Index, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship

from server.db.database import Base

class Repository(Base):
    """
    储存相关的仓库
    """
    __tablename__= "repository"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True, comment="仓库名称，如 linux-kernel")
    repo_url = Column(String(500), nullable=False, comment="Git 仓库 URL，如 https://git.kernel.org/.../linux.git")
    local_path = Column(String(500), nullable=True, comment="本地克隆路径，如 /data/linux")
    default_branch = Column(String(100), nullable=False, default="master", comment="默认分支，如 master/main")
    is_active = Column(Boolean, default=True, comment="是否启用监测")
    last_fetched_at = Column(DateTime, nullable=True, comment="最后一次拉取更新的时间")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Repository(name={self.name}, url={self.repo_url})>"

class GithubCommit(Base):
    """存储从 GitHub/Git 仓库拉取的原始 commit 记录"""
    __tablename__ = "github_commits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    commit_hash = Column(String(40), unique=True, nullable=False, index=True, comment="Git commit SHA")
    author = Column(String(255), nullable=False)
    author_email = Column(String(255), nullable=True)
    commit_date = Column(DateTime, nullable=False, index=True)
    message = Column(Text, nullable=False, comment="完整的 commit message")
    diff = Column(Text, nullable=True, comment="commit 的代码变更（可选，可能很大）")
    repo_url = Column(String(500), nullable=True, comment="来源仓库 URL")
    branch = Column(String(100), nullable=True, default="master")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关联到分析结果（一个 commit 可以有多条分析记录）
    analyses = relationship("LLMAnalyse", back_populates="commit", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<GithubCommit(commit_hash={self.commit_hash[:7]}, author={self.author})>"


class LLMAnalyse(Base):
    """存储大模型对某个 commit 的分析结果"""
    __tablename__ = "llm_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    commit_id = Column(Integer, ForeignKey("github_commits.id", ondelete="CASCADE"), nullable=False, index=True)

    # 分析结果字段
    is_security_related = Column(Boolean, default=False, index=True, comment="是否与安全相关")
    vulnerability_type = Column(String(100), nullable=True, comment="漏洞类型，如 use-after-free")
    affected_subsystem = Column(String(100), nullable=True, comment="影响的子系统，如 netfilter, bpf")
    severity = Column(
        Enum("Critical", "High", "Medium", "Low", name="severity_enum"),
        nullable=True,
        index=True,
        comment="严重程度"
    )
    cve_id = Column(String(50), nullable=True, index=True, comment="关联的 CVE 编号")
    summary = Column(Text, nullable=True, comment="一句话摘要")

    # 元数据
    model_name = Column(String(50), nullable=True, comment="使用的大模型名称，如 deepseek-chat")
    analysis_cost = Column(Integer, nullable=True, comment="API 调用消耗的 token 数或成本")
    raw_response = Column(Text, nullable=True, comment="大模型返回的原始 JSON 文本，用于审计")
    analyzed_at = Column(DateTime, server_default=func.now(), comment="分析时间")

    # 关联关系
    commit = relationship("GithubCommit", back_populates="analyses")

    def __repr__(self):
        return f"<LLMAnalyse(commit_id={self.commit_id}, security={self.is_security_related})>"

    # 添加复合索引以提升查询效率
    __table_args__ = (
        Index("ix_commit_severity", "commit_id", "severity"),
        Index("ix_is_security_date", "is_security_related", "analyzed_at"),
    )