from pipeline.enrich import failure_next_action
from pipeline.normalize import (
    normalize_company_name,
    normalize_domain,
    normalize_email,
    parse_employee_count,
)
from pipeline.resolve import resolve_entities
from pipeline.score import score_entity


def test_normalize_domain():
    assert normalize_domain("https://www.Example.com/path") == "example.com"


def test_parse_employee_count_range():
    assert parse_employee_count("51-200") == 125


def test_invalid_email_becomes_blank():
    assert normalize_email("not-an-email") == ""


def test_normalize_company_name_removes_suffix():
    assert normalize_company_name("Acme Technologies Pvt Ltd") == "acme"


def test_resolve_duplicate_by_domain():
    rows = [
        {"row_number": 1, "company_name": "Acme", "normalized_company_name": "acme", "domain": "acme.com"},
        {"row_number": 2, "company_name": "Acme Inc", "normalized_company_name": "acme", "domain": "acme.com"},
    ]

    entities, summary = resolve_entities(rows)

    assert len(entities) == 1
    assert summary["duplicate_records_merged"] == 1


def test_does_not_merge_different_no_domain_companies():
    rows = [
        {"row_number": 1, "company_name": "Acme", "normalized_company_name": "acme", "domain": ""},
        {"row_number": 2, "company_name": "Beta", "normalized_company_name": "beta", "domain": ""},
    ]

    entities, summary = resolve_entities(rows)

    assert len(entities) == 2
    assert summary["duplicate_records_merged"] == 0


def test_score_successful_hiring_company():
    entity = {
        "domain": "example.com",
        "email": "a@example.com",
        "source_record_count": 2,
        "enrichment_status": "success",
        "enrichment": {
            "employee_count": 120,
            "industry": "Software",
            "hiring_now": True,
            "last_funding_months_ago": 6,
            "tech_signals": ["python", "aws"],
        },
    }

    score, reasons = score_entity(entity)

    assert score > 80
    assert "active_hiring_signal" in reasons


def test_failed_enrichment_gets_penalty():
    entity = {
        "domain": "",
        "email": "",
        "source_record_count": 1,
        "enrichment_status": "skipped",
        "enrichment": {},
    }

    score, reasons = score_entity(entity)

    assert score == 0
    assert "enrichment_incomplete" in reasons


def test_failed_status_is_retry_eligible():
    retry_eligible, next_action = failure_next_action("failed", "http_500")

    assert retry_eligible is True
    assert next_action == "retry_later"
