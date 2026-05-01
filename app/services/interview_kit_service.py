import json
from json import JSONDecodeError
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.orm import Session

from app.models.audit_log import AuditEventType
from app.models.candidate import Candidate
from app.models.candidate_job_match import CandidateJobMatch
from app.models.candidate_review import CandidateReview
from app.models.document_chunk import DocumentChunk
from app.models.interview_kit import InterviewKit
from app.schemas.interview_kit import InterviewKitCreate, InterviewKitGenerateRequest
from app.services.audit_log_service import AuditLogService
from app.services.chat_model_service import get_chat_model


class InterviewKitService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def generate_for_candidate(
        self,
        *,
        candidate: Candidate,
        payload: InterviewKitGenerateRequest,
    ) -> InterviewKit:
        cv_text = ""
        cv_document_id = candidate.cv_document_id

        if candidate.cv_document_id is not None:
            cv_text = self._get_document_text(candidate.cv_document_id)

        latest_review = (
            self.db.query(CandidateReview)
            .filter(CandidateReview.candidate_id == candidate.id)
            .order_by(CandidateReview.created_at.desc())
            .first()
        )

        latest_match_query = self.db.query(CandidateJobMatch).filter(
            CandidateJobMatch.candidate_id == candidate.id
        )

        if payload.job_description_document_id is not None:
            latest_match_query = latest_match_query.filter(
                CandidateJobMatch.job_description_document_id == payload.job_description_document_id
            )

        latest_match = latest_match_query.order_by(CandidateJobMatch.created_at.desc()).first()

        jd_text = ""
        if payload.job_description_document_id is not None:
            jd_text = self._get_document_text(payload.job_description_document_id)

        kit_data = self._generate_kit(
            candidate=candidate,
            cv_text=cv_text,
            jd_text=jd_text,
            latest_review=latest_review,
            latest_match=latest_match,
            role_name=payload.role_name,
        )

        interview_kit = InterviewKit(
            **InterviewKitCreate(
                candidate_id=candidate.id,
                cv_document_id=cv_document_id,
                job_description_document_id=payload.job_description_document_id,
                candidate_review_id=latest_review.id if latest_review else None,
                candidate_job_match_id=latest_match.id if latest_match else None,
                role_name=payload.role_name or candidate.role_applied_for,
                summary=kit_data["summary"],
                technical_questions=kit_data.get("technical_questions", []),
                behavioral_questions=kit_data.get("behavioral_questions", []),
                risk_based_questions=kit_data.get("risk_based_questions", []),
                evaluation_rubric=kit_data.get("evaluation_rubric", []),
                source_metadata={
                    "source": "interview_kit_service",
                    "has_cv": bool(cv_text),
                    "has_job_description": bool(jd_text),
                    "candidate_review_id": str(latest_review.id) if latest_review else None,
                    "candidate_job_match_id": str(latest_match.id) if latest_match else None,
                },
            ).model_dump()
        )

        self.db.add(interview_kit)
        self.db.flush()

        AuditLogService(self.db).record(
            event_type=AuditEventType.INTERVIEW_KIT_CREATED,
            entity_type="interview_kit",
            entity_id=str(interview_kit.id),
            actor="agent",
            metadata={
                "candidate_id": str(candidate.id),
                "cv_document_id": str(cv_document_id) if cv_document_id else None,
                "job_description_document_id": (
                    str(payload.job_description_document_id)
                    if payload.job_description_document_id
                    else None
                ),
                "candidate_review_id": str(latest_review.id) if latest_review else None,
                "candidate_job_match_id": str(latest_match.id) if latest_match else None,
            },
        )

        self.db.commit()
        self.db.refresh(interview_kit)

        return interview_kit

    def _get_document_text(self, document_id) -> str:
        chunks = (
            self.db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
            .all()
        )

        return "\n\n".join(chunk.content for chunk in chunks).strip()

    def _generate_kit(
        self,
        *,
        candidate: Candidate,
        cv_text: str,
        jd_text: str,
        latest_review: CandidateReview | None,
        latest_match: CandidateJobMatch | None,
        role_name: str | None,
    ) -> dict[str, Any]:
        model = get_chat_model()

        review_context = ""
        if latest_review is not None:
            review_context = (
                f"Latest Review Summary: {latest_review.summary}\n"
                f"Review Score: {latest_review.score}\n"
                f"Review Recommendation: {latest_review.recommendation.value}\n"
                f"Review Risks: {latest_review.risks}\n"
            )

        match_context = ""
        if latest_match is not None:
            match_context = (
                f"Latest Match Summary: {latest_match.summary}\n"
                f"Match Score: {latest_match.match_score}\n"
                f"Missing Skills: {latest_match.missing_skills}\n"
                f"Interview Focus Areas: {latest_match.interview_focus_areas}\n"
            )

        messages = [
            SystemMessage(
                content=(
                    "You are an interview planning assistant. Generate structured interview "
                    "questions using only job-relevant criteria. Return only valid JSON. "
                    "No markdown. No explanation outside JSON."
                )
            ),
            HumanMessage(
                content=(
                    f"Candidate: {candidate.full_name}\n"
                    f"Role: {role_name or candidate.role_applied_for or 'Not specified'}\n\n"
                    f"Candidate CV:\n{cv_text or 'No CV text available'}\n\n"
                    f"Job Description:\n{jd_text or 'No job description provided'}\n\n"
                    f"Candidate Review:\n{review_context or 'No review available'}\n\n"
                    f"Candidate Job Match:\n{match_context or 'No match available'}\n\n"
                    "Return JSON with exactly this shape:\n"
                    "{\n"
                    '  "summary": "short interview plan summary",\n'
                    '  "technical_questions": [\n'
                    '    {"question": "question", "purpose": "purpose", '
                    '"expected_signals": ["signal"]}\n'
                    "  ],\n"
                    '  "behavioral_questions": [\n'
                    '    {"question": "question", "purpose": "purpose", '
                    '"expected_signals": ["signal"]}\n'
                    "  ],\n"
                    '  "risk_based_questions": [\n'
                    '    {"question": "question", "purpose": "purpose", '
                    '"expected_signals": ["signal"]}\n'
                    "  ],\n"
                    '  "evaluation_rubric": [\n'
                    '    {"area": "area", "strong_signal": "strong signal", '
                    '"weak_signal": "weak signal"}\n'
                    "  ]\n"
                    "}\n"
                )
            ),
        ]

        response = model.invoke(messages)
        return self._parse_json(str(response.content).strip())

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
