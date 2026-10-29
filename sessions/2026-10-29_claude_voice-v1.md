# Session: Floris voice v1 and the voice process

- **Date:** 2026-10-29 · **Tool:** Claude (claude.ai)

## What I did
- Checked his LinkedIn export (`Rich_Media.csv`) for AI writing: `voice/export-analysis.md`.
- Owner decision: exclude 11 and 18 May 2026; info-only 28 Sep 2026, 17 Dec 2025, 25 Feb 2026, 12 Aug 2026; use the other 23 fully (`config/voice_sources.yaml`).
- `scripts/import_linkedin_export.py`: imports Rich_Media/Shares/Comments CSVs, de-duplicates, classifies, writes `voice/corpus/` (examples file used in drafting).
- Rewrote `voice/floris.md` (v1) from the 23 own-voice posts, with real quotes, post shapes, endings, humour, numbers, avoid-list and checklist.
- `docs/VOICE_PROCESS.md`: the repeatable process. Drafting now includes his real example posts.
- Also today: stat card polish (2x render), standards (natural phrasing, double size, breathing room), income-caps draft (owner's rewrite is current), edit lessons in `voice/edits/2026-10-owner.md`.

## Next
- Owner: source `Shares.csv` and `Comments.csv` (UTF-8 if possible), then re-run the import and update the voice file.
