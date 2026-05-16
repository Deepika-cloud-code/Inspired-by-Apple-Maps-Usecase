# Real-Time Place Intelligence System

## Problem Statement

Digital map applications become inaccurate when real-world places change faster than the database updates.

Examples include:

- A restaurant closes permanently
- A store moves from Building A to Building B
- Business hours change
- A place is duplicated under slightly different names
- A new business opens at an old address

If stale data remains in the map system, users may:

- Navigate to incorrect locations
- Visit closed businesses
- See outdated business details
- Experience poor trust in the mapping platform

---

# What We Are Trying to Solve

We are building a **Place Change Verification System** that can detect and verify real-world business changes using multiple open-source signals.

The system should answer questions such as:

- Is this place still active?
- Did this business move?
- Is the address different across sources?
- Is this place duplicated?
- Should the master place database be updated?
- How confident are we about this change?

---

# Core Idea

Instead of trusting a single source blindly, the system gathers evidence from multiple independent signals.

## Data Sources

- Chicago Business Licenses
- OpenStreetMap POI data
- Yelp dataset
- Simulated user reports

---

# Decision-Making Logic

The system compares evidence across all sources and generates a confidence-based decision.

## Confidence Outcomes

| Confidence Level | Action |
|---|---|
| High Confidence | Propose automatic database update |
| Medium Confidence | Send for human review |
| Low Confidence | Store as weak signal for future verification |

---

# Goal of the System

Build a scalable, intelligent, and continuously updating place intelligence platform that can:

- Detect stale map information
- Verify business changes using evidence
- Reduce incorrect map records
- Improve trust in location-based applications
- Support future AI agents and RAG-based reasoning systems

---

# Dataset Mapping and Business Signals

The project uses multiple independent open-source datasets to verify whether place information in a mapping system is accurate, stale, moved, duplicated, or inactive.

Each dataset contributes a different type of business signal.

---

# Dataset Mapping

| File Name | Internal Dataset Name | Purpose | Signal Type |
|---|---|---|---|
| `Business_Licenses_20260505.csv` | `raw_business_license_history` | Historical Chicago business license records | Official government/business history signal |
| `Business_Licenses_-_Current_Active_20260505.csv` | `raw_current_active_licenses` | Currently active licensed businesses in Chicago | Official active-business verification signal |
| `export.geojson` | `raw_osm_places` | OpenStreetMap points-of-interest and location data | Map/location intelligence signal |
| `yelp_academic_dataset_business.json` | `raw_yelp_businesses` | Yelp business metadata and business activity data | Commercial/business activity signal |

---

# Business Questions Answered by Each Dataset

## 1. Chicago Business License History Dataset

### File

```text
Business_Licenses_20260505.csv
```

### Purpose

Provides historical government business license records.

### Questions It Helps Answer

- Was this business previously active?
- Did the business change address?
- Did the business category/activity change?
- Was the license expired or renewed?
- Does the historical address differ from current records?

### Example Signals

| Observation | Possible Interpretation |
|---|---|
| License expired | Possible closure |
| Address changed | Possible relocation |
| New business activity | Category/type update |

---

## 2. Chicago Current Active Licenses Dataset

### File

```text
Business_Licenses_-_Current_Active_20260505.csv
```

### Purpose

Represents officially active businesses currently licensed in Chicago.

### Questions It Helps Answer

- Is the business currently active?
- Is the business officially operating?
- Does the business still exist in current records?

### Example Signals

| Observation | Possible Interpretation |
|---|---|
| Business missing from active licenses | Possible closure |
| Active status confirmed | Likely operational |

---

## 3. OpenStreetMap Dataset

### File

```text
export.geojson
```

### Purpose

Represents map-based place and POI information.

### Questions It Helps Answer

- Does the place currently exist on the map?
- What coordinates are associated with the place?
- Does the address match official records?
- What category/type does the map system assign?
- Are opening hours available?

### Example Signals

| Observation | Possible Interpretation |
|---|---|
| Address mismatch | Possible move |
| Coordinates changed | Possible relocation |
| Place removed from OSM | Possible closure |

---

## 4. Yelp Business Dataset

### File

```text
yelp_academic_dataset_business.json
```

### Purpose

Provides commercial business metadata and consumer-facing business information.

### Questions It Helps Answer

- Does Yelp consider the business open?
- What categories are associated with the business?
- Does Yelp address match official/map records?
- Is the business still actively listed?
- What are the business hours?

