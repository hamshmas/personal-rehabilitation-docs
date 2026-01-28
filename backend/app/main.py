"""
개인회생 서류 관리 시스템 - FastAPI 메인 애플리케이션
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.database import init_db
from .api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 이벤트"""
    # 시작 시 DB 테이블 생성
    await init_db()
    yield
    # 종료 시 정리 작업


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="개인회생 신청 서류 자동 발급 및 관리 시스템",
    lifespan=lifespan,
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",  # Next.js 개발 서버
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy"}
