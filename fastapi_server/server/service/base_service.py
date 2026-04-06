
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from twisted.conch.ssh.connection import messages

from server.db.database import get_db
from server.service.data_collector import GitHubCollector
from server.service.models import Repository, LLMAnalyse, GithubCommit
from server.service.schemas import RepositoryAdd, RepositoryAddResponse, RepositoryDelete, RepositoryDeleteResponse, \
    RepositoryGetAllResponse, RepositoryOut, RepositoryChangeResponse, RepositoryChange, SearchCommitResponse, \
    SearchCommit
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/addRepository", response_model=RepositoryAddResponse)
async def add_repository(
        request: RepositoryAdd,
        db: Session = Depends(get_db)
):
    #检查是否已经存在该URL和branch
    existing = db.query(Repository).filter(Repository.repo_url == request.repo_url,
                                           Repository.default_branch == request.default_branch).first()
    if existing:
        raise HTTPException(status_code=400, detail="该仓库分支已存在")

    #添加对象
    repo = Repository(
        name=request.name,
        repo_url=request.repo_url,
        default_branch=request.default_branch,
        is_active=request.is_active,
        last_fetched_at=None,
    )
    db.add(repo)
    db.commit()
    res = RepositoryAddResponse(
        code=200,
        message="添加成功"
    )
    return res


@router.post("/deleteRepository",response_model=RepositoryDeleteResponse)
async def delete_repository(
        request: RepositoryDelete,
        db: Session = Depends(get_db)
):
    #定义数据时采用了级联删除
    repo = db.query(Repository).filter(Repository.id == request.id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="仓库不存在")
    db.delete(repo)
    db.commit()
    res = RepositoryDeleteResponse(
        code=200,
        message="删除成功"
    )
    return res


@router.get("/getAllRepositories", response_model=RepositoryGetAllResponse)
async def get_all_repositories(db: Session = Depends(get_db)):
    repos = db.query(Repository).all()
    repos_out = []

    for repo in repos:
        count = 0
        gms = db.query(GithubCommit).filter(GithubCommit.repo_id == repo.id)
        for gm in gms:
            las = db.query(LLMAnalyse).filter(LLMAnalyse.commit_id == gm.id,LLMAnalyse.is_security_related==True).all()
            count += len(las)
        repo_out = RepositoryOut(
            id=repo.id,
            name = repo.name,
            repo_url=repo.repo_url,
            default_branch=repo.default_branch,
            is_active=repo.is_active,
            last_fetched_at=repo.last_fetched_at,
            created_at=repo.created_at,
            vuln_count=count
        )
        repos_out.append(repo_out)
    return RepositoryGetAllResponse(code=200, repositories=repos_out)


@router.post("/changeRepository",response_model=RepositoryChangeResponse)
async def change_repository(
        request:RepositoryChange,
        db:Session = Depends(get_db)
):
    repo = db.query(Repository).filter(Repository.id == request.id).first()
    if not  repo:
        raise HTTPException(status_code=404,detail="仓库不存在")

    if request.default_branch is not None:
        repo.default_branch = request.default_branch

    if request.is_active is not None:
        repo.is_active = request.is_active
    db.commit()
    return RepositoryChangeResponse(
        code = 200,
        message ="修改成功"
    )

@router.post("/searchCommit",response_model=SearchCommitResponse)
async def search_commit(
        request:SearchCommit,
        db:Session=Depends(get_db)
):
    collector = GitHubCollector()
    repo = db.query(Repository).filter(Repository.id == request.id).first()
    collector.sync_repository(repo)
    return SearchCommitResponse(
        code=200
    )



