from pathlib import Path
from typing import Any, Dict, List, Tuple
import re

import chromadb
from chromadb.config import Settings
from langchain_huggingface import HuggingFaceEmbeddings
from rank_bm25 import BM25Okapi


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHROMA_DIR = PROJECT_ROOT / "data" / "vector_store" / "chroma"
COLLECTION_NAME = "place_intelligence_evidence"


def get_collection():
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )

    return client.get_collection(name=COLLECTION_NAME)


def tokenize(text: str) -> List[str]:
    """
    Simple tokenizer for BM25 keyword search.
    Converts text to lowercase words.
    """
    if not text:
        return []

    return re.findall(r"\b[a-zA-Z0-9_#']+\b", text.lower())


def get_all_documents_from_chroma() -> Dict[str, Any]:
    """
    Loads all stored evidence documents from ChromaDB.

    This is needed for BM25 because BM25 ranks over the text corpus.
    """
    collection = get_collection()

    return collection.get(
        include=["documents", "metadatas"]
    )


def dense_vector_search(question: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Dense semantic search using embeddings + ChromaDB.
    Lower distance means more similar.
    """
    collection = get_collection()

    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    question_embedding = embedding_model.embed_query(question)

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    ranked_results = []

    for rank, (doc_id, document, metadata, distance) in enumerate(
        zip(ids, documents, metadatas, distances), start=1
    ):
        ranked_results.append(
            {
                "id": doc_id,
                "document": document,
                "metadata": metadata,
                "dense_rank": rank,
                "dense_distance": distance,
            }
        )

    return ranked_results


def bm25_keyword_search(question: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """
    BM25 keyword search over all evidence documents.
    Higher BM25 score means stronger keyword match.
    """
    chroma_data = get_all_documents_from_chroma()

    ids = chroma_data.get("ids", [])
    documents = chroma_data.get("documents", [])
    metadatas = chroma_data.get("metadatas", [])

    if not documents:
        return []

    tokenized_corpus = [tokenize(doc) for doc in documents]
    bm25 = BM25Okapi(tokenized_corpus)

    tokenized_question = tokenize(question)
    scores = bm25.get_scores(tokenized_question)

    scored_results = []

    for doc_id, document, metadata, score in zip(ids, documents, metadatas, scores):
        scored_results.append(
            {
                "id": doc_id,
                "document": document,
                "metadata": metadata,
                "bm25_score": float(score),
            }
        )

    scored_results.sort(key=lambda x: x["bm25_score"], reverse=True)

    top_results = []

    for rank, result in enumerate(scored_results[:top_k], start=1):
        result["bm25_rank"] = rank
        top_results.append(result)

    return top_results


def reciprocal_rank_fusion(
    dense_results: List[Dict[str, Any]],
    bm25_results: List[Dict[str, Any]],
    rrf_k: int = 60,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Combines dense search ranking and BM25 ranking using Reciprocal Rank Fusion.

    RRF score formula:
        score = 1 / (rrf_k + rank)

    Documents that rank high in both dense and BM25 search get stronger final scores.
    """
    fused: Dict[str, Dict[str, Any]] = {}

    for result in dense_results:
        doc_id = result["id"]
        dense_rank = result["dense_rank"]

        if doc_id not in fused:
            fused[doc_id] = {
                "id": doc_id,
                "document": result["document"],
                "metadata": result["metadata"],
                "rrf_score": 0.0,
                "dense_rank": None,
                "bm25_rank": None,
                "dense_distance": None,
                "bm25_score": None,
                "matched_by": [],
            }

        fused[doc_id]["rrf_score"] += 1 / (rrf_k + dense_rank)
        fused[doc_id]["dense_rank"] = dense_rank
        fused[doc_id]["dense_distance"] = result.get("dense_distance")
        fused[doc_id]["matched_by"].append("dense_vector")

    for result in bm25_results:
        doc_id = result["id"]
        bm25_rank = result["bm25_rank"]

        if doc_id not in fused:
            fused[doc_id] = {
                "id": doc_id,
                "document": result["document"],
                "metadata": result["metadata"],
                "rrf_score": 0.0,
                "dense_rank": None,
                "bm25_rank": None,
                "dense_distance": None,
                "bm25_score": None,
                "matched_by": [],
            }

        fused[doc_id]["rrf_score"] += 1 / (rrf_k + bm25_rank)
        fused[doc_id]["bm25_rank"] = bm25_rank
        fused[doc_id]["bm25_score"] = result.get("bm25_score")
        fused[doc_id]["matched_by"].append("bm25_keyword")

    final_results = list(fused.values())
    final_results.sort(key=lambda x: x["rrf_score"], reverse=True)

    return final_results[:top_k]


def hybrid_search(question: str, dense_top_k: int = 15, bm25_top_k: int = 15, final_top_k: int = 5):
    dense_results = dense_vector_search(question=question, top_k=dense_top_k)
    bm25_results = bm25_keyword_search(question=question, top_k=bm25_top_k)

    final_results = reciprocal_rank_fusion(
        dense_results=dense_results,
        bm25_results=bm25_results,
        rrf_k=60,
        top_k=final_top_k,
    )

    return final_results


def print_hybrid_results(results: List[Dict[str, Any]]) -> None:
    if not results:
        print("No hybrid search results found.")
        return

    for index, result in enumerate(results, start=1):
        print("=" * 100)
        print(f"HYBRID RESULT {index}")
        print("=" * 100)
        print(f"Document ID: {result['id']}")
        print(f"RRF Score: {result['rrf_score']}")
        print(f"Dense Rank: {result['dense_rank']}")
        print(f"BM25 Rank: {result['bm25_rank']}")
        print(f"Dense Distance: {result['dense_distance']}")
        print(f"BM25 Score: {result['bm25_score']}")
        print(f"Matched By: {', '.join(result['matched_by'])}")
        print(f"Metadata: {result['metadata']}")
        print("-" * 100)
        print(result["document"])
        print("=" * 100)
        print()


def main():
    question = input("Ask a question about place intelligence evidence: ").strip()

    if not question:
        print("Question cannot be empty.")
        return

    results = hybrid_search(
        question=question,
        dense_top_k=15,
        bm25_top_k=15,
        final_top_k=5,
    )

    print_hybrid_results(results)


if __name__ == "__main__":
    main()