#数据验证与序列化
#定义API相关Response的输入输出数据结构
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from server.service.models import Repository, LLMAnalyse


# request
class RepositoryOut(BaseModel):
    id: int
    name: str
    repo_url: str
    default_branch: str
    is_active: bool
    last_fetched_at: Optional[datetime] = None
    created_at: datetime
    vuln_count:int
    class Config:
        from_attributes = True

class LLMAnalyseOut(BaseModel):
    id: int
    vulnerability_type: Optional[str] = None
    affected_subsystem: Optional[str] = None
    severity: Optional[str] = None
    cve_id: Optional[str] = None
    summary: str
    model_name: Optional[str] = None
    analyzed_at: str


class AnalyzeRepo(BaseModel):
    id:int


class GetVulnStats(BaseModel):
    id:int

class RepositoryAdd(BaseModel):
    name : str
    repo_url : str
    default_branch : str
    is_active : bool

class RepositoryDelete(BaseModel):
    id:int

class RepositoryChange(BaseModel):
    id:int
    default_branch: str
    is_active: bool

class SearchCommit(BaseModel):
    id:int

class GetVulnerabilities(BaseModel):
    id:int
    page:int
    page_size:int
    severity: Optional[str] = None

 #response
class RepositoryDeleteResponse(BaseModel):
    code : int
    message : str

class RepositoryGetAllResponse(BaseModel):
    code:   int
    repositories:   List[RepositoryOut]

class RepositoryChangeResponse(BaseModel):
    code:   int
    message:    str

class SearchCommitResponse(BaseModel):
    code:int

class RepositoryAddResponse(BaseModel):
    code: int
    message: str

class GetVulnStatsResponse(BaseModel):
    code:int
    stats:dict


class GetVulnerabilitiesResponse(BaseModel):
    code:int
    vulnList: List[LLMAnalyseOut]
    total:int

class AnalyzeRepoResponse(BaseModel):
    code:int