"""
의뢰인 모델
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # 암호화된 주민등록번호
    resident_number_enc = Column(String(500), nullable=True)

    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)

    # Codef Connected ID (계정 연동 시)
    codef_connected_id = Column(String(255), nullable=True)

    # 공동인증서 정보 (암호화 저장)
    cert_der2pem_enc = Column(Text, nullable=True)  # 암호화된 인증서 (DER2PEM)
    cert_key2pem_enc = Column(Text, nullable=True)  # 암호화된 개인키 (KEY2PEM)
    cert_subject = Column(String(255), nullable=True)  # 인증서 주체 (이름)
    cert_valid_until = Column(DateTime(timezone=True), nullable=True)  # 인증서 만료일

    memo = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 관계
    cases = relationship("Case", back_populates="client")
    created_by = relationship("User", foreign_keys=[created_by_id])
