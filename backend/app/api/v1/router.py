"""
API v1 Router
Aggregates all v1 endpoints
"""
from fastapi import APIRouter

from .endpoints import chat, search, health, data, calculator

router = APIRouter(prefix="/v1")

# Include all endpoint routers
router.include_router(chat.router, tags=["chat"])
router.include_router(search.router, tags=["search"])
router.include_router(health.router, tags=["health"])
router.include_router(data.router, prefix="/data", tags=["data"])
router.include_router(calculator.router, prefix="/calculate", tags=["calculator"])
