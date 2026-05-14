import json
from pathlib import Path

import pandas as pd


# This file is inside:
# place-intelligence-system/ingestion/inspect_raw_files.py
#
# parents[1] takes us back to:
# place-intelligence-system/
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"


BUSINESS_LICENSE_HISTORY_FILE = "Business_Licenses_20260505.csv"
CURRENT_ACTIVE_LICENSE_FILE = "Business_Licenses_-_Current_Active_20260505.csv"
OSM_GEOJSON_FILE = "export.geojson"
YELP_BUSINESS_FILE = "yelp_academic_dataset_business.json"


def print_section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def inspect_csv(file_name: str, sample_rows: int = 5) -> None:
    path = RAW_DIR / file_name

    print_section(f"Inspecting CSV: {file_name}")

    if not path.exists():
        print(f"File not found: {path}")
        return

    df_sample = pd.read_csv(path, nrows=sample_rows, low_memory=False)

    print(f"File path: {path}")
    print(f"Sample shape: {df_sample.shape}")

    print("\nColumns:")
    for col in df_sample.columns:
        print(f" - {col}")

    print("\nSample rows:")
    print(df_sample.head(sample_rows))

    print("\nSample data types:")
    print(df_sample.dtypes)


def count_csv_rows(file_name: str) -> None:
    path = RAW_DIR / file_name

    print_section(f"Counting rows for CSV: {file_name}")

    if not path.exists():
        print(f"File not found: {path}")
        return

    row_count = 0

    for chunk in pd.read_csv(path, chunksize=100_000, low_memory=False):
        row_count += len(chunk)

    print(f"Total rows: {row_count:,}")


def inspect_geojson(file_name: str) -> None:
    path = RAW_DIR / file_name

    print_section(f"Inspecting GeoJSON: {file_name}")

    if not path.exists():
        print(f"File not found: {path}")
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])

    print(f"File path: {path}")
    print(f"GeoJSON type: {data.get('type')}")
    print(f"Generator: {data.get('generator')}")
    print(f"Timestamp: {data.get('timestamp')}")
    print(f"Total OSM features: {len(features):,}")

    if not features:
        print("No features found.")
        return

    first_feature = features[0]
    first_properties = first_feature.get("properties", {})
    first_geometry = first_feature.get("geometry", {})

    print("\nFirst feature properties:")
    for key, value in first_properties.items():
        print(f" - {key}: {value}")

    print("\nFirst feature geometry:")
    print(first_geometry)

    amenity_counts = {}

    for feature in features:
        properties = feature.get("properties", {})
        amenity = properties.get("amenity", "UNKNOWN")
        amenity_counts[amenity] = amenity_counts.get(amenity, 0) + 1

    print("\nAmenity counts:")
    for amenity, count in sorted(amenity_counts.items(), key=lambda x: x[1], reverse=True):
        print(f" - {amenity}: {count}")


def inspect_yelp_business_json(file_name: str, sample_rows: int = 5) -> None:
    path = RAW_DIR / file_name

    print_section(f"Inspecting Yelp JSON: {file_name}")

    if not path.exists():
        print(f"File not found: {path}")
        return

    records = []

    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= sample_rows:
                break
            records.append(json.loads(line))

    if not records:
        print("No records found.")
        return

    df_sample = pd.DataFrame(records)

    print(f"File path: {path}")
    print(f"Sample shape: {df_sample.shape}")

    print("\nColumns:")
    for col in df_sample.columns:
        print(f" - {col}")

    print("\nSample rows:")
    print(df_sample.head(sample_rows))

    print("\nFirst business record:")
    for key, value in records[0].items():
        print(f" - {key}: {value}")


def count_yelp_json_rows(file_name: str) -> None:
    path = RAW_DIR / file_name

    print_section(f"Counting rows for Yelp JSON: {file_name}")

    if not path.exists():
        print(f"File not found: {path}")
        return

    row_count = 0

    with open(path, "r", encoding="utf-8") as f:
        for _ in f:
            row_count += 1

    print(f"Total Yelp business records: {row_count:,}")


def main() -> None:
    print_section("RAW DATA INSPECTION STARTED")
    print(f"Raw data directory: {RAW_DIR}")

    inspect_csv(BUSINESS_LICENSE_HISTORY_FILE)
    count_csv_rows(BUSINESS_LICENSE_HISTORY_FILE)

    inspect_csv(CURRENT_ACTIVE_LICENSE_FILE)
    count_csv_rows(CURRENT_ACTIVE_LICENSE_FILE)

    inspect_geojson(OSM_GEOJSON_FILE)

    inspect_yelp_business_json(YELP_BUSINESS_FILE)
    count_yelp_json_rows(YELP_BUSINESS_FILE)

    print_section("RAW DATA INSPECTION COMPLETED")


if __name__ == "__main__":
    main()