### Example Signals

| Observation | Possible Interpretation |
|---|---|
| `is_open = 0` | Possible closure |
| Address differs from OSM/license | Possible relocation |
| Missing listing | Possible inactive business |

---

# Why Multiple Signals Matter

No single dataset is fully reliable.

The system compares evidence across all sources before deciding whether the master place database should be updated.

## Example

| Source | Observation |
|---|---|
| Chicago Active License | Business active |
| OSM | Place exists |
| Yelp | `is_open = 0` |
| User Reports | Multiple closure complaints |

The system then:

- Retrieves evidence
- Compares conflicting signals
- Calculates confidence
- Proposes a database update recommendation

---

# Final Goal

Build a scalable AI-powered place intelligence platform capable of:

- Detecting stale map records
- Verifying business changes
- Identifying relocations and closures
- Reducing incorrect map information
- Supporting future RAG and agentic AI workflows

---

# Current Implementation Progress: PostgreSQL Ingestion and dbt Staging Layer

This section documents the implementation completed so far, from raw dataset ingestion into PostgreSQL to the creation and validation of dbt staging models.

---

# 1. PostgreSQL Setup

A local PostgreSQL database was set up using Docker Compose.

PostgreSQL is used as the central database/warehouse for this project. It stores both the raw ingested source data and the transformed dbt models.

The project currently uses the following services:

| Service | Purpose |
|---|---|
| PostgreSQL | Stores raw and transformed project data |
| Adminer | Browser-based SQL interface for querying PostgreSQL |
| dbt Docs | Browser-based documentation and lineage viewer for dbt models |

Adminer is used to inspect tables, run SQL queries, and validate row counts.

```text
Adminer URL: http://localhost:8080
```

dbt Docs is used to view dbt models, sources, and lineage.

```text
dbt Docs URL: http://localhost:8081
```

The local PostgreSQL connection uses:

```text
Host: 127.0.0.1
Port: 5433
Database: place_intel
User: place_user
```

Inside Docker containers, services connect to PostgreSQL using:

```text
Host: postgres
Port: 5432
```

---

# 2. Raw Data Ingestion into PostgreSQL

The raw datasets were ingested into PostgreSQL using Python ingestion scripts.

The purpose of the ingestion step was to load the original source data into raw PostgreSQL tables without applying heavy business logic.

This follows an ELT-style approach:

```text
Extract raw files
Load raw data into PostgreSQL
Transform later using dbt
```

The following raw tables were created in PostgreSQL:

| Source File | PostgreSQL Raw Table | Description |
|---|---|---|
| `Business_Licenses_20260505.csv` | `raw_business_license_history` | Historical Chicago business license records |
| `Business_Licenses_-_Current_Active_20260505.csv` | `raw_current_active_licenses` | Current active Chicago business license records |
| `export.geojson` | `raw_osm_places` | OpenStreetMap place and POI records |
| `yelp_academic_dataset_business.json` | `raw_yelp_businesses` | Yelp business metadata records |

The raw tables were validated in PostgreSQL using Adminer.

Example validation query:

```sql
select count(*)
from raw_current_active_licenses;
```

---

# 3. dbt Project Setup

A dbt project was configured to transform the raw PostgreSQL tables into cleaner analytical models.

dbt was connected to PostgreSQL using a `profiles.yml` file with two targets:

| Target | Purpose |
|---|---|
| `local` | Used when running dbt from Windows/PowerShell |
| `docker` | Used when running dbt inside Docker containers |

The local dbt target connects to PostgreSQL using:

```text
Host: 127.0.0.1
Port: 5433
Database: place_intel
```

The Docker dbt target connects to PostgreSQL using:

```text
Host: postgres
Port: 5432
Database: place_intel
```

The dbt connection was tested using:

```powershell
poetry run dbt debug --target local
```

The dbt project was also parsed successfully using:

```powershell
poetry run dbt parse --target local
```

---

# 4. dbt Source Configuration

The raw PostgreSQL tables were registered as dbt sources inside:

```text
models/staging/sources.yml
```

The following raw tables were added as dbt sources:

```text
raw_business_license_history
raw_current_active_licenses
raw_osm_places
raw_yelp_businesses
```

The source configuration allows dbt models to reference raw PostgreSQL tables using dbt source syntax.

Example:

```sql
{{ source('raw', 'raw_current_active_licenses') }}
```

This makes the dbt models cleaner, more maintainable, and easier to document.

---

# 5. dbt Staging Layer

