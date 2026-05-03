

# Smart HR Assistant Backend

Smart HR Assistant Backend is a local-first Agentic AI backend built with FastAPI, LangGraph, LangChain, PostgreSQL, SQLAlchemy, Alembic, and Ollama.

The project demonstrates how an AI assistant can support HR and recruitment workflows such as candidate screening, CV review, job matching, document Q&A, interview kit generation, email drafting, human approval, outbox-based email sending, and multi-agent workflow orchestration.

---

## Project Purpose

This project was created as a hands-on Agentic AI portfolio project. The main goal is to show how a real-world assistant can be designed beyond simple chat by combining agents, tools, workflow persistence, approval flows, and business-specific automation.

The backend is designed to run locally first, while keeping the architecture clean enough to deploy to cloud platforms later.

---

## Tech Stack

| Area | Technology |
|---|---|
| Backend API | FastAPI |
| Agent Orchestration | LangGraph |
| LLM Integration | LangChain |
| Local LLM | Ollama |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Package Manager | Poetry |
| Testing | Pytest |
| Email | Console Provider / SMTP Provider |
| Architecture | Service + Tool + Agent based design |

---

## Core Features

### Candidate Management

- Create and manage candidates
- Link CV documents to candidates
- Update candidate status
- View a full candidate timeline

### Document Management

- Upload CVs, job descriptions, policies, and assignments
- Extract and store document text
- Chunk documents for retrieval
- Search uploaded documents
- Ask questions from uploaded documents

### Candidate Review

- Review a candidate using their profile and CV
- Generate structured review output
- Persist score, recommendation, strengths, risks, and interview focus areas
- Link review results to agent runs and candidate timelines

### Candidate Job Matching

- Match a candidate CV against a job description
- Generate match score and recommendation
- Identify matched skills, missing skills, risks, and interview focus areas

### Interview Kit Generation

- Generate technical interview questions
- Generate behavioral questions
- Generate risk-based questions
- Generate evaluation rubric
- Link interview kits to candidate reviews and job matches

### Email Drafting

- Draft candidate emails using candidate and role context
- Support template-based rendering
- Support customizable variables such as company name, recruiter name, interview date, interview time, interview link, and role name

### Human Approval Flow

- AI-generated email drafts are submitted for human approval
- Approval requests can be reviewed and updated before approval
- Approved requests can be executed into outbox messages

### Outbox and SMTP-Ready Sending

- Store generated emails in an outbox
- Test email sending locally using the console provider
- Switch to SMTP by changing environment variables
- Keep email sending provider-based so Gmail, Zoho, SendGrid, Mailgun, Amazon SES, or other SMTP providers can be used later

### Multi-Agent System

The backend includes a supervisor-based multi-agent design:

```text
User Message
    ↓
Supervisor Agent
    ↓
Candidate Agent / Document Agent / Email Agent / Workflow Agent / General Agent
```

Specialist agents handle focused responsibilities instead of placing all logic inside one general assistant.

### Multi-Step Workflow Agent

The workflow agent can run a complete interview preparation flow from one chat message:

```text
Prepare interview workflow for candidate <candidate_id> for QA Intern using job description <job_description_id> on 10 May 2026 at 10:00 AM https://meet.google.com/test
```

This can trigger:

1. Candidate review
2. Job matching
3. Interview kit generation
4. Email draft generation
5. Approval request creation
6. Workflow persistence
7. Candidate timeline update

---

## Architecture Overview

The project follows a layered architecture:

```text
API Layer
  └── FastAPI endpoints

Agent Layer
  └── LangGraph supervisor and specialist agents

Tool Layer
  └── Reusable business actions called by agents

Service Layer
  └── Core business logic and persistence orchestration

Model Layer
  └── SQLAlchemy database models

Schema Layer
  └── Pydantic request and response contracts
```

This separation keeps the system easier to test, extend, and debug.

---

## Architecture Evolution

### 1. Basic Assistant Backend

The project started as a simple FastAPI assistant backend with conversations, messages, and a local LLM response flow.

This proved the basic chat loop, but it was not enough for real HR automation.

### 2. Document-Aware Assistant

