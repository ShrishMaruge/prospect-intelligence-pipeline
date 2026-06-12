from __future__ import annotations

import csv
import json
from pathlib import Path


RANKED_FIELDS = [
    "entity_id", "company_name", "domain", "score", "score_reasons",
    "final_industry", "final_employee_count", "country", "contact_name",
    "contact_title", "email", "hiring_now", "recent_funding_months_ago",
    "tech_signals", "revenue_band", "enrichment_status", "enrichment_reason",
    "enrichment_attempts", "source_record_count", "source_row_numbers",
]

FAILED_FIELDS = [
    "entity_id", "company_name", "domain", "status", "reason", "attempts",
    "retry_eligible", "next_action",
]

NORMALIZED_FIELDS = [
    "row_number", "company_name", "normalized_company_name", "domain",
    "source_industry", "country", "employee_count_source", "contact_name",
    "contact_title", "email", "source", "last_seen",
]

RESOLVED_FIELDS = [
    "entity_id", "company_name", "normalized_company_name", "domain",
    "source_industry", "country", "employee_count_source", "contact_name",
    "contact_title", "email", "source", "last_seen", "source_record_count",
    "source_row_numbers",
]


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")

    with temp.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    temp.replace(path)


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2, sort_keys=True, default=str), encoding="utf-8")
    temp.replace(path)


def compact_enriched_records(enriched: list[dict]) -> list[dict]:
    records = []

    for row in enriched:
        records.append(
            {
                "entity_id": row.get("entity_id"),
                "company_name": row.get("company_name"),
                "domain": row.get("domain"),
                "enrichment_status": row.get("enrichment_status"),
                "enrichment_reason": row.get("enrichment_reason"),
                "enrichment_attempts": row.get("enrichment_attempts"),
                "enrichment": row.get("enrichment", {}),
            }
        )

    return records


def write_stage_outputs(
    output_dir: Path,
    normalized: list[dict],
    resolved: list[dict],
    enriched: list[dict],
) -> None:
    write_csv(output_dir / "normalized_records.csv", normalized, NORMALIZED_FIELDS)
    write_csv(output_dir / "resolved_entities.csv", resolved, RESOLVED_FIELDS)
    write_json(output_dir / "enriched_records.json", compact_enriched_records(enriched))


def write_outputs(output_dir: Path, ranked: list[dict], failures: list[dict], summary: dict) -> None:
    write_csv(output_dir / "ranked_prospects.csv", ranked, RANKED_FIELDS)
    write_csv(output_dir / "failed_enrichments.csv", failures, FAILED_FIELDS)
    write_csv(output_dir / "dead_letter_enrichments.csv", failures, FAILED_FIELDS)
    write_json(output_dir / "run_summary.json", summary)
