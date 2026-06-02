from pathlib import Path

import chromadb
from chromadb.config import Settings
from langchain_huggingface import HuggingFaceEmbeddings


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHROMA_DIR = PROJECT_ROOT / "data" / "vector_store" / "chroma"
COLLECTION_NAME = "place_intelligence_evidence"


def get_collection():
    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )

    return client.get_collection(name=COLLECTION_NAME)


def search_evidence(question: str, top_k: int = 5):
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

    return results


def print_results(results):
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        print("No matching evidence found.")
        return

    for i, (doc, metadata, distance) in enumerate(
        zip(documents, metadatas, distances), start=1
    ):
        print("=" * 100)
        print(f"RESULT {i}")
        print(f"Distance: {distance}")
        print(f"Metadata: {metadata}")
        print("-" * 100)
        print(doc)
        print("=" * 100)
        print()


def main():
    question = input("Ask a question about place intelligence evidence: ").strip()

    if not question:
        print("Question cannot be empty.")
        return

    results = search_evidence(question=question, top_k=5)
    print_results(results)


if __name__ == "__main__":
    main()