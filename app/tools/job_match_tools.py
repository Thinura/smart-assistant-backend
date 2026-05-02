from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.schemas.candidate_job_match import CandidateJobMatchRequest
from app.services.candidate_job_match_service import CandidateJobMatchService
from app.tools.base import BaseTool, ToolResult


class MatchCandidateToJobTool(BaseTool):
    name = "match_candidate_to_job"
    description = "Matches a candidate CV against a job description document."
    requires_approval = False

    def __init__(self, db: Session) -> None:
        self.db = db

    def run(self, payload: dict[str, Any]) -> ToolResult:
        try:
            candidate_id = UUID(str(payload.get("candidate_id")))
            job_description_document_id = UUID(str(payload.get("job_description_document_id")))
        except (TypeError, ValueError):
            return ToolResult(
                success=False,
                error="candidate_id and job_description_document_id must be valid UUIDs",
            )

        candidate = self.db.get(Candidate, candidate_id)

        if candidate is None:
            return ToolResult(
                success=False,
                error="Candidate not found",
            )

        try:
            match = CandidateJobMatchService(self.db).match_candidate_to_job(
                candidate=candidate,
                payload=CandidateJobMatchRequest(
                    job_description_document_id=job_description_document_id,
                    role_name=payload.get("role_name"),
                ),
            )

            return ToolResult(
                success=True,
                data={
                    "id": str(match.id),
                    "candidate_id": str(match.candidate_id),
                    "cv_document_id": str(match.cv_document_id) if match.cv_document_id else None,
                    "job_description_document_id": str(match.job_description_document_id),
                    "role_name": match.role_name,
                    "summary": match.summary,
                    "match_score": match.match_score,
                    "recommendation": match.recommendation.value
                    if hasattr(match.recommendation, "value")
                    else match.recommendation,
                    "confidence": match.confidence.value
                    if hasattr(match.confidence, "value")
                    else match.confidence,
                    "matched_skills": match.matched_skills,
                    "missing_skills": match.missing_skills,
                    "risks": match.risks,
                    "interview_focus_areas": match.interview_focus_areas,
                },
            )
        except ValueError as exc:
            return ToolResult(success=False, error=str(exc))
