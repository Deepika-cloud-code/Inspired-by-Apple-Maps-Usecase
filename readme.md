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

---

# 14. Intermediate Layer Implementation

After completing the staging layer, the next step was to create intermediate models.

The purpose of the intermediate layer is to:

- Clean and deduplicate records within each source
- Preserve source-specific evidence columns
- Standardize common matching fields
- Prepare data for fuzzy matching and final marts

The following intermediate models were created:

| Model Name | Input Model | Purpose |
|---|---|---|
| `int_current_active_license_cleaned` | `stg_current_active_licenses` | Cleans and deduplicates current active Chicago license records |
| `int_license_history_cleaned` | `stg_business_license_history` | Cleans and deduplicates historical license records |
| `int_osm_places_cleaned` | `stg_osm_places` | Cleans and deduplicates OpenStreetMap POI records |
| `int_yelp_businesses_cleaned` | `stg_yelp_businesses` | Cleans and deduplicates Yelp business records |
| `int_all_place_sources` | All cleaned intermediate models | Combines all source evidence into one standardized evidence table |

---

# 15. Why Source-Specific Intermediate Models Were Created

Initially, a single `UNION ALL` model was considered to combine all staging tables directly.

However, that would have caused two problems:

1. Duplicate records within each source would remain unresolved.
2. Important source-specific fields could be lost when forcing all datasets into one common structure.

For example:

| Source | Important Source-Specific Evidence |
|---|---|
| Chicago Licenses | `license_status`, `business_activity`, `license_term_expiration_date`, `date_issued` |
| OpenStreetMap | `amenity`, `shop`, `tourism`, `opening_hours`, `website`, `raw_geometry` |
| Yelp | `stars`, `review_count`, `is_open`, `categories`, `hours`, `attributes` |

Therefore, the pipeline first creates source-specific cleaned intermediate models and then combines them into a unified evidence table.

The improved flow is:

```text
staging models
   ↓
source-specific cleaned intermediate models
   ↓
int_all_place_sources
   ↓
fuzzy matching
   ↓
clusters
   ↓
marts
```

---

# 16. Unified Evidence Table: `int_all_place_sources`

The model:

```text
int_all_place_sources
```

combines the cleaned intermediate models into one comparison-ready evidence table.

It includes common fields such as:

```text
source_system
source_type
source_record_id
normalized_business_name
normalized_address
normalized_city
normalized_state
normalized_postal_code
latitude
longitude
place_category
source_says_active
source_match_key
source_specific_evidence
```

The `source_specific_evidence` column is stored as JSONB. This allows the model to preserve important unique details from each dataset while still keeping a common structure for matching.

Example:

```text
Chicago license row → license evidence stored in source_specific_evidence
Yelp row → review/status evidence stored in source_specific_evidence
OSM row → POI/geometry evidence stored in source_specific_evidence
```

This model acts as the central evidence table for downstream matching and RAG.

---

# 17. Fuzzy Matching Implementation

Exact matching was not enough because different sources write business names and addresses differently.

Example:

```text
10 n state st
10 north state street
10 N State Street
```

To solve this, PostgreSQL fuzzy matching was added using the `pg_trgm` extension.

The extension was enabled using:

```powershell
docker exec -it place_intel_postgres psql -U place_user -d place_intel -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
```

The fuzzy matching model created was:

```text
int_place_fuzzy_match_candidates
```

This model compares Chicago current active license records against Yelp and OSM records using:

```text
business name similarity
address similarity
category similarity
city/state/ZIP matching
street number matching
```

Fuzzy match types include:

| Match Type | Meaning |
|---|---|
| `strong_fuzzy_match` | Strong name and address similarity |
| `medium_fuzzy_match` | Moderate name and address similarity |
| `name_zip_match` | Strong name match with same ZIP |
| `address_supported_match` | Address similarity supports the match |

The model creates a weighted fuzzy score using:

```text
name similarity
address similarity
category similarity
```

This improves matching across inconsistent source formats.

---

# 18. Fuzzy Cluster Model

After fuzzy match candidates were created, a cluster model was built:

```text
int_place_fuzzy_clusters_all_anchors
```

This model creates one logical place cluster per Chicago current active license record.

It includes both:

```text
records that matched Yelp/OSM
records that did not match any external source
```

This was important because the earlier fuzzy cluster model only included records that already had Yelp/OSM matches. That excluded active Chicago businesses with no external validation.

The corrected all-anchor model includes:

```text
Chicago current active license + matched Yelp/OSM evidence if available
Chicago current active license + no external match if unavailable
```

