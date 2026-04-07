from django.db.models.expressions import result
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, desc
from twisted.conch.ssh.connection import messages

from server.db.database import get_db
from server.service.analysis_service import AnalysisService
from server.service.data_collector import GitHubCollector
from server.service.models import Repository, LLMAnalyse, GithubCommit
from server.service.schemas import RepositoryAdd, RepositoryAddResponse, RepositoryDelete, RepositoryDeleteResponse, \
    RepositoryGetAllResponse, RepositoryOut, RepositoryChangeResponse, RepositoryChange, SearchCommitResponse, \
    SearchCommit, GetVulnStats, GetVulnStatsResponse, GetVulnerabilities, GetVulnerabilitiesResponse, LLMAnalyseOut, \
    AnalyzeRepo, AnalyzeRepoResponse
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

@router.post("/getVulnStats",response_model=GetVulnStatsResponse)
async def get_vuln_stats(
        request:GetVulnStats,
        db:Session=Depends(get_db)
):
    gcs = db.query(GithubCommit).filter(GithubCommit.repo_id == request.id).all()
    llms = []

    for gc in gcs:
        llm = db.query(LLMAnalyse).filter(LLMAnalyse.commit_id==gc.id,LLMAnalyse.is_security_related==True).all()
        llms.extend(llm)

    result = {
        'totalVulns': 0,
        'critical': 0,
        'high': 0,
        'medium': 0,
        'low': 0,
    }
    for l in llms:
        result['totalVulns']+=1
        if l.severity:
            if l.severity == "Critical":
                result['critical']+=1
            elif l.severity == "High":
                result['high']+=1
            elif l.severity =="Medium":
                result['medium']+=1
            elif l.severity =="Low":
                result['low'] +=1
        else:
            continue
    return GetVulnStatsResponse(
        code=200,
        stats=result
    )


@router.post("/getVulnerabilities", response_model=GetVulnerabilitiesResponse)
async def get_vulnerabilities(
        request: GetVulnerabilities,
        db: Session = Depends(get_db)
):
    query = db.query(LLMAnalyse).join(
        GithubCommit, LLMAnalyse.commit_id == GithubCommit.id
    ).filter(
        GithubCommit.repo_id == request.id,
        LLMAnalyse.is_security_related == True
    )

    # 严重程度过滤（如果提供了 severity 且非空）
    if request.severity:
        query = query.filter(LLMAnalyse.severity == request.severity)

    # 获取总记录数
    total = query.count()

    # 分页 + 按 commit 日期倒序排序（最新的在前）
    query = query.order_by(desc(GithubCommit.created_at)).offset(
        (request.page - 1) * request.page_size
    ).limit(request.page_size)

    llms = query.all()

    # 转换为响应模型列表
    vuln_list = []
    for llm in llms:
        vuln_list.append(LLMAnalyseOut(
            id=llm.id,
            vulnerability_type=llm.vulnerability_type,
            affected_subsystem=llm.affected_subsystem,
            severity=llm.severity,
            cve_id=llm.cve_id,
            summary=llm.summary,
            model_name=llm.model_name,
            analyzed_at=llm.analyzed_at.isoformat() if hasattr(llm.analyzed_at, 'isoformat') else str(llm.analyzed_at)
        ))

    return GetVulnerabilitiesResponse(
        code=200,
        vulnList=vuln_list,
        total = total
    )

@router.post("/analyzeRepo", response_model=AnalyzeRepoResponse)
async def analyze_repo(
        request:AnalyzeRepo,
):
    analysis_service =  AnalysisService()
    analysis_service.analyze_unanalyzed_repo_commits(request.id)

    return AnalyzeRepoResponse(
        code=200
    )







