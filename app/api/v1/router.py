from fastapi import APIRouter

from app.api.v1.endpoints.agent_runs import router as agent_runs_router
from app.api.v1.endpoints.approvals import router as approvals_router
from app.api.v1.endpoints.audit_logs import router as audit_logs_router
from app.api.v1.endpoints.candidate_reviews import router as candidate_reviews_router
from app.api.v1.endpoints.candidates import router as candidates_router
from app.api.v1.endpoints.chat import router as chat_router
from app.api.v1.endpoints.conversations import router as conversations_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.documents import router as documents_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.outbox import router as outbox_router
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

api_router.include_router(
    candidates_router,
    prefix="/candidates",
    tags=["Candidates"],
)

api_router.include_router(
    approvals_router,
    prefix="/approvals",
    tags=["Approvals"],
)

api_router.include_router(
    audit_logs_router,
    prefix="/audit-logs",
    tags=["Audit Logs"],
)

api_router.include_router(
    outbox_router,
    prefix="/outbox",
    tags=["outbox"],
)

api_router.include_router(
    candidate_reviews_router,
    prefix="/candidate-reviews",
    tags=["candidate-reviews"],
)

api_router.include_router(
    dashboard_router,
    prefix="/dashboard",
    tags=["dashboard"],
)
