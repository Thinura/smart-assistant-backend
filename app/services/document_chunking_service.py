class DocumentChunkingService:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 120) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> list[str]:
        cleaned_text = " ".join(text.split())

        if not cleaned_text:
            return []

        chunks: list[str] = []
        start = 0

        while start < len(cleaned_text):
            end = start + self.chunk_size
            chunk = cleaned_text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            if end >= len(cleaned_text):
                break

            start = end - self.chunk_overlap

        return chunks
