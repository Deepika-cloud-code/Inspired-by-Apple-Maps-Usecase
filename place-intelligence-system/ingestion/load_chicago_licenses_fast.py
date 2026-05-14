import os
import re
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

BUSINESS_LICENSE_HISTORY_FILE = "Business_Licenses_20260505.csv"
CURRENT_ACTIVE_LICENSE_FILE = "Business_Licenses_-_Current_Active_20260505.csv"


def clean_column_name(col: str) -> str:
    col = col.strip().lower()
    col = re.sub(r"[^a-z0-9]+", "_", col)
    col = col.strip("_")
    return col


def get_connection():
    load_dotenv(PROJECT_ROOT / ".env", override=True)

    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


def create_table_from_csv_header(conn, file_path: Path, table_name: str):
    sample_df = pd.read_csv(file_path, nrows=5, low_memory=False)

    cleaned_columns = [clean_column_name(col) for col in sample_df.columns]

    column_defs = ",\n".join(
        [f'"{col}" TEXT' for col in cleaned_columns]
    )

    create_sql = f"""
    DROP TABLE IF EXISTS {table_name};

    CREATE TABLE {table_name} (
        {column_defs}
    );
    """

    with conn.cursor() as cur:
        cur.execute(create_sql)

    conn.commit()

    return cleaned_columns


def create_clean_temp_csv(original_path: Path, cleaned_path: Path):
    print(f"Creating cleaned temp CSV: {cleaned_path}")

    first_chunk = True
    total_rows = 0

    for chunk in pd.read_csv(original_path, chunksize=100_000, low_memory=False):
        chunk.columns = [clean_column_name(col) for col in chunk.columns]

        chunk.to_csv(
            cleaned_path,
            mode="w" if first_chunk else "a",
            index=False,
            header=first_chunk,
            encoding="utf-8",
        )

        total_rows += len(chunk)
        first_chunk = False
        print(f"Prepared {total_rows:,} rows")

    print(f"Finished temp CSV: {cleaned_path}")


def copy_csv_to_postgres(conn, csv_path: Path, table_name: str):
    print(f"Loading with COPY: {csv_path.name} → {table_name}")

    with conn.cursor() as cur:
        with open(csv_path, "r", encoding="utf-8") as f:
            copy_sql = f"""
            COPY {table_name}
            FROM STDIN
            WITH (
                FORMAT CSV,
                HEADER TRUE,
                DELIMITER ',',
                QUOTE '"',
                ESCAPE '"'
            );
            """
            cur.copy_expert(copy_sql, f)

    conn.commit()
    print(f"Finished loading {table_name}")


def load_csv_fast(file_name: str, table_name: str):
    original_path = RAW_DIR / file_name
    temp_path = RAW_DIR / f"temp_cleaned_{file_name}"

    conn = get_connection()

    try:
        create_table_from_csv_header(conn, original_path, table_name)
        create_clean_temp_csv(original_path, temp_path)
        copy_csv_to_postgres(conn, temp_path, table_name)
    finally:
        conn.close()

    if temp_path.exists():
        temp_path.unlink()
        print(f"Deleted temp file: {temp_path.name}")


def main():
    load_csv_fast(
        BUSINESS_LICENSE_HISTORY_FILE,
        "raw_business_license_history",
    )

    load_csv_fast(
        CURRENT_ACTIVE_LICENSE_FILE,
        "raw_current_active_licenses",
    )


if __name__ == "__main__":
    main()