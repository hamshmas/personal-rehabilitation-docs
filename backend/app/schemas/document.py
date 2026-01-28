"""
서류 관련 스키마
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..models.document import DocumentType, DocumentStatus, ApiSource
from ..models.case import CourtType


class DocumentCreate(BaseModel):
    """서류 생성"""
    case_id: int
    document_type: DocumentType
    file_name: str
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None


class DocumentUpload(BaseModel):
    """서류 업로드"""
    case_id: int
    document_type: DocumentType
    note: Optional[str] = None


class DocumentResponse(BaseModel):
    """서류 응답"""
    id: int
    case_id: int
    document_type: DocumentType
    document_name: str  # 한글명
    file_name: str
    file_path: str
    file_size: Optional[int]
    api_source: ApiSource
    issued_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class RequiredDocumentResponse(BaseModel):
    """필요 서류 응답"""
    id: int
    case_id: int
    document_type: DocumentType
    document_name: str  # 한글명
    is_required: bool
    status: DocumentStatus
    note: Optional[str]
    issue_guide: Optional[str]
    issue_url: Optional[str]
    is_auto_available: bool
    uploaded_document: Optional[DocumentResponse] = None

    class Config:
        from_attributes = True


class DocumentAutoRequest(BaseModel):
    """서류 자동 발급 요청"""
    case_id: int
    document_type: DocumentType
    additional_params: Optional[Dict[str, Any]] = None


class DocumentAutoResponse(BaseModel):
    """서류 자동 발급 응답"""
    success: bool
    document_type: DocumentType
    message: str
    document: Optional[DocumentResponse] = None
    api_response: Optional[Dict[str, Any]] = None


# 서류 유형 한글명 매핑
DOCUMENT_NAMES = {
    DocumentType.FAMILY_RELATION_CERT: "가족관계증명서",
    DocumentType.MARRIAGE_CERT: "혼인관계증명서",
    DocumentType.RESIDENT_REGISTER: "주민등록등본",
    DocumentType.RESIDENT_ABSTRACT: "주민등록초본",
    DocumentType.LEASE_CONTRACT: "임대차계약서",
    DocumentType.FREE_RESIDENCE_CONFIRM: "무상거주확인서",
    DocumentType.DEBT_CERTIFICATE: "부채증명서",
    DocumentType.LOCAL_TAX_CERT: "지방세 세목별 과세증명서",
    DocumentType.LAND_REGISTRY: "지적전산자료조회결과",
    DocumentType.REAL_ESTATE_REGISTER: "등기사항전부증명서",
    DocumentType.BUILDING_REGISTER: "건축물대장",
    DocumentType.LAND_REGISTER: "토지대장",
    DocumentType.VEHICLE_REGISTER: "자동차등록원부",
    DocumentType.VEHICLE_PRICE: "자동차 시가확인자료",
    DocumentType.INSURANCE_STATUS: "보험가입내역조회",
    DocumentType.INSURANCE_REFUND: "해약환급금 내역",
    DocumentType.HEALTH_INSURANCE_CERT: "건강보험자격득실확인서",
    DocumentType.PENSION_CERT: "연금산정용 가입내역확인서",
    DocumentType.INCOME_CERT: "소득금액증명",
    DocumentType.HEALTH_INSURANCE_PAYMENT: "건강보험료확인서",
    DocumentType.EMPLOYMENT_CERT: "재직증명서",
    DocumentType.SALARY_STATEMENT: "급여명세서",
    DocumentType.WITHHOLDING_TAX: "근로소득원천징수영수증",
    DocumentType.SEVERANCE_CERT: "퇴직금확인서",
    DocumentType.BUSINESS_LICENSE: "사업자등록증",
    DocumentType.VAT_CERT: "부가가치세과세표준증명",
    DocumentType.FINANCIAL_STATEMENT: "표준재무제표증명",
    DocumentType.BANK_STATEMENT: "금융계좌 거래내역서",
    DocumentType.CREDIT_CARD_STATEMENT: "신용카드 사용내역서",
    DocumentType.CREDIT_EDUCATION_CERT: "신용교육 이수증",
    DocumentType.PREVIOUS_CASE_DOCS: "과거 회생/파산 서류",
    DocumentType.DIVORCE_DOCS: "이혼 관련 서류",
    DocumentType.OTHER: "기타 서류",
}

# 발급 안내 URL
DOCUMENT_URLS = {
    DocumentType.FAMILY_RELATION_CERT: "https://www.gov.kr/mw/AA020InfoCappView.do?HighCtgCD=A01010&CappBizCD=13100000015",
    DocumentType.MARRIAGE_CERT: "https://www.gov.kr/mw/AA020InfoCappView.do?HighCtgCD=A01010&CappBizCD=13100000016",
    DocumentType.RESIDENT_REGISTER: "https://www.gov.kr/mw/AA020InfoCappView.do?HighCtgCD=A01010&CappBizCD=12500000029",
    DocumentType.RESIDENT_ABSTRACT: "https://www.gov.kr/mw/AA020InfoCappView.do?HighCtgCD=A01010&CappBizCD=12500000030",
    DocumentType.LOCAL_TAX_CERT: "https://www.wetax.go.kr",
    DocumentType.REAL_ESTATE_REGISTER: "https://www.iros.go.kr",
    DocumentType.BUILDING_REGISTER: "https://www.gov.kr/mw/AA020InfoCappView.do?HighCtgCD=A09002&CappBizCD=15000000066",
    DocumentType.LAND_REGISTER: "https://www.gov.kr/mw/AA020InfoCappView.do?HighCtgCD=A09002&CappBizCD=15000000073",
    DocumentType.VEHICLE_REGISTER: "https://www.gov.kr/mw/AA020InfoCappView.do?HighCtgCD=A09006&CappBizCD=15100000177",
    DocumentType.INSURANCE_STATUS: "https://www.credit4u.or.kr",
    DocumentType.HEALTH_INSURANCE_CERT: "https://www.nhis.or.kr",
    DocumentType.PENSION_CERT: "https://www.nps.or.kr",
    DocumentType.INCOME_CERT: "https://www.hometax.go.kr",
    DocumentType.VAT_CERT: "https://www.hometax.go.kr",
    DocumentType.FINANCIAL_STATEMENT: "https://www.hometax.go.kr",
    DocumentType.CREDIT_EDUCATION_CERT: "https://www.educredit.or.kr",
}

# API 자동 발급 가능 여부
AUTO_AVAILABLE_DOCUMENTS = {
    DocumentType.HEALTH_INSURANCE_CERT: True,  # Codef
    DocumentType.PENSION_CERT: True,  # Codef
    DocumentType.INSURANCE_STATUS: True,  # Codef
    DocumentType.REAL_ESTATE_REGISTER: True,  # Codef
    DocumentType.BUILDING_REGISTER: True,  # 공공데이터포털
    DocumentType.LAND_REGISTER: True,  # 공공데이터포털
    DocumentType.VEHICLE_REGISTER: True,  # 공공데이터포털
}


class DocumentListResponse(BaseModel):
    """서류 목록 응답"""
    items: List[DocumentResponse]
    total: int
    skip: int
    limit: int


# 법원별 필요 서류 목록
COURT_REQUIRED_DOCUMENTS: Dict[CourtType, List[DocumentType]] = {
    CourtType.DAEGU: [
        DocumentType.FAMILY_RELATION_CERT,
        DocumentType.RESIDENT_REGISTER,
        DocumentType.HEALTH_INSURANCE_CERT,
        DocumentType.PENSION_CERT,
        DocumentType.INCOME_CERT,
        DocumentType.LOCAL_TAX_CERT,
        DocumentType.LAND_REGISTRY,
        DocumentType.REAL_ESTATE_REGISTER,
        DocumentType.VEHICLE_REGISTER,
        DocumentType.INSURANCE_STATUS,
        DocumentType.BANK_STATEMENT,
        DocumentType.CREDIT_EDUCATION_CERT,
    ],
    CourtType.BUSAN: [
        DocumentType.FAMILY_RELATION_CERT,
        DocumentType.MARRIAGE_CERT,
        DocumentType.RESIDENT_REGISTER,
        DocumentType.RESIDENT_ABSTRACT,
        DocumentType.HEALTH_INSURANCE_CERT,
        DocumentType.PENSION_CERT,
        DocumentType.INCOME_CERT,
        DocumentType.HEALTH_INSURANCE_PAYMENT,
        DocumentType.LOCAL_TAX_CERT,
        DocumentType.LAND_REGISTRY,
        DocumentType.REAL_ESTATE_REGISTER,
        DocumentType.BUILDING_REGISTER,
        DocumentType.LAND_REGISTER,
        DocumentType.VEHICLE_REGISTER,
        DocumentType.VEHICLE_PRICE,
        DocumentType.INSURANCE_STATUS,
        DocumentType.INSURANCE_REFUND,
        DocumentType.BANK_STATEMENT,
        DocumentType.CREDIT_CARD_STATEMENT,
        DocumentType.CREDIT_EDUCATION_CERT,
    ],
    CourtType.DAEJEON: [
        DocumentType.FAMILY_RELATION_CERT,
        DocumentType.RESIDENT_REGISTER,
        DocumentType.HEALTH_INSURANCE_CERT,
        DocumentType.PENSION_CERT,
        DocumentType.INCOME_CERT,
        DocumentType.LOCAL_TAX_CERT,
        DocumentType.LAND_REGISTRY,
        DocumentType.REAL_ESTATE_REGISTER,
        DocumentType.VEHICLE_REGISTER,
        DocumentType.INSURANCE_STATUS,
        DocumentType.BANK_STATEMENT,
        DocumentType.CREDIT_EDUCATION_CERT,
    ],
    CourtType.JEONJU: [
        DocumentType.FAMILY_RELATION_CERT,
        DocumentType.RESIDENT_REGISTER,
        DocumentType.HEALTH_INSURANCE_CERT,
        DocumentType.PENSION_CERT,
        DocumentType.INCOME_CERT,
        DocumentType.LOCAL_TAX_CERT,
        DocumentType.LAND_REGISTRY,
        DocumentType.REAL_ESTATE_REGISTER,
        DocumentType.VEHICLE_REGISTER,
        DocumentType.INSURANCE_STATUS,
        DocumentType.BANK_STATEMENT,
        DocumentType.CREDIT_EDUCATION_CERT,
    ],
    CourtType.CHEONGJU: [
        DocumentType.FAMILY_RELATION_CERT,
        DocumentType.RESIDENT_REGISTER,
        DocumentType.HEALTH_INSURANCE_CERT,
        DocumentType.PENSION_CERT,
        DocumentType.INCOME_CERT,
        DocumentType.LOCAL_TAX_CERT,
        DocumentType.LAND_REGISTRY,
        DocumentType.REAL_ESTATE_REGISTER,
        DocumentType.VEHICLE_REGISTER,
        DocumentType.INSURANCE_STATUS,
        DocumentType.BANK_STATEMENT,
        DocumentType.CREDIT_EDUCATION_CERT,
    ],
}
