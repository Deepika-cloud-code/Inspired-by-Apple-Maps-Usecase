import os
from typing import Any, Dict, List

import chromadb
import psycopg2
import requests
from chromadb.config import Settings
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from psycopg2.extras import RealDictCursor

from rag.rag_answer import answer_question


load_dotenv()

app = FastAPI(
    title="Place Intelligence API",
    description="API layer for Postgres marts, ChromaDB evidence retrieval, and Groq-powered RAG.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_DIR = os.path.join(PROJECT_ROOT, "data", "vector_store", "chroma")
COLLECTION_NAME = "place_intelligence_evidence"


class AskRequest(BaseModel):
    question: str
    top_k: int = 5


def get_required_env(key: str) -> str:
    value = os.getenv(key)

    if value is None or value.strip() == "":
        raise ValueError(f"Missing required environment variable: {key}")

    return value


def get_connection():
    return psycopg2.connect(
        host=get_required_env("POSTGRES_HOST"),
        port=get_required_env("POSTGRES_PORT"),
        dbname=get_required_env("POSTGRES_DB"),
        user=get_required_env("POSTGRES_USER"),
        password=get_required_env("POSTGRES_PASSWORD"),
    )


def run_query(query: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]


@app.get("/")
def root():
    return {
        "message": "Place Intelligence API is running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "place-intelligence-api"}


@app.get("/health/full")
def full_health():
    health_status = {
        "api": {"status": "ok"},
        "postgres": {"status": "unknown"},
        "chromadb": {"status": "unknown"},
        "groq": {"status": "unknown"},
        "dbt_docs": {"status": "unknown"},
    }

    try:
        rows = run_query("select 1 as ok;")
        health_status["postgres"] = {"status": "ok", "result": rows[0]["ok"]}
    except Exception as exc:
        health_status["postgres"] = {"status": "error", "detail": str(exc)}

    try:
        client = chromadb.PersistentClient(
            path=CHROMA_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
        collection = client.get_collection(name=COLLECTION_NAME)
        health_status["chromadb"] = {
            "status": "ok",
            "collection": COLLECTION_NAME,
            "document_count": collection.count(),
            "path": CHROMA_DIR,
        }
    except Exception as exc:
        health_status["chromadb"] = {"status": "error", "detail": str(exc)}

    try:
        groq_key = get_required_env("GROQ_API_KEY")
        groq_model = get_required_env("GROQ_MODEL")
        health_status["groq"] = {
            "status": "configured",
            "model": groq_model,
            "api_key_present": bool(groq_key),
        }
    except Exception as exc:
        health_status["groq"] = {"status": "error", "detail": str(exc)}

    dbt_docs_url = os.getenv("DBT_DOCS_URL", "http://localhost:8081")
    try:
        response = requests.get(dbt_docs_url, timeout=3)
        health_status["dbt_docs"] = {
            "status": "ok" if response.status_code == 200 else "warning",
            "url": dbt_docs_url,
            "status_code": response.status_code,
        }
    except Exception as exc:
        health_status["dbt_docs"] = {
            "status": "error",
            "url": dbt_docs_url,
            "detail": str(exc),
        }

    return health_status


@app.get("/datasources/summary")
def datasource_summary():
    query = """
        select 'raw_business_license_history' as table_name, count(*) as row_count
        from raw_business_license_history

        union all

        select 'raw_current_active_licenses' as table_name, count(*) as row_count
        from raw_current_active_licenses

        union all

        select 'raw_osm_places' as table_name, count(*) as row_count
        from raw_osm_places

        union all

        select 'raw_yelp_businesses' as table_name, count(*) as row_count
        from raw_yelp_businesses

        union all

        select 'mart_place_status_summary' as table_name, count(*) as row_count
        from mart_place_status_summary

        union all

        select 'mart_place_change_detection' as table_name, count(*) as row_count
        from mart_place_change_detection
        order by table_name;
    """
    return {"data": run_query(query)}


@app.get("/analytics/source-coverage")
def source_coverage():
    query = """
        select
            matched_sources,
            count(*) as row_count
        from mart_place_status_summary
        group by matched_sources
        order by row_count desc;
    """
    return {"data": run_query(query)}


@app.get("/analytics/place-status-counts")
def place_status_counts():
    query = """
        select
            final_place_status,
            confidence_level,
            recommended_action,
            count(*) as row_count
        from mart_place_status_summary
        group by
            final_place_status,
            confidence_level,
            recommended_action
        order by row_count desc;
    """
    return {"data": run_query(query)}


@app.get("/analytics/change-detection-counts")
def change_detection_counts():
    query = """
        select
            change_detection_status,
            closure_signal,
            replacement_signal,
            external_staleness_signal,
            confidence_level,
            recommended_action,
            count(*) as row_count
        from mart_place_change_detection
        group by
            change_detection_status,
            closure_signal,
            replacement_signal,
            external_staleness_signal,
            confidence_level,
            recommended_action
        order by row_count desc;
    """
    return {"data": run_query(query)}


@app.get("/samples/place-status")
def sample_place_status(limit: int = 25):
    query = f"""
        select
            place_cluster_id,
            canonical_business_name,
            canonical_address,
            canonical_city,
            final_place_status,
            confidence_level,
            recommended_action,
            matched_sources,
            fuzzy_match_types
        from mart_place_status_summary
        limit {limit};
    """
    return {"data": run_query(query)}


@app.get("/samples/change-detection")
def sample_change_detection(limit: int = 25):
    query = f"""
        select
            place_change_id,
            historical_business_name,
            historical_address,
            historical_city,
            change_detection_status,
            confidence_level,
            recommended_action,
            replacement_business_name
        from mart_place_change_detection
        limit {limit};
    """
    return {"data": run_query(query)}


@app.post("/rag/ask")
def rag_ask(request: AskRequest):
    response = answer_question(question=request.question, top_k=request.top_k)
    return response