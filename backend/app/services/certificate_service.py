"""
공동인증서 처리 서비스
- PKCS#12 (.pfx, .p12) 파일에서 인증서 정보 추출
- Hyphen API 호출용 DER2PEM, KEY2PEM 생성
"""
import base64
from typing import Tuple, Optional
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
from cryptography import x509


class CertificateService:
    """공동인증서 처리 서비스"""

    @staticmethod
    def extract_certificate_info(
        cert_file_content: bytes,
        password: str
    ) -> Tuple[str, str]:
        """
        PKCS#12 인증서 파일에서 DER2PEM, KEY2PEM 추출

        Args:
            cert_file_content: 인증서 파일 바이너리 내용
            password: 인증서 비밀번호

        Returns:
            Tuple[der2pem, key2pem]: Base64 인코딩된 인증서와 개인키

        Raises:
            ValueError: 인증서 파일이 유효하지 않거나 비밀번호가 틀린 경우
        """
        try:
            # PKCS#12 파일 로드
            private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
                cert_file_content,
                password.encode('utf-8'),
                default_backend()
            )

            if not certificate or not private_key:
                raise ValueError("인증서 또는 개인키를 찾을 수 없습니다")

            # 인증서를 PEM 형식으로 변환
            cert_pem = certificate.public_bytes(serialization.Encoding.PEM)

            # 개인키를 암호화된 PEM 형식으로 변환
            key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.BestAvailableEncryption(password.encode('utf-8'))
            )

            # PEM 헤더/푸터 및 개행문자 제거 후 Base64만 추출
            der2pem = CertificateService._extract_base64_from_pem(cert_pem.decode('utf-8'))
            key2pem = CertificateService._extract_base64_from_pem(key_pem.decode('utf-8'))

            return der2pem, key2pem

        except Exception as e:
            if "Invalid password" in str(e) or "mac verify failure" in str(e):
                raise ValueError("인증서 비밀번호가 올바르지 않습니다")
            raise ValueError(f"인증서 처리 실패: {str(e)}")

    @staticmethod
    def _extract_base64_from_pem(pem_string: str) -> str:
        """
        PEM 문자열에서 Base64 데이터만 추출
        (헤더, 푸터, 개행문자 제거)
        """
        lines = pem_string.strip().split('\n')
        # 헤더와 푸터 제거
        data_lines = [
            line for line in lines
            if not line.startswith('-----')
        ]
        # 개행 없이 합치기
        return ''.join(data_lines)

    @staticmethod
    def get_certificate_info(cert_file_content: bytes, password: str) -> dict:
        """
        인증서 상세 정보 조회

        Returns:
            dict: 인증서 정보 (주체, 발급자, 유효기간 등)
        """
        try:
            private_key, certificate, _ = pkcs12.load_key_and_certificates(
                cert_file_content,
                password.encode('utf-8'),
                default_backend()
            )

            if not certificate:
                raise ValueError("인증서를 찾을 수 없습니다")

            # 주체(Subject) 정보 추출
            subject = certificate.subject
            subject_cn = None
            for attr in subject:
                if attr.oid == x509.oid.NameOID.COMMON_NAME:
                    subject_cn = attr.value
                    break

            # 발급자(Issuer) 정보 추출
            issuer = certificate.issuer
            issuer_cn = None
            for attr in issuer:
                if attr.oid == x509.oid.NameOID.COMMON_NAME:
                    issuer_cn = attr.value
                    break

            return {
                "subject": subject_cn or str(subject),
                "issuer": issuer_cn or str(issuer),
                "valid_from": certificate.not_valid_before_utc.isoformat(),
                "valid_until": certificate.not_valid_after_utc.isoformat(),
                "serial_number": str(certificate.serial_number),
            }

        except Exception as e:
            if "Invalid password" in str(e) or "mac verify failure" in str(e):
                raise ValueError("인증서 비밀번호가 올바르지 않습니다")
            raise ValueError(f"인증서 정보 조회 실패: {str(e)}")

    @staticmethod
    def validate_certificate(cert_file_content: bytes, password: str) -> bool:
        """
        인증서 유효성 검증

        Returns:
            bool: 유효한 인증서인지 여부
        """
        try:
            from datetime import datetime, timezone

            private_key, certificate, _ = pkcs12.load_key_and_certificates(
                cert_file_content,
                password.encode('utf-8'),
                default_backend()
            )

            if not certificate or not private_key:
                return False

            # 유효기간 확인
            now = datetime.now(timezone.utc)
            if now < certificate.not_valid_before_utc or now > certificate.not_valid_after_utc:
                return False

            return True

        except Exception:
            return False
