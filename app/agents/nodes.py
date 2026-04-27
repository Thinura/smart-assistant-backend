from uuid import UUID

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.intents import (
    detect_intent_by_rules,
    get_intent_classifier_prompt,
    normalize_intent,
)
from app.agents.state import AgentState
from app.models.approval_request import ApprovalActionType
from app.services.chat_model_service import get_chat_model
from app.services.tool_execution_service import ToolExecutionService


def classify_intent(state: AgentState) -> AgentState:
    rule_based_intent = detect_intent_by_rules(state["user_message"])

    if rule_based_intent is not None:
        return {
            **state,
            "intent": rule_based_intent,
        }

    model = get_chat_model()

    messages = [
        SystemMessage(content=get_intent_classifier_prompt()),
        HumanMessage(content=state["user_message"]),
    ]

    response = model.invoke(messages)
    intent = normalize_intent(str(response.content))

    return {
        **state,
        "intent": intent,
    }


def generate_general_response(state: AgentState) -> AgentState:
    model = get_chat_model()

    messages = [
        SystemMessage(
            content=(
                "You are Smart Assistant, a helpful AI assistant for agentic AI, "
                "HR, recruitment, and productivity workflows. "
                "Answer clearly and concisely."
            )
        ),
        HumanMessage(content=state["user_message"]),
    ]

    response = model.invoke(messages)

    return {
        **state,
        "assistant_message": str(response.content).strip(),
    }


def handle_document_qa(state: AgentState) -> AgentState:
    from app.db.session import SessionLocal

    db = SessionLocal()

    try:
        tool_execution_service = ToolExecutionService(db)

        result, tool_call = tool_execution_service.run_tool(
            tool_name="search_documents",
            payload={
                "query": state["user_message"],
                "top_k": 3,
                "document_type": detect_document_type_filter(state["user_message"]),
            },
            agent_run_id=state.get("agent_run_id"),
        )

        tool_result = {
            "tool_name": "search_documents",
            "tool_call_id": str(tool_call.id),
            "success": result.success,
            "data": result.data,
            "error": result.error,
        }

        existing_tool_results = state.get("tool_results", [])

        if not result.success or result.data is None:
            return {
                **state,
                "tool_results": [*existing_tool_results, tool_result],
                "assistant_message": "I could not search the uploaded documents right now.",
            }

        results = result.data.get("results", [])

        sources = [
            {
                "document_id": item["document_id"],
                "chunk_id": item["chunk_id"],
                "chunk_index": item["chunk_index"],
                "source": item["source"],
                "document_type": item.get("document_type"),
                "distance": item["distance"],
            }
            for item in results
        ]
        if not results:
            return {
                **state,
                "tool_results": [*existing_tool_results, tool_result],
                "sources": sources,
                "assistant_message": (
                    "I could not find relevant information in the uploaded documents."
                ),
            }

        context = "\n\n".join(
            f"Source: {item['source']}\nContent: {item['content']}" for item in results
        )

        model = get_chat_model()

        messages = [
            SystemMessage(
                content=(
                    "You are Smart Assistant. Answer the user's question using only "
                    "the provided document context. If the answer is not available "
                    "in the context, say you could not find it in the uploaded documents."
                )
            ),
            HumanMessage(
                content=(f"Document context:\n{context}\n\nUser question:\n{state['user_message']}")
            ),
        ]

        response = model.invoke(messages)

        return {
            **state,
            "tool_results": [*existing_tool_results, tool_result],
            "sources": [],
            "assistant_message": str(response.content).strip(),
        }

    finally:
        db.close()


def handle_candidate_review(state: AgentState) -> AgentState:
    from app.db.session import SessionLocal

    db = SessionLocal()

    try:
        tool_execution_service = ToolExecutionService(db)

        # For now, the user must include candidate_id in the message.
        # Example: "Review candidate b984ec8a-bcf3-4a11-b7a7-09c55ddf094e"
        candidate_id = extract_uuid_from_text(state["user_message"])

        if candidate_id is None:
            return {
                **state,
                "assistant_message": (
                    "Please provide the candidate ID so I can review the candidate."
                ),
            }

        result, tool_call = tool_execution_service.run_tool(
            tool_name="review_candidate",
            payload={
                "candidate_id": str(candidate_id),
            },
            agent_run_id=state.get("agent_run_id"),
        )

        tool_result = {
            "tool_name": "review_candidate",
            "tool_call_id": str(tool_call.id),
            "success": result.success,
            "data": result.data,
            "error": result.error,
        }

        existing_tool_results = state.get("tool_results", [])

        if not result.success or result.data is None:
            return {
                **state,
                "tool_results": [*existing_tool_results, tool_result],
                "assistant_message": result.error or "Candidate review failed.",
            }

        candidate = result.data["candidate"]
        review = result.data["review"]

        assistant_message = (
            f"Summary: {review['summary']}\n\n"
            f"Score: {review['score']}/100\n"
            f"Recommendation: {review['recommendation']}\n"
            f"Confidence: {review['confidence']}\n\n"
            "Strengths:\n"
            + "\n".join(f"- {item}" for item in review["strengths"])
            + "\n\nRisks/Gaps:\n"
            + "\n".join(f"- {item}" for item in review["risks"])
            + "\n\nInterview Focus Areas:\n"
            + "\n".join(f"- {item}" for item in review["interview_focus_areas"])
        )

        return {
            **state,
            "tool_results": [*existing_tool_results, tool_result],
            "sources": [
                {
                    "candidate_id": candidate["id"],
                    "cv_document_id": candidate["cv_document_id"],
                    "source": candidate["cv_source"],
                }
            ],
            "assistant_message": assistant_message,
        }

    finally:
        db.close()


def handle_email_draft(state: AgentState) -> AgentState:
    from app.db.session import SessionLocal

    db = SessionLocal()

    try:
        tool_execution_service = ToolExecutionService(db)
        candidate_id = extract_uuid_from_text(state["user_message"])

        if candidate_id is None:
            return {
                **state,
                "assistant_message": ("Please provide the candidate ID so I can draft the email."),
            }

        email_type = detect_email_type(state["user_message"])

        draft_result, draft_tool_call = tool_execution_service.run_tool(
            tool_name="draft_candidate_email",
            payload={
                "candidate_id": str(candidate_id),
                "email_type": email_type,
                "tone": "professional and kind",
            },
            agent_run_id=state.get("agent_run_id"),
        )

        existing_tool_results = state.get("tool_results", [])

        draft_tool_result = {
            "tool_name": "draft_candidate_email",
            "tool_call_id": str(draft_tool_call.id),
            "success": draft_result.success,
            "data": draft_result.data,
            "error": draft_result.error,
        }

        if not draft_result.success or draft_result.data is None:
            return {
                **state,
                "tool_results": [*existing_tool_results, draft_tool_result],
                "assistant_message": draft_result.error or "Email draft failed.",
            }

        candidate = draft_result.data["candidate"]
        email = draft_result.data["email"]

        approval_result, approval_tool_call = tool_execution_service.run_tool(
            tool_name="create_approval_request",
            payload={
                "agent_run_id": str(state["agent_run_id"]) if state.get("agent_run_id") else None,
                "action_type": ApprovalActionType.EMAIL_DRAFT.value,
                "title": f"Approve {email_type} email for {candidate['full_name']}",
                "description": ("Human review is required before this candidate email is used."),
                "action_payload": {
                    "candidate_id": candidate["id"],
                    "candidate_email": candidate["email"],
                    "email_type": email["type"],
                    "subject": email["subject"],
                    "draft_body": email["body"],
                },
            },
            agent_run_id=state.get("agent_run_id"),
        )

        approval_tool_result = {
            "tool_name": "create_approval_request",
            "tool_call_id": str(approval_tool_call.id),
            "success": approval_result.success,
            "data": approval_result.data,
            "error": approval_result.error,
        }

        all_tool_results = [
            *existing_tool_results,
            draft_tool_result,
            approval_tool_result,
        ]

        if not approval_result.success or approval_result.data is None:
            return {
                **state,
                "tool_results": all_tool_results,
                "assistant_message": (
                    "The email draft was created, but approval request creation failed."
                ),
            }

        approval_request_id = approval_result.data["approval_request_id"]

        assistant_message = (
            "Email draft created and submitted for human approval.\n\n"
            f"Approval Request ID: {approval_request_id}\n"
            f"Candidate: {candidate['full_name']}\n"
            f"Email Type: {email['type']}\n"
            f"Subject: {email['subject']}\n\n"
            f"Draft:\n{email['body']}"
        )

        return {
            **state,
            "tool_results": all_tool_results,
            "sources": [
                {
                    "candidate_id": candidate["id"],
                    "source": "candidate_profile",
                }
            ],
            "assistant_message": assistant_message,
        }

    finally:
        db.close()


def handle_unknown_intent(state: AgentState) -> AgentState:
    return {
        **state,
        "assistant_message": (
            "I could not clearly understand the request. "
            "Please ask again with a little more context."
        ),
    }


def detect_document_type_filter(message: str) -> str | None:
    normalized_message = message.lower()

    if "policy" in normalized_message:
        return "policy"

    if "cv" in normalized_message or "resume" in normalized_message:
        return "cv"

    if "job description" in normalized_message or "jd" in normalized_message:
        return "job_description"

    if "assignment" in normalized_message:
        return "assignment"

    return None


def extract_uuid_from_text(text: str) -> UUID | None:
    for token in text.replace(",", " ").replace(".", " ").split():
        try:
            return UUID(token)
        except ValueError:
            continue

    return None


def detect_email_type(message: str) -> str:
    normalized_message = message.lower()

    if "reject" in normalized_message or "rejection" in normalized_message:
        return "rejection"

    if "shortlist" in normalized_message or "selected" in normalized_message:
        return "shortlist"

    if "interview" in normalized_message or "invite" in normalized_message:
        return "interview_invite"

    if "follow" in normalized_message:
        return "follow_up"

    return "general"
