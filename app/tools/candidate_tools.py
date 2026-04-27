from typing import Any
from uuid import UUID

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.chat_model_service import get_chat_model
from app.tools.base import BaseTool, ToolResult


class ReviewCandidateTool(BaseTool):
    name = "review_candidate"
    description = "Reviews a candidate using their profile and linked CV document."
    requires_approval = False

    def __init__(self, db: Session) -> None:
        self.db = db

    def run(self, payload: dict[str, Any]) -> ToolResult:
        candidate_id = self._parse_candidate_id(payload.get("candidate_id"))

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

        model = get_chat_model()

        messages = [
            SystemMessage(
                content=(
                    "You are an HR recruitment assistant. Review candidates fairly using "
                    "only job-relevant criteria. Do not consider protected or personal "
                    "attributes. Return a concise, professional review."
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
                    "Return the review using this structure:\n"
                    "Summary:\n"
                    "Strengths:\n"
                    "Risks/Gaps:\n"
                    "Interview Focus Areas:\n"
                    "Recommendation: shortlist / hold / reject\n"
                )
            ),
        ]

        response = model.invoke(messages)
        review_text = str(response.content).strip()

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
                "review": review_text,
            },
        )

    def _parse_candidate_id(self, value: Any) -> UUID | None:
        if value is None:
            return None

        try:
            return UUID(str(value))
        except ValueError:
            return None
