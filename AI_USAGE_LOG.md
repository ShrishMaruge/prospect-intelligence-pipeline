# AI Usage Log

## Summary

I used AI as a development assistant during this task. I did not use it as a replacement for understanding the project. I used it to break down the problem, generate implementation ideas, review tradeoffs, draft documentation, and prepare explanations that I could defend in my own words.

## Where I Used AI

I used AI for these parts of the project:

- Understanding the task brief and converting it into backend pipeline requirements.
- Planning the project structure.
- Designing the main pipeline stages: ingestion, normalization, entity resolution, enrichment, scoring, and output.
- Drafting initial Python implementation ideas.
- Thinking through retry, timeout, failure handling, and caching for the enrichment API.
- Drafting README and architecture documentation.
- Creating basic tests for important pipeline behavior.
- Preparing explanations for why specific design decisions were made.

## What I Reviewed Myself

I reviewed the following areas myself so I could understand and defend the project:

- Why normalization must happen before duplicate resolution.
- Why domain-first duplicate matching is safer than name-only matching.
- Why conservative fuzzy matching is better than aggressive merging.
- Why enrichment failures should be recorded instead of crashing the run.
- Why caching makes the pipeline safer to rerun.
- Why scoring should be explainable and rule-based for this task.
- What each output file is used for.

## What I Did Not Understand At First

At first, I was not fully clear on how strict duplicate resolution should be. A more aggressive approach could merge more records, but it could also merge different companies incorrectly.

I resolved this by choosing a conservative strategy:

1. Trust exact normalized domain matches first.
2. Use company-name similarity only when domain is missing.
3. Keep the similarity threshold high.

This may leave some duplicates unresolved, but it avoids the more serious problem of false merges.

## Decision I Made Against Blind AI Use

I kept the scoring logic rule-based and explainable instead of making it more complicated.

A more advanced model might look impressive, but for this task it would be harder to justify. The reviewer needs to understand why a prospect is ranked highly. Rule-based scoring makes each decision visible through score reasons like `active_hiring_signal`, `target_industry`, and `recent_funding`.

## Hardest Part

The hardest part was handling the enrichment API safely. The API can fail, return not found, respond slowly, or return partial data.

I handled this by adding:

- retries
- timeout handling
- cache storage
- failure recording
- continuation after individual failures

This makes the pipeline more realistic because real backend services often depend on unreliable external APIs.

## What I Would Improve With More Time

With more time, I would improve the project by adding:

- bounded concurrent enrichment while respecting rate limits
- richer run summary metrics
- separate retry flow for failed enrichments
- more tests for malformed input data
- configurable scoring weights for different ideal customer profiles
- structured logs for each pipeline stage

## Final Note

AI helped me move faster, but the main decisions in the project are ones I can explain: normalize before matching, match by domain first, retry and cache enrichment, record failures, and keep scoring explainable.
