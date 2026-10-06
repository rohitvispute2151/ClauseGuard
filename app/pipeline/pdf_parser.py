import io
import logging
from dataclasses import dataclass, field
import pypdf

logger = logging.getLogger(__name__)


@dataclass
class PageText:
    page_number: int
    content: str
    has_text_layer: bool = True
    metadata: dict = field(default_factory=dict)


class PDFParser:
    """Extracts text from PDF documents with page boundaries preserved."""

    def parse(self, file_bytes: bytes) -> list[PageText]:
        stream = io.BytesIO(file_bytes)
        reader = pypdf.PdfReader(stream)
        pages: list[PageText] = []

        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            text = page.extract_text() or ""
            cleaned_text = self._clean_text(text)
            has_text = len(cleaned_text.strip()) > 0

            pages.append(
                PageText(
                    page_number=page_num,
                    content=cleaned_text,
                    has_text_layer=has_text,
                    metadata={"char_count": len(cleaned_text)},
                )
            )

        logger.info(f"Parsed {len(pages)} pages from PDF")
        return pages

    def _clean_text(self, text: str) -> str:
        """Normalize line endings and excessive whitespace while preserving paragraph breaks."""
        lines = [line.strip() for line in text.splitlines()]
        paragraphs: list[str] = []
        current: list[str] = []

        for line in lines:
            if not line:
                if current:
                    paragraphs.append(" ".join(current))
                    current = []
            else:
                current.append(line)
        if current:
            paragraphs.append(" ".join(current))

        return "\n\n".join(paragraphs)
