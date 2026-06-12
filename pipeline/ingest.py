from __future__ import annotations

import csv
from pathlib import Path

from .normalize import (
    clean_text,
    normalize_company_name,
    normalize_country,
    normalize_domain,
    normalize_email,
    parse_date,
    parse_employee_count,
)


def pick(row: dict, *names: str) -> str:
    lowered = {k.lower().strip(): v for k, v in row.items()}
    for name in names:
        if name.lower() in lowered:
            return lowered[name.lower()]
    return ""


def normalize_row(row: dict, row_number: int) -> dict:
    company_name = clean_text(pick(row, "company", "company_name", "name"))
    domain = normalize_domain(pick(row, "domain", "website", "company_domain", "url"))
    email = normalize_email(pick(row, "email", "contact_email"))
    employee_count = parse_employee_count(pick(row, "employee_count", "employees", "company_size"))

    return {
        "row_number": row_number,
        "company_name": company_name,
        "normalized_company_name": normalize_company_name(company_name),
        "domain": domain,
        "source_industry": clean_text(pick(row, "industry", "sector")),
        "country": normalize_country(pick(row, "country", "location")),
        "employee_count_source": employee_count,
        "contact_name": clean_text(pick(row, "contact_name", "person", "lead_name")),
        "contact_title": clean_text(pick(row, "title", "job_title", "contact_title")),
        "email": email,
        "source": clean_text(pick(row, "source")),
        "last_seen": parse_date(pick(row, "last_seen", "date", "created_at")),
    }


def ingest_and_normalize(input_path: Path) -> tuple[list[dict], dict]:
    rows: list[dict] = []

    with input_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for index, row in enumerate(reader, start=1):
            normalized = normalize_row(row, index)
            if normalized["company_name"] or normalized["domain"]:
                rows.append(normalized)

    summary = {
        "raw_records": index if "index" in locals() else 0,
        "normalized_records": len(rows),
        "dropped_records": (index if "index" in locals() else 0) - len(rows),
    }

    return rows, summary