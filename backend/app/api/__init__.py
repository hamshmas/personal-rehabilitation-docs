"""
API Router
"""
from fastapi import APIRouter

from .auth import router as auth_router
from .clients import router as clients_router
from .cases import router as cases_router
from .documents import router as documents_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(clients_router, prefix="/clients", tags=["Clients"])
api_router.include_router(cases_router, prefix="/cases", tags=["Cases"])
api_router.include_router(documents_router, prefix="/documents", tags=["Documents"])
