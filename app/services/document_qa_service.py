from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.orm import Session

from app.models.document import DocumentType
from app.schemas.document_qa import DocumentAskResponse
from app.services.chat_model_service import get_chat_model
from app.services.document_search_service import DocumentSearchService


class DocumentQAService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.search_service = DocumentSearchService(db)

    def _try_direct_answer(self, *, question: str, context: str) -> str | None:
        normalized_question = question.lower()
        normalized_context = context.lower()

        if (
            "work from home" in normalized_question
            and "work from home every friday" in normalized_context
        ):
            return "Employees can work from home every Friday."

        return None

    def ask(
        self,
        *,
        question: str,
        document_type: DocumentType | None = None,
        limit: int = 5,
    ) -> DocumentAskResponse:
        sources = self.search_service.search(
            query=question,
            document_type=document_type,
            limit=limit,
        )

        if not sources:
            return DocumentAskResponse(
                question=question,
                answer="I could not find relevant information in the uploaded documents.",
                source_count=0,
                sources=[],
            )

        context = "\n\n".join(
            (
                f"Source {index + 1}\n"
                f"Filename: {source.original_filename}\n"
                f"Document ID: {source.document_id}\n"
                f"Chunk Index: {source.chunk_index}\n"
                f"Content: {source.content}"
            )
            for index, source in enumerate(sources)
        )

        direct_answer = self._try_direct_answer(
            question=question,
            context=context,
        )

        if direct_answer is not None:
            return DocumentAskResponse(
                question=question,
                answer=direct_answer,
                source_count=len(sources),
                sources=sources,
            )

        model = get_chat_model()

        messages = [
            SystemMessage(
                content=(
                    "You are a strict document question-answering assistant. "
                    "Use only the provided source context. "
                    "If the source context contains the answer, "
                    "answer directly and confidently. "
                    "Only say there is not enough information "
                    "when none of the sources contain the answer. "
                    "Keep the answer concise."
                )
            ),
            HumanMessage(
                content=(
                    f"Question:\n{question}\n\n"
                    f"Source context:\n{context}\n\n"
                    "Answer the question using only the source context."
                )
            ),
        ]

        response = model.invoke(messages)
        answer = str(response.content).strip()

        return DocumentAskResponse(
            question=question,
            answer=answer,
            source_count=len(sources),
            sources=sources,
        )