The staging layer was created to clean and standardize each raw source table.

The following staging models were created:

```text
stg_current_active_licenses
stg_business_license_history
stg_osm_places
stg_yelp_businesses
```

The staging layer standardizes commonly needed fields such as:

```text
normalized_business_name
normalized_address
normalized_city
normalized_state
normalized_postal_code
source_system
source_says_active
```

These standardized fields will later be used for matching the same business across multiple datasets.

---

# 6. Staging Model: Current Active Licenses

The model:

```text
stg_current_active_licenses
```

was created from:

```text
raw_current_active_licenses
```

This model represents officially active business licenses in Chicago.

Key transformations include:

- Preserving original license and business fields
- Standardizing business name, address, city, state, and postal code
- Creating normalized fields for future matching
- Adding readable license status fields
- Adding source metadata
- Marking the dataset as an active-business signal

Important derived fields include:

```text
normalized_business_name
normalized_address
normalized_city
normalized_state
normalized_postal_code
license_status_code
license_status_category
source_system
source_says_active
```

Since this dataset represents current active licenses, the model sets:

```sql
true as source_says_active
```

This means the current active license table is treated as an official active-business signal.

The model was run using:

```powershell
poetry run dbt run --select stg_current_active_licenses --target local
```

The output model was validated in PostgreSQL using Adminer.

Example validation query:

```sql
select count(*)
from stg_current_active_licenses;
```

---

# 7. Staging Model: Business License History

The model:

```text
stg_business_license_history
```

was created from:

```text
raw_business_license_history
```

This model represents historical Chicago business license records.

Key transformations include:

- Preserving historical license records
- Standardizing business name and address fields
- Creating normalized fields for future matching
- Converting license status codes into readable categories
- Adding source metadata

Observed license status codes include:

```text
AAC
AAI
INQ
REA
REV
```

Current simple business logic:

| License Status Code | Interpretation |
|---|---|
| `AAC` | Active |
| `AAI` | Inactive or inactive-related status |
| `INQ` | Inquiry or pending review |
| `REA` | Renewal or reactivation-related status |
| `REV` | Revoked |

Important derived fields include:

```text
license_status_code
license_status_category
source_says_active
source_system
```

This model helps identify whether a business existed historically, changed status, or may no longer be active.

The model was run using:

```powershell
poetry run dbt run --select stg_business_license_history --target local
```

---

# 8. Staging Model: OpenStreetMap Places

The model:

```text
stg_osm_places
```

was created from:

```text
raw_osm_places
```

This model represents map-based place and point-of-interest data from OpenStreetMap.

The raw OSM table includes fields such as:

```text
osm_id
name
amenity
shop
tourism
house_number
street
city
state
postcode
latitude
longitude
raw_properties
raw_geometry
```

Key transformations include:

- Standardizing place name
- Creating a normalized address by combining house number and street
- Standardizing city, state, and postal code
- Creating a common `place_category` field using `amenity`, `shop`, or `tourism`
- Preserving raw GeoJSON properties and geometry
- Adding source metadata

Important derived fields include:

```text
normalized_business_name
normalized_address
normalized_city
normalized_state
normalized_postal_code
place_category
source_system
source_says_active
```

For OSM, `source_says_active` is set to:

```sql
null::boolean as source_says_active
```

This is because OpenStreetMap presence is useful as a map/location signal, but it does not always prove that a business is currently active.

The model was run using:

```powershell
poetry run dbt run --select stg_osm_places --target local
```

---

# 9. Staging Model: Yelp Businesses

The model:

```text
stg_yelp_businesses
```

was created from:

```text
raw_yelp_businesses
```

This model represents Yelp business metadata.

The raw Yelp table includes fields such as:

```text
business_id
name
address
city
state
postal_code
latitude
longitude
stars
review_count
is_open
categories
hours
attributes
raw_record
```

Key transformations include:

- Standardizing business name
- Standardizing address, city, state, and postal code
- Creating a common `place_category` field from Yelp categories
- Converting Yelp `is_open` into a readable status
- Converting Yelp `is_open` into a boolean active signal
- Adding source metadata

Yelp uses numeric values for `is_open`:

| `is_open` Value | Meaning |
|---|---|
| `1` | Open |
| `0` | Closed |

Important derived fields include:

```text
normalized_business_name
normalized_address
normalized_city
normalized_state
normalized_postal_code
place_category
yelp_open_status
source_says_active
source_system
```

The model logic uses numeric comparison because `is_open` is stored as a numeric field.

Example logic:

```sql
case
    when is_open = 1 then 'open'
    when is_open = 0 then 'closed'
    when is_open is null then 'missing_status'
    else 'unknown'
end as yelp_open_status
```

The model was run using:

```powershell
poetry run dbt run --select stg_yelp_businesses --target local
```

---

# 10. Validation in PostgreSQL Using Adminer

After each dbt model was created, the output was validated inside PostgreSQL using Adminer.

Example validation queries:

```sql
select count(*)
from stg_current_active_licenses;
```

```sql
select *
from stg_current_active_licenses
limit 10;
```

```sql
select
    license_status_code,
    license_status_category,
    count(*) as row_count
from stg_current_active_licenses
group by
    license_status_code,
    license_status_category
order by row_count desc;
```

```sql
select
    is_open,
    yelp_open_status,
    source_says_active,
    count(*) as row_count
from stg_yelp_businesses
group by
    is_open,
    yelp_open_status,
    source_says_active
order by row_count desc;
```

These queries confirmed that dbt successfully created queryable staging models inside PostgreSQL.

---

# 11. Current Pipeline Flow

The completed pipeline so far is:

```text
Raw CSV / JSON / GeoJSON files
        ↓
Python ingestion scripts
        ↓
PostgreSQL raw tables
        ↓
dbt source definitions
        ↓
dbt staging models
        ↓
PostgreSQL staging views
        ↓
Validation using Adminer SQL queries
```

Current implemented architecture:

```text
External datasets
        ↓
Python ingestion
        ↓
raw_* tables in PostgreSQL
        ↓
dbt transformations
        ↓
stg_* models in PostgreSQL
        ↓
SQL validation in Adminer
```

---

# 12. Why This Is ELT and Not Traditional ETL

This project follows an ELT approach.

ELT means:

```text
Extract → Load → Transform
```

In this project:

```text
Extract: Raw files are collected from source datasets
Load: Python scripts load raw data into PostgreSQL
Transform: dbt transforms the raw tables inside PostgreSQL
```

So the flow is:

```text
Raw files
   ↓
Loaded into PostgreSQL first
   ↓
Transformed by dbt inside PostgreSQL
```

This is different from traditional ETL.

ETL means:

```text
Extract → Transform → Load
```

In ETL, data is cleaned and transformed before being loaded into the database.

In this project, the raw data is loaded first, and the transformations happen afterward using dbt. Therefore, the project is ELT.

dbt is responsible for the transformation step.

---

# 13. What Materialized Inside PostgreSQL Means

When running a command such as:

```powershell
poetry run dbt run --select stg_current_active_licenses --target local
```

dbt sends the SQL model to PostgreSQL and creates a queryable object inside the database.

That object can be a:

| Materialization Type | Meaning |
|---|---|
| View | PostgreSQL stores the SQL query definition, and results are calculated when queried |
| Table | PostgreSQL stores the transformed result physically as rows |
| Incremental Table | PostgreSQL stores rows and only processes new or changed data on future runs |

For the staging layer, the models are currently materialized as views.

This means the staging models are available to query in PostgreSQL, but they do not duplicate all data as physical tables.

Example:

```sql
select *
from stg_current_active_licenses
limit 10;
```

This works because dbt created `stg_current_active_licenses` as a queryable PostgreSQL view.

The following dbt models are currently completed:

| Layer | Model Name | Source Table |
|---|---|---|
| Staging | `stg_current_active_licenses` | `raw_current_active_licenses` |
| Staging | `stg_business_license_history` | `raw_business_license_history` |
| Staging | `stg_osm_places` | `raw_osm_places` |
| Staging | `stg_yelp_businesses` | `raw_yelp_businesses` |

The next planned step is to build the first intermediate dbt model:

```text
int_all_place_sources
```

This model will combine all four staging models into one standardized place-source table.

The purpose of the intermediate model is to prepare the data for cross-source comparison.

It will help detect:

- Whether the same place exists across multiple sources
- Whether a place is missing from one or more sources
- Whether Yelp says closed while official licenses say active
- Whether OSM has a different address than license/Yelp data
- Whether a business may be duplicated
- Whether a place may need human review

Planned flow:

```text
stg_current_active_licenses
stg_business_license_history
stg_osm_places
stg_yelp_businesses
        ↓
int_all_place_sources
        ↓
future marts for closure, relocation, duplicate, and confidence scoring
```