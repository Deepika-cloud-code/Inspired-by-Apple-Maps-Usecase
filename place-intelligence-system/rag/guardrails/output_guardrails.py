from dataclasses import dataclass
from typing import List


@dataclass
class OutputGuardrailResult:
    is_allowed: bool
    status: str
    message: str


EMPTY_ANSWER_MESSAGE = "Generated answer is empty."

MISSING_EVIDENCE_CITATION_MESSAGE = (
    "The generated answer did not cite retrieved evidence clearly enough. "
    "Please try again with a more specific question."
)

OUT_OF_SCOPE_OUTPUT_MESSAGE = (
    "The generated answer appears to include content outside the Place Intelligence System. "
    "Please ask a question related to place status, source evidence, closures, replacements, "
    "confidence levels, or recommended actions."
)


PROJECT_TERMS: List[str] = [
    "evidence",
    "business",
    "place",
    "status",
    "confidence",
    "recommended action",
    "license",
    "chicago",
    "yelp",
    "openstreetmap",
    "osm",
    "closure",
    "replacement",
    "active",
    "inactive",
    "mart",
    "source",
]


def _contains_project_terms(answer: str) -> bool:
    normalized_answer = answer.lower()
    return any(term in normalized_answer for term in PROJECT_TERMS)


def _contains_evidence_reference(answer: str) -> bool:
    normalized_answer = answer.lower()

    citation_markers = [
        "evidence document",
        "evidence used",
        "based on the evidence",
        "cited evidence",
        "document 1",
        "document 2",
        "document 3",
    ]

    return any(marker in normalized_answer for marker in citation_markers)


def validate_output_answer(
    answer: str,
    require_evidence_reference: bool = True,
) -> OutputGuardrailResult:
    """
    Starter output guardrail.

    Checks that:
    - answer is not empty
    - answer is related to the Place Intelligence domain
    - answer cites evidence if required
    """

    if answer is None or answer.strip() == "":
        return OutputGuardrailResult(
            is_allowed=False,
            status="blocked_empty_answer",
            message=EMPTY_ANSWER_MESSAGE,
        )

    if not _contains_project_terms(answer):
        return OutputGuardrailResult(
            is_allowed=False,
            status="blocked_out_of_scope_output",
            message=OUT_OF_SCOPE_OUTPUT_MESSAGE,
        )

    if require_evidence_reference and not _contains_evidence_reference(answer):
        return OutputGuardrailResult(
            is_allowed=False,
            status="blocked_missing_evidence_reference",
            message=MISSING_EVIDENCE_CITATION_MESSAGE,
        )

    return OutputGuardrailResult(
        is_allowed=True,
        status="passed",
        message="Generated answer passed output guardrail.",
    )