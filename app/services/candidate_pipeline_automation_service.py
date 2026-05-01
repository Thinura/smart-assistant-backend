from sqlalchemy.orm import Session

from app.models.approval_request import ApprovalActionType
from app.models.candidate import Candidate
from app.models.candidate_review import CandidateReview, CandidateReviewRecommendation
from app.models.email_template import EmailTemplateType
from app.services.email_template_service import EmailTemplateService


class CandidatePipelineAutomationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def handle_candidate_review_created(
        self,
        *,
        candidate: Candidate,
        review: CandidateReview,
    ) -> None:
        from app.services.tool_execution_service import ToolExecutionService

        if review.recommendation != CandidateReviewRecommendation.SHORTLIST:
            return

        if not candidate.email:
            return

        existing_approval = self._has_existing_interview_approval(candidate)

        if existing_approval:
            return

        tool_execution_service = ToolExecutionService(self.db)

        action_payload = self._build_interview_invite_payload(
            candidate=candidate,
            review=review,
        )

        tool_execution_service.run_tool(
            tool_name="create_approval_request",
            payload={
                "agent_run_id": str(review.agent_run_id) if review.agent_run_id else None,
                "action_type": ApprovalActionType.EMAIL_DRAFT.value,
                "title": f"Approve interview invite email for {candidate.full_name}",
                "description": (
                    "Candidate was shortlisted by AI review. "
                    "Human approval is required before sending the interview invite."
                ),
                "action_payload": action_payload,
            },
            agent_run_id=review.agent_run_id,
        )

    def _has_existing_interview_approval(self, candidate: Candidate) -> bool:
        from app.models.approval_request import ApprovalRequest

        existing = (
            self.db.query(ApprovalRequest)
            .filter(
                ApprovalRequest.action_payload["candidate_id"].astext == str(candidate.id),
                ApprovalRequest.action_payload["email_type"].astext == "interview_invite",
            )
            .first()
        )

        return existing is not None

    def _build_interview_invite_payload(
        self,
        *,
        candidate: Candidate,
        review: CandidateReview,
    ) -> dict:
        template_service = EmailTemplateService(self.db)
        template = template_service.get_active_template_by_type(
            EmailTemplateType.INTERVIEW_INVITE,
        )

        base_variables = {
            "candidate_name": candidate.full_name,
            "candidate_email": candidate.email or "",
            "role_name": candidate.role_applied_for or "your application",
            "company_name": "",
            "interview_date": "",
            "interview_time": "",
            "interview_link": "",
            "recruiter_name": "",
            "assignment_deadline": "",
            "location": "",
            "salary_range": "",
            "next_steps": "",
        }

        if template is not None:
            rendered = template_service.render_template(
                template=template,
                variables=base_variables,
            )

            if not rendered.missing_variables:
                return {
                    "candidate_id": str(candidate.id),
                    "candidate_email": candidate.email,
                    "email_type": "interview_invite",
                    "subject": rendered.subject,
                    "draft_body": rendered.body,
                    "template_id": str(template.id),
                    "template_name": template.name,
                    "template_variables": rendered.used_variables,
                    "source": "candidate_pipeline_automation",
                    "candidate_review_id": str(review.id),
                }

            return {
                "candidate_id": str(candidate.id),
                "candidate_email": candidate.email,
                "email_type": "interview_invite",
                "subject": f"Interview invitation for "
                f"{candidate.role_applied_for or 'your application'}",
                "draft_body": (
                    f"Hi {candidate.full_name},\n\n"
                    "You have been shortlisted for the next stage. "
                    "Please confirm your availability for an interview.\n\n"
                    "Scheduling details are required before this email is sent:\n"
                    "- company_name\n"
                    "- interview_date\n"
                    "- interview_time\n"
                    "- interview_link\n"
                    "- recruiter_name\n\n"
                    "Best regards"
                ),
                "template_id": str(template.id),
                "template_name": template.name,
                "missing_template_variables": rendered.missing_variables,
                "source": "candidate_pipeline_automation",
                "candidate_review_id": str(review.id),
            }

        return {
            "candidate_id": str(candidate.id),
            "candidate_email": candidate.email,
            "email_type": "interview_invite",
            "subject": f"Interview invitation for "
            f"{candidate.role_applied_for or 'your application'}",
            "draft_body": (
                f"Hi {candidate.full_name},\n\n"
                "You have been shortlisted for the next stage. "
                "Please confirm your availability for an interview.\n\n"
                "Best regards"
            ),
            "source": "candidate_pipeline_automation",
            "candidate_review_id": str(review.id),
        }
