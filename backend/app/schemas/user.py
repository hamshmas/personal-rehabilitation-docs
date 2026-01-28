"""
사용자 관련 스키마
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from ..models.user import UserRole


class UserCreate(BaseModel):
    """사용자 생성"""
    email: EmailStr
    password: str
    name: str
    role: UserRole = UserRole.STAFF


class UserLogin(BaseModel):
    """로그인"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """사용자 응답"""
    id: int
    email: str
    name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT 토큰"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """토큰 데이터"""
    user_id: Optional[int] = None
    email: Optional[str] = None