Document upload, text extraction, chunking, and document search were added. This allowed the assistant to answer questions based on uploaded CVs, job descriptions, and HR policies.

### 3. Tool-Based Agent Design

The logic was then shifted into reusable tools such as:

- `search_documents`
- `review_candidate`
- `draft_candidate_email`
- `create_approval_request`
- `match_candidate_to_job`
- `generate_interview_kit`

This was an important shift because agents became orchestrators instead of containing all business logic directly.

### 4. Human-in-the-Loop Approval

For HR use cases, the assistant should not directly send candidate emails without review. The flow was changed to require approval before an email can move to the outbox.

```text
AI drafts email
    ↓
Human approval request
    ↓
Approved request execution
    ↓
Outbox message
    ↓
Email provider
```

### 5. Multi-Agent Routing

A supervisor agent was added to route requests to specialist agents. This made the system closer to a real agentic application and easier to extend with new agents.

### 6. Workflow Persistence

Multi-step workflows were originally visible only through agent runs and tool calls. A dedicated workflow persistence layer was added so the product can show clear workflow history for each candidate.

### 7. Candidate Timeline

The candidate timeline was extended to show related records in one place, including reviews, job matches, interview kits, approvals, outbox messages, agent runs, audit logs, and workflow records.

---

## Key Issues Solved

### Document Q&A Context Handling

The document Q&A flow originally retrieved relevant chunks but the generated answer did not always use the context properly. The prompt and retrieval flow were improved so answers are grounded in uploaded documents.

### Agent Run Linking

Candidate review records needed to be connected back to the agent run that generated them. The review tool was updated to accept and persist `agent_run_id`.

### Database Session Consistency

The chat endpoint and graph nodes initially used separate database sessions. This caused visibility and foreign key issues during agent execution. The active database session is now passed through the LangGraph state so tools and agents operate within the same request context.

### Human Approval Safety

Email generation was changed from direct sending to an approval-first design. This makes the workflow safer and more realistic for HR operations.

### Tool Registry Completeness

As the system grew, newly added business capabilities needed to be registered as tools. The tool registry was expanded so the workflow agent can call job matching and interview kit generation tools.

### Service and Tool Alignment

Tool wrappers were aligned with existing service method signatures instead of duplicating business logic. This keeps endpoint behavior and agent behavior consistent.

### Circular Import Handling

When workflow persistence was added, model imports caused circular import issues. Model loading was adjusted so runtime imports remain clean while Alembic can still access metadata for migrations.

### Timeline Visibility

Workflow records were added to the candidate timeline so product users can see the complete candidate journey in one response.

---

## Local Setup

### Prerequisites

Install:

- Python 3.12
- Poetry
- Docker
- Docker Compose
- Ollama

Check versions:

```bash
python3 --version
poetry --version
docker --version
ollama --version
```

---

## Clone the Repository

```bash
git clone <your-repository-url>
cd smart-assistant-backend
```

---

## Install Dependencies

```bash
poetry install
```

Optional:

```bash
poetry shell
```

---

## Environment Variables

Create a local environment file:

```bash
cp .env.example .env
```

Example `.env`:

```env
APP_NAME=Smart HR Assistant Backend
APP_ENV=local
API_PREFIX=/api/v1

DATABASE_URL=postgresql+psycopg://smart_user:smart_password@localhost:5432/smart_assistant
TEST_DATABASE_URL=postgresql+psycopg://smart_user:smart_password@localhost:5432/smart_assistant_test

OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_LLM_MODEL=llama3.1

EMAIL_PROVIDER=console

SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
SMTP_FROM_NAME=Smart HR Assistant
SMTP_USE_TLS=true
```

For local development, keep:

```env
EMAIL_PROVIDER=console
```

For SMTP sending, change:

```env
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your_username
SMTP_PASSWORD=your_password
SMTP_FROM_EMAIL=hr@example.com
SMTP_FROM_NAME=HR Team
SMTP_USE_TLS=true
```

---

## Start Local Services

Start PostgreSQL:

```bash
docker compose up -d
```

Check running containers:

```bash
docker ps
```

---

## Start Ollama

Pull the local LLM model:

```bash
ollama pull llama3.1
```

Start Ollama:

```bash
ollama serve
```

