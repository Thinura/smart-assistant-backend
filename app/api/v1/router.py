from fastapi import APIRouter

from app.api.v1.endpoints.agent_runs import router as agent_runs_router
from app.api.v1.endpoints.chat import router as chat_router
from app.api.v1.endpoints.conversations import router as conversations_router
from app.api.v1.endpoints.documents import router as documents_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.tools import router as tools_router

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

api_router.include_router(
    agent_runs_router,
    prefix="/agent-runs",
    tags=["Agent Runs"],
)

api_router.include_router(
    tools_router,
    prefix="/tools",
    tags=["Tools"],
)

api_router.include_router(
    documents_router,
    prefix="/documents",
    tags=["Documents"],
)
