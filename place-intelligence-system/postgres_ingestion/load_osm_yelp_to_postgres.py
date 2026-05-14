import os
import json
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

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

    connection_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    return create_engine(connection_url)


def load_osm_geojson(engine):
    file_path = RAW_DIR / OSM_GEOJSON_FILE

    print(f"\nLoading OSM GeoJSON: {file_path.name} → raw_osm_places")

    with open(file_path, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

    rows = []

    for feature in geojson_data.get("features", []):
        props = feature.get("properties", {})
        geometry = feature.get("geometry", {})

        coordinates = geometry.get("coordinates", [None, None])

        latitude = None
        longitude = None

        if geometry.get("type") == "Point" and len(coordinates) >= 2:
            longitude = coordinates[0]
            latitude = coordinates[1]

        rows.append(
            {
                "osm_id": props.get("@id"),
                "name": props.get("name"),
                "amenity": props.get("amenity"),
                "shop": props.get("shop"),
                "tourism": props.get("tourism"),
                "house_number": props.get("addr:housenumber"),
                "street": props.get("addr:street"),
                "city": props.get("addr:city"),
                "state": props.get("addr:state"),
                "postcode": props.get("addr:postcode"),
                "phone": props.get("phone"),
                "website": props.get("website"),
                "opening_hours": props.get("opening_hours"),
                "latitude": latitude,
                "longitude": longitude,
                "raw_properties": json.dumps(props),
                "raw_geometry": json.dumps(geometry),
            }
        )

    df = pd.DataFrame(rows)

    df.to_sql(
        "raw_osm_places",
        engine,
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=5000,
    )

    print(f"Finished loading raw_osm_places: {len(df):,} rows")


def load_yelp_business_json(engine, chunksize=50_000):
    file_path = RAW_DIR / YELP_BUSINESS_FILE

    print(f"\nLoading Yelp JSON: {file_path.name} → raw_yelp_businesses")

    first_chunk = True
    rows = []
    total_rows = 0

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)

            rows.append(
                {
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
                }
            )

            if len(rows) >= chunksize:
                df = pd.DataFrame(rows)

                df.to_sql(
                    "raw_yelp_businesses",
                    engine,
                    if_exists="replace" if first_chunk else "append",
                    index=False,
                    method="multi",
                    chunksize=5000,
                )

                total_rows += len(df)
                print(f"Loaded {total_rows:,} Yelp rows")

                rows = []
                first_chunk = False

    if rows:
        df = pd.DataFrame(rows)

        df.to_sql(
            "raw_yelp_businesses",
            engine,
            if_exists="replace" if first_chunk else "append",
            index=False,
            method="multi",
            chunksize=5000,
        )

        total_rows += len(df)
        print(f"Loaded {total_rows:,} Yelp rows")

    print("Finished loading raw_yelp_businesses")


def main():
    engine = get_engine()

    load_osm_geojson(engine)
    load_yelp_business_json(engine)


if __name__ == "__main__":
    main()