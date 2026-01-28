"""
의뢰인 관련 스키마
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class ClientCreate(BaseModel):
    """의뢰인 생성"""
    name: str
    resident_number: Optional[str] = None  # 주민번호 (암호화 저장됨)
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    memo: Optional[str] = None


class ClientUpdate(BaseModel):
    """의뢰인 수정"""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    memo: Optional[str] = None


class ClientResponse(BaseModel):
    """의뢰인 응답"""
    id: int
    name: str
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    memo: Optional[str]
    has_codef_connection: bool = False  # Codef 연동 여부
    created_at: datetime

    class Config:
        from_attributes = True


class ClientDetail(ClientResponse):
    """의뢰인 상세 (주민번호 마스킹 포함)"""
    resident_number_masked: Optional[str] = None  # 마스킹된 주민번호


class ClientListResponse(BaseModel):
    """의뢰인 목록 응답"""
    items: list[ClientResponse]
    total: int
    skip: int
    limit: int
