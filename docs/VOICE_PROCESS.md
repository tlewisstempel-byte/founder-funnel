# Tone of voice process

How Floris's voice file is built and kept up to date. Same process for Tim, Sinead and the company page.

## 1. Collect
- LinkedIn: Settings & Privacy > Data privacy > Get a copy of your data > **larger data archive**.
- Files we use: `Shares.csv` (every post incl. text-only), `Rich_Media.csv` (posts with media), `Comments.csv` (comments: often the most natural writing).
- Keep the raw zip out of the repo (personal data). If emoji and £ show as "?", re-export or open/save the CSV as UTF-8.

## 2. Import
```bash
python3 scripts/import_linkedin_export.py path/to/export-folder
```
Writes `voice/corpus/floris_posts.jsonl`, `voice/corpus/floris_examples.md` (own-voice posts for drafting prompts) and `voice/corpus/import_report.md`.

## 3. Classify each post
In `config/voice_sources.yaml`, by post date:
- **use**: his own voice, used fully (default).
- **info_only**: AI-assisted posts: facts and argument flow only, never wording.
- **exclude**: AI-written posts: ignored entirely.

How to spot AI writing: see the avoid list in `voice/floris.md` section 10 and `voice/export-analysis.md`. When unsure, mark `info_only` and ask the owner.

## 4. Write or update the voice file
`voice/floris.md` is written from the **use** posts only: one-paragraph summary, sentence rhythm, openings, post shapes, endings, humour, people, numbers, words, emoji/hashtags, topics, and a checklist, each with real quotes. Facts he has made public go in the facts list with the post date.

## 5. Use it
The bot's drafting prompt includes `voice/floris.md`, recent examples from `voice/corpus/floris_examples.md`, and `voice/edits/`. The hand-run prompt (`prompts/draft-post.md`) lists the same files.

## 6. Keep learning
- Every Floris edit and owner edit is captured; monthly, `founder-engine edits-summary` writes `voice/edits/YYYY-MM.md`.
- Owner reviews and folds the lessons into `voice/floris.md` (dated changelog at the bottom).
- Re-import the export every 6 months or after a burst of new posts.

## Changelog
- 2026-10-29: v1 from `Rich_Media.csv` (23 own-voice posts). Excluded 11 and 18 May 2026; info-only 28 Sep 2026, 17 Dec 2025, 25 Feb 2026, 12 Aug 2026. Waiting for `Shares.csv` and `Comments.csv`.
