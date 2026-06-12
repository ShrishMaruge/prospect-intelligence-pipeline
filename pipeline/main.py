from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from .enrich import enrich_entities
from .ingest import ingest_and_normalize
from .output import write_outputs, write_stage_outputs
from .resolve import resolve_entities
from .score import score_and_rank


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prospect intelligence pipeline")
    parser.add_argument("--input", default="data/raw_prospects.csv")
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--state-dir", default="state")
    parser.add_argument("--api-url", default="http://127.0.0.1:8900")
    return parser


def percentage(part: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round((part / total) * 100, 2)


def score_distribution(ranked: list[dict]) -> dict:
    buckets = {
        "0_24": 0,
        "25_49": 0,
        "50_74": 0,
        "75_99": 0,
        "100_plus": 0,
    }

    for row in ranked:
        score = int(row["score"])
        if score >= 100:
            buckets["100_plus"] += 1
        elif score >= 75:
            buckets["75_99"] += 1
        elif score >= 50:
            buckets["50_74"] += 1
        elif score >= 25:
            buckets["25_49"] += 1
        else:
            buckets["0_24"] += 1

    return buckets


def top_prospects(ranked: list[dict], limit: int = 10) -> list[dict]:
    return [
        {
            "company_name": row.get("company_name"),
            "domain": row.get("domain"),
            "score": row.get("score"),
            "score_reasons": row.get("score_reasons"),
            "enrichment_status": row.get("enrichment_status"),
        }
        for row in ranked[:limit]
    ]


def run(args: argparse.Namespace) -> dict:
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    state_dir = Path(args.state_dir)

    normalized, ingest_summary = ingest_and_normalize(input_path)
    entities, resolution_summary = resolve_entities(normalized)

    enriched, enrichment_summary, failures = enrich_entities(
        entities,
        cache_path=state_dir / "enrichment_cache.json",
        base_url=args.api_url,
    )

    ranked, scoring_summary = score_and_rank(enriched)

    failure_breakdown = Counter(row["reason"] for row in failures)
    total_enriched = len(enriched)
    total_cache_lookups = enrichment_summary["enrichment_api_calls"] + enrichment_summary["enrichment_cache_hits"]

    summary = {
        **ingest_summary,
        **resolution_summary,
        **enrichment_summary,
        **scoring_summary,
        "enrichment_success_rate": percentage(enrichment_summary["enrichment_success"], total_enriched),
        "cache_hit_rate": percentage(enrichment_summary["enrichment_cache_hits"], total_cache_lookups),
        "failure_breakdown": dict(failure_breakdown),
        "score_distribution": score_distribution(ranked),
        "top_10_prospects": top_prospects(ranked),
        "output_files": {
            "ranked_prospects": str(output_dir / "ranked_prospects.csv"),
            "failed_enrichments": str(output_dir / "failed_enrichments.csv"),
            "dead_letter_enrichments": str(output_dir / "dead_letter_enrichments.csv"),
            "normalized_records": str(output_dir / "normalized_records.csv"),
            "resolved_entities": str(output_dir / "resolved_entities.csv"),
            "enriched_records": str(output_dir / "enriched_records.json"),
            "run_summary": str(output_dir / "run_summary.json"),
        },
    }

    write_stage_outputs(output_dir, normalized, entities, enriched)
    write_outputs(output_dir, ranked, failures, summary)
    return summary


def main() -> None:
    args = build_parser().parse_args()
    summary = run(args)

    print("Pipeline finished successfully")
    print(f"Raw records: {summary['raw_records']}")
    print(f"Normalized records: {summary['normalized_records']}")
    print(f"Resolved entities: {summary['resolved_entities']}")
    print(f"Duplicates merged: {summary['duplicate_records_merged']}")
    print(f"Enriched successfully: {summary['enrichment_success']}")
    print(f"Enrichment success rate: {summary['enrichment_success_rate']}%")
    print(f"Cache hit rate: {summary['cache_hit_rate']}%")
    print(
        "Failed/not found/skipped: "
        f"{summary['enrichment_failed'] + summary['enrichment_not_found'] + summary['enrichment_skipped']}"
    )
    print(f"Ranked prospects: {summary['ranked_prospects']}")
    print(f"Outputs written to: {summary['output_files']['ranked_prospects']}")


if __name__ == "__main__":
    main()
