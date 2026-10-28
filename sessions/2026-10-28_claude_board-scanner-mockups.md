# Session: news scanner, ideas board, Notion + Slack mock-ups

- **Date:** 2026-10-28 · **Tool:** Claude (claude.ai) · **Branch:** claude/board-scanner-2026-10-28 (merged)

## What I did
- `scanner.py` + `config/sources.yaml`: daily RSS/Atom scan (GOV.UK, Google News searches), keyword pre-filter, model triage (relevance, duplicates, score, urgency), never repeats an item. Tested live: 13 matches on 28 Oct, incl. the income-caps story from six outlets and off-topic "shared ownership" stories (boats, Cyprus) that the model must reject.
- `board.py`: one board over every idea and post; columns New → Picked → Drafting → With Floris → Approved → Published (+ Dropped); Markdown and CSV exports.
- Wednesday digest in Slack with tick boxes, Confirm picks, Draft all picked now; `/board`, `/scan`; urgent news alerts.
- `notion_sync.py`: one-way mirror with upsert on Engine ID and a dry-run transport; never blocks the pipeline.
- Mock-ups: `mockups/` (Slack payloads, previews and Block Kit Builder links; board CSV and Markdown). Notion TEST page + database + Board view created in the wrong workspace (Captain Scarlet Content Hub) for testing.
- Diagrams: `docs/WORKFLOW.md`, `docs/TECH_STACK.md`. Sync rules written into `COLLABORATION.md` and `AGENTS.md`.
- 27 tests pass.

## Decisions
Wednesday founder content review; board in Notion + Slack; 24h reminder deprioritised. See decisions log.

## Next
- Owner: test Slack workspace; reconnect Notion to Stairpay; build the strong people list tomorrow.
- Open: is the Wednesday review the same session as the weekly Floris meeting?
