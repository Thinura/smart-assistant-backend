from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.schemas.interview_kit import InterviewKitGenerateRequest
from app.services.interview_kit_service import InterviewKitService
from app.tools.base import BaseTool, ToolResult


class GenerateInterviewKitTool(BaseTool):
    name = "generate_interview_kit"
    description = "Generates an interview kit for a candidate and role."
    requires_approval = False

    def __init__(self, db: Session) -> None:
        self.db = db

    def run(self, payload: dict[str, Any]) -> ToolResult:
        try:
            candidate_id = UUID(str(payload.get("candidate_id")))
        except (TypeError, ValueError):
            return ToolResult(
                success=False,
                error="candidate_id must be a valid UUID",
            )

        candidate = self.db.get(Candidate, candidate_id)

        if candidate is None:
            return ToolResult(
                success=False,
                error="Candidate not found",
            )

        job_description_document_id = self._parse_optional_uuid(
            payload.get("job_description_document_id")
        )

        if payload.get("job_description_document_id") and job_description_document_id is None:
            return ToolResult(
                success=False,
                error="job_description_document_id must be a valid UUID",
            )

        request = InterviewKitGenerateRequest(
            job_description_document_id=job_description_document_id,
            role_name=payload.get("role_name"),
        )

        try:
            interview_kit = InterviewKitService(self.db).generate_for_candidate(
                candidate=candidate,
                payload=request,
            )

            return ToolResult(
                success=True,
                data={
                    "id": str(interview_kit.id),
                    "candidate_id": str(interview_kit.candidate_id),
                    "cv_document_id": str(interview_kit.cv_document_id)
                    if interview_kit.cv_document_id
                    else None,
                    "job_description_document_id": str(interview_kit.job_description_document_id)
                    if interview_kit.job_description_document_id
                    else None,
                    "candidate_review_id": str(interview_kit.candidate_review_id)
                    if interview_kit.candidate_review_id
                    else None,
                    "candidate_job_match_id": str(interview_kit.candidate_job_match_id)
                    if interview_kit.candidate_job_match_id
                    else None,
                    "role_name": interview_kit.role_name,
                    "status": interview_kit.status.value
                    if hasattr(interview_kit.status, "value")
                    else interview_kit.status,
                    "summary": interview_kit.summary,
                    "technical_questions": interview_kit.technical_questions,
                    "behavioral_questions": interview_kit.behavioral_questions,
                    "risk_based_questions": interview_kit.risk_based_questions,
                    "evaluation_rubric": interview_kit.evaluation_rubric,
                },
            )

        except ValueError as exc:
            return ToolResult(success=False, error=str(exc))

    def _parse_optional_uuid(self, value: Any) -> UUID | None:
        if value is None or value == "":
            return None

        try:
            return UUID(str(value))
        except ValueError:
            return None
