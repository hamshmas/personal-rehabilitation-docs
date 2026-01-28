"""
서류 발급 서비스 (Hyphen API 연동)
"""
import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.document import Document, RequiredDocument, DocumentType, DocumentStatus
from ..models.case import Case
from ..schemas.document import AUTO_AVAILABLE_DOCUMENTS, DOCUMENT_NAMES
from ..core.config import settings
from .hyphen_service import HyphenService


class DocumentService:
    """서류 발급 서비스"""

    def __init__(self, db: AsyncSession, hyphen_service: Optional[HyphenService] = None):
        self.db = db
        self.hyphen_service = hyphen_service or HyphenService()

    async def auto_issue_document(
        self,
        case_id: int,
        document_type: DocumentType,
        name: str,
        resident_number: str,
        user_id: int,
        **kwargs
    ) -> Dict[str, Any]:
        """
        자동 서류 발급

        Args:
            case_id: 사건 ID
            document_type: 서류 유형
            name: 의뢰인 성명
            resident_number: 주민등록번호
            user_id: 발급 요청 사용자 ID
            **kwargs: 추가 파라미터

        Returns:
            발급 결과
        """
        if not AUTO_AVAILABLE_DOCUMENTS.get(document_type, False):
            return {
                "success": False,
                "error": "자동 발급이 지원되지 않는 서류입니다",
            }

        # 필수 서류 상태를 진행중으로 업데이트
        await self._update_required_status(case_id, document_type, DocumentStatus.IN_PROGRESS)

        try:
            # 서류 유형별 API 호출
            result = await self._call_hyphen_api(
                document_type, name, resident_number, **kwargs
            )

            # Hyphen API 성공 응답 확인
            if result.get("code") == "0000" or result.get("success"):
                # 성공 - 결과 저장
                document = await self._save_document(
                    case_id=case_id,
                    document_type=document_type,
                    api_response=result,
                    user_id=user_id,
                )

                await self._update_required_status(
                    case_id, document_type, DocumentStatus.COMPLETED, document.id
                )

                return {
                    "success": True,
                    "document_id": document.id,
                    "data": result.get("data"),
                }
            else:
                # 실패
                await self._update_required_status(
                    case_id, document_type, DocumentStatus.NOT_STARTED
                )
                return {
                    "success": False,
                    "error": result.get("message", "알 수 없는 오류"),
                    "code": result.get("code"),
                }

        except Exception as e:
            await self._update_required_status(
                case_id, document_type, DocumentStatus.NOT_STARTED
            )
            return {
                "success": False,
                "error": str(e),
            }

    async def _call_hyphen_api(
        self,
        document_type: DocumentType,
        name: str,
        resident_number: str,
        **kwargs
    ) -> Dict[str, Any]:
        """서류 유형에 따른 Hyphen API 호출"""

        cert_type = kwargs.get("cert_type", "simple")

        if document_type == DocumentType.HEALTH_INSURANCE_CERT:
            return await self.hyphen_service.get_health_insurance_status(
                name, resident_number, cert_type
            )

        elif document_type == DocumentType.HEALTH_INSURANCE_PAYMENT:
            return await self.hyphen_service.get_health_insurance_payment(
                name,
                resident_number,
                kwargs.get("start_date", ""),
                kwargs.get("end_date", ""),
                cert_type,
            )

        elif document_type == DocumentType.NATIONAL_PENSION:
            return await self.hyphen_service.get_national_pension_status(
                name, resident_number, cert_type
            )

        elif document_type == DocumentType.EMPLOYMENT_INSURANCE:
            return await self.hyphen_service.get_employment_insurance(
                name, resident_number, cert_type
            )

        elif document_type == DocumentType.REAL_ESTATE_REGISTER:
            return await self.hyphen_service.get_real_estate_register(
                kwargs.get("address", ""),
                kwargs.get("register_type", "building"),
            )

        elif document_type == DocumentType.BUSINESS_STATUS:
            return await self.hyphen_service.get_business_status(
                kwargs.get("business_number", "")
            )

        elif document_type == DocumentType.RESIDENT_REGISTER:
            return await self.hyphen_service.get_resident_registration(
                name, resident_number, cert_type
            )

        elif document_type == DocumentType.LOCAL_TAX_CERT:
            return await self.hyphen_service.get_local_tax_certificate(
                name, resident_number, cert_type
            )

        elif document_type == DocumentType.INCOME_CERT:
            return await self.hyphen_service.get_income_certificate(
                name, resident_number, kwargs.get("year", ""), cert_type
            )

        elif document_type == DocumentType.VEHICLE_REGISTER:
            return await self.hyphen_service.get_vehicle_registration(
                name, resident_number, kwargs.get("vehicle_number", "")
            )

        else:
            raise ValueError(f"지원되지 않는 서류 유형: {document_type}")

    async def _save_document(
        self,
        case_id: int,
        document_type: DocumentType,
        api_response: Dict[str, Any],
        user_id: int,
    ) -> Document:
        """API 응답 결과를 문서로 저장"""

        # 저장 디렉토리 생성
        save_dir = os.path.join(settings.UPLOAD_DIR, str(case_id), "auto")
        os.makedirs(save_dir, exist_ok=True)

        # JSON 파일로 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{document_type.value}_{timestamp}.json"
        file_path = os.path.join(save_dir, file_name)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(api_response, f, ensure_ascii=False, indent=2)

        # DB에 문서 정보 저장
        document = Document(
            case_id=case_id,
            document_type=document_type,
            file_path=file_path,
            file_name=file_name,
            file_size=os.path.getsize(file_path),
            mime_type="application/json",
            api_source="hyphen",
            api_response=api_response,
            uploaded_by_id=user_id,
        )
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)

        return document

    async def _update_required_status(
        self,
        case_id: int,
        document_type: DocumentType,
        status: DocumentStatus,
        document_id: Optional[int] = None,
    ):
        """필수 서류 상태 업데이트"""
        result = await self.db.execute(
            select(RequiredDocument).where(
                RequiredDocument.case_id == case_id,
                RequiredDocument.document_type == document_type,
            )
        )
        required_doc = result.scalar_one_or_none()

        if required_doc:
            required_doc.status = status
            if document_id:
                required_doc.document_id = document_id

    async def get_missing_documents(self, case_id: int) -> List[Dict[str, Any]]:
        """미비 서류 목록 조회"""
        result = await self.db.execute(
            select(RequiredDocument).where(
                RequiredDocument.case_id == case_id,
                RequiredDocument.status != DocumentStatus.COMPLETED,
                RequiredDocument.is_required == True,
            )
        )
        missing_docs = result.scalars().all()

        return [
            {
                "document_type": doc.document_type.value,
                "document_name": DOCUMENT_NAMES.get(doc.document_type),
                "status": doc.status.value,
                "auto_available": AUTO_AVAILABLE_DOCUMENTS.get(doc.document_type, False),
            }
            for doc in missing_docs
        ]

    async def batch_auto_issue(
        self,
        case_id: int,
        name: str,
        resident_number: str,
        user_id: int,
    ) -> Dict[str, Any]:
        """자동 발급 가능한 모든 서류 일괄 발급"""
        results = {
            "success": [],
            "failed": [],
        }

        # 미비 서류 중 자동 발급 가능한 것들 조회
        missing_docs = await self.get_missing_documents(case_id)
        auto_available = [
            doc for doc in missing_docs
            if doc["auto_available"]
        ]

        for doc in auto_available:
            document_type = DocumentType(doc["document_type"])
            result = await self.auto_issue_document(
                case_id=case_id,
                document_type=document_type,
                name=name,
                resident_number=resident_number,
                user_id=user_id,
            )

            if result["success"]:
                results["success"].append({
                    "document_type": document_type.value,
                    "document_name": doc["document_name"],
                    "document_id": result["document_id"],
                })
            else:
                results["failed"].append({
                    "document_type": document_type.value,
                    "document_name": doc["document_name"],
                    "error": result.get("error"),
                })

        return results
