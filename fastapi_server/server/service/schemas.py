#数据验证与序列化
#定义API相关Response的输入输出数据结构
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from server.service.models import Repository

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

    #request


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
class RepositoryAddResponse:
    code: int
    message: str
