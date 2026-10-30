# START HERE: Stairpay Founder Content Engine

If you are an LLM (any model, any tool) picking this project up, read this file first, then follow the reading order below. Everything you need is in this folder.

## What this is

A pipeline that turns Stairpay's anonymised data, team input and weekly founder conversations into 4-5 LinkedIn posts a week for Floris ten Nijenhuis (founder, Stairpay), plus a light team amplification layer. Design goal: Floris's effort trends towards zero; the B2B marketing lead's effort starts low and falls; everyone else is near-zero lift.

## Status

Phase 0-1 (2026-10-28). Slack bot code is built and tested with simulated Slack (`docs/SLACK_BOT.md`); not yet connected to any real workspace. Cloud project and data access are pending. See `decisions/DECISIONS.md`, "Open items".

## Reading order

1. `decisions/DECISIONS.md`: what has been decided, by whom, and what is still open
2. `ARCHITECTURE.md`: how the system fits together
3. `playbooks/README.md`: weekly rhythm and the universal post SOP
4. `playbooks/*.md`: one playbook per post type (template + SOP + team funnel)
5. `voice/`: how Floris, the team and the company page sound (`docs/VOICE_PROCESS.md` explains how the voice files are built)
6. `brand/`: design tokens and logos for visuals
7. `data/DATA_CONTRACT.md`: what we need from the SQL database (anonymised)
8. `trends/watchlist.md`: who and what we monitor
9. `config/pipeline.example.yaml`: all tunable settings
   - `BACKLOG.md`: what is being shipped now; `drafts/`: post drafts; `prompts/`: prompts to hand-run in any LLM
10. `COLLABORATION.md`: how several LLMs and devices work on this at once (git + Obsidian). **Read before editing.**
11. `sessions/`: handoff notes; read the latest three
12. `meetings/` (weekly Floris meeting kit), `team/` (intake for Tim and Sinead, one-pager for Floris), `brand/visuals/` (chart and card generator)
13. `docs/WORKFLOW.md`, `docs/TECH_STACK.md` (diagrams), `docs/NOTION.md`, `mockups/` (Slack and Notion mock-ups)
14. `docs/AGENT_PA_BRIEF.md`: one-page brief for the owner's PA agent
15. `docs/SLACK_BOT.md`: the Slack bot (what it does, setup, code map); code in `src/founder_engine/`, tests in `tests/`

## Hard rules (never break these)

1. Nothing is published without Floris's approval.
2. Nothing un-anonymised ever enters this workflow. Data arrives pre-anonymised and aggregated.
3. Floris's LinkedIn account is never automated: he posts himself. No scraping of LinkedIn, no shared passwords.
4. No customer, partner or individual is named without written OK.
5. No secrets in this repo. Keys live in the cloud secret store; `.env.example` lists names only.
6. All model calls go through one module (`src/founder_engine/llm.py`) so the provider can be swapped by changing config.
7. Every inbound and outbound integration (Slack, Notion, Google Docs, SQL) is an adapter. Swapping one must not touch the core.

## People

| Role | Responsibility |
|---|---|
| Floris | Founder. Weekly 15-30 min conversation (recorded). Approves drafts within 24h in Slack. Posts himself. |
| B2B marketing lead | Owner of the system. Edits drafts, runs the weekly review. |
| Tim (CPO) | Product angles. Receives amplification tasks. |
| Sinead (B2C marketing) | Shared-owner / resident angles. Receives amplification tasks. |

## If you are asked to continue the work

Check `decisions/DECISIONS.md` for the latest state, make changes as files in this folder, and log any new decision there with a date.
