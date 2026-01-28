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
    status: DocumentStatus,
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

    required_doc.status = status
    await db.flush()

    return {"message": "상태가 업데이트되었습니다", "status": status}
