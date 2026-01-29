"""
Hyphen API 연동 서비스
https://hyphen.im - 정부24 스크래핑 API

인증: OAuth 2.0
암호화: AES128-CBC + Base64 (개인정보)
"""
import httpx
import base64
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from ..core.config import settings


class HyphenService:
    """Hyphen API 서비스 클래스"""

    # API 엔드포인트
    BASE_URL = "https://api.hyphen.im"
    TOKEN_URL = f"{BASE_URL}/oauth/token"

    # 정부24 API 엔드포인트 (실제 엔드포인트는 파트너 등록 후 확인 필요)
    ENDPOINTS = {
        # 정부24
        "resident_copy": "/v1/gov24/resident/copy",           # 주민등록등본
        "resident_abstract": "/v1/gov24/resident/abstract",   # 주민등록초본
        "local_tax": "/v1/gov24/tax/local",                   # 지방세 납세증명
        "vehicle": "/v1/gov24/vehicle/registration",          # 자동차등록원부
        # 건강보험공단
        "nhis_qualification": "/v1/nhis/qualification",       # 건강보험 자격득실
        "nhis_payment": "/v1/nhis/payment",                   # 건강보험료 납부내역
        # 국민연금
        "nps_status": "/v1/nps/status",                       # 국민연금 가입내역
        # 고용보험
        "ei_status": "/v1/ei/status",                         # 고용보험 가입내역
        # 대법원
        "realestate": "/v1/court/realestate",                 # 부동산등기부등본
        # 국세청
        "business_status": "/v1/nts/business/status",         # 사업자등록상태
        "income_cert": "/v1/nts/income",                      # 소득금액증명원
    }

    def __init__(self, test_mode: bool = True):
        """
        Hyphen API 초기화

        Args:
            test_mode: 테스트베드 모드 (기본값 True)
        """
        self.user_id = settings.HYPHEN_CLIENT_ID
        self.hkey = settings.HYPHEN_API_KEY
        self.ekey = getattr(settings, 'HYPHEN_EKEY', '')  # 암호화 키
        self.test_mode = test_mode  # 테스트베드 모드
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    def _pad(self, data: bytes, block_size: int = 16) -> bytes:
        """PKCS7 패딩"""
        padding_len = block_size - (len(data) % block_size)
        return data + bytes([padding_len] * padding_len)

    def _get_iv(self) -> bytes:
        """IV 생성 (user_id를 16바이트로)"""
        iv = self.user_id.encode('utf-8')
        if len(iv) < 16:
            iv = iv + b'\x00' * (16 - len(iv))
        return iv[:16]

    def encrypt_data(self, data: str) -> str:
        """
        AES128-CBC 암호화 + Base64 인코딩

        Args:
            data: 암호화할 데이터 (주민등록번호 등)

        Returns:
            암호화된 문자열
        """
        if not self.ekey:
            raise ValueError("HYPHEN_EKEY가 설정되지 않았습니다")

        key = self.ekey.encode('utf-8')[:16]
        iv = self._get_iv()

        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()

        padded_data = self._pad(data.encode('utf-8'))
        encrypted = encryptor.update(padded_data) + encryptor.finalize()

        return base64.b64encode(encrypted).decode('utf-8')

    async def _get_access_token(self) -> str:
        """
        OAuth 2.0 액세스 토큰 발급

        Returns:
            액세스 토큰
        """
        # 캐시된 토큰이 유효하면 재사용
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at:
                return self._access_token

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.TOKEN_URL,
                json={
                    "user_id": self.user_id,
                    "hkey": self.hkey,
                },
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            data = response.json()

            self._access_token = data["access_token"]
            # 만료 시간 설정 (약간의 여유를 두고)
            expires_in = data.get("expires_in", 604800)  # 기본 7일
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)

            return self._access_token

    async def _request(
        self,
        endpoint: str,
        data: Dict[str, Any],
        use_legacy_auth: bool = True,  # Hyphen은 기본적으로 legacy auth 사용
    ) -> Dict[str, Any]:
        """
        Hyphen API 요청

        Args:
            endpoint: API 엔드포인트
            data: 요청 데이터
            use_legacy_auth: 기존 인증 방식 사용 여부 (기본값 True)

        Returns:
            API 응답
        """
        url = f"{self.BASE_URL}{endpoint}"

        # 기본 헤더 설정
        headers = {
            "Content-Type": "application/json",
            "user-id": self.user_id,
            "Hkey": self.hkey,
        }

        # 테스트베드 모드일 경우 헤더 추가
        if self.test_mode:
            headers["hyphen-gustation"] = "test"

        if not use_legacy_auth:
            token = await self._get_access_token()
            headers["Authorization"] = f"Bearer {token}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=data)

            # 응답 로깅 (디버그용)
            print(f"[Hyphen API] {endpoint}")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text[:500] if response.text else 'No content'}")

            response.raise_for_status()
            return response.json()

    # ========== 정부24 주민등록 ==========

    async def get_resident_copy(
        self,
        name: str,
        resident_number: str,
        cert_type: str = "KAKAO",  # KAKAO, PASS, PAYCO, KB, NAVER 등
        phone_number: Optional[str] = None,
        telecom: Optional[str] = None,  # SKT, KT, LGU, SKT_MVNO, KT_MVNO, LGU_MVNO
    ) -> Dict[str, Any]:
        """
        주민등록등본 조회/발급

        Args:
            name: 성명
            resident_number: 주민등록번호 (암호화됨)
            cert_type: 인증 방식
            phone_number: 휴대폰 번호
            telecom: 통신사

        Returns:
            주민등록등본 정보
        """
        data = {
            "name": name,
            "jumin": self.encrypt_data(resident_number),
            "certType": cert_type,
        }
        if phone_number:
            data["phoneNo"] = phone_number
        if telecom:
            data["telecom"] = telecom

        return await self._request(self.ENDPOINTS["resident_copy"], data)

    async def get_resident_abstract(
        self,
        name: str,
        resident_number: str,
        cert_type: str = "KAKAO",
        phone_number: Optional[str] = None,
        telecom: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        주민등록초본 조회/발급
        """
        data = {
            "name": name,
            "jumin": self.encrypt_data(resident_number),
            "certType": cert_type,
        }
        if phone_number:
            data["phoneNo"] = phone_number
        if telecom:
            data["telecom"] = telecom

        return await self._request(self.ENDPOINTS["resident_abstract"], data)

    # ========== 정부24 증명서 ==========

    async def get_local_tax_certificate(
        self,
        name: str,
        resident_number: str,
        cert_type: str = "KAKAO",
    ) -> Dict[str, Any]:
        """
        지방세 납세증명서 발급
        """
        data = {
            "name": name,
            "jumin": self.encrypt_data(resident_number),
            "certType": cert_type,
        }
        return await self._request(self.ENDPOINTS["local_tax"], data)

    async def get_vehicle_registration(
        self,
        name: str,
        resident_number: str,
        vehicle_number: str,
        cert_type: str = "KAKAO",
    ) -> Dict[str, Any]:
        """
        자동차등록원부 조회
        """
        data = {
            "name": name,
            "jumin": self.encrypt_data(resident_number),
            "carNo": vehicle_number,
            "certType": cert_type,
        }
        return await self._request(self.ENDPOINTS["vehicle"], data)

    # ========== 건강보험공단 ==========

    async def get_health_insurance_status(
        self,
        name: str,
        resident_number: str,
        cert_type: str = "KAKAO",
    ) -> Dict[str, Any]:
        """
        건강보험 자격득실확인서 조회
        """
        data = {
            "name": name,
            "jumin": self.encrypt_data(resident_number),
            "certType": cert_type,
        }
        return await self._request(self.ENDPOINTS["nhis_qualification"], data)

    async def get_health_insurance_payment(
        self,
        name: str,
        resident_number: str,
        start_date: str,
        end_date: str,
        cert_type: str = "KAKAO",
    ) -> Dict[str, Any]:
        """
        건강보험료 납부내역 조회

        Args:
            start_date: 조회 시작일 (YYYYMM)
            end_date: 조회 종료일 (YYYYMM)
        """
        data = {
            "name": name,
            "jumin": self.encrypt_data(resident_number),
            "startDate": start_date,
            "endDate": end_date,
            "certType": cert_type,
        }
        return await self._request(self.ENDPOINTS["nhis_payment"], data)

    # ========== 국민연금공단 ==========

    async def get_national_pension_status(
        self,
        name: str,
        resident_number: str,
        cert_type: str = "KAKAO",
    ) -> Dict[str, Any]:
        """
        국민연금 가입내역 조회
        """
        data = {
            "name": name,
            "jumin": self.encrypt_data(resident_number),
            "certType": cert_type,
        }
        return await self._request(self.ENDPOINTS["nps_status"], data)

    # ========== 고용보험 ==========

    async def get_employment_insurance(
        self,
        name: str,
        resident_number: str,
        cert_type: str = "KAKAO",
    ) -> Dict[str, Any]:
        """
        고용보험 가입내역 조회
        """
        data = {
            "name": name,
            "jumin": self.encrypt_data(resident_number),
            "certType": cert_type,
        }
        return await self._request(self.ENDPOINTS["ei_status"], data)

    # ========== 대법원 등기 ==========

    async def get_real_estate_register(
        self,
        address: str,
        register_type: str = "building",  # land, building, collective
    ) -> Dict[str, Any]:
        """
        부동산등기부등본 발급

        Args:
            address: 부동산 주소
            register_type: 등기 유형 (land: 토지, building: 건물, collective: 집합건물)
        """
        type_map = {
            "land": "1",
            "building": "2",
            "collective": "3",
        }
        data = {
            "address": address,
            "registerType": type_map.get(register_type, "2"),
        }
        return await self._request(self.ENDPOINTS["realestate"], data)

    # ========== 국세청 ==========

    async def get_business_status(
        self,
        business_number: str,
    ) -> Dict[str, Any]:
        """
        사업자등록상태 조회
        """
        data = {
            "businessNo": business_number.replace("-", ""),
        }
        return await self._request(self.ENDPOINTS["business_status"], data)

    async def get_income_certificate(
        self,
        name: str,
        resident_number: str,
        year: str,
        cert_type: str = "KAKAO",
    ) -> Dict[str, Any]:
        """
        소득금액증명원 발급

        Args:
            year: 귀속년도 (YYYY)
        """
        data = {
            "name": name,
            "jumin": self.encrypt_data(resident_number),
            "year": year,
            "certType": cert_type,
        }
        return await self._request(self.ENDPOINTS["income_cert"], data)
