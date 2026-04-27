from typing import Any
from uuid import UUID

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.chat_model_service import get_chat_model
from app.tools.base import BaseTool, ToolResult


class DraftCandidateEmailTool(BaseTool):
    name = "draft_candidate_email"
    description = "Drafts a candidate email using candidate profile and linked CV context."
    requires_approval = True

    def __init__(self, db: Session) -> None:
        self.db = db

    def run(self, payload: dict[str, Any]) -> ToolResult:
        candidate_id = self._parse_candidate_id(payload.get("candidate_id"))
        email_type = str(payload.get("email_type", "general")).strip().lower()
        tone = str(payload.get("tone", "professional and kind")).strip()

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

        cv_context = self._get_cv_context(candidate)

        model = get_chat_model()

        messages = [
            SystemMessage(
                content=(
                    "You are an HR assistant. Draft candidate emails professionally, "
                    "kindly, and clearly. Do not include internal evaluation notes, "
                    "scores, private comments, or sensitive reasoning. Return only the email body."
                )
            ),
            HumanMessage(
                content=(
                    "Draft an email using the following details:\n\n"
                    f"Candidate name: {candidate.full_name}\n"
                    f"Candidate email: {candidate.email or 'Not provided'}\n"
                    f"Role applied for: {candidate.role_applied_for or 'Not specified'}\n"
                    f"Email type: {email_type}\n"
                    f"Tone: {tone}\n\n"
                    f"CV context for personalization, if useful:\n{cv_context}\n\n"
                    "Rules:\n"
                    "- Keep it concise.\n"
                    "- Be respectful and human.\n"
                    "- Return only the email body.\n"
                    "- Do not include a subject line.\n"
                    "- Do not start with 'Subject:'.\n"
                    "- Do not mention protected attributes.\n"
                    "- Do not mention AI or automated review.\n"
                    "- Do not include subject line.\n"
                )
            ),
        ]

        response = model.invoke(messages)
        draft_body = self._clean_email_body(str(response.content))

        subject = self._build_subject(
            email_type=email_type,
            role_applied_for=candidate.role_applied_for,
        )

        return ToolResult(
            success=True,
            data={
                "candidate": {
                    "id": str(candidate.id),
                    "full_name": candidate.full_name,
                    "email": candidate.email,
                    "role_applied_for": candidate.role_applied_for,
                },
                "email": {
                    "type": email_type,
                    "subject": subject,
                    "body": draft_body,
                    "tone": tone,
                },
            },
        )

    def _get_cv_context(self, candidate: Candidate) -> str:
        if candidate.cv_document_id is None:
            return "No linked CV document."

        cv_document = self.db.get(Document, candidate.cv_document_id)

        if cv_document is None:
            return "Linked CV document not found."

        chunks = (
            self.db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == candidate.cv_document_id)
            .order_by(DocumentChunk.chunk_index.asc())
            .limit(3)
            .all()
        )

        if not chunks:
            return "Linked CV document has no extracted chunks."

        return "\n\n".join(chunk.content for chunk in chunks)

    def _build_subject(self, email_type: str, role_applied_for: str | None) -> str:
        role = role_applied_for or "your application"

        if email_type == "rejection":
            return f"Update on your application for {role}"

        if email_type == "shortlist":
            return f"Next steps for your application for {role}"

        if email_type == "interview_invite":
            return f"Interview invitation for {role}"

        if email_type == "follow_up":
            return f"Follow-up regarding your application for {role}"

        return f"Update regarding {role}"

    def _parse_candidate_id(self, value: Any) -> UUID | None:
        if value is None:
            return None

        try:
            return UUID(str(value))
        except ValueError:
            return None

    def _clean_email_body(self, body: str) -> str:
        lines = body.strip().splitlines()

        while lines and not lines[0].strip():
            lines.pop(0)

        if lines and lines[0].strip().lower().startswith("subject:"):
            lines.pop(0)

        while lines and not lines[0].strip():
            lines.pop(0)

        return "\n".join(lines).strip()
