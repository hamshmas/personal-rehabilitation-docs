"""
의뢰인 관리 API 라우터
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from ..core.database import get_db
from ..core.security import get_current_user, encrypt_sensitive_data, decrypt_sensitive_data
from ..models.user import User
from ..models.client import Client
from ..schemas.client import ClientCreate, ClientUpdate, ClientResponse, ClientListResponse
from ..services.certificate_service import CertificateService

router = APIRouter()
cert_service = CertificateService()


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


# ========== 공동인증서 관리 ==========

class CertificateUploadResponse(BaseModel):
    """인증서 업로드 응답"""
    success: bool
    message: str
    cert_subject: Optional[str] = None
    cert_valid_until: Optional[str] = None


class CertificateStatusResponse(BaseModel):
    """인증서 상태 응답"""
    has_certificate: bool
    cert_subject: Optional[str] = None
    cert_valid_until: Optional[str] = None
    is_expired: bool = False


@router.post("/{client_id}/certificate", response_model=CertificateUploadResponse)
async def upload_certificate(
    client_id: int,
    cert_file: UploadFile = File(..., description="공동인증서 파일 (.pfx, .p12)"),
    cert_password: str = Form(..., description="인증서 비밀번호"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    의뢰인 공동인증서 업로드

    인증서 파일과 비밀번호를 받아 인증서 정보를 추출하고 암호화하여 저장합니다.
    비밀번호는 저장하지 않으며, 매번 자동발급 시 입력해야 합니다.
    """
    # 의뢰인 확인
    result = await db.execute(
        select(Client).where(Client.id == client_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="의뢰인을 찾을 수 없습니다"
        )

    # 파일 확장자 확인
    if not cert_file.filename:
        raise HTTPException(status_code=400, detail="파일명이 없습니다")

    file_ext = cert_file.filename.lower().split('.')[-1]
    if file_ext not in ['pfx', 'p12']:
        raise HTTPException(
            status_code=400,
            detail="지원하지 않는 파일 형식입니다. .pfx 또는 .p12 파일만 가능합니다."
        )

    try:
        # 파일 내용 읽기
        cert_content = await cert_file.read()

        # 인증서 유효성 검증
        if not cert_service.validate_certificate(cert_content, cert_password):
            raise HTTPException(
                status_code=400,
                detail="인증서가 유효하지 않거나 만료되었습니다"
            )

        # 인증서 정보 추출
        cert_info = cert_service.get_certificate_info(cert_content, cert_password)

        # DER2PEM, KEY2PEM 추출
        der2pem, key2pem = cert_service.extract_certificate_info(cert_content, cert_password)

        # 암호화하여 저장
        client.cert_der2pem_enc = encrypt_sensitive_data(der2pem)
        client.cert_key2pem_enc = encrypt_sensitive_data(key2pem)
        client.cert_subject = cert_info["subject"]
        client.cert_valid_until = datetime.fromisoformat(cert_info["valid_until"].replace('Z', '+00:00'))

        await db.flush()

        return CertificateUploadResponse(
            success=True,
            message="인증서가 성공적으로 등록되었습니다",
            cert_subject=cert_info["subject"],
            cert_valid_until=cert_info["valid_until"],
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"인증서 처리 중 오류가 발생했습니다: {str(e)}")


@router.get("/{client_id}/certificate", response_model=CertificateStatusResponse)
async def get_certificate_status(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """의뢰인 공동인증서 등록 상태 조회"""
    result = await db.execute(
        select(Client).where(Client.id == client_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="의뢰인을 찾을 수 없습니다"
        )

    has_cert = bool(client.cert_der2pem_enc and client.cert_key2pem_enc)
    is_expired = False

    if has_cert and client.cert_valid_until:
        from datetime import timezone
        is_expired = datetime.now(timezone.utc) > client.cert_valid_until

    return CertificateStatusResponse(
        has_certificate=has_cert,
        cert_subject=client.cert_subject,
        cert_valid_until=client.cert_valid_until.isoformat() if client.cert_valid_until else None,
        is_expired=is_expired,
    )


@router.delete("/{client_id}/certificate", status_code=status.HTTP_204_NO_CONTENT)
async def delete_certificate(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """의뢰인 공동인증서 삭제"""
    result = await db.execute(
        select(Client).where(Client.id == client_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="의뢰인을 찾을 수 없습니다"
        )

    client.cert_der2pem_enc = None
    client.cert_key2pem_enc = None
    client.cert_subject = None
    client.cert_valid_until = None

    await db.flush()
