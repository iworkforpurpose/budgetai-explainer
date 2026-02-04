"""
API v1 Router
Aggregates all v1 endpoints
"""
from fastapi import APIRouter

from .endpoints import chat, search, health

router = APIRouter(prefix="/v1")

# Include all endpoint routers
router.include_router(chat.router, tags=["chat"])
router.include_router(search.router, tags=["search"])
router.include_router(health.router, tags=["health"])
