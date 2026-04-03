import datetime
import pytz
from fastapi import APIRouter, Depends,HTTPException


from server.db.database import get_db
from server.service.models import Repository
from server.service.schemas import RepositoryAdd, RepositoryAddResponse
from sqlalchemy.orm import Session
router = APIRouter()



@router.post("/addRepository",response_model=RepositoryAddResponse)
async def add_repository(
        request:RepositoryAdd,
        db: Session = Depends(get_db)
):

    #检查是否已经存在该URL和branch
    existing = db.query(Repository).filter(Repository.repo_url == request.repo_url,
                                           Repository.default_branch == request.default_branch).first()
    if existing:
        raise HTTPException(status_code = 400,detail="该仓库分支已存在")

    #添加对象
    repo = Repository(
        name = request.name,
        repo_url = request.repo_url,
        default_branch = request.default_branch,
        is_active = request.is_active,
        last_fetched_at = None,

    )
    db.add(repo)
    db.commit()
    res = {
        'code':200,
        'message':"添加成功！"
    }
    return res

