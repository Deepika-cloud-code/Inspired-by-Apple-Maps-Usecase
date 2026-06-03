import os
from typing import List

from dotenv import load_dotenv
from groq import Groq

from query_vector_store import search_evidence


load_dotenv()


def get_required_env(key: str) -> str:
    value = os.getenv(key)

    if value is None or value.strip() == "":
        raise ValueError(
            f"Missing required environment variable: {key}. "
            f"Please define it in your .env file."
        )

    return value


def extract_documents_from_results(results) -> List[str]:
    documents = results.get("documents", [[]])[0]

    if not documents:
        return []

    return documents


def build_context(documents: List[str]) -> str:
    context_blocks = []

    for index, document in enumerate(documents, start=1):
        context_blocks.append(
            f"""
Evidence Document {index}:
{document}
""".strip()
        )

    return "\n\n---\n\n".join(context_blocks)


def ask_groq(question: str, context: str) -> str:
    client = Groq(api_key=get_required_env("GROQ_API_KEY"))

    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    system_prompt = """
You are a place intelligence analyst.

You answer questions using only the provided evidence from the place intelligence system.

The evidence comes from Postgres marts and ChromaDB retrieval.

Rules:
1. Do not invent facts.
2. If the evidence is not enough, say that the evidence is not enough.
3. Explain the answer in simple business language.
4. Mention the status, confidence level, recommended action, and evidence when available.
5. Keep the answer concise but clear.
""".strip()

    user_prompt = f"""
User Question:
{question}

Retrieved Evidence:
{context}

Answer the user's question using the retrieved evidence.
""".strip()

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=700,
    )

    return response.choices[0].message.content


def main():
    question = input("Ask a question about place intelligence evidence: ").strip()

    if not question:
        print("Question cannot be empty.")
        return

    print("\nSearching ChromaDB for evidence...\n")
    results = search_evidence(question=question, top_k=5)

    documents = extract_documents_from_results(results)

    if not documents:
        print("No matching evidence found in ChromaDB.")
        return

    context = build_context(documents)

    print("Sending retrieved evidence to Groq...\n")
    answer = ask_groq(question=question, context=context)

    print("=" * 100)
    print("GROQ RAG ANSWER")
    print("=" * 100)
    print(answer)
    print("=" * 100)


if __name__ == "__main__":
    main()