"""
의뢰인 관리 API 라우터
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..core.database import get_db
from ..core.security import get_current_user, encrypt_sensitive_data, decrypt_sensitive_data
from ..models.user import User
from ..models.client import Client
from ..schemas.client import ClientCreate, ClientUpdate, ClientResponse, ClientListResponse

router = APIRouter()


@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: ClientCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """새 의뢰인 등록"""
    # 주민등록번호 암호화
    encrypted_resident_number = None
    if client_data.resident_number:
        encrypted_resident_number = encrypt_sensitive_data(client_data.resident_number)

    client = Client(
        name=client_data.name,
        resident_number_enc=encrypted_resident_number,
        phone=client_data.phone,
        email=client_data.email,
        address=client_data.address,
        memo=client_data.memo,
        created_by_id=current_user.id,
    )
    db.add(client)
    await db.flush()
    await db.refresh(client)

    return client


@router.get("/", response_model=ClientListResponse)
async def list_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """의뢰인 목록 조회"""
    query = select(Client)

    if search:
        query = query.where(
            Client.name.ilike(f"%{search}%") |
            Client.phone.ilike(f"%{search}%")
        )

    # 전체 개수
    count_result = await db.execute(
        select(Client.id).where(Client.name.ilike(f"%{search}%") if search else True)
    )
    total = len(count_result.all())

    # 페이징
    query = query.order_by(Client.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    clients = result.scalars().all()

    return ClientListResponse(
        items=clients,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """의뢰인 상세 조회"""
    result = await db.execute(
        select(Client)
        .options(selectinload(Client.cases))
        .where(Client.id == client_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="의뢰인을 찾을 수 없습니다"
        )

    return client


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    client_data: ClientUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """의뢰인 정보 수정"""
    result = await db.execute(
        select(Client).where(Client.id == client_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="의뢰인을 찾을 수 없습니다"
        )

    update_data = client_data.model_dump(exclude_unset=True)

    # 주민등록번호 암호화
    if "resident_number" in update_data and update_data["resident_number"]:
        update_data["resident_number_enc"] = encrypt_sensitive_data(
            update_data.pop("resident_number")
        )
    elif "resident_number" in update_data:
        del update_data["resident_number"]

    for field, value in update_data.items():
        setattr(client, field, value)

    await db.flush()
    await db.refresh(client)

    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """의뢰인 삭제"""
    result = await db.execute(
        select(Client).where(Client.id == client_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="의뢰인을 찾을 수 없습니다"
        )

    await db.delete(client)
