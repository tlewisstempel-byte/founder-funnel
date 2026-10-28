# Data contract: request to engineering

**From:** B2B marketing · **Status:** DRAFT proposal, to agree together · **Purpose:** give the content pipeline a safe, anonymised feed from the Stairpay database so Floris's LinkedIn posts can use real platform data.

## What we need, in one paragraph
A read-only, anonymised and aggregated data feed, refreshed weekly, that the content pipeline can query. No raw customer data should ever reach this workflow: anonymisation happens on your side, before the feed.

## Principles
1. **Aggregated only.** No row represents one person or one home.
2. **No direct or indirect identifiers.** No names, emails, addresses, user or home IDs, free text, or fine-grained location. Region level at most (to agree).
3. **Minimum cohort size.** Any published number must come from a group of at least N. Proposal: **N = 10**, to be agreed with Floris and whoever advises Stairpay on UK GDPR. Cells below N are suppressed or merged, not published.
4. **Coarse time.** Month level, not exact dates, unless the aggregate is large.
5. **Stable definitions.** Each metric has a written definition so a post can state it accurately.
6. **Provenance.** Each metric carries its period and count so every published figure can cite its source.

## Proposed format (pick what is easiest for you)
- **Preferred:** views in the existing warehouse/database with a dedicated read-only credential; or
- A scheduled export of CSV files into a cloud storage bucket; or
- A small internal endpoint returning JSON.

Refresh: weekly (Monday morning UK time) is enough to start.

## Candidate metrics (to refine after we know what exists)
Names are placeholders; please tell us what really exists.

| Area | Examples |
|---|---|
| Platform scale | Homes on platform over time (monthly); active users |
| Staircasing | Share of owners who staircase; typical share bought; time from interest to completion |
| Resales | Number of resales, typical time to sell, by region |
| Costs | Service charge and rent trends (aggregated bands) |
| Engagement | Which tools residents use most, in aggregate |
| Provider-side | Aggregated trends by provider size band (only above cohort threshold) |

## Fields the feed should include
`metric_name`, `period_start`, `period_end`, `value`, `count_in_cohort`, `segment` (e.g. region or size band, optional), `definition_id`, `generated_at`.

## What we will do with it
Run saved queries against the feed to propose post ideas, render charts, and store the query and period behind every published figure. Nothing goes public without Floris's approval.

## Questions for engineering
1. What metrics can you produce safely, and how are they defined today?
2. Which tooling do you prefer to expose them with?
3. Who owns the anonymisation logic and its review?
4. Can access be read-only and revocable?
5. How soon could a first sample (dummy or real aggregate) be available?

## Sign-off
- Floris (what is safe to publish): ______
- Engineering (anonymisation correct): ______
- Legal/GDPR check (if required): ______
