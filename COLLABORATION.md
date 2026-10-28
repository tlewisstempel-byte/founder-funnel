# Collaboration protocol: many LLMs, many devices

Goal: several LLMs (and humans) can work on this project at the same time, on one device or many, without overwriting each other. **Git is the sync layer. The Obsidian vault is this same folder.** There is no second copy.

## Setup (once per device)

1. Clone the GitHub repo: `git clone <repo-url> stairpay-founder-engine`
2. In Obsidian: **Open folder as vault** and choose that folder (or, if it sits inside an existing vault, just browse to it). Do not copy files into a different vault.
3. Optional: install the community plugin "Obsidian Git" to auto-pull and auto-commit on a timer.
4. `.obsidian/` settings that are personal (workspace, cache) are git-ignored; shared ones are not.
5. Use **one sync method only** for this folder. If the vault is on iCloud, Dropbox or Obsidian Sync, keep the repo outside the synced area or exclude it; mixing git with a file-sync service can corrupt `.git`.

## Rules for every LLM and human

1. **Pull before you start, push when you stop.** `git pull --rebase`, then work, then commit and `git push`.
2. **One branch per working session.** Name it `<tool>/<topic>-<date>`, e.g. `claude/voice-floris-2026-11-03`. Merge to `main` through a pull request, or fast-forward if you worked alone.
3. **Several LLMs on one device: use one git worktree each**, never the same working folder:
   `git worktree add ../engine-<tool> -b <tool>/<topic>-<date>`
4. **One writer per file at a time.** Before editing a shared file (`ARCHITECTURE.md`, `decisions/DECISIONS.md`), check `sessions/` for another active session touching it. Prefer adding new files to editing shared ones.
5. **Append-only logs.** Never rewrite history in `decisions/DECISIONS.md`: add a dated row. Session notes are one new file per session (below), so they never conflict.
6. **Small, focused commits** with a clear message. Do not reformat files you were not asked to change.
7. **Never commit secrets, raw data or personal data.** Only anonymised, aggregated data may appear in this repo.
8. **Hard rules in `START_HERE.md` apply to everyone.**

## Session notes (how work survives across LLMs and devices)

At the end of every session, add one file: `sessions/YYYY-MM-DD_<tool>_<topic>.md` with:
- What I did
- What changed (files)
- Decisions made (also logged in `decisions/DECISIONS.md`)
- What is next / blockers
- Questions for a human

Start every session by reading `START_HERE.md`, `decisions/DECISIONS.md` and the **latest three files in `sessions/`**.

## Merge conflicts

If git reports a conflict in a Markdown file: keep both sides, tidy by hand, and note it in your session file. If unsure, stop and ask a human.

## Obsidian conventions

- Plain Markdown only; relative links; no plugin-specific syntax that breaks other tools.
- Front-matter is optional. If used, keep `status:` (draft, agreed, stale) and `updated:` (date).
- Attachments (images, logos) live next to the files that use them, not in a global folder.

## Tool entry points

Each tool reads its own pointer file, and each points here: `AGENTS.md` (generic), `CLAUDE.md` (Claude). Add more (e.g. for other assistants) if needed. Keep the content in `START_HERE.md`, never duplicated in the pointers.