Important fields include:

```text
place_cluster_id
canonical_business_name
canonical_address
matched_sources
matched_source_count
found_in_current_active_license
found_in_yelp
found_in_osm
active_signal_count
inactive_signal_count
fuzzy_match_types
concatenated_values
cluster_strength
preliminary_place_status
matched_source_evidence
```

The `concatenated_values` column shows the actual fields used for matching, such as:

```text
NAME_MATCH
ADDRESS_MATCH
CITY_MATCH
STATE_MATCH
ZIP_MATCH
NAME_SIMILARITY
ADDRESS_SIMILARITY
CATEGORY_SIMILARITY
MATCH_SCORE
MATCH_TYPE
```

This makes the fuzzy matching logic easier to validate manually.

---

# 19. Mart Layer

The project currently has two main mart tables.

```text
models/marts/
├── mart_place_status_summary.sql
└── mart_place_change_detection.sql
```

These marts represent the business-ready layer of the project.

---

# 20. Mart: `mart_place_status_summary`

The model:

```text
mart_place_status_summary
```

answers current place status questions.

It uses:

```text
int_place_fuzzy_clusters_all_anchors
```

as input.

This mart answers questions such as:

- Is this place likely active?
- Is it supported by OSM?
- Is it supported by Yelp?
- Is it officially active but missing external validation?
- What confidence level should be assigned?
- What recommended action should be taken?

Important output columns include:

```text
place_cluster_id
canonical_business_name
canonical_address
matched_sources
found_in_yelp
found_in_osm
final_place_status
confidence_level
recommended_action
concatenated_values
matched_source_evidence
```

Example final statuses:

| Final Status | Meaning |
|---|---|
| `officially_active_but_missing_external_sources` | The business is active in Chicago license data but has no Yelp/OSM match |
| `likely_active_with_osm_support` | The business is active in Chicago license data and matched with OSM |
| `likely_active_with_yelp_support` | The business is active in Chicago license data and matched with Yelp |
| `verified_active` | The business has support from Chicago license, Yelp, and OSM |

Example recommended actions:

| Recommended Action | Meaning |
|---|---|
| `officially_active_but_missing_external_sources` | Keep the official active record but note missing external validation |
| `active_but_missing_yelp_validation` | OSM supports the place, but Yelp evidence is missing |
| `keep_active_with_yelp_support` | Yelp supports the official active license signal |
| `approve_as_verified_active` | Multiple sources support active status |

---

# 21. Mart: `mart_place_change_detection`

The model:

```text
mart_place_change_detection
```

uses the historical Chicago license data to detect business changes over time.

It compares:

```text
historical business licenses
current active licenses
external Yelp/OSM listings
```

This mart answers questions such as:

- Did this place change over time?
- Did an old business close?
- Did a new business replace an old business at the same address?
- Does a business have historical continuity?
- Are there multiple active or recent businesses at the same address?

Important output columns include:

```text
place_change_id
historical_business_name
historical_address
historical_license_status_code
has_current_active_at_same_address
same_business_still_active
different_business_now_at_same_address
replacement_business_name
change_detection_status
closure_signal
replacement_signal
external_staleness_signal
confidence_level
recommended_action
evidence_summary
```

Example change detection statuses:

| Change Detection Status | Meaning |
|---|---|
| `historical_business_likely_closed` | Historical business has no current active license at the same address |
| `old_business_replaced_by_new_business` | A different current active business exists at the same address |
| `business_has_historical_continuity` | Historical and current active records appear to describe the same business |
| `same_address_has_multiple_active_or_recent_businesses_needs_review` | Same address has multiple signals and should be reviewed |
| `change_status_unknown` | Signals are not strong enough for a clear decision |

This mart makes the historical license dataset useful for closure and replacement detection.

---

# 22. Validation Queries

A separate SQL validation file was created:

```text
validation_queries.sql
```

This file contains manual validation queries for:

- Raw table row counts
- Staging model row counts
- Intermediate model row counts
- Source distribution
- Activity signal distribution
- Fuzzy match type distribution
- Fuzzy cluster validation
- Active status mart validation
- Change detection mart validation
- Duplicate checks
- Null checks
- Sample RAG evidence records

Example validation query:

```sql
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
```

Example change detection validation query:

```sql
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
```

These queries were used to confirm that the marts produced meaningful categories.

---

# 23. RAG Layer Overview

After the dbt marts were completed, a RAG layer was added on top of the trusted Postgres outputs.

The purpose of the RAG layer is not to replace the marts.

Instead:

