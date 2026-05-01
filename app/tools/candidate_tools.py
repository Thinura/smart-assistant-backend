import json
from json import JSONDecodeError
from typing import Any
from uuid import UUID

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.schemas.candidate_review import CandidateReviewCreate
from app.services.candidate_pipeline_automation_service import (
    CandidatePipelineAutomationService,
)
from app.services.candidate_review_service import CandidateReviewService
from app.services.chat_model_service import get_chat_model
from app.tools.base import BaseTool, ToolResult


class ReviewCandidateTool(BaseTool):
    name = "review_candidate"
    description = "Reviews a candidate using their profile and linked CV document."
    requires_approval = False

    def __init__(self, db: Session) -> None:
        self.db = db

    def _parse_optional_uuid(self, value: Any) -> UUID | None:
        if value is None:
            return None

        try:
            return UUID(str(value))
        except ValueError:
            return None

    def _parse_candidate_id(self, value: Any) -> UUID | None:
        if value is None:
            return None

        try:
            return UUID(str(value))
        except ValueError:
            return None

    def run(self, payload: dict[str, Any]) -> ToolResult:
        candidate_id = self._parse_candidate_id(payload.get("candidate_id"))
        agent_run_id = self._parse_optional_uuid(payload.get("agent_run_id"))

        if candidate_id is None:
            return ToolResult(
                success=False,
                error="candidate_id is required and must be a valid UUID",
            )

        candidate = self.db.get(Candidate, candidate_id)

        if candidate is None:
            return ToolResult(
                success=False,
                error="Candidate not found",
            )

        if candidate.cv_document_id is None:
            return ToolResult(
                success=False,
                error="Candidate does not have a linked CV document",
            )

        cv_document = self.db.get(Document, candidate.cv_document_id)

        if cv_document is None:
            return ToolResult(
                success=False,
                error="Linked CV document not found",
            )

        cv_chunks = (
            self.db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == candidate.cv_document_id)
            .order_by(DocumentChunk.chunk_index.asc())
            .all()
        )

        cv_text = "\n\n".join(chunk.content for chunk in cv_chunks)

        if not cv_text.strip():
            return ToolResult(
                success=False,
                error="Linked CV document has no extracted chunks",
            )

        try:
            review = self._generate_structured_review(
                candidate=candidate,
                cv_text=cv_text,
            )
        except RuntimeError as exc:
            return ToolResult(
                success=False,
                error=str(exc),
            )

        review_data = review if isinstance(review, dict) else review.model_dump()

        persisted_review = CandidateReviewService(self.db).create_review(
            CandidateReviewCreate(
                candidate_id=candidate.id,
                agent_run_id=agent_run_id,
                cv_document_id=candidate.cv_document_id,
                role_applied_for=candidate.role_applied_for,
                summary=review_data["summary"],
                score=review_data.get("score"),
                recommendation=review_data["recommendation"],
                confidence=review_data["confidence"],
                strengths=review_data.get("strengths", []),
                risks=review_data.get("risks", []),
                interview_focus_areas=review_data.get("interview_focus_areas", []),
                source_metadata={
                    "source": "review_candidate_tool",
                    "cv_document_id": str(candidate.cv_document_id),
                    "cv_source": cv_document.original_filename,
                },
            )
        )

        CandidatePipelineAutomationService(self.db).handle_candidate_review_created(
            candidate=candidate,
            review=persisted_review,
        )
        self.db.commit()
        self.db.refresh(persisted_review)

        return ToolResult(
            success=True,
            data={
                "candidate": {
                    "id": str(candidate.id),
                    "full_name": candidate.full_name,
                    "email": candidate.email,
                    "role_applied_for": candidate.role_applied_for,
                    "status": candidate.status.value,
                    "cv_document_id": str(candidate.cv_document_id),
                    "cv_source": cv_document.original_filename,
                },
                "review": review_data,
                "candidate_review_id": str(persisted_review.id),
                "agent_run_id": str(agent_run_id) if agent_run_id else None,
            },
        )

    def _generate_structured_review(
        self,
        candidate: Candidate,
        cv_text: str,
    ) -> dict[str, Any]:
        model = get_chat_model()

        messages = [
            SystemMessage(
                content=(
                    "You are an HR recruitment assistant. Review candidates fairly using "
                    "only job-relevant criteria. Do not consider protected or personal "
                    "attributes. Return only valid JSON. Do not use markdown. Do not add "
                    "any text before or after the JSON."
                )
            ),
            HumanMessage(
                content=(
                    "Candidate profile:\n"
                    f"Name: {candidate.full_name}\n"
                    f"Role applied for: {candidate.role_applied_for or 'Not specified'}\n"
                    f"Notes: {candidate.notes or 'None'}\n\n"
                    "CV content:\n"
                    f"{cv_text}\n\n"
                    "Return JSON with exactly this shape:\n"
                    "{\n"
                    '  "summary": "short professional summary",\n'
                    '  "score": 0,\n'
                    '  "strengths": ["strength 1", "strength 2"],\n'
                    '  "risks": ["risk or gap 1"],\n'
                    '  "interview_focus_areas": ["focus area 1"],\n'
                    '  "recommendation": "shortlist",\n'
                    '  "confidence": "medium"\n'
                    "}\n\n"
                    "Rules:\n"
                    "- score must be between 0 and 100\n"
                    "- recommendation must be one of: shortlist, hold, reject\n"
                    "- confidence must be one of: low, medium, high\n"
                    "- use only evidence from the candidate profile and CV content\n"
                )
            ),
        ]

        response = model.invoke(messages)
        raw_content = str(response.content).strip()

        try:
            return self._parse_review_json(raw_content)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise RuntimeError(
                f"Candidate review model returned invalid structured output: {raw_content}"
            ) from exc

    def _parse_review_json(self, content: str) -> dict[str, Any]:
        cleaned_content = content.strip()

        try:
            return json.loads(cleaned_content)
        except JSONDecodeError:
            pass

        start_index = cleaned_content.find("{")
        end_index = cleaned_content.rfind("}")

        if start_index == -1:
            raise RuntimeError(
                f"Candidate review model returned invalid structured output: {content}"
            )

        if end_index == -1:
            repaired_content = cleaned_content[start_index:] + "}"
        else:
            repaired_content = cleaned_content[start_index : end_index + 1]

        try:
            return json.loads(repaired_content)
        except JSONDecodeError as exc:
            raise RuntimeError(
                f"Candidate review model returned invalid structured output: {content}"
            ) from exc

    def _extract_json_object(self, raw_content: str) -> str:
        cleaned_content = raw_content.strip()

        if cleaned_content.startswith("```"):
            cleaned_content = cleaned_content.replace("```json", "").replace("```", "").strip()

        start_index = cleaned_content.find("{")
        end_index = cleaned_content.rfind("}")

        if start_index == -1:
            return cleaned_content

        if end_index == -1:
            return cleaned_content[start_index:]

        return cleaned_content[start_index : end_index + 1]

    def _repair_json_object(self, content: str) -> str:
        repaired_content = content.strip()

        if not repaired_content.startswith("{"):
            repaired_content = "{" + repaired_content

        open_braces = repaired_content.count("{")
        close_braces = repaired_content.count("}")

        if close_braces < open_braces:
            repaired_content += "}" * (open_braces - close_braces)

        return repaired_content
