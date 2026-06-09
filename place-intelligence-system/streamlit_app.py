import os

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


st.set_page_config(
    page_title="Place Intelligence System",
    page_icon="🗺️",
    layout="wide",
)


def api_get(path: str):
    response = requests.get(f"{API_BASE_URL}{path}", timeout=30)
    response.raise_for_status()
    return response.json()


def api_post(path: str, payload: dict):
    response = requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=120)
    response.raise_for_status()
    return response.json()


def to_dataframe(payload: dict) -> pd.DataFrame:
    return pd.DataFrame(payload.get("data", []))


st.sidebar.title("Place Intelligence")
page = st.sidebar.radio(
    "Select Page",
    [
        "System Health",
        "Data Sources & Analytics",
        "RAG Assistant",
    ],
)


if page == "System Health":
    st.title("System Health")

    st.write("This page checks whether the API, Postgres, ChromaDB, Groq configuration, and dbt Docs are available.")

    if st.button("Run Health Check"):
        try:
            health = api_get("/health/full")

            col1, col2, col3, col4, col5 = st.columns(5)

            services = [
                ("API", health.get("api", {}), col1),
                ("Postgres", health.get("postgres", {}), col2),
                ("ChromaDB", health.get("chromadb", {}), col3),
                ("Groq", health.get("groq", {}), col4),
                ("dbt Docs", health.get("dbt_docs", {}), col5),
            ]

            for name, status, col in services:
                with col:
                    state = status.get("status", "unknown")
                    if state in ["ok", "configured"]:
                        st.success(f"{name}: {state}")
                    elif state == "warning":
                        st.warning(f"{name}: {state}")
                    else:
                        st.error(f"{name}: {state}")

            st.subheader("Full Health Details")
            st.json(health)

        except Exception as exc:
            st.error(f"Health check failed: {exc}")


elif page == "Data Sources & Analytics":
    st.title("Data Sources & Analytics")

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Datasource Row Counts",
            "Source Coverage",
            "Place Status Mart",
            "Change Detection Mart",
        ]
    )

    with tab1:
        st.subheader("Datasource and Mart Row Counts")

        try:
            df = to_dataframe(api_get("/datasources/summary"))
            st.dataframe(df, use_container_width=True)

            if not df.empty:
                chart_df = df.set_index("table_name")
                st.bar_chart(chart_df["row_count"])

        except Exception as exc:
            st.error(f"Failed to load datasource summary: {exc}")

    with tab2:
        st.subheader("Matched Source Coverage")

        try:
            df = to_dataframe(api_get("/analytics/source-coverage"))
            st.dataframe(df, use_container_width=True)

            if not df.empty:
                chart_df = df.set_index("matched_sources")
                st.bar_chart(chart_df["row_count"])

        except Exception as exc:
            st.error(f"Failed to load source coverage: {exc}")

    with tab3:
        st.subheader("Place Status Summary Mart")

        try:
            df = to_dataframe(api_get("/analytics/place-status-counts"))
            st.dataframe(df, use_container_width=True)

            if not df.empty:
                status_counts = (
                    df.groupby("final_place_status", as_index=False)["row_count"]
                    .sum()
                    .sort_values("row_count", ascending=False)
                )
                st.bar_chart(status_counts.set_index("final_place_status")["row_count"])

            st.subheader("Sample Place Status Records")
            sample_df = to_dataframe(api_get("/samples/place-status?limit=25"))
            st.dataframe(sample_df, use_container_width=True)

        except Exception as exc:
            st.error(f"Failed to load place status mart: {exc}")

    with tab4:
        st.subheader("Change Detection Mart")

        try:
            df = to_dataframe(api_get("/analytics/change-detection-counts"))
            st.dataframe(df, use_container_width=True)

            if not df.empty:
                change_counts = (
                    df.groupby("change_detection_status", as_index=False)["row_count"]
                    .sum()
                    .sort_values("row_count", ascending=False)
                )
                st.bar_chart(change_counts.set_index("change_detection_status")["row_count"])

            st.subheader("Sample Change Detection Records")
            sample_df = to_dataframe(api_get("/samples/change-detection?limit=25"))
            st.dataframe(sample_df, use_container_width=True)

        except Exception as exc:
            st.error(f"Failed to load change detection mart: {exc}")


elif page == "RAG Assistant":
    st.title("RAG Assistant")

    st.write(
        "Ask natural-language questions about active places, missing validation, closures, replacements, and evidence."
    )

    question = st.text_area(
        "Question",
        value="Why is a place marked active but missing Yelp validation?",
        height=100,
    )

    top_k = st.slider("Number of evidence documents", min_value=3, max_value=10, value=5)

    if st.button("Ask RAG"):
        if not question.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Retrieving evidence and generating answer..."):
                try:
                    result = api_post(
                        "/rag/ask",
                        {
                            "question": question,
                            "top_k": top_k,
                        },
                    )

                    st.subheader("Answer")
                    st.write(result.get("answer", ""))

                    st.subheader("Evidence Used")
                    evidence = result.get("evidence", [])

                    for item in evidence:
                        with st.expander(f"Evidence Rank {item.get('rank')}"):
                            st.write("Metadata")
                            st.json(item.get("metadata", {}))

                            st.write("Retrieval Scores")
                            st.json(
                                {
                                    "rrf_score": item.get("rrf_score"),
                                    "dense_rank": item.get("dense_rank"),
                                    "bm25_rank": item.get("bm25_rank"),
                                    "matched_by": item.get("matched_by"),
                                }
                            )

                            st.write("Document")
                            st.text(item.get("document", ""))

                except Exception as exc:
                    st.error(f"RAG request failed: {exc}")