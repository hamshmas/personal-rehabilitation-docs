"""
Codef API 연동 서비스
"""
import json
from typing import Optional, Dict, Any
from easycodefpy import Codef, ServiceType
import httpx

from ..core.config import settings


class CodefService:
    """Codef API 서비스 클래스"""

    def __init__(self, use_demo: bool = True):
        """
        Args:
            use_demo: True면 데모 환경, False면 정식 환경
        """
        self.codef = Codef()
        self.codef.public_key = settings.CODEF_PUBLIC_KEY
        self.use_demo = use_demo

        if use_demo:
            self.codef.set_demo_client_info(
                settings.CODEF_DEMO_CLIENT_ID,
                settings.CODEF_DEMO_CLIENT_SECRET
            )
        else:
            self.codef.set_client_info(
                settings.CODEF_CLIENT_ID,
                settings.CODEF_CLIENT_SECRET
            )

    async def create_connected_id(
        self,
        organization: str,
        login_type: str,
        user_id: str,
        user_password: str,
    ) -> Dict[str, Any]:
        """
        Codef Connected ID 생성 (계정 등록)

        Args:
            organization: 기관코드 (예: '0004' - 건강보험공단)
            login_type: 로그인 방식 ('0': ID/PW, '1': 인증서)
            user_id: 사용자 ID
            user_password: 비밀번호 (RSA 암호화 필요)

        Returns:
            Connected ID 정보
        """
        account_list = [{
            'countryCode': 'KR',
            'businessType': 'BK',
            'clientType': 'P',
            'organization': organization,
            'loginType': login_type,
            'id': user_id,
            'password': user_password,
        }]

        result = self.codef.create_account(
            ServiceType.DEMO if self.use_demo else ServiceType.PRODUCT,
            account_list
        )
        return json.loads(result)

    async def get_health_insurance_status(
        self,
        connected_id: str,
        identity: str,
    ) -> Dict[str, Any]:
        """
        건강보험 자격득실 확인서 조회

        Args:
            connected_id: Codef Connected ID
            identity: 주민등록번호

        Returns:
            건강보험 자격 정보
        """
        parameter = {
            'connectedId': connected_id,
            'organization': '0004',  # 건강보험공단
            'identity': identity,
        }

        result = self.codef.request_product(
            "/v1/kr/public/pp/nhis-join-career",
            ServiceType.DEMO if self.use_demo else ServiceType.PRODUCT,
            parameter
        )
        return json.loads(result)

    async def get_health_insurance_payment(
        self,
        connected_id: str,
        identity: str,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """
        건강보험료 납부내역 조회

        Args:
            connected_id: Codef Connected ID
            identity: 주민등록번호
            start_date: 조회 시작일 (YYYYMM)
            end_date: 조회 종료일 (YYYYMM)

        Returns:
            건강보험료 납부 내역
        """
        parameter = {
            'connectedId': connected_id,
            'organization': '0004',
            'identity': identity,
            'startDate': start_date,
            'endDate': end_date,
        }

        result = self.codef.request_product(
            "/v1/kr/public/pp/nhis-payment",
            ServiceType.DEMO if self.use_demo else ServiceType.PRODUCT,
            parameter
        )
        return json.loads(result)

    async def get_national_pension_status(
        self,
        connected_id: str,
        identity: str,
    ) -> Dict[str, Any]:
        """
        국민연금 가입내역 조회

        Args:
            connected_id: Codef Connected ID
            identity: 주민등록번호

        Returns:
            국민연금 가입 내역
        """
        parameter = {
            'connectedId': connected_id,
            'organization': '0005',  # 국민연금공단
            'identity': identity,
        }

        result = self.codef.request_product(
            "/v1/kr/public/pp/nps-join-info",
            ServiceType.DEMO if self.use_demo else ServiceType.PRODUCT,
            parameter
        )
        return json.loads(result)

    async def get_business_status(
        self,
        business_number: str,
    ) -> Dict[str, Any]:
        """
        사업자등록상태 조회 (인증 불필요)

        Args:
            business_number: 사업자등록번호

        Returns:
            사업자 상태 정보
        """
        parameter = {
            'organization': '0001',  # 국세청
            'businessNumber': business_number,
        }

        result = self.codef.request_product(
            "/v1/kr/public/nt/business/status",
            ServiceType.DEMO if self.use_demo else ServiceType.PRODUCT,
            parameter
        )
        return json.loads(result)

    async def get_real_estate_register(
        self,
        connected_id: str,
        register_type: str,
        address: str,
    ) -> Dict[str, Any]:
        """
        부동산등기부등본 발급

        Args:
            connected_id: Codef Connected ID
            register_type: 등기 유형 ('0': 토지, '1': 건물, '2': 집합건물)
            address: 부동산 주소

        Returns:
            등기부등본 정보
        """
        parameter = {
            'connectedId': connected_id,
            'organization': '0002',  # 대법원
            'registerType': register_type,
            'address': address,
        }

        result = self.codef.request_product(
            "/v1/kr/public/rt/real-estate-register",
            ServiceType.DEMO if self.use_demo else ServiceType.PRODUCT,
            parameter
        )
        return json.loads(result)

    async def get_employment_insurance(
        self,
        connected_id: str,
        identity: str,
    ) -> Dict[str, Any]:
        """
        고용보험 가입내역 조회

        Args:
            connected_id: Codef Connected ID
            identity: 주민등록번호

        Returns:
            고용보험 가입 내역
        """
        parameter = {
            'connectedId': connected_id,
            'organization': '0006',  # 고용보험
            'identity': identity,
        }

        result = self.codef.request_product(
            "/v1/kr/public/pp/ei-join-info",
            ServiceType.DEMO if self.use_demo else ServiceType.PRODUCT,
            parameter
        )
        return json.loads(result)

    def encrypt_password(self, password: str) -> str:
        """
        RSA 공개키로 비밀번호 암호화

        Args:
            password: 평문 비밀번호

        Returns:
            암호화된 비밀번호
        """
        return self.codef.encrypt(password)
