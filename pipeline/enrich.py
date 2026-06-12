from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path


RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def load_cache(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_cache(path: Path, cache: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(cache, indent=2, sort_keys=True), encoding="utf-8")
    temp.replace(path)


def post_json(url: str, payload: dict, timeout: float) -> tuple[int, dict]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, {"detail": exc.read().decode("utf-8", errors="replace")}


def enrich_domain(domain: str, base_url: str, max_attempts: int = 4) -> dict:
    if not domain:
        return {"status": "skipped", "reason": "missing_domain", "attempts": 0, "data": None}

    url = f"{base_url.rstrip('/')}/enrich"
    last_error = ""

    for attempt in range(1, max_attempts + 1):
        time.sleep(0.15 * attempt)

        try:
            status, payload = post_json(url, {"domain": domain}, timeout=4)
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            continue

        if status == 200:
            return {"status": "success", "reason": "", "attempts": attempt, "data": payload}

        if status == 404:
            return {"status": "not_found", "reason": "provider_404", "attempts": attempt, "data": None}

        if status == 422:
            return {"status": "failed", "reason": "provider_422", "attempts": attempt, "data": None}

        last_error = f"http_{status}: {payload.get('detail', '')}"

        if status not in RETRYABLE_STATUS:
            break

    return {
        "status": "failed",
        "reason": last_error or "max_attempts_exceeded",
        "attempts": max_attempts,
        "data": None,
    }


def failure_next_action(status: str, reason: str) -> tuple[bool, str]:
    if status == "failed":
        return True, "retry_later"
    if status == "not_found":
        return False, "verify_domain_or_accept_not_found"
    if status == "skipped" and reason == "missing_domain":
        return False, "fix_or_source_domain"
    return False, "review"


def enrich_entities(entities: list[dict], cache_path: Path, base_url: str) -> tuple[list[dict], dict, list[dict]]:
    cache = load_cache(cache_path)
    enriched = []
    failures = []
    api_calls = 0
    cache_hits = 0

    for entity in entities:
        domain = entity.get("domain", "")

        if domain and domain in cache:
            result = cache[domain]
            cache_hits += 1
        else:
            result = enrich_domain(domain, base_url)
            if domain:
                cache[domain] = result
                save_cache(cache_path, cache)
            api_calls += 1

        row = entity.copy()
        row["enrichment_status"] = result["status"]
        row["enrichment_reason"] = result["reason"]
        row["enrichment_attempts"] = result["attempts"]
        row["enrichment"] = result["data"] or {}
        enriched.append(row)

        if result["status"] != "success":
            retry_eligible, next_action = failure_next_action(result["status"], result["reason"])
            failures.append(
                {
                    "entity_id": row["entity_id"],
                    "company_name": row["company_name"],
                    "domain": domain,
                    "status": result["status"],
                    "reason": result["reason"],
                    "attempts": result["attempts"],
                    "retry_eligible": retry_eligible,
                    "next_action": next_action,
                }
            )

    summary = {
        "enrichment_success": sum(1 for r in enriched if r["enrichment_status"] == "success"),
        "enrichment_failed": sum(1 for r in enriched if r["enrichment_status"] == "failed"),
        "enrichment_not_found": sum(1 for r in enriched if r["enrichment_status"] == "not_found"),
        "enrichment_skipped": sum(1 for r in enriched if r["enrichment_status"] == "skipped"),
        "enrichment_api_calls": api_calls,
        "enrichment_cache_hits": cache_hits,
    }

    return enriched, summary, failures
