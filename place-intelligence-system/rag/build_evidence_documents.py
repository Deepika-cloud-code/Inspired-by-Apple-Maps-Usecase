import os
from dataclasses import dataclass
from typing import Any, Dict, List

import pandas as pd
import psycopg2
from dotenv import load_dotenv


load_dotenv()


@dataclass
class EvidenceDocument:
    document_id: str
    document_type: str
    text: str
    metadata: Dict[str, Any]


def get_required_env(key: str) -> str:
    value = os.getenv(key)

    if value is None or value.strip() == "":
        raise ValueError(
            f"Missing required environment variable: {key}. "
            f"Please define it in your .env file."
        )

    return value


def get_connection():
    return psycopg2.connect(
        host=get_required_env("POSTGRES_HOST"),
        port=get_required_env("POSTGRES_PORT"),
        dbname=get_required_env("POSTGRES_DB"),
        user=get_required_env("POSTGRES_USER"),
        password=get_required_env("POSTGRES_PASSWORD"),
    )


def read_sql(query: str) -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)


def build_status_documents(limit: int = 1000) -> List[EvidenceDocument]:
    query = f"""
        select
            place_cluster_id,
            canonical_business_name,
            canonical_address,
            canonical_city,
            canonical_state,
            canonical_postal_code,
            final_place_status,
            confidence_level,
            recommended_action,
            matched_sources,
            fuzzy_match_types,
            concatenated_values
        from mart_place_status_summary
        limit {limit}
    """

    df = read_sql(query)
    documents: List[EvidenceDocument] = []

    for _, row in df.iterrows():
        text = f"""
Document Type: Current Place Status
Place Cluster ID: {row["place_cluster_id"]}
Business Name: {row["canonical_business_name"]}
Address: {row["canonical_address"]}, {row["canonical_city"]}, {row["canonical_state"]} {row["canonical_postal_code"]}
Final Place Status: {row["final_place_status"]}
Confidence Level: {row["confidence_level"]}
Recommended Action: {row["recommended_action"]}
Matched Sources: {row["matched_sources"]}
Fuzzy Match Types: {row["fuzzy_match_types"]}
Evidence: {row["concatenated_values"]}
""".strip()

        documents.append(
            EvidenceDocument(
                document_id=f"status::{row['place_cluster_id']}",
                document_type="current_place_status",
                text=text,
                metadata={
                    "document_type": "current_place_status",
                    "place_cluster_id": row["place_cluster_id"],
                    "business_name": row["canonical_business_name"],
                    "city": row["canonical_city"],
                    "status": row["final_place_status"],
                    "confidence_level": row["confidence_level"],
                    "recommended_action": row["recommended_action"],
                },
            )
        )

    return documents


def build_change_documents(limit: int = 1000) -> List[EvidenceDocument]:
    query = f"""
        select
            place_change_id,
            historical_business_name,
            historical_address,
            historical_city,
            historical_state,
            historical_postal_code,
            change_detection_status,
            closure_signal,
            replacement_signal,
            external_staleness_signal,
            confidence_level,
            recommended_action,
            evidence_summary
        from mart_place_change_detection
        limit {limit}
    """

    df = read_sql(query)
    documents: List[EvidenceDocument] = []

    for _, row in df.iterrows():
        text = f"""
Document Type: Place Change Detection
Place Change ID: {row["place_change_id"]}
Historical Business Name: {row["historical_business_name"]}
Historical Address: {row["historical_address"]}, {row["historical_city"]}, {row["historical_state"]} {row["historical_postal_code"]}
Change Detection Status: {row["change_detection_status"]}
Closure Signal: {row["closure_signal"]}
Replacement Signal: {row["replacement_signal"]}
External Staleness Signal: {row["external_staleness_signal"]}
Confidence Level: {row["confidence_level"]}
Recommended Action: {row["recommended_action"]}
Evidence Summary: {row["evidence_summary"]}
""".strip()

        documents.append(
            EvidenceDocument(
                document_id=f"change::{row['place_change_id']}",
                document_type="place_change_detection",
                text=text,
                metadata={
                    "document_type": "place_change_detection",
                    "place_change_id": row["place_change_id"],
                    "business_name": row["historical_business_name"],
                    "city": row["historical_city"],
                    "status": row["change_detection_status"],
                    "confidence_level": row["confidence_level"],
                    "recommended_action": row["recommended_action"],
                },
            )
        )

    return documents


def main():
    status_docs = build_status_documents(limit=1000)
    change_docs = build_change_documents(limit=1000)

    all_docs = status_docs + change_docs

    print(f"Built {len(status_docs)} current place status evidence documents.")
    print(f"Built {len(change_docs)} place change detection evidence documents.")
    print(f"Built {len(all_docs)} total evidence documents.")

    if all_docs:
        print("\nSample evidence document:\n")
        print(all_docs[0].text)
    else:
        print("No evidence documents were built. Check mart tables in Postgres.")


if __name__ == "__main__":
    main()