```text
Postgres marts = trusted structured evidence layer
RAG = natural-language explanation and question-answering layer
```

The RAG system allows users to ask questions such as:

```text
Why is this place marked active but missing Yelp validation?
Which businesses were replaced by new businesses?
Why would a historical business be marked likely closed?
Give me places that are officially active but missing external sources.
```

The RAG system uses the mart outputs as evidence.

---

# 24. RAG Evidence Document Generation

The file:

```text
rag/build_evidence_documents.py
```

reads from the two mart tables:

```text
mart_place_status_summary
mart_place_change_detection
```

It converts each row into an evidence document.

Example evidence document from `mart_place_status_summary`:

```text
Document Type: Current Place Status
Business Name: smith & wollensky
Address: 318 n state st, chicago, IL 60654
Final Place Status: likely_active_with_osm_support
Confidence Level: medium_confidence
Recommended Action: active_but_missing_yelp_validation
Matched Sources: openstreetmap, chicago_current_active_license
Evidence: NAME_MATCH, ADDRESS_MATCH, similarity scores, and match type
```

Example evidence document from `mart_place_change_detection`:

```text
Document Type: Place Change Detection
Historical Business Name: aldi #32
Historical Address: 1840 n clybourn ave, chicago, IL
Change Detection Status: old_business_replaced_by_new_business
Confidence Level: medium_confidence
Recommended Action: mark_old_business_as_replaced
Evidence Summary: historical business and replacement business at same address
```

The evidence documents are represented in Python using a dataclass:

```python
@dataclass
class EvidenceDocument:
    document_id: str
    document_type: str
    text: str
    metadata: Dict[str, Any]
```

The dataclass is only a temporary in-memory structure. It does not store data permanently.

---

# 25. Local Vector Store with ChromaDB

The file:

```text
rag/build_vector_store.py
```

converts evidence text into embeddings and stores them in a local ChromaDB vector store.

The flow is:

```text
Postgres mart rows
   ↓
Evidence text documents
   ↓
Embedding model converts text to vectors
   ↓
ChromaDB stores vectors, text, and metadata locally
```

The vector store is stored locally at:

```text
data/vector_store/chroma
```

This folder contains ChromaDB internal files such as:

```text
chroma.sqlite3
data_level0.bin
header.bin
index_metadata.pickle
length.bin
link_lists.bin
```

These files represent the local vector database and similarity search index.

The vector store folder is ignored by Git using:

```gitignore
data/vector_store/
```

---

# 26. Embedding Model

The project uses a local Hugging Face sentence-transformer embedding model:

```text
sentence-transformers/all-MiniLM-L6-v2
```

This model converts evidence text into numerical vectors.

Example:

```text
"Business is active in Chicago license and matched with OSM"
```

becomes a vector like:

```text
[0.012, -0.331, 0.872, ...]
```

These vectors allow semantic search.

The embedding model does not generate answers. It only converts text into meaning-based numerical representations.

---

# 27. Dense Vector Retrieval

The file:

```text
rag/query_vector_store.py
```

performs dense vector retrieval.

The retrieval flow is:

```text
User question
   ↓
Question converted into embedding
   ↓
ChromaDB compares question vector with stored evidence vectors
   ↓
Top matching evidence documents are returned
```

This allows the system to retrieve evidence based on meaning, not only exact keyword matching.

Example question:

```text
Why is a place marked active but missing Yelp validation?
```

The retriever returned evidence where:

```text
recommended_action = active_but_missing_yelp_validation
matched_sources = openstreetmap, chicago_current_active_license
```

This confirmed that dense vector retrieval was working.

---

# 28. Hybrid Search: Dense Search + BM25 + Reciprocal Rank Fusion

After dense retrieval was tested, hybrid search was added using:

```text
rag/hybrid_query.py
```

The hybrid search combines:

```text
Dense vector search
BM25 keyword search
Reciprocal Rank Fusion
```

## Dense Vector Search

Dense search finds semantically similar evidence.

It is useful for questions like:

```text
Why does this business look stale?
Which places may have changed?
```

## BM25 Keyword Search

BM25 stands for:

```text
Best Matching 25
```

It is a keyword-based ranking algorithm.

BM25 is useful for exact terms such as:

```text
ALDI #32
Smith & Wollensky
60654
Yelp
replacement
```

## Reciprocal Rank Fusion

Reciprocal Rank Fusion combines the ranking results from dense search and BM25.

Documents that rank highly in both search methods receive stronger final rankings.

The RRF score is based on:

```text
1 / (k + rank)
```

This avoids manually assigning fixed weights such as 40% BM25 and 60% vector search.