In another terminal, verify the model:

```bash
ollama run llama3.1
```

---

## Run Database Migrations

Run migrations for both local and test databases:

```bash
make migrate-all
```

Manual alternative:

```bash
poetry run alembic upgrade head
ALEMBIC_DATABASE_URL=postgresql+psycopg://smart_user:smart_password@localhost:5432/smart_assistant_test poetry run alembic upgrade head
```

---

## Run the Backend

```bash
make run
```

Or:

```bash
poetry run uvicorn app.main:app --reload
```

The API runs at:

```text
http://localhost:8000
```

Swagger documentation:

```text
http://localhost:8000/docs
```

Health check:

```bash
curl http://localhost:8000/api/v1/health
```

---

## Tests and Code Quality

Run all tests:

```bash
make test
```

Run lint checks:

```bash
make lint
```

Auto-fix lint issues:

```bash
make fix
```

Run a focused test file:

```bash
poetry run pytest app/tests/test_multi_agent_workflow.py -vv -s
```

Check app import:

```bash
poetry run python -c "from app.main import app; print('ok')"
```

---

## Running the Main Workflow Locally

After the backend, database, migrations, and Ollama are running, the main workflow can be executed through the chat endpoint.

High-level local flow:

```text
Create conversation
Upload CV
Create candidate
Upload job description
Create interview email template
Send workflow request to chat endpoint
Review approval request
Execute approval
Send outbox message
View candidate timeline
```

The workflow request format:

```text
Prepare interview workflow for candidate <candidate_id> for QA Intern using job description <job_description_id> on 10 May 2026 at 10:00 AM https://meet.google.com/test
```

Expected workflow output includes:

```text
Interview workflow prepared successfully.

Workflow ID: ...
Candidate: ...
Review Score: ...
Recommendation: ...
Job match score: ...
Interview kit created: ...

Approval Request ID: ...
Email Subject: ...

Next step: review and approve the generated email before sending.
```

---

## Hosting Approach

The project is designed to be deployed in stages.

### Local Development

For development, the recommended setup is:

- FastAPI running locally
- PostgreSQL running in Docker
- Ollama running locally
- Console email provider

This keeps development free and simple.

### Simple Cloud Hosting

Possible backend hosting platforms:

- Render
- Railway
- Fly.io
- DigitalOcean App Platform
- AWS ECS

Possible PostgreSQL providers:

- Supabase
- Railway PostgreSQL
- Render PostgreSQL
- Neon
- AWS RDS

Possible LLM providers:

- Local Ollama for development
- Hosted Ollama server
- OpenAI-compatible API
- Groq
- Together AI
- AWS Bedrock

Possible email providers:

- Gmail SMTP
- Zoho SMTP
- SendGrid SMTP
- Mailgun SMTP
- Amazon SES

---

## Recommended Production Architecture

```text
Frontend or Mobile App
        ↓
FastAPI Backend
        ↓
PostgreSQL Database
        ↓
LLM Provider
        ↓
SMTP Provider
```

For production, a hosted LLM provider is recommended unless a dedicated GPU server is available.

---

## Current Status

Implemented:

- Candidate CRUD
- Document upload and document search
- Document Q&A
- Candidate review
- Candidate job matching
- Interview kit generation
- Email templates
- Email draft generation
- Human approval flow
- Outbox
- Console and SMTP-ready email provider design
- Multi-agent supervisor
- Specialist agents
- Workflow agent
- Workflow persistence
- Candidate timeline integration
- Audit logs
- Automated test coverage for core flows

---

## Next Improvements

Planned improvements:

- Frontend dashboard
- React Native mobile app
- Streaming chat responses
- Voice input and text-to-speech output
- Better natural language variable extraction
- Role-based access control
- Background worker for outbox sending
- Email delivery retries
- Workflow failure recovery
- Docker production deployment
- CI/CD pipeline

---

## Useful Commands

```bash
poetry install
docker compose up -d
make migrate-all
make run
make test
make lint
make fix
```

Focused workflow test:

```bash
poetry run pytest app/tests/test_multi_agent_workflow.py -vv -s
```

App import check:

```bash
poetry run python -c "from app.main import app; print('ok')"
```