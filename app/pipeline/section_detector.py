import re
from dataclasses import dataclass
from app.core.constants import ClauseType
from app.pipeline.pdf_parser import PageText


@dataclass
class Section:
    name: str
    page_number: int
    clause_hint: ClauseType | None
    content: str


class SectionDetector:
    """Identifies structural contract sections and clause type hints."""

    HEADING_PATTERNS = [
        re.compile(r"^(?:section|article|clause)?\s*(\d+[\.\d]*)\s*[:\-\.]?\s*([A-Z\s,–\-/]{3,80})$", re.IGNORECASE),
        re.compile(r"^(\d+\.[\d\.]*)\s+([A-Za-z\s,–\-/]{3,80})$"),
        re.compile(r"^([A-Z\s]{4,60})$"),
    ]

    KEYWORD_MAP: dict[str, ClauseType] = {
        "termination": ClauseType.TERMINATION,
        "term and termination": ClauseType.TERMINATION,
        "cancellation": ClauseType.TERMINATION,
        "liability": ClauseType.LIABILITY_CAP,
        "limitation of liability": ClauseType.LIABILITY_CAP,
        "indemnity": ClauseType.INDEMNITY,
        "indemnification": ClauseType.INDEMNITY,
        "renewal": ClauseType.AUTO_RENEWAL,
        "automatic renewal": ClauseType.AUTO_RENEWAL,
        "governing law": ClauseType.GOVERNING_LAW,
        "jurisdiction": ClauseType.GOVERNING_LAW,
        "confidential": ClauseType.CONFIDENTIALITY,
        "confidentiality": ClauseType.CONFIDENTIALITY,
        "intellectual property": ClauseType.IP_OWNERSHIP,
        "proprietary rights": ClauseType.IP_OWNERSHIP,
        "non-compete": ClauseType.NON_COMPETE,
        "non-competition": ClauseType.NON_COMPETE,
        "force majeure": ClauseType.FORCE_MAJEURE,
        "assignment": ClauseType.ASSIGNMENT,
    }

    def detect(self, pages: list[PageText]) -> list[Section]:
        sections: list[Section] = []
        current_name = "General Provisions"
        current_hint: ClauseType | None = None
        current_content: list[str] = []
        current_page = 1

        for page in pages:
            lines = page.content.split("\n")
            for line in lines:
                trimmed = line.strip()
                if not trimmed:
                    continue
                detected_heading = self._check_heading(trimmed)
                if detected_heading:
                    if current_content:
                        sections.append(
                            Section(
                                name=current_name,
                                page_number=current_page,
                                clause_hint=current_hint,
                                content="\n".join(current_content),
                            )
                        )
                        current_content = []

                    current_name = detected_heading
                    current_hint = self._match_clause_type(detected_heading)
                    current_page = page.page_number
                else:
                    current_content.append(trimmed)

        if current_content:
            sections.append(
                Section(
                    name=current_name,
                    page_number=current_page,
                    clause_hint=current_hint,
                    content="\n".join(current_content),
                )
            )

        return sections

    def _check_heading(self, paragraph: str) -> str | None:
        trimmed = paragraph.strip().rstrip(".:-")
        if len(trimmed) > 120 or "\n" in trimmed:
            return None

        for pattern in self.HEADING_PATTERNS:
            match = pattern.match(trimmed)
            if match:
                groups = match.groups()
                return groups[-1].strip().title()

        # Check for standalone keywords or numbered headings (e.g. '2. Term and Termination')
        lower = trimmed.lower()
        cleaned = re.sub(r"^\d+[\.\d]*\s*", "", lower).strip()
        for kw in self.KEYWORD_MAP:
            if cleaned == kw or cleaned == f"section {kw}" or cleaned == f"article {kw}":
                return cleaned.title()

        return None

    def _match_clause_type(self, heading: str) -> ClauseType | None:
        lower = heading.lower()
        for kw, clause_type in self.KEYWORD_MAP.items():
            if kw in lower:
                return clause_type
        return None
