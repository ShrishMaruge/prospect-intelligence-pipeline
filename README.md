# Prospect Intelligence Pipeline

## Overview

Prospect Intelligence Pipeline is a Python-based backend data processing system that transforms a messy prospect export into a clean, deduplicated, enriched, scored, and ranked prospect dataset.

The project was built for the Week 0 Day 3+4 Backend Engineering Task. The objective is to demonstrate practical backend engineering skills including:

* Data normalization
* Entity resolution and deduplication
* External API integration
* Failure handling and retries
* Caching and rerun safety
* Explainable prospect scoring
* Observability and reporting
* Automated testing

The pipeline is designed to continue operating even when the enrichment service returns failures, missing data, or intermittent errors.

---

## Pipeline Workflow

```text
Raw Prospect CSV
        │
        ▼
Ingestion & Normalization
        │
        ▼
Entity Resolution
        │
        ▼
Enrichment API
        │
        ▼
Prospect Scoring
        │
        ▼
Ranked Outputs & Reports
```

---

## Input

The pipeline reads:

```text
data/raw_prospects.csv
```

The input dataset may contain:

* Duplicate companies
* Inconsistent company names
* Invalid domains
* Missing fields
* Different employee-count formats
* Invalid emails
* Mixed country formats

---

## Outputs

The pipeline generates:

```text
outputs/ranked_prospects.csv
outputs/failed_enrichments.csv
outputs/run_summary.json
outputs/normalized_records.csv
outputs/resolved_entities.csv
outputs/enriched_records.json
outputs/dead_letter_enrichments.csv

state/enrichment_cache.json
```

### ranked_prospects.csv

Final ranked list of prospects containing:

* Company information
* Prospect score
* Score explanations
* Enrichment signals
* Contact information
* Source record counts

### failed_enrichments.csv

Records where enrichment failed, returned not found, or could not be processed.

### run_summary.json

Pipeline observability report containing:

* Raw record count
* Normalized record count
* Duplicate merge statistics
* Enrichment success and failure counts
* Cache metrics
* Score distribution
* Top prospects

### normalized_records.csv

Records immediately after the normalization stage.

### resolved_entities.csv

Records after duplicate resolution and entity consolidation.

### enriched_records.json

Compact enrichment results returned from the enrichment service.

### dead_letter_enrichments.csv

Failed enrichment records preserved for investigation and future retry.

### enrichment_cache.json

Persistent cache used to avoid repeating enrichment requests on reruns.

---

## Project Structure

```text
prospect_pipeline/
├── data/
│   └── raw_prospects.csv
├── mock_enrichment_api/
│   └── app.py
├── pipeline/
│   ├── __init__.py
│   ├── normalize.py
│   ├── ingest.py
│   ├── resolve.py
│   ├── enrich.py
│   ├── score.py
│   ├── output.py
│   └── main.py
├── tests/
│   ├── conftest.py
│   └── test_pipeline.py
├── outputs/
├── state/
├── README.md
├── ARCHITECTURE.md
├── AI_USAGE_LOG.md
├── requirements.txt
├── run_all.py
├── Dockerfile
├── docker-compose.yml
└── .gitignore
```

---

## Installation

Install project dependencies:

```bash
pip install -r requirements.txt
```

---

## Running The Pipeline

Primary execution command:

```bash
python run_all.py
```

This command:

1. Starts the mock enrichment API
2. Waits for API health confirmation
3. Executes the full pipeline
4. Generates output files
5. Stops the API process

Example output:

```text
Pipeline finished successfully
Raw records: 486
Normalized records: 485
Resolved entities: 222
Duplicates merged: 263
Enriched successfully: 174
Failed/not found/skipped: 48
Ranked prospects: 222
```

Because the enrichment service intentionally introduces intermittent failures, enrichment counts may vary slightly between runs.

---

## Running Tests

Execute all automated tests:

```bash
pytest
```

Current test coverage includes:

* Domain normalization
* Company-name normalization
* Employee-count parsing
* Invalid email handling
* Duplicate resolution
* False-merge prevention
* Scoring behavior
* Enrichment failure handling
* Retry eligibility checks

---

## Docker Support

Docker support is included.

Build and run:

```bash
docker-compose up --build
```

If Docker Desktop is unavailable, use:

```bash
python run_all.py
```

The task requirements allow either Docker execution or a clearly documented equivalent.

---

## Failure Handling

The mock enrichment service intentionally behaves like a real-world unreliable dependency.

Possible responses include:

* HTTP 500 errors
* HTTP 404 responses
* Partial records
* Slow responses
* Rate-limit style behavior

The pipeline handles these situations using:

* Retries
* Request timeouts
* Failure recording
* Persistent caching
* Graceful continuation

A small number of enrichment failures is expected and does not indicate a pipeline failure.

---

## Rerun Safety

The pipeline is designed to be safely rerunnable.

Safety mechanisms include:

* Persistent enrichment cache
* Deterministic output generation
* Atomic file writes
* Idempotent processing behavior

Rerunning the pipeline should not duplicate records or corrupt previous outputs.

---

## Design Principles

The implementation follows several guiding principles:

### Normalize Before Matching

Data quality issues are corrected before duplicate detection.

### Domain-First Resolution

Domains are treated as the strongest company identifier.

### Conservative Matching

Name-based matching is used only when domain information is unavailable.

### Explainable Scoring

Scores are generated using transparent business rules instead of opaque models.

### Failure Tolerance

External API failures should not stop the pipeline.

### Observability

Each stage produces outputs that make pipeline behavior easy to inspect and debug.

---

## Documentation

Additional implementation details are available in:

```text
ARCHITECTURE.md
AI_USAGE_LOG.md
```

These documents describe architectural decisions, engineering tradeoffs, implementation details, and AI-assisted development practices.

---

## Author Notes

This project focuses on practical backend engineering decisions rather than building the most complex solution possible.

The emphasis is on correctness, reliability, explainability, rerun safety, and clear operational visibility.