The hybrid retrieval flow is:

```text
User question
   ↓
Dense vector search
   ↓
BM25 keyword search
   ↓
Reciprocal Rank Fusion
   ↓
Top evidence documents
```

This improves retrieval quality for both semantic and exact lookup questions.

---

# 29. Groq LLM Answer Layer

The file:

```text
rag/rag_answer.py
```

adds a Groq LLM response layer on top of hybrid retrieval.

The flow is:

```text
User question
   ↓
Hybrid search retrieves evidence
   ↓
Retrieved evidence is passed to Groq
   ↓
Groq generates a natural-language answer
```

The Groq API key and model name are stored in `.env`:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=your_selected_groq_model_here
```

The code fully depends on `.env` and does not hardcode the Groq model name.

The system prompt instructs the model to:

- Use only retrieved evidence
- Avoid inventing facts
- Explain in simple business language
- Mention status, confidence, recommended action, and evidence
- Cite evidence document numbers and relevant details
- Clearly say when evidence is not enough

This makes the RAG output more trustworthy and grounded.

---

# 30. Current RAG Architecture

The current local RAG architecture is:

```text
Postgres marts
   ↓
Evidence document generation
   ↓
Sentence-transformer embeddings
   ↓
Local ChromaDB vector store
   ↓
Dense vector retrieval
   ↓
BM25 keyword retrieval
   ↓
Reciprocal Rank Fusion
   ↓
Groq LLM answer generation
```

Current RAG files:

| File | Purpose |
|---|---|
| `rag/build_evidence_documents.py` | Reads Postgres marts and creates evidence text |
| `rag/build_vector_store.py` | Converts evidence text into embeddings and stores them in ChromaDB |
| `rag/query_vector_store.py` | Tests dense vector retrieval from ChromaDB |
| `rag/hybrid_query.py` | Performs hybrid retrieval using dense search, BM25, and RRF |
| `rag/rag_answer.py` | Uses hybrid retrieval and Groq to generate natural-language answers |

---

# 31. Environment Variables

The project uses `.env` for configuration.

Example `.env` values:

```env
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5433
POSTGRES_DB=place_intel
POSTGRES_USER=place_user
POSTGRES_PASSWORD=place_password

GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=your_selected_groq_model_here
```

The `.env` file should not be committed to GitHub.

A safe `.env.example` file can be committed with placeholder values.

---

# 32. Example RAG Questions

The current RAG system can answer questions such as:

```text
Why is a place marked active but missing Yelp validation?
```

```text
Give me 2 places which have change of place.
```

```text
Why was ALDI #32 marked as replaced?
```

```text
Give me places that are officially active but missing external sources.
```

```text
Why would a historical business be marked likely closed?
```

```text
Give me evidence for Smith & Wollensky.
```

---

# 33. Current End-to-End Pipeline

The full implemented pipeline is now:

```text
Raw CSV / JSON / GeoJSON files
   ↓
Python ingestion scripts
   ↓
PostgreSQL raw tables
   ↓
dbt staging models
   ↓
dbt intermediate cleaned models
   ↓
Unified evidence table
   ↓
Fuzzy matching and clustering
   ↓
dbt mart tables
   ↓
Evidence document generation
   ↓
Embedding generation
   ↓
Local ChromaDB vector store
   ↓
Hybrid search
   ↓
Groq-powered RAG answer generation
```

---

# 34. Current Project Status

Completed:

- Dockerized PostgreSQL setup
- Adminer browser-based database access
- Raw data ingestion into PostgreSQL
- dbt project setup
- dbt staging models
- dbt intermediate cleaned models
- Unified evidence table
- Fuzzy matching using `pg_trgm`
- All-anchor fuzzy cluster model
- Active status mart
- Change detection mart
- Validation SQL file
- Evidence document generation
- Local ChromaDB vector store
- Dense vector retrieval
- Hybrid retrieval using BM25 and Reciprocal Rank Fusion
- Groq-based RAG answer generation

---

# 35. Next Planned Steps

The next planned steps are:

1. Add or improve dbt tests and documentation.
2. Add `.env.example`.
3. Add a FastAPI endpoint for RAG question answering.
4. Optionally build a simple Streamlit UI.
5. Later, consider adding Google Maps API as an enrichment source or live agent tool.
6. For cloud deployment, evaluate Cloud SQL + pgvector, Vertex AI Vector Search, or Chroma Cloud.

The current local system is sufficient for development and portfolio demonstration.

# Guardrails

Added guardrails: input(domain), output(starter code), retreival(starter code)