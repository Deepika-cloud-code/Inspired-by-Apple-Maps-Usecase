# 1. Keep a small static list of project-domain words
# 2. Load business names, statuses, actions, and document types from ChromaDB
# 3. Allow the question if it matches either:
#    - project-domain terms
#    - actual business/place names from your evidence
#    - actual status/action values from marts
# 4. Block clearly unrelated questions
# 5. Provide user feedback on why a question was blocked

# This version does not rely only on hardcoded terms. It uses:

# Static project terms
# +
# Actual business names from Chroma metadata
# +
# Actual statuses from marts
# +
# Actual recommended actions
# +
# Actual document types

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set

import chromadb
from chromadb.config import Settings


@dataclass
class InputGuardrailResult:
    is_allowed: bool
    status: str
    message: str


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHROMA_DIR = PROJECT_ROOT / "data" / "vector_store" / "chroma"
COLLECTION_NAME = "place_intelligence_evidence"


STATIC_DOMAIN_KEYWORDS: List[str] = [
    "place",
    "places",
    "business",
    "businesses",
    "license",
    "licenses",
    "chicago",
    "yelp",
    "osm",
    "openstreetmap",
    "source",
    "sources",
    "evidence",
    "active",
    "inactive",
    "closed",
    "closure",
    "replaced",
    "replacement",
    "changed",
    "change",
    "validation",
    "external",
    "confidence",
    "recommended",
    "recommendation",
    "action",
    "mart",
    "marts",
    "status",
    "stale",
    "map",
    "maps",
    "address",
    "matched",
    "matching",
    "fuzzy",
    "rag",
    "cluster",
    "clusters",
    "current",
    "historical",
    "history",
    "open",
    "missing",
    "datasource",
    "data source",
    "row count",
    "dbt",
    "postgres",
    "postgresql",
    "chroma",
    "chromadb",
    "groq",
    "change detection",
    "place status",
    "source coverage",
]


BLOCKED_KEYWORDS: List[str] = [
    "president",
    "prime minister",
    "election",
    "stock",
    "crypto",
    "bitcoin",
    "weather",
    "sports",
    "football",
    "movie",
    "recipe",
    "health",
    "medical",
    "dating",
    "love letter",
    "leetcode",
    "resume",
    "cover letter",
    "salary",
    "visa",
    "immigration",
    "makeup",
    "travel itinerary",
]


OUT_OF_SCOPE_MESSAGE = (
    "I can only answer questions related to the Place Intelligence System, "
    "such as business status, closures, replacements, source evidence, "
    "Chicago licenses, Yelp, OpenStreetMap, confidence levels, recommended actions, "
    "dbt marts, and RAG evidence. Please ask a question related to this project."
)


EMPTY_QUESTION_MESSAGE = "Question cannot be empty."


def normalize_text(text: str) -> str:
    return text.lower().strip()


def tokenize(text: str) -> List[str]:
    if not text:
        return []

    return re.findall(r"\b[a-zA-Z0-9_#'&.-]+\b", text.lower())


def contains_phrase(text: str, phrases: List[str]) -> bool:
    return any(phrase.lower() in text for phrase in phrases)


def get_chroma_collection():
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )

    return client.get_collection(name=COLLECTION_NAME)


def load_dynamic_allowed_terms_from_chroma(limit: int = 5000) -> Set[str]:
    """
    Builds a dynamic allowed-term set from ChromaDB evidence metadata.

    This is better than blindly extracting every word from the full evidence text.
    Metadata fields are cleaner and more domain-specific.
    """

    allowed_terms: Set[str] = set()

    try:
        collection = get_chroma_collection()
        data = collection.get(
            include=["metadatas", "documents"],
            limit=limit,
        )

        metadatas = data.get("metadatas", []) or []
        documents = data.get("documents", []) or []

        for metadata in metadatas:
            if not metadata:
                continue

            for key in [
                "business_name",
                "city",
                "status",
                "confidence_level",
                "recommended_action",
                "document_type",
            ]:
                value = metadata.get(key)

                if value is None:
                    continue

                value_text = str(value).lower().strip()

                if value_text:
                    allowed_terms.add(value_text)

                for token in tokenize(value_text):
                    if len(token) >= 3:
                        allowed_terms.add(token)

        # Add selected structured phrases from evidence text.
        # Do not add every token from every document, because that makes guardrails too loose.
        structured_phrases = [
            "final place status",
            "confidence level",
            "recommended action",
            "matched sources",
            "fuzzy match types",
            "change detection status",
            "closure signal",
            "replacement signal",
            "external staleness signal",
            "evidence summary",
            "current place status",
            "place change detection",
        ]

        for phrase in structured_phrases:
            allowed_terms.add(phrase)

        # Optional: add important source/system words if they appear in documents.
        source_terms = [
            "chicago_current_active_license",
            "chicago_business_license_history",
            "openstreetmap",
            "yelp",
            "officially_active_but_missing_external_sources",
            "active_but_missing_yelp_validation",
            "old_business_replaced_by_new_business",
            "historical_business_likely_closed",
            "business_has_historical_continuity",
        ]

        for term in source_terms:
            allowed_terms.add(term.lower())

    except Exception:
        # If Chroma is unavailable, fallback to static keywords only.
        return set(STATIC_DOMAIN_KEYWORDS)

    return allowed_terms.union(set(STATIC_DOMAIN_KEYWORDS))


def validate_place_intelligence_question(question: str) -> InputGuardrailResult:
    """
    Input guardrail for the Place Intelligence RAG chatbot.

    This guardrail allows:
    - project-domain questions
    - questions containing actual business/place/status/action terms from ChromaDB
    - questions about evidence, marts, sources, closures, replacements, and validation

    It blocks clearly unrelated questions before retrieval or LLM calls.
    """

    if question is None or question.strip() == "":
        return InputGuardrailResult(
            is_allowed=False,
            status="blocked_empty_question",
            message=EMPTY_QUESTION_MESSAGE,
        )

    normalized_question = normalize_text(question)

    has_blocked_topic = contains_phrase(normalized_question, BLOCKED_KEYWORDS)

    dynamic_allowed_terms = load_dynamic_allowed_terms_from_chroma()

    question_tokens = set(tokenize(normalized_question))

    has_allowed_phrase = any(
        allowed_term in normalized_question
        for allowed_term in dynamic_allowed_terms
        if " " in allowed_term or "_" in allowed_term
    )

    has_allowed_token = any(
        token in dynamic_allowed_terms
        for token in question_tokens
    )

    has_allowed_topic = has_allowed_phrase or has_allowed_token

    if has_blocked_topic and not has_allowed_topic:
        return InputGuardrailResult(
            is_allowed=False,
            status="blocked_out_of_scope",
            message=OUT_OF_SCOPE_MESSAGE,
        )

    if not has_allowed_topic:
        return InputGuardrailResult(
            is_allowed=False,
            status="blocked_out_of_scope",
            message=OUT_OF_SCOPE_MESSAGE,
        )

    return InputGuardrailResult(
        is_allowed=True,
        status="passed",
        message="Question passed input guardrail.",
    )