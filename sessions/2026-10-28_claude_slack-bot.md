# Session: Slack bot build

- **Date:** 2026-10-28 · **Tool:** Claude (claude.ai) · **Branch:** claude/slack-bot-2026-10-28 (merged to main)

## What I did
Built the Slack bot as a Python package (`src/founder_engine/`) with 15 passing tests that simulate Slack and the model (`pytest`). Flows: ideas (channel + `/idea`), drafting (`/draft`, fast lane, 2 variants + hooks + claims checklist), owner review card, Floris approval DM with edit capture, "I've posted it" with live-text diff, team tasks per `config/funnels.yaml`, daily comment list (`#comment-queue` + `/comments`), `/buffer`, monthly edit summary. Added Slack manifest, Dockerfile for Cloud Run, setup guide `docs/SLACK_BOT.md`.

## Decisions
Owner reviews every draft first; Floris gets DMs; SQLite locally, Firestore on Cloud Run; owner will create a test workspace. Logged in `decisions/DECISIONS.md`.

## Next
1. Owner: create the test workspace and app (steps in `docs/SLACK_BOT.md`), share tokens securely, plus an Anthropic API key with a spend limit.
2. Claude: run the bot end to end in the test workspace; fix what real Slack shows up.
3. Then: 24h reminder and buffer swap-in; Floris meeting kit; idea bank view; chart renderer.

## Not verified
Real Slack behaviour (only simulated so far); real model output quality; current model name for `LLM_MODEL`.
