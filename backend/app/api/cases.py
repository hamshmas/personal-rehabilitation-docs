"""
사건 관리 API 라우터
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.client import Client
from ..models.case import Case, CourtType, CaseStatus
from ..models.document import RequiredDocument, DocumentType, DocumentStatus
from ..schemas.case import CaseCreate, CaseUpdate, CaseResponse, CaseListResponse
from ..schemas.document import COURT_REQUIRED_DOCUMENTS

router = APIRouter()


def create_required_documents(case_id: int, court_type: CourtType) -> List[RequiredDocument]:
    """법원 유형에 따른 필수 서류 목록 생성"""
    required_docs = []
    document_types = COURT_REQUIRED_DOCUMENTS.get(court_type, [])

    for doc_type in document_types:
        required_doc = RequiredDocument(
            case_id=case_id,
            document_type=doc_type,
            is_required=True,
            status=DocumentStatus.NOT_STARTED,
        )
        required_docs.append(required_doc)

    return required_docs


@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    case_data: CaseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """새 사건 생성"""
    # 의뢰인 존재 확인
    result = await db.execute(
        select(Client).where(Client.id == case_data.client_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="의뢰인을 찾을 수 없습니다"
        )

    # 사건 생성
    case = Case(
        client_id=case_data.client_id,
        court_type=case_data.court_type,
        status=CaseStatus.PREPARING,
        memo=case_data.memo,
        created_by_id=current_user.id,
    )
    db.add(case)
    await db.flush()

    # 필수 서류 목록 생성
    required_docs = create_required_documents(case.id, case_data.court_type)
    for doc in required_docs:
        db.add(doc)

    await db.flush()
    await db.refresh(case)

    return case


@router.get("/", response_model=CaseListResponse)
async def list_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[CaseStatus] = None,
    court_type: Optional[CourtType] = None,
    client_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """사건 목록 조회"""
    query = select(Case).options(selectinload(Case.client))

    if status:
        query = query.where(Case.status == status)
    if court_type:
        query = query.where(Case.court_type == court_type)
    if client_id:
        query = query.where(Case.client_id == client_id)

    # 전체 개수 계산
    count_query = select(Case.id)
    if status:
        count_query = count_query.where(Case.status == status)
    if court_type:
        count_query = count_query.where(Case.court_type == court_type)
    if client_id:
        count_query = count_query.where(Case.client_id == client_id)

    count_result = await db.execute(count_query)
    total = len(count_result.all())

    # 페이징
    query = query.order_by(Case.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    cases = result.scalars().all()

    return CaseListResponse(
        items=cases,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """사건 상세 조회"""
    result = await db.execute(
        select(Case)
        .options(
            selectinload(Case.client),
            selectinload(Case.required_documents),
            selectinload(Case.documents),
        )
        .where(Case.id == case_id)
    )
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사건을 찾을 수 없습니다"
        )

    return case


@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: int,
    case_data: CaseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """사건 정보 수정"""
    result = await db.execute(
        select(Case).where(Case.id == case_id)
    )
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사건을 찾을 수 없습니다"
        )

    update_data = case_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case, field, value)

    await db.flush()
    await db.refresh(case)

    return case


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """사건 삭제"""
    result = await db.execute(
        select(Case).where(Case.id == case_id)
    )
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사건을 찾을 수 없습니다"
        )

    await db.delete(case)


@router.get("/{case_id}/documents/status")
async def get_document_status(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """사건별 서류 진행 현황"""
    result = await db.execute(
        select(Case)
        .options(selectinload(Case.required_documents))
        .where(Case.id == case_id)
    )
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사건을 찾을 수 없습니다"
        )

    total = len(case.required_documents)
    completed = sum(
        1 for doc in case.required_documents
        if doc.status == DocumentStatus.COMPLETED
    )
    in_progress = sum(
        1 for doc in case.required_documents
        if doc.status == DocumentStatus.IN_PROGRESS
    )
    not_started = sum(
        1 for doc in case.required_documents
        if doc.status == DocumentStatus.NOT_STARTED
    )

    return {
        "case_id": case_id,
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "not_started": not_started,
        "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
    }
