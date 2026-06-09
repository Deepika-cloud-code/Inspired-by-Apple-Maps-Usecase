from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class RetrievalGuardrailResult:
    is_allowed: bool
    status: str
    message: str


NO_EVIDENCE_MESSAGE = (
    "I could not find enough matching evidence in the Place Intelligence vector store "
    "to answer this question. Try asking about business status, closures, replacements, "
    "source evidence, Chicago licenses, Yelp, OpenStreetMap, or recommended actions."
)


WEAK_EVIDENCE_MESSAGE = (
    "The retrieved evidence appears weak or only partially relevant. "
    "Please ask a more specific Place Intelligence question, such as a business name, "
    "status type, source name, or recommended action."
)


def _has_required_result_fields(result: Dict[str, Any]) -> bool:
    return bool(result.get("document")) and bool(result.get("metadata"))


def _is_score_reasonable(result: Dict[str, Any]) -> bool:
    """
    Starter relevance check.

    RRF score is usually small, but if a result has either dense_rank or bm25_rank,
    we can consider it retrievable evidence for now.

    Later, you can tighten this with:
    - minimum RRF score
    - maximum dense distance
    - minimum BM25 score
    - required metadata fields
    """

    dense_rank = result.get("dense_rank")
    bm25_rank = result.get("bm25_rank")

    return dense_rank is not None or bm25_rank is not None


def validate_retrieved_evidence(
    results: List[Dict[str, Any]],
    min_results: int = 1,
) -> RetrievalGuardrailResult:
    """
    Retrieval guardrail for hybrid search results.

    This blocks the LLM call when:
    - no evidence was retrieved
    - retrieved results are malformed
    - retrieved evidence is too weak

    For now this is intentionally simple. It can be improved later with
    RRF score thresholds, dense distance thresholds, metadata filtering,
    and source-specific checks.
    """

    if not results:
        return RetrievalGuardrailResult(
            is_allowed=False,
            status="blocked_no_retrieved_evidence",
            message=NO_EVIDENCE_MESSAGE,
        )

    valid_results = [
        result
        for result in results
        if _has_required_result_fields(result) and _is_score_reasonable(result)
    ]

    if len(valid_results) < min_results:
        return RetrievalGuardrailResult(
            is_allowed=False,
            status="blocked_weak_or_malformed_evidence",
            message=WEAK_EVIDENCE_MESSAGE,
        )

    return RetrievalGuardrailResult(
        is_allowed=True,
        status="passed",
        message="Retrieved evidence passed retrieval guardrail.",
    )