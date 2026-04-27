from enum import StrEnum


class AgentIntent(StrEnum):
    GENERAL_CHAT = "general_chat"
    DOCUMENT_QA = "document_qa"
    CANDIDATE_REVIEW = "candidate_review"
    EMAIL_DRAFT = "email_draft"
    UNKNOWN = "unknown"


INTENT_DESCRIPTIONS: dict[AgentIntent, str] = {
    AgentIntent.GENERAL_CHAT: "General assistant questions or normal conversation.",
    AgentIntent.DOCUMENT_QA: "Questions that require answering from uploaded documents.",
    AgentIntent.CANDIDATE_REVIEW: "Requests to review CVs, candidates, assignments, or JD fit.",
    AgentIntent.EMAIL_DRAFT: "Requests to draft candidate or HR-related emails.",
    AgentIntent.UNKNOWN: "Fallback when the request cannot be classified.",
}


CLASSIFIABLE_INTENTS: list[AgentIntent] = [
    AgentIntent.GENERAL_CHAT,
    AgentIntent.DOCUMENT_QA,
    AgentIntent.CANDIDATE_REVIEW,
    AgentIntent.EMAIL_DRAFT,
    AgentIntent.UNKNOWN,
]


def get_intent_labels() -> list[str]:
    return [intent.value for intent in CLASSIFIABLE_INTENTS]


def get_intent_classifier_prompt() -> str:
    labels = ", ".join(get_intent_labels())

    descriptions = "\n".join(
        f"- {intent.value}: {description}" for intent, description in INTENT_DESCRIPTIONS.items()
    )

    return (
        "You are an intent classifier for an agentic AI recruitment assistant.\n"
        f"Return only one label from this list: {labels}.\n\n"
        "Intent descriptions:\n"
        f"{descriptions}\n\n"
        "Important: return only the label. Do not explain."
    )


def normalize_intent(value: str) -> AgentIntent:
    normalized = value.strip().lower()

    for intent in CLASSIFIABLE_INTENTS:
        if normalized == intent.value:
            return intent

    return AgentIntent.UNKNOWN


def detect_intent_by_rules(message: str) -> AgentIntent | None:
    normalized_message = message.strip().lower()

    document_keywords = [
        "uploaded document",
        "uploaded file",
        "from the document",
        "from uploaded document",
        "according to the document",
        "according to uploaded document",
        "based on the document",
        "based on uploaded document",
        "policy document",
        "document says",
        "file says",
        "pdf",
        "docx",
    ]

    candidate_keywords = [
        "review candidate",
        "review this candidate",
        "candidate review",
        "review this cv",
        "review cv",
        "match this candidate",
        "match candidate",
        "jd match",
        "job description match",
        "resume review",
        "assignment review",
    ]

    email_keywords = [
        "draft email",
        "write email",
        "email draft",
        "rejection email",
        "shortlist email",
        "interview invite",
        "follow-up email",
        "candidate email",
    ]

    if any(keyword in normalized_message for keyword in document_keywords):
        return AgentIntent.DOCUMENT_QA

    if any(keyword in normalized_message for keyword in candidate_keywords):
        return AgentIntent.CANDIDATE_REVIEW

    if any(keyword in normalized_message for keyword in email_keywords):
        return AgentIntent.EMAIL_DRAFT

    return None
