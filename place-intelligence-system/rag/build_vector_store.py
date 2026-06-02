from pathlib import Path
from typing import List

import chromadb
from chromadb.config import Settings
from langchain_huggingface import HuggingFaceEmbeddings

from build_evidence_documents import EvidenceDocument, build_change_documents, build_status_documents


CHROMA_DIR = Path("data/vector_store/chroma")
COLLECTION_NAME = "place_intelligence_evidence"


def build_all_evidence_documents(limit_per_mart: int = 1000) -> List[EvidenceDocument]:
    status_docs = build_status_documents(limit=limit_per_mart)
    change_docs = build_change_documents(limit=limit_per_mart)

    all_docs = status_docs + change_docs

    print(f"Built {len(status_docs)} current place status documents.")
    print(f"Built {len(change_docs)} place change detection documents.")
    print(f"Built {len(all_docs)} total evidence documents.")

    return all_docs


def create_chroma_collection():
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Evidence documents generated from Postgres marts."},
    )

    return collection


def build_vector_store(limit_per_mart: int = 1000):
    documents = build_all_evidence_documents(limit_per_mart=limit_per_mart)

    if not documents:
        print("No documents found. Check your Postgres mart tables.")
        return

    print("Loading local embedding model...")
    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    texts = [doc.text for doc in documents]
    ids = [doc.document_id for doc in documents]
    metadatas = [doc.metadata for doc in documents]

    print("Creating embeddings...")
    embeddings = embedding_model.embed_documents(texts)

    print("Creating/opening Chroma collection...")
    collection = create_chroma_collection()

    print("Clearing old documents from collection...")
    existing = collection.get()
    if existing and existing.get("ids"):
        collection.delete(ids=existing["ids"])

    print("Adding documents to ChromaDB...")
    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print("Vector store build complete.")
    print(f"Stored {collection.count()} documents in ChromaDB.")
    print(f"ChromaDB path: {CHROMA_DIR}")


def main():
    build_vector_store(limit_per_mart=1000)


if __name__ == "__main__":
    main()