from __future__ import annotations


TARGET_INDUSTRIES = {"Software", "Healthcare", "Finance", "Retail", "Education", "Manufacturing"}
TARGET_TECH = {"python", "react", "aws", "gcp", "azure", "salesforce", "hubspot"}


def score_entity(entity: dict) -> tuple[int, list[str]]:
    score = 0
    reasons = []
    enrichment = entity.get("enrichment", {})

    employee_count = enrichment.get("employee_count") or entity.get("employee_count_source")
    industry = enrichment.get("industry") or entity.get("source_industry")
    tech_signals = set(enrichment.get("tech_signals") or [])

    if employee_count:
        if 50 <= int(employee_count) <= 1500:
            score += 25
            reasons.append("ideal_employee_range")
        elif int(employee_count) > 1500:
            score += 12
            reasons.append("large_company")
        else:
            score += 5
            reasons.append("small_company")

    if industry in TARGET_INDUSTRIES:
        score += 20
        reasons.append("target_industry")

    if enrichment.get("hiring_now") is True:
        score += 25
        reasons.append("active_hiring_signal")

    funding_months = enrichment.get("last_funding_months_ago")
    if funding_months is not None and funding_months <= 12:
        score += 15
        reasons.append("recent_funding")

    if tech_signals & TARGET_TECH:
        score += 10
        reasons.append("relevant_tech_stack")

    if entity.get("email"):
        score += 8
        reasons.append("valid_contact_email")

    if entity.get("domain"):
        score += 7
        reasons.append("valid_domain")

    if entity.get("source_record_count", 1) > 1:
        score += 5
        reasons.append("multiple_source_mentions")

    if entity.get("enrichment_status") != "success":
        score -= 10
        reasons.append("enrichment_incomplete")

    return max(score, 0), reasons


def score_and_rank(enriched_entities: list[dict]) -> tuple[list[dict], dict]:
    ranked = []

    for entity in enriched_entities:
        score, reasons = score_entity(entity)
        enrichment = entity.get("enrichment", {})

        row = entity.copy()
        row["score"] = score
        row["score_reasons"] = ";".join(reasons)
        row["final_employee_count"] = enrichment.get("employee_count") or entity.get("employee_count_source") or ""
        row["final_industry"] = enrichment.get("industry") or entity.get("source_industry") or ""
        row["hiring_now"] = enrichment.get("hiring_now")
        row["recent_funding_months_ago"] = enrichment.get("last_funding_months_ago")
        row["tech_signals"] = ",".join(enrichment.get("tech_signals") or [])
        row["revenue_band"] = enrichment.get("revenue_band") or ""
        ranked.append(row)

    ranked.sort(key=lambda r: (-r["score"], r["company_name"].lower()))

    summary = {
        "ranked_prospects": len(ranked),
        "top_score": ranked[0]["score"] if ranked else 0,
        "average_score": round(sum(r["score"] for r in ranked) / len(ranked), 2) if ranked else 0,
    }

    return ranked, summary