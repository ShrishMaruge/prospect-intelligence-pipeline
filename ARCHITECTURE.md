# Architecture

## Overview

This project implements a backend prospect intelligence pipeline. It converts a messy raw prospect export into a clean, deduplicated, enriched, scored, and ranked list of companies.

The task is not only to process a CSV. It is to design a small backend workflow that can survive real-world data problems: inconsistent fields, duplicates, missing values, unreliable external services, partial failures, reruns, and the need for clear observability.

The pipeline follows this flow:

```text
Raw CSV
-> Ingestion + normalization
-> Entity resolution
-> Enrichment
-> Scoring
-> Output + run summary
```

The main entry point is:

```bash
python run_all.py
```

`run_all.py` starts the mock enrichment API, waits for the `/health` endpoint to respond, runs the pipeline, and stops the API when the run finishes.

## Component 1: Ingestion And Normalization

Files:

```text
pipeline/ingest.py
pipeline/normalize.py
```

The ingestion stage reads `data/raw_prospects.csv` and converts each row into a consistent internal schema.

The raw data contains inconsistent values such as mixed casing, malformed domains, inconsistent employee counts, missing values, invalid emails, and inconsistent country/location fields. The pipeline cleans the fields before any matching or scoring happens.

Important normalized fields include:

- company name
- normalized company name
- domain
- industry
- country
- employee count
- contact name
- contact title
- email
- source
- date fields

Examples:

```text
https://www.Example.com/path -> example.com
51-200 -> 125
USA -> United States
invalid email -> blank email
```

I chose to keep imperfect records when they still contain a usable company name or domain. Dropping too aggressively would lose potentially useful companies. Records are only dropped when they do not contain enough identity information to be useful.

## Component 2: Entity Resolution

File:

```text
pipeline/resolve.py
```

Entity resolution detects duplicate company records and collapses them into one resolved entity.

The matching strategy is conservative:

1. Exact normalized domain match first.
2. Name-based matching only when a record has no domain.
3. High similarity threshold for name matching.

I chose domain-first matching because a cleaned domain is usually the strongest company identifier. Company names can appear in many forms:

```text
Acme
Acme Inc.
Acme Technologies Pvt Ltd
```

But if multiple records share the same normalized domain, they are much more likely to represent the same company.

For records without domains, the pipeline uses normalized company-name similarity. The threshold is intentionally high to reduce false merges. This may leave some true duplicates unresolved, but that is safer than merging two different companies into one incorrect record.

This tradeoff matters because false merges damage the final output more than missed merges. A missed duplicate is inconvenient. A false merge can make the ranked prospect list misleading.

## Component 3: Enrichment Client

File:

```text
pipeline/enrich.py
```

The enrichment stage calls the provided mock enrichment API for each resolved company.

The API is intentionally unreliable. It can:

- return transient `500` errors
- return `404` not found
- respond slowly
- return partial data
- require retry/backoff behavior

The pipeline handles this by using:

- retries for retryable status codes
- small backoff between attempts
- request timeouts
- enrichment cache
- failure recording

The cache is stored in:

```text
state/enrichment_cache.json
```

This makes reruns safer. If a domain was already enriched, the pipeline can reuse the cached result instead of calling the API again. This avoids duplicate work and helps the pipeline recover from interrupted runs.

Failures are written to:

```text
outputs/failed_enrichments.csv
```

This means the pipeline does not hide failed records. It records them clearly and continues processing the rest of the dataset.

## Component 4: Scoring

File:

```text
pipeline/score.py
```

The scoring stage ranks prospects using explainable rules. Each company receives a score and a list of score reasons.

Signals used in scoring include:

- employee count
- target industry
- active hiring signal
- recent funding
- relevant technology signals
- valid contact email
- valid domain
- multiple source mentions
- enrichment completeness

Example score reasons:

```text
ideal_employee_range
target_industry
active_hiring_signal
recent_funding
relevant_tech_stack
valid_contact_email
valid_domain
multiple_source_mentions
enrichment_incomplete
```

I kept scoring rule-based because this task values explainability. A reviewer can inspect a row and understand why it ranked highly. A more complex model would be harder to defend and unnecessary for the task scope.

## Component 5: Output And Observability

Files:

```text
pipeline/output.py
pipeline/main.py
```

The pipeline writes these main outputs:

```text
outputs/ranked_prospects.csv
outputs/failed_enrichments.csv
outputs/dead_letter_enrichments.csv
outputs/normalized_records.csv
outputs/resolved_entities.csv
outputs/enriched_records.json
outputs/run_summary.json
```

`ranked_prospects.csv` is the final ranked list.

`failed_enrichments.csv` records enrichment failures, skipped records, and not-found results.

`run_summary.json` records Run-level metrics such as:

- raw records
- normalized records
- dropped records
- resolved entities
- duplicates merged
- enrichment successes
- enrichment failures
- not-found enrichments
- skipped enrichments
- API calls
- cache hits
- ranked prospect count
- top score
- average score
- enrichment success rate
- cache hit rate
- failure breakdown by reason
- score distribution
- top 10 prospects

This makes the pipeline observable. After a run, someone can quickly tell what happened and whether the run was healthy.

The pipeline also writes intermediate stage outputs. `normalized_records.csv` shows the cleaned input records, `resolved_entities.csv` shows the deduplicated company records, and `enriched_records.json` shows compact enrichment results. These files make the pipeline easier to inspect during review and easier to debug if a later stage behaves unexpectedly.

`dead_letter_enrichments.csv` acts as a dead-letter path for records that did not enrich successfully. It includes whether the record is retry eligible and what the next action should be.

## Rerun Safety

The pipeline is designed to be safe to rerun.

Rerun safety is handled through:

- deterministic normalization
- deterministic output paths
- enrichment caching
- temporary-file writes before replacing final outputs
- no manual editing of the dataset

Running the pipeline again does not duplicate output rows. It rebuilds the outputs from the current input and cached enrichment state.

## Failure Handling

The enrichment API is expected to fail sometimes. This project treats API failure as part of normal backend operation.

Failure handling includes:

- retrying transient errors
- treating `404` as a valid not-found result
- skipping missing-domain enrichment safely
- writing failure records
- continuing with the rest of the dataset

This matches the task requirement that the pipeline should not fall over because an external service is slow or unreliable.

## Tests

Tests live in:

```text
tests/test_pipeline.py
```

The tests cover core logic:

- domain normalization
- employee-count parsing
- invalid email handling
- company-name suffix normalization
- duplicate resolution by domain
- avoiding false merges for unrelated no-domain companies
- scoring behavior for a strong prospect
- score penalty for failed or skipped enrichment
- retry eligibility for failed enrichment records

These tests focus on the parts most likely to break or affect output quality.

## Key Tradeoffs

### Conservative Duplicate Matching

The entity resolution logic may leave some duplicates unresolved, especially when records lack domains. I accepted this because false merges are more harmful than missed duplicates.

### Explainable Scoring

The scoring model is simple and rule-based. This is intentional. The goal is to produce a ranking that can be explained in a review conversation, not a black-box score.

### Sequential Enrichment

The enrichment process is sequential. This is simpler and safer for the rate-limited mock API. With more time, I would add bounded concurrency while still respecting the rate limit.

### Cache Includes Failures

The cache stores both successes and non-success results. This helps rerun safety and avoids repeatedly calling the API for domains already known to be not found or failed. A future improvement would be to make retry behavior configurable for failed records.

## Final Summary

This project builds a complete backend pipeline for prospect intelligence. It reads messy company data, normalizes it, resolves duplicate companies, enriches records through an unreliable API, scores prospects using explainable rules, and writes ranked outputs with a run summary.

The most important design choices are domain-first duplicate resolution, resilient enrichment through retry/cache/failure recording, explainable scoring, and observable output. These choices make the pipeline practical, rerunnable, and defensible in a technical review.

