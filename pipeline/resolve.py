from __future__ import annotations

from difflib import SequenceMatcher

from .normalize import stable_id


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def merge_records(records: list[dict]) -> dict:
    best = records[0].copy()

    for record in records[1:]:
        for key, value in record.items():
            if key == "row_number":
                continue

            if not best.get(key) and value:
                best[key] = value

        if record.get("email") and not best.get("email"):
            best["email"] = record["email"]

    best["source_row_numbers"] = ",".join(str(r["row_number"]) for r in records)
    best["source_record_count"] = len(records)
    best["entity_id"] = stable_id(best.get("domain", ""), best.get("normalized_company_name", ""))
    return best


def resolve_entities(rows: list[dict]) -> tuple[list[dict], dict]:
    domain_groups: dict[str, list[dict]] = {}
    no_domain: list[dict] = []

    for row in rows:
        if row["domain"]:
            domain_groups.setdefault(row["domain"], []).append(row)
        else:
            no_domain.append(row)

    groups = list(domain_groups.values())

    for row in no_domain:
        placed = False
        for group in groups:
            representative = group[0]
            if similarity(row["normalized_company_name"], representative["normalized_company_name"]) >= 0.92:
                group.append(row)
                placed = True
                break

        if not placed:
            groups.append([row])

    entities = [merge_records(group) for group in groups]

    summary = {
        "resolved_entities": len(entities),
        "duplicate_records_merged": len(rows) - len(entities),
        "domain_group_count": len(domain_groups),
        "no_domain_records": len(no_domain),
    }

    return entities, summary