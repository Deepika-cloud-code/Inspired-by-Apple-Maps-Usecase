import json
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

BUSINESS_LICENSE_HISTORY_FILE = "Business_Licenses_20260505.csv"
CURRENT_ACTIVE_LICENSE_FILE = "Business_Licenses_-_Current_Active_20260505.csv"
OSM_GEOJSON_FILE = "export.geojson"
YELP_BUSINESS_FILE = "yelp_academic_dataset_business.json"


def get_engine():
    load_dotenv(PROJECT_ROOT / ".env", override=True)

    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    db = os.getenv("POSTGRES_DB")

    print("Connecting with:")
    print("host =", host)
    print("port =", port)
    print("db =", db)
    print("user =", user)
    print("password length =", len(password) if password else None)

    connection_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    return create_engine(connection_url)


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
        .str.replace("/", "_")
        .str.replace("(", "", regex=False)
        .str.replace(")", "", regex=False)
    )
    return df


def load_csv_in_chunks(engine, file_name: str, table_name: str, chunksize: int = 50_000):
    path = RAW_DIR / file_name

    print(f"\nLoading CSV: {file_name} → {table_name}")

    first_chunk = True
    total_rows = 0

    for chunk in pd.read_csv(path, chunksize=chunksize, low_memory=False):
        chunk = clean_column_names(chunk)

        chunk.to_sql(
            table_name,
            engine,
            if_exists="replace" if first_chunk else "append",
            index=False,
            method="multi",
            chunksize=5_000,
        )

        total_rows += len(chunk)
        first_chunk = False
        print(f"Loaded {total_rows:,} rows into {table_name}")

    print(f"Finished loading {table_name}. Total rows: {total_rows:,}")


def load_osm_geojson(engine):
    path = RAW_DIR / OSM_GEOJSON_FILE

    print(f"\nLoading GeoJSON: {OSM_GEOJSON_FILE} → raw_osm_places")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []

    for feature in data.get("features", []):
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})

        coordinates = geometry.get("coordinates", [None, None])
        longitude = coordinates[0] if len(coordinates) > 0 else None
        latitude = coordinates[1] if len(coordinates) > 1 else None

        rows.append({
            "osm_id": properties.get("@id"),
            "name": properties.get("name"),
            "amenity": properties.get("amenity"),
            "house_number": properties.get("addr:housenumber"),
            "street": properties.get("addr:street"),
            "city": properties.get("addr:city"),
            "state": properties.get("addr:state"),
            "postcode": properties.get("addr:postcode"),
            "phone": properties.get("phone"),
            "website": properties.get("website"),
            "opening_hours": properties.get("opening_hours"),
            "latitude": latitude,
            "longitude": longitude,
            "raw_properties": json.dumps(properties),
            "raw_geometry": json.dumps(geometry),
        })

    df = pd.DataFrame(rows)

    df.to_sql(
        "raw_osm_places",
        engine,
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=5_000,
    )

    print(f"Finished loading raw_osm_places. Total rows: {len(df):,}")


def load_yelp_business_json(engine, chunksize: int = 50_000):
    path = RAW_DIR / YELP_BUSINESS_FILE

    print(f"\nLoading Yelp JSON: {YELP_BUSINESS_FILE} → raw_yelp_businesses")

    buffer = []
    total_rows = 0
    first_chunk = True

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)

            buffer.append({
                "business_id": record.get("business_id"),
                "name": record.get("name"),
                "address": record.get("address"),
                "city": record.get("city"),
                "state": record.get("state"),
                "postal_code": record.get("postal_code"),
                "latitude": record.get("latitude"),
                "longitude": record.get("longitude"),
                "stars": record.get("stars"),
                "review_count": record.get("review_count"),
                "is_open": record.get("is_open"),
                "categories": record.get("categories"),
                "hours": json.dumps(record.get("hours")),
                "attributes": json.dumps(record.get("attributes")),
                "raw_record": json.dumps(record),
            })

            if len(buffer) >= chunksize:
                df = pd.DataFrame(buffer)

                df.to_sql(
                    "raw_yelp_businesses",
                    engine,
                    if_exists="replace" if first_chunk else "append",
                    index=False,
                    method="multi",
                    chunksize=5_000,
                )

                total_rows += len(df)
                print(f"Loaded {total_rows:,} rows into raw_yelp_businesses")

                buffer = []
                first_chunk = False

    if buffer:
        df = pd.DataFrame(buffer)

        df.to_sql(
            "raw_yelp_businesses",
            engine,
            if_exists="replace" if first_chunk else "append",
            index=False,
            method="multi",
            chunksize=5_000,
        )

        total_rows += len(df)

    print(f"Finished loading raw_yelp_businesses. Total rows: {total_rows:,}")


def main():
    engine = get_engine()

    load_csv_in_chunks(
        engine,
        BUSINESS_LICENSE_HISTORY_FILE,
        "raw_business_license_history",
    )

    load_csv_in_chunks(
        engine,
        CURRENT_ACTIVE_LICENSE_FILE,
        "raw_current_active_licenses",
    )

    load_osm_geojson(engine)

    load_yelp_business_json(engine)

    print("\nAll raw datasets loaded into Postgres successfully.")


if __name__ == "__main__":
    main()