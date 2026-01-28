"""
사건(케이스) 모델
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from ..core.database import Base


class CourtType(str, enum.Enum):
    """관할 법원"""
    DAEGU = "daegu"  # 대구지방법원
    BUSAN = "busan"  # 부산회생법원
    DAEJEON = "daejeon"  # 대전지방법원
    JEONJU = "jeonju"  # 전주지방법원
    CHEONGJU = "cheongju"  # 청주지방법원


class CaseStatus(str, enum.Enum):
    """사건 상태"""
    PREPARING = "preparing"  # 서류 준비 중
    SUBMITTED = "submitted"  # 신청서 제출
    REVIEWING = "reviewing"  # 심사 중
    APPROVED = "approved"  # 개시결정
    COMPLETED = "completed"  # 완료
    REJECTED = "rejected"  # 기각


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 사건 정보
    court_type = Column(Enum(CourtType), nullable=False)
    case_number = Column(String(50), nullable=True)  # 사건번호 (접수 후)
    status = Column(Enum(CaseStatus), default=CaseStatus.PREPARING)

    # 메모
    memo = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계
    client = relationship("Client", back_populates="cases")
    created_by = relationship("User", foreign_keys=[created_by_id])
    required_documents = relationship("RequiredDocument", back_populates="case", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="case", cascade="all, delete-orphan")
