"""
서류 관련 모델
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from ..core.database import Base


class DocumentType(str, enum.Enum):
    """서류 유형"""
    # 인적사항 및 주거 관련
    FAMILY_RELATION_CERT = "family_relation_cert"  # 가족관계증명서
    MARRIAGE_CERT = "marriage_cert"  # 혼인관계증명서
    RESIDENT_REGISTER = "resident_register"  # 주민등록등본
    RESIDENT_ABSTRACT = "resident_abstract"  # 주민등록초본
    LEASE_CONTRACT = "lease_contract"  # 임대차계약서
    FREE_RESIDENCE_CONFIRM = "free_residence_confirm"  # 무상거주확인서

    # 채무 관련
    DEBT_CERTIFICATE = "debt_certificate"  # 부채증명서

    # 재산 관련 - 과세
    LOCAL_TAX_CERT = "local_tax_cert"  # 지방세 세목별 과세증명서

    # 재산 관련 - 부동산
    LAND_REGISTRY = "land_registry"  # 지적전산자료조회결과
    REAL_ESTATE_REGISTER = "real_estate_register"  # 등기사항전부증명서
    BUILDING_REGISTER = "building_register"  # 건축물대장
    LAND_REGISTER = "land_register"  # 토지대장

    # 재산 관련 - 자동차
    VEHICLE_REGISTER = "vehicle_register"  # 자동차등록원부
    VEHICLE_PRICE = "vehicle_price"  # 자동차 시가확인자료

    # 재산 관련 - 보험
    INSURANCE_STATUS = "insurance_status"  # 보험가입내역조회
    INSURANCE_REFUND = "insurance_refund"  # 해약환급금 내역

    # 소득 관련 - 일반
    HEALTH_INSURANCE_CERT = "health_insurance_cert"  # 건강보험자격득실확인서
    PENSION_CERT = "pension_cert"  # 연금산정용 가입내역확인서
    INCOME_CERT = "income_cert"  # 소득금액증명
    HEALTH_INSURANCE_PAYMENT = "health_insurance_payment"  # 건강보험료확인서

    # 소득 관련 - 급여
    EMPLOYMENT_CERT = "employment_cert"  # 재직증명서
    SALARY_STATEMENT = "salary_statement"  # 급여명세서
    WITHHOLDING_TAX = "withholding_tax"  # 근로소득원천징수영수증
    SEVERANCE_CERT = "severance_cert"  # 퇴직금확인서

    # 소득 관련 - 영업
    BUSINESS_LICENSE = "business_license"  # 사업자등록증
    VAT_CERT = "vat_cert"  # 부가가치세과세표준증명
    FINANCIAL_STATEMENT = "financial_statement"  # 표준재무제표증명

    # 기타
    BANK_STATEMENT = "bank_statement"  # 금융계좌 거래내역서
    CREDIT_CARD_STATEMENT = "credit_card_statement"  # 신용카드 사용내역서
    CREDIT_EDUCATION_CERT = "credit_education_cert"  # 신용교육 이수증
    PREVIOUS_CASE_DOCS = "previous_case_docs"  # 과거 회생/파산 서류
    DIVORCE_DOCS = "divorce_docs"  # 이혼 관련 서류

    # 기타 첨부
    OTHER = "other"  # 기타 서류


class DocumentStatus(str, enum.Enum):
    """서류 상태"""
    NOT_STARTED = "not_started"  # 미시작
    IN_PROGRESS = "in_progress"  # 진행 중
    COMPLETED = "completed"  # 완료
    REQUIRED = "required"  # 필요
    NOT_REQUIRED = "not_required"  # 해당없음


class ApiSource(str, enum.Enum):
    """API 출처"""
    MANUAL = "manual"  # 수동 업로드
    CODEF = "codef"  # Codef API
    DATA_GO_KR = "data_go_kr"  # 공공데이터포털


class RequiredDocument(Base):
    """사건별 필요 서류 목록"""
    __tablename__ = "required_documents"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    is_required = Column(Boolean, default=True)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.NOT_STARTED)
    note = Column(Text, nullable=True)  # 비고
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)  # 업로드된 서류

    # 발급 안내 정보
    issue_guide = Column(Text, nullable=True)  # 발급 방법 안내
    issue_url = Column(String(500), nullable=True)  # 발급 링크
    is_auto_available = Column(Boolean, default=False)  # API 자동 발급 가능 여부

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계
    case = relationship("Case", back_populates="required_documents")
    document = relationship("Document", foreign_keys=[document_id])


class Document(Base):
    """발급된/업로드된 서류"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # 파일 정보
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)

    # API 발급 정보
    api_source = Column(String(50), default="manual_upload")  # manual_upload, hyphen, etc.
    api_response = Column(JSON, nullable=True)  # API 응답 원본

    # 메타데이터
    issued_at = Column(DateTime(timezone=True), nullable=True)  # 발급일
    valid_until = Column(DateTime(timezone=True), nullable=True)  # 유효기간

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계
    case = relationship("Case", back_populates="documents")
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_id])
