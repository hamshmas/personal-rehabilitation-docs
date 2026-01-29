"""
서류 관리 API 라우터
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import aiofiles
import os
from datetime import datetime

from ..core.database import get_db
from ..core.security import get_current_user
from ..core.config import settings
from ..models.user import User
from ..models.case import Case
from ..models.document import Document, RequiredDocument, DocumentType, DocumentStatus
from ..schemas.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentListResponse,
    RequiredDocumentResponse,
    DOCUMENT_NAMES,
    DOCUMENT_URLS,
    AUTO_AVAILABLE_DOCUMENTS,
)

router = APIRouter()


@router.get("/types")
async def get_document_types(
    current_user: User = Depends(get_current_user)
):
    """서류 유형 목록 조회"""
    return [
        {
            "type": doc_type.value,
            "name": DOCUMENT_NAMES.get(doc_type, doc_type.value),
            "url": DOCUMENT_URLS.get(doc_type),
            "auto_available": AUTO_AVAILABLE_DOCUMENTS.get(doc_type, False),
        }
        for doc_type in DocumentType
    ]


@router.get("/case/{case_id}", response_model=List[RequiredDocumentResponse])
async def get_case_required_documents(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """사건별 필수 서류 목록 조회"""
    result = await db.execute(
        select(RequiredDocument).where(RequiredDocument.case_id == case_id)
    )
    required_docs = result.scalars().all()

    return [
        RequiredDocumentResponse(
            id=doc.id,
            case_id=doc.case_id,
            document_type=doc.document_type,
            document_name=DOCUMENT_NAMES.get(doc.document_type, doc.document_type.value),
            is_required=doc.is_required,
            status=doc.status,
            note=doc.note,
            issue_guide=doc.issue_guide,
            issue_url=DOCUMENT_URLS.get(doc.document_type),
            is_auto_available=AUTO_AVAILABLE_DOCUMENTS.get(doc.document_type, False),
        )
        for doc in required_docs
    ]


@router.post("/upload/{case_id}", response_model=DocumentResponse)
async def upload_document(
    case_id: int,
    document_type: DocumentType,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """서류 파일 업로드"""
    # 사건 존재 확인
    result = await db.execute(
        select(Case).where(Case.id == case_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사건을 찾을 수 없습니다"
        )

    # 파일 크기 확인
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"파일 크기는 {settings.MAX_UPLOAD_SIZE // 1024 // 1024}MB를 초과할 수 없습니다"
        )

    # 파일 저장 경로 생성
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(case_id))
    os.makedirs(upload_dir, exist_ok=True)

    # 파일명 생성 (타임스탬프 + 원본명)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(upload_dir, safe_filename)

    # 파일 저장
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)

    # DB에 문서 정보 저장
    document = Document(
        case_id=case_id,
        document_type=document_type,
        file_path=file_path,
        file_name=file.filename,
        file_size=len(content),
        mime_type=file.content_type,
        api_source="manual_upload",
        uploaded_by_id=current_user.id,
    )
    db.add(document)
    await db.flush()

    # 필수 서류 상태 업데이트
    req_result = await db.execute(
        select(RequiredDocument).where(
            RequiredDocument.case_id == case_id,
            RequiredDocument.document_type == document_type,
        )
    )
    required_doc = req_result.scalar_one_or_none()
    if required_doc:
        required_doc.status = DocumentStatus.COMPLETED
        required_doc.document_id = document.id

    await db.flush()
    await db.refresh(document)

    return document


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """서류 상세 조회"""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="서류를 찾을 수 없습니다"
        )

    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """서류 삭제"""
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="서류를 찾을 수 없습니다"
        )

    # 파일 삭제
    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    # 필수 서류 상태 초기화
    req_result = await db.execute(
        select(RequiredDocument).where(
            RequiredDocument.document_id == document_id
        )
    )
    required_doc = req_result.scalar_one_or_none()
    if required_doc:
        required_doc.status = DocumentStatus.NOT_STARTED
        required_doc.document_id = None

    await db.delete(document)


@router.put("/required/{required_doc_id}/status")
async def update_required_document_status(
    required_doc_id: int,
    new_status: DocumentStatus,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """필수 서류 상태 수동 업데이트"""
    result = await db.execute(
        select(RequiredDocument).where(RequiredDocument.id == required_doc_id)
    )
    required_doc = result.scalar_one_or_none()

    if not required_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="필수 서류를 찾을 수 없습니다"
        )

    required_doc.status = new_status
    await db.flush()

    return {"message": "상태가 업데이트되었습니다", "status": new_status}


# ========== 서류 자동 발급 API ==========

from ..services.hyphen_service import HyphenService
from ..models.client import Client
from ..core.security import decrypt_sensitive_data
from pydantic import BaseModel
import json

hyphen_service = HyphenService()


class AutoIssueRequest(BaseModel):
    """자동 발급 요청"""
    cert_type: str = "KAKAO"  # KAKAO, PASS, NAVER 등
    phone_number: Optional[str] = None
    telecom: Optional[str] = None  # SKT, KT, LGU


class AutoIssueResponse(BaseModel):
    """자동 발급 응답"""
    success: bool
    message: str
    document_type: str
    data: Optional[dict] = None


@router.post("/auto-issue/{case_id}/{document_type}", response_model=AutoIssueResponse)
async def auto_issue_document(
    case_id: int,
    document_type: DocumentType,
    request: AutoIssueRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    서류 자동 발급 (Hyphen API 연동)

    지원 서류:
    - health_insurance_cert: 건강보험 자격득실확인서
    - pension_cert: 국민연금 가입내역
    - resident_register: 주민등록등본
    - resident_abstract: 주민등록초본
    - income_cert: 소득금액증명원
    """
    # 사건 및 의뢰인 정보 조회
    case_result = await db.execute(
        select(Case).where(Case.id == case_id)
    )
    case = case_result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="사건을 찾을 수 없습니다")

    client_result = await db.execute(
        select(Client).where(Client.id == case.client_id)
    )
    client = client_result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="의뢰인을 찾을 수 없습니다")

    # 주민등록번호 복호화
    if not client.resident_number_enc:
        raise HTTPException(
            status_code=400,
            detail="의뢰인의 주민등록번호가 등록되지 않았습니다"
        )

    try:
        resident_number = decrypt_sensitive_data(client.resident_number_enc)
    except Exception:
        raise HTTPException(status_code=400, detail="주민등록번호 복호화 실패")

    # Hyphen API 호출
    try:
        api_response = None

        if document_type == DocumentType.HEALTH_INSURANCE_CERT:
            api_response = await hyphen_service.get_health_insurance_status(
                name=client.name,
                resident_number=resident_number,
                cert_type=request.cert_type,
            )
        elif document_type == DocumentType.PENSION_CERT:
            api_response = await hyphen_service.get_national_pension_status(
                name=client.name,
                resident_number=resident_number,
                cert_type=request.cert_type,
            )
        elif document_type == DocumentType.RESIDENT_REGISTER:
            api_response = await hyphen_service.get_resident_copy(
                name=client.name,
                resident_number=resident_number,
                cert_type=request.cert_type,
                phone_number=request.phone_number,
                telecom=request.telecom,
            )
        elif document_type == DocumentType.RESIDENT_ABSTRACT:
            api_response = await hyphen_service.get_resident_abstract(
                name=client.name,
                resident_number=resident_number,
                cert_type=request.cert_type,
                phone_number=request.phone_number,
                telecom=request.telecom,
            )
        elif document_type == DocumentType.INCOME_CERT:
            current_year = str(datetime.now().year - 1)
            api_response = await hyphen_service.get_income_certificate(
                name=client.name,
                resident_number=resident_number,
                year=current_year,
                cert_type=request.cert_type,
            )
        elif document_type == DocumentType.LOCAL_TAX_CERT:
            api_response = await hyphen_service.get_local_tax_certificate(
                name=client.name,
                resident_number=resident_number,
                cert_type=request.cert_type,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"{DOCUMENT_NAMES.get(document_type, document_type.value)}은(는) 자동 발급을 지원하지 않습니다"
            )

        # API 응답 저장
        upload_dir = os.path.join(settings.UPLOAD_DIR, str(case_id))
        os.makedirs(upload_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{timestamp}_{document_type.value}.json"
        file_path = os.path.join(upload_dir, file_name)

        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(api_response, ensure_ascii=False, indent=2))

        # DB에 문서 정보 저장
        document = Document(
            case_id=case_id,
            document_type=document_type,
            file_path=file_path,
            file_name=file_name,
            file_size=len(json.dumps(api_response)),
            mime_type="application/json",
            api_source="hyphen",
            api_response=api_response,
            uploaded_by_id=current_user.id,
            issued_at=datetime.now(),
        )
        db.add(document)
        await db.flush()

        # 필수 서류 상태 업데이트
        req_result = await db.execute(
            select(RequiredDocument).where(
                RequiredDocument.case_id == case_id,
                RequiredDocument.document_type == document_type,
            )
        )
        required_doc = req_result.scalar_one_or_none()
        if required_doc:
            required_doc.status = DocumentStatus.COMPLETED
            required_doc.document_id = document.id

        await db.commit()

        return AutoIssueResponse(
            success=True,
            message=f"{DOCUMENT_NAMES.get(document_type, document_type.value)} 발급 완료",
            document_type=document_type.value,
            data=api_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return AutoIssueResponse(
            success=False,
            message=f"API 호출 실패: {str(e)}",
            document_type=document_type.value,
        )


@router.get("/auto-issue/supported")
async def get_supported_auto_issue_documents(
    current_user: User = Depends(get_current_user)
):
    """자동 발급 지원 서류 목록"""
    supported = [
        {"type": "health_insurance_cert", "name": "건강보험 자격득실확인서", "api": "건강보험공단"},
        {"type": "pension_cert", "name": "국민연금 가입내역", "api": "국민연금공단"},
        {"type": "resident_register", "name": "주민등록등본", "api": "정부24"},
        {"type": "resident_abstract", "name": "주민등록초본", "api": "정부24"},
        {"type": "income_cert", "name": "소득금액증명원", "api": "국세청"},
        {"type": "local_tax_cert", "name": "지방세 납세증명", "api": "정부24"},
    ]
    return {
        "supported_documents": supported,
        "cert_types": ["KAKAO", "PASS", "NAVER", "PAYCO", "KB"],
        "telecoms": ["SKT", "KT", "LGU", "SKT_MVNO", "KT_MVNO", "LGU_MVNO"],
    }


@router.get("/auto-issue/test")
async def test_hyphen_connection(
    current_user: User = Depends(get_current_user)
):
    """Hyphen API 연결 테스트"""
    # API 설정 확인
    config_status = {
        "user_id": bool(settings.HYPHEN_CLIENT_ID),
        "api_key": bool(settings.HYPHEN_API_KEY),
        "ekey": bool(getattr(settings, 'HYPHEN_EKEY', '')),
    }

    if not all(config_status.values()):
        return {
            "success": False,
            "message": "Hyphen API 설정이 불완전합니다",
            "config_status": config_status,
            "help": ".env 파일에 HYPHEN_CLIENT_ID, HYPHEN_API_KEY, HYPHEN_EKEY를 설정하세요",
        }

    # 사업자등록상태 조회 테스트 (인증 불필요)
    try:
        result = await hyphen_service.get_business_status("1234567890")
        return {
            "success": True,
            "message": "Hyphen API 연결 성공",
            "test_mode": hyphen_service.test_mode,
            "test_result": result,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"API 호출 실패: {str(e)}",
            "test_mode": hyphen_service.test_mode,
        }
