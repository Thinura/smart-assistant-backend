from fastapi import APIRouter

from app.api.v1.endpoints.chat import router as chat_router
from app.api.v1.endpoints.conversations import router as conversations_router
from app.api.v1.endpoints.health import router as health_router

api_router = APIRouter()

api_router.include_router(
    health_router,
    prefix="/health",
    tags=["Health"],
)

api_router.include_router(
    conversations_router,
    prefix="/conversations",
    tags=["Conversations"],
)

api_router.include_router(
    chat_router,
    prefix="/chat",
    tags=["Chat"],
)