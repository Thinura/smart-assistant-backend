import json
from json import JSONDecodeError
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.audit_log import AuditEventType
from app.models.candidate import Candidate
from app.models.candidate_job_match import CandidateJobMatch
from app.models.document import Document, DocumentType
from app.models.document_chunk import DocumentChunk
from app.schemas.candidate_job_match import (
    CandidateJobMatchCreate,
    CandidateJobMatchRequest,
)
from app.services.audit_log_service import AuditLogService
from app.services.chat_model_service import get_chat_model


class CandidateJobMatchService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def match_candidate_to_job(
        self,
        *,
        candidate: Candidate,
        payload: CandidateJobMatchRequest,
    ) -> CandidateJobMatch:
        if candidate.cv_document_id is None:
            raise ValueError("Candidate does not have a linked CV document")

        cv_document = self.db.get(Document, candidate.cv_document_id)

        if cv_document is None:
            raise ValueError("Candidate CV document not found")

        if cv_document.document_type != DocumentType.CV:
            raise ValueError("Candidate linked document must be a CV")

        jd_document = self.db.get(Document, payload.job_description_document_id)

        if jd_document is None:
            raise ValueError("Job description document not found")

        if jd_document.document_type != DocumentType.JOB_DESCRIPTION:
            raise ValueError("Document must be of type job_description")

        cv_text = self._get_document_text(cv_document)
        jd_text = self._get_document_text(jd_document)

        match_data = self._generate_match(
            candidate=candidate,
            cv_text=cv_text,
            jd_text=jd_text,
            role_name=payload.role_name,
        )

        match = CandidateJobMatch(
            **CandidateJobMatchCreate(
                candidate_id=candidate.id,
                cv_document_id=cv_document.id,
                job_description_document_id=jd_document.id,
                role_name=payload.role_name or candidate.role_applied_for,
                summary=match_data["summary"],
                match_score=match_data["match_score"],
                recommendation=match_data["recommendation"],
                confidence=match_data["confidence"],
                matched_skills=match_data.get("matched_skills", []),
                missing_skills=match_data.get("missing_skills", []),
                risks=match_data.get("risks", []),
                interview_focus_areas=match_data.get("interview_focus_areas", []),
                source_metadata={
                    "source": "candidate_job_match_service",
                    "cv_filename": cv_document.original_filename,
                    "jd_filename": jd_document.original_filename,
                },
            ).model_dump()
        )

        self.db.add(match)
        self.db.flush()

        AuditLogService(self.db).record(
            event_type=AuditEventType.CANDIDATE_JOB_MATCH_CREATED,
            entity_type="candidate_job_match",
            entity_id=str(match.id),
            actor="agent",
            metadata={
                "candidate_id": str(candidate.id),
                "cv_document_id": str(cv_document.id),
                "job_description_document_id": str(jd_document.id),
                "match_score": match.match_score,
                "recommendation": match.recommendation.value,
                "confidence": match.confidence.value,
            },
        )

        self.db.commit()
        self.db.refresh(match)

        return match

    def _get_document_text(self, document: Document) -> str:
        chunks = (
            self.db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document.id)
            .order_by(DocumentChunk.chunk_index.asc())
            .all()
        )

        text = "\n\n".join(chunk.content for chunk in chunks).strip()

        if not text:
            raise ValueError(f"Document {document.id} has no extracted chunks")

        return text

    def _generate_match(
        self,
        *,
        candidate: Candidate,
        cv_text: str,
        jd_text: str,
        role_name: str | None,
    ) -> dict[str, Any]:
        model = get_chat_model()

        messages = [
            SystemMessage(
                content=(
                    "You are a recruitment matching assistant. Compare a candidate CV "
                    "against a job description using only job-relevant criteria. "
                    "Return only valid JSON. No markdown. No explanation outside JSON."
                )
            ),
            HumanMessage(
                content=(
                    f"Candidate name: {candidate.full_name}\n"
                    f"Candidate role applied for: {candidate.role_applied_for or 'Not specified'}\n"
                    f"Target role: {role_name or candidate.role_applied_for or 'Not specified'}\n\n"
                    f"Candidate CV:\n{cv_text}\n\n"
                    f"Job Description:\n{jd_text}\n\n"
                    "Return JSON with exactly this shape:\n"
                    "{\n"
                    '  "summary": "short match summary",\n'
                    '  "match_score": 0,\n'
                    '  "matched_skills": ["skill 1"],\n'
                    '  "missing_skills": ["gap 1"],\n'
                    '  "risks": ["risk 1"],\n'
                    '  "interview_focus_areas": ["focus area 1"],\n'
                    '  "recommendation": "match",\n'
                    '  "confidence": "medium"\n'
                    "}\n\n"
                    "Rules:\n"
                    "- match_score must be between 0 and 100\n"
                    "- recommendation must be one of: strong_match, "
                    "match, partial_match, not_recommended\n"
                    "- confidence must be one of: low, medium, high\n"
                )
            ),
        ]

        response = model.invoke(messages)
        raw_content = str(response.content).strip()

        try:
            return self._parse_json(raw_content)
        except (JSONDecodeError, ValidationError) as exc:
            raise ValueError(
                f"Candidate match model returned invalid structured output: {raw_content}"
            ) from exc

    def _parse_json(self, content: str) -> dict[str, Any]:
        cleaned_content = content.strip()

        try:
            return json.loads(cleaned_content)
        except JSONDecodeError:
            pass

        start_index = cleaned_content.find("{")
        end_index = cleaned_content.rfind("}")

        if start_index == -1:
            raise JSONDecodeError("No JSON object found", cleaned_content, 0)

        if end_index == -1:
            repaired_content = cleaned_content[start_index:] + "}"
        else:
            repaired_content = cleaned_content[start_index : end_index + 1]

        return json.loads(repaired_content)
