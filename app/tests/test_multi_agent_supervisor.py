from app.agents.supervisor import supervisor_agent


def test_supervisor_routes_candidate_review_to_candidate_agent() -> None:
    state = {
        "user_message": "Review candidate 123 for QA Intern",
    }

    result = supervisor_agent(state)

    assert result["selected_agent"] == "candidate_agent"


def test_supervisor_routes_email_request_to_email_agent() -> None:
    state = {
        "user_message": "Draft an interview invite email for candidate 123",
    }

    result = supervisor_agent(state)

    assert result["selected_agent"] == "email_agent"


def test_supervisor_routes_document_question_to_document_agent() -> None:
    state = {
        "user_message": "What does the policy document say about remote work?",
    }

    result = supervisor_agent(state)

    assert result["selected_agent"] == "document_agent"


def test_supervisor_routes_unknown_message_to_general_agent() -> None:
    state = {
        "user_message": "Hello there",
    }

    result = supervisor_agent(state)

    assert result["selected_agent"] == "general_agent"
