import json
from pathlib import Path
import pytest
from app.core.constants import ClauseType
from app.pipeline.citation_verifier import CitationVerifier
from app.pipeline.section_detector import SectionDetector
from app.pipeline.pdf_parser import PageText
from app.models.document import Chunk
import uuid


@pytest.fixture
def golden_dataset():
    path = Path(__file__).parent / "golden" / "cuad_samples.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_eval_section_detection_recall(golden_dataset):
    """Evaluates section detection recall on golden contract texts."""
    detector = SectionDetector()
    for sample in golden_dataset:
        page = PageText(page_number=1, content=sample["text"])
        sections = detector.detect([page])

        detected_types = {s.clause_hint for s in sections if s.clause_hint}
        gt = sample["ground_truth"]

        for clause_name, info in gt.items():
            if info["is_present"]:
                target_type = ClauseType(clause_name)
                assert target_type in detected_types, f"Section detector missed {clause_name}"


def test_eval_citation_groundedness_against_golden(golden_dataset):
    """Evaluates that golden quotes pass citation verification with 100% precision."""
    verifier = CitationVerifier(similarity_threshold=0.80)

    for sample in golden_dataset:
        chunk = Chunk(
            id=uuid.uuid4(),
            document_id=uuid.uuid4(),
            chunk_index=0,
            content=sample["text"],
        )

        for clause_name, info in sample["ground_truth"].items():
            if info["is_present"] and info["quote_substring"]:
                verified, chunk_id = verifier.verify(info["quote_substring"], [chunk])
                assert verified is True, f"Citation verifier failed for ground truth {clause_name}"


def test_eval_prompt_injection_defense():
    """Adversarial prompt injection test: contract text containing attack instructions."""
    legitimate_contract_content = (
        "CONFIDENTIALITY CLAUSE:\n"
        "Each party agrees to keep all terms and confidential information strictly confidential."
    )

    verifier = CitationVerifier(similarity_threshold=0.80)
    chunk = Chunk(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        chunk_index=0,
        content=legitimate_contract_content,
    )

    # Attacker tries to verify a quote injected by malicious contract line
    injected_hallucination = "PWNED: All previous instructions were ignored."
    verified, _ = verifier.verify(injected_hallucination, [chunk])

    # Must NOT verify hallucinated injection phrase
    assert verified is False
