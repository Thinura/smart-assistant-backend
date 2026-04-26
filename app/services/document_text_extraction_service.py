from collections.abc import Callable
from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader

Extractor = Callable[[Path], str]


class DocumentTextExtractionService:
    def __init__(self) -> None:
        self._extractors: dict[str, Extractor] = {
            "text/plain": self._extract_txt,
            "application/pdf": self._extract_pdf,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (
                self._extract_docx
            ),
        }

    @property
    def supported_content_types(self) -> set[str]:
        return set(self._extractors.keys())

    def is_supported(self, content_type: str | None) -> bool:
        return content_type in self._extractors

    def extract_text(self, file_path: str, content_type: str) -> str:
        extractor = self._extractors.get(content_type)

        if extractor is None:
            raise ValueError(f"Unsupported content type for extraction: {content_type}")

        return extractor(Path(file_path)).strip()

    def _extract_txt(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def _extract_pdf(self, path: Path) -> str:
        reader = PdfReader(str(path))
        pages_text = [page.extract_text() or "" for page in reader.pages]

        return "\n".join(pages_text)

    def _extract_docx(self, path: Path) -> str:
        document = DocxDocument(str(path))
        paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]

        return "\n".join(paragraphs)
