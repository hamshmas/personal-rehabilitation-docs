"""
애플리케이션 설정
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # 앱 설정
    APP_NAME: str = "개인회생 서류 관리 시스템"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 데이터베이스 (SQLite 기본값, PostgreSQL 권장)
    DATABASE_URL: str = "sqlite+aiosqlite:///./rehabilitation_docs.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT 인증
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24시간

    # Hyphen API (https://hyphen.im)
    HYPHEN_API_KEY: str = ""      # HKey
    HYPHEN_CLIENT_ID: str = ""    # User ID
    HYPHEN_EKEY: str = ""         # 암호화 키 (AES128)
    HYPHEN_BASE_URL: str = "https://api.hyphen.im"

    # 파일 저장
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # 암호화 키 (개인정보 암호화용)
    ENCRYPTION_KEY: str = "your-encryption-key-32-bytes-long"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
