"""
用户认证相关工具函数
包含：JWT处理、密码哈希验证
"""

import jwt
from jwt import ExpiredSignatureError, PyJWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
from fastapi import HTTPException, status, Depends, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.service import models

load_dotenv()

# 配置加载
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "240"))

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Token 数据结构模型
class TokenData(BaseModel):
    email: str | None = None


# ------------------ 密码处理函数 ------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码与哈希是否匹配"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码的bcrypt哈希"""
    return pwd_context.hash(password)


# ------------------ JWT 处理函数 ------------------
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """创建JWT访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "sub": data.get("email", "")
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """解码JWT令牌，验证签名和过期时间"""
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub"]}
        )
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"无效的Token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ------------------ FastAPI依赖函数 ------------------
async def get_token_from_header(authorization: str = Header(None)) -> str:
    """从HTTP Header中提取Bearer Token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证信息或格式错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return authorization[7:]  # 去掉 "Bearer " 前缀


async def get_current_user(
    token: str = Depends(get_token_from_header),
    db: Session = Depends(get_db)
) -> models.User:
    """获取当前登录用户，用于保护需要认证的接口"""
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token中缺少用户信息",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户已被禁用"
            )
        return user

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"认证失败: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# 可选：获取当前用户（不强制要求登录）
async def get_optional_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> models.User | None:
    """获取当前用户，如果未登录则返回None"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    try:
        token = authorization[7:]
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            return None
        
        user = db.query(models.User).filter(models.User.email == email).first()
        return user
    except:
        return None
