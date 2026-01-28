"""
사건 관련 스키마
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from ..models.case import CourtType, CaseStatus


class CaseCreate(BaseModel):
    """사건 생성"""
    client_id: int
    court_type: CourtType
    memo: Optional[str] = None


class CaseUpdate(BaseModel):
    """사건 수정"""
    court_type: Optional[CourtType] = None
    case_number: Optional[str] = None
    status: Optional[CaseStatus] = None
    memo: Optional[str] = None


class CaseResponse(BaseModel):
    """사건 응답"""
    id: int
    client_id: int
    client_name: str
    court_type: CourtType
    court_name: str  # 법원 한글명
    case_number: Optional[str]
    status: CaseStatus
    status_name: str  # 상태 한글명
    memo: Optional[str]
    created_at: datetime

    # 서류 현황
    total_documents: int = 0
    completed_documents: int = 0
    progress_percent: float = 0.0

    class Config:
        from_attributes = True


class CaseDetail(CaseResponse):
    """사건 상세"""
    required_documents: List["RequiredDocumentSummary"] = []


class RequiredDocumentSummary(BaseModel):
    """필요 서류 요약"""
    id: int
    document_type: str
    document_name: str  # 한글명
    is_required: bool
    status: str
    is_auto_available: bool
    issue_url: Optional[str]


# 법원 한글명 매핑
COURT_NAMES = {
    CourtType.DAEGU: "대구지방법원",
    CourtType.BUSAN: "부산회생법원",
    CourtType.DAEJEON: "대전지방법원",
    CourtType.JEONJU: "전주지방법원",
    CourtType.CHEONGJU: "청주지방법원",
}

# 상태 한글명 매핑
STATUS_NAMES = {
    CaseStatus.PREPARING: "서류 준비 중",
    CaseStatus.SUBMITTED: "신청서 제출",
    CaseStatus.REVIEWING: "심사 중",
    CaseStatus.APPROVED: "개시결정",
    CaseStatus.COMPLETED: "완료",
    CaseStatus.REJECTED: "기각",
}


class CaseListResponse(BaseModel):
    """사건 목록 응답"""
    items: list[CaseResponse]
    total: int
    skip: int
    limit: int
