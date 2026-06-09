import os
from typing import Any, Dict, List

from dotenv import load_dotenv
from groq import Groq

from rag.hybrid_query import hybrid_search

from rag.guardrails.input_guardrails import validate_place_intelligence_question
from rag.guardrails.output_guardrails import validate_output_answer
from rag.guardrails.retrieval_guardrails import validate_retrieved_evidence


load_dotenv()


def get_required_env(key: str) -> str:
    value = os.getenv(key)

    if value is None or value.strip() == "":
        raise ValueError(
            f"Missing required environment variable: {key}. "
            f"Please define it in your .env file."
        )

    return value


def build_context_from_hybrid_results(results: List[Dict[str, Any]]) -> str:
    context_blocks = []

    for index, result in enumerate(results, start=1):
        metadata = result.get("metadata", {})
        document = result.get("document", "")

        context_blocks.append(
            f"""
Evidence Document {index}
Document ID: {result.get("id")}
RRF Score: {result.get("rrf_score")}
Dense Rank: {result.get("dense_rank")}
BM25 Rank: {result.get("bm25_rank")}
Matched By: {result.get("matched_by")}
Metadata: {metadata}

{document}
""".strip()
        )

    return "\n\n---\n\n".join(context_blocks)


def generate_answer_with_groq(question: str, context: str) -> str:
    client = Groq(api_key=get_required_env("GROQ_API_KEY"))
    model_name = get_required_env("GROQ_MODEL")

    system_prompt = """
You are a place intelligence analyst.

You answer questions using only the provided evidence from the place intelligence system.
The evidence comes from Postgres marts, ChromaDB vector search, BM25 keyword search, and Reciprocal Rank Fusion retrieval.

Rules:
1. Do not invent facts.
2. If the evidence is not enough, say that the evidence is not enough.
3. Explain the answer in simple business language.
4. Mention the status, confidence level, recommended action, and evidence when available.
5. Cite the evidence details you used, such as Evidence Document number, place/business name, address, status, matched sources, confidence level, recommended action, and evidence summary.
6. If multiple evidence documents support the answer, summarize the common pattern and cite 2-3 examples.
7. If the retrieved evidence is only partially relevant, say that clearly.
8. Keep the answer concise, clear, and useful.
9. If the user asks a question outside the Place Intelligence System, do not answer it.
10. Do not answer general knowledge, coding, personal, health, finance, sports, politics, or unrelated questions.
""".strip()

    user_prompt = f"""
User Question:
{question}

Retrieved Evidence:
{context}

Answer the user's question using only the retrieved evidence.
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

def build_evidence_payload(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    evidence = []

    for index, result in enumerate(results, start=1):
        evidence.append(
            {
                "rank": index,
                "document_id": result.get("id"),
                "rrf_score": result.get("rrf_score"),
                "dense_rank": result.get("dense_rank"),
                "bm25_rank": result.get("bm25_rank"),
                "dense_distance": result.get("dense_distance"),
                "bm25_score": result.get("bm25_score"),
                "matched_by": result.get("matched_by"),
                "metadata": result.get("metadata"),
                "document": result.get("document"),
            }
        )

    return evidence


def answer_question(question: str, top_k: int = 5) -> Dict[str, Any]:
    input_guardrail = validate_place_intelligence_question(question)

    if not input_guardrail.is_allowed:
        return {
            "question": question,
            "answer": input_guardrail.message,
            "evidence": [],
            "guardrails": {
                "input": input_guardrail.status,
                "retrieval": "not_run",
                "output": "not_run",
            },
        }

    results = hybrid_search(
        question=question,
        dense_top_k=15,
        bm25_top_k=15,
        final_top_k=top_k,
    )

    retrieval_guardrail = validate_retrieved_evidence(results)

    if not retrieval_guardrail.is_allowed:
        return {
            "question": question,
            "answer": retrieval_guardrail.message,
            "evidence": [],
            "guardrails": {
                "input": input_guardrail.status,
                "retrieval": retrieval_guardrail.status,
                "output": "not_run",
            },
        }

    context = build_context_from_hybrid_results(results)
    answer = generate_answer_with_groq(question=question, context=context)

    output_guardrail = validate_output_answer(answer)

    if not output_guardrail.is_allowed:
        return {
            "question": question,
            "answer": output_guardrail.message,
            "evidence": build_evidence_payload(results),
            "guardrails": {
                "input": input_guardrail.status,
                "retrieval": retrieval_guardrail.status,
                "output": output_guardrail.status,
            },
        }

    return {
        "question": question,
        "answer": answer,
        "evidence": build_evidence_payload(results),
        "guardrails": {
            "input": input_guardrail.status,
            "retrieval": retrieval_guardrail.status,
            "output": output_guardrail.status,
        },
    }


def print_answer(response: Dict[str, Any]) -> None:
    print("=" * 100)
    print("QUESTION")
    print("=" * 100)
    print(response["question"])

    print("\n" + "=" * 100)
    print("GUARDRAILS")
    print("=" * 100)
    print(response.get("guardrails", {}))

    print("\n" + "=" * 100)
    print("ANSWER")
    print("=" * 100)
    print(response["answer"])

    print("\n" + "=" * 100)
    print("EVIDENCE USED")
    print("=" * 100)

    for item in response["evidence"]:
        print(f"\nEvidence Rank: {item['rank']}")
        print(f"Document ID: {item['document_id']}")
        print(f"RRF Score: {item['rrf_score']}")
        print(f"Dense Rank: {item['dense_rank']}")
        print(f"BM25 Rank: {item['bm25_rank']}")
        print(f"Dense Distance: {item['dense_distance']}")
        print(f"BM25 Score: {item['bm25_score']}")
        print(f"Matched By: {item['matched_by']}")
        print(f"Metadata: {item['metadata']}")
        print("-" * 100)
        print(item["document"][:1000])
        print("-" * 100)


def main():
    question = input("Ask a question about place intelligence evidence: ").strip()

    response = answer_question(question=question, top_k=5)
    print_answer(response)


if __name__ == "__main__":
    main()