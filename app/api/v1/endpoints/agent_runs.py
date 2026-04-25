from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession
from app.models.agent_run import AgentRun
from app.schemas.agent_run import AgentRunResponse

router = APIRouter()


@router.get("/{agent_run_id}", response_model=AgentRunResponse)
def get_agent_run(
    agent_run_id: UUID,
    db: DbSession,
) -> AgentRun:
    agent_run = db.get(AgentRun, agent_run_id)

    if agent_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent run not found",
        )

    return agent_run
