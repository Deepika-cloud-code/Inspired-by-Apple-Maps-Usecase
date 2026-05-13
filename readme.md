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

# Dataset Mapping and Business Signals

The project uses multiple independent open-source datasets to verify whether place information in a mapping system is accurate, stale, moved, duplicated, or inactive.

Each dataset contributes a different type of business signal.

---

# Dataset Mapping

| File Name | Internal Dataset Name | Purpose | Signal Type |
|---|---|---|---|
| `Business_Licenses_20260505.csv` | `raw_business_license_history` | Historical Chicago business license records | Official government/business history signal |
| `Business_Licenses_-_Current_Active_20260505.csv` | `raw_current_active_licenses` | Currently active licensed businesses in Chicago | Official active-business verification signal |
| `export.geojson` | `raw_osm_places` | OpenStreetMap points-of-interest (POI) and location data | Map/location intelligence signal |
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

# 2. Chicago Current Active Licenses Dataset

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

# 3. OpenStreetMap (OSM) Dataset

### File

```text
export.geojson
```

### Purpose

Represents map-based place and POI (Point-of-Interest) information.

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

# 4. Yelp Business Dataset

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
- retrieves evidence
- compares conflicting signals
- calculates confidence
- proposes a database update recommendation

---

# Final Goal

Build a scalable AI-powered place intelligence platform capable of:

- Detecting stale map records
- Verifying business changes
- Identifying relocations and closures
- Reducing incorrect map information
- Supporting future RAG and agentic AI workflows