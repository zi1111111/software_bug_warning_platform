"""
用户服务路由
包含：注册、登录、验证码发送、获取当前用户
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.service import models, schemas
from server.service.auth_utils import (
    get_password_hash, verify_password, create_access_token, get_current_user
)
from server.service.email_utils import send_verification_email, verify_email_code

router = APIRouter(prefix="/user", tags=["用户认证"])


@router.post("/send-verification-code", response_model=schemas.MessageResponse)
def send_verification_code(request: schemas.EmailVerificationRequest, db: Session = Depends(get_db)):
    """发送邮箱验证码"""
    # 检查邮箱是否已注册
    existing_user = db.query(models.User).filter(models.User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册"
        )

    # 发送验证码
    if send_verification_email(request.email):
        return schemas.MessageResponse(code=200, message="验证码已发送，请查收邮件")
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证码发送失败，请稍后重试"
        )


@router.post("/register", response_model=schemas.Token)
def register(user: schemas.UserCreateWithVerification, db: Session = Depends(get_db)):
    """带邮箱验证的用户注册"""
    # 1. 验证邮箱验证码
    if not verify_email_code(user.email, user.verification_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误或已过期"
        )

    # 2. 检查邮箱是否已存在
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )

    # 3. 创建新用户
    hashed_password = get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        is_active=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 4. 创建访问令牌
    access_token = create_access_token(data={"email": new_user.email})

    return schemas.Token(
        access_token=access_token,
        token_type="bearer",
        user=schemas.UserResponse(
            id=new_user.id,
            email=new_user.email,
            created_at=new_user.created_at
        )
    )


@router.post("/login", response_model=schemas.Token)
def login(login_data: schemas.UserLogin, db: Session = Depends(get_db)):
    """密码登录"""
    # 查询用户
    user = db.query(models.User).filter(models.User.email == login_data.email).first()

    # 验证用户存在
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证用户状态
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )

    # 验证密码
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 创建访问令牌
    access_token = create_access_token(data={"email": user.email})

    return schemas.Token(
        access_token=access_token,
        token_type="bearer",
        user=schemas.UserResponse(
            id=user.id,
            email=user.email,
            created_at=user.created_at
        )
    )


@router.post("/login-with-code", response_model=schemas.Token)
def login_with_code(login_data: schemas.UserLoginValidCode, db: Session = Depends(get_db)):
    """验证码登录（无需密码）"""
    # 验证邮箱验证码
    if not verify_email_code(login_data.email, login_data.verification_code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="验证码错误或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 查询用户是否存在
    user = db.query(models.User).filter(models.User.email == login_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在，请先注册",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证用户状态
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )

    # 创建访问令牌
    access_token = create_access_token(data={"email": user.email})

    return schemas.Token(
        access_token=access_token,
        token_type="bearer",
        user=schemas.UserResponse(
            id=user.id,
            email=user.email,
            created_at=user.created_at
        )
    )


@router.post("/send-login-code", response_model=schemas.MessageResponse)
def send_login_code(request: schemas.EmailVerificationRequest, db: Session = Depends(get_db)):
    """发送登录验证码（用于验证码登录）"""
    # 检查用户是否存在
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在，请先注册"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )

    # 发送验证码
    if send_verification_email(request.email):
        return schemas.MessageResponse(code=200, message="验证码已发送，请查收邮件")
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证码发送失败，请稍后重试"
        )


@router.get("/me", response_model=schemas.GetCurrentUserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return schemas.GetCurrentUserResponse(
        code=200,
        user=schemas.UserResponse(
            id=current_user.id,
            email=current_user.email,
            created_at=current_user.created_at
        )
    )


@router.post("/logout", response_model=schemas.MessageResponse)
def logout():
    """用户退出登录（前端清除token即可，后端可扩展黑名单功能）"""
    return schemas.MessageResponse(code=200, message="退出成功")
