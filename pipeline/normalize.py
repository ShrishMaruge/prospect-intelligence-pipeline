from __future__ import annotations

import re
from datetime import datetime
from email.utils import parseaddr


LEGAL_SUFFIXES = {
    "inc", "ltd", "llc", "limited", "corp", "corporation", "pvt", "private",
    "company", "co", "group", "holdings", "solutions", "technologies"
}

COUNTRY_MAP = {
    "usa": "United States",
    "us": "United States",
    "united states": "United States",
    "uk": "United Kingdom",
    "united kingdom": "United Kingdom",
    "india": "India",
    "in": "India",
}


def clean_text(value: str | None) -> str:
    return " ".join((value or "").strip().split())


def normalize_domain(value: str | None) -> str:
    domain = (value or "").strip().lower()
    domain = re.sub(r"^https?://", "", domain)
    domain = re.sub(r"^www\.", "", domain)
    domain = domain.split("/")[0].split("?")[0]
    return domain.strip()


def normalize_company_name(value: str | None) -> str:
    name = clean_text(value)
    name = re.sub(r"[^\w\s]", " ", name.lower())
    parts = [p for p in name.split() if p not in LEGAL_SUFFIXES]
    return " ".join(parts)


def normalize_country(value: str | None) -> str:
    key = clean_text(value).lower()
    return COUNTRY_MAP.get(key, clean_text(value))


def parse_employee_count(value: str | None) -> int | None:
    text = (value or "").lower().replace(",", "").strip()
    if not text:
        return None

    numbers = [int(n) for n in re.findall(r"\d+", text)]
    if not numbers:
        return None

    if "+" in text:
        return numbers[0]

    if "-" in text or "to" in text:
        return int(sum(numbers[:2]) / len(numbers[:2]))

    return numbers[0]


def normalize_email(value: str | None) -> str:
    email = parseaddr(value or "")[1].lower().strip()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return ""
    return email


def parse_date(value: str | None) -> str:
    text = clean_text(value)
    if not text:
        return ""

    formats = ["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass

    return text


def stable_id(domain: str, normalized_name: str) -> str:
    base = domain or normalized_name or "unknown"
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")