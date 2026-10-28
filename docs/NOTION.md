# Notion: the ideas board view

The bot's log is the source of truth. Notion shows it as a board the team can browse:
**New → Picked → Drafting → With Floris → Approved → Published** (+ Dropped). Sync is one-way (bot → Notion), matched on `Engine ID`, so re-syncing updates rows instead of duplicating them. If Notion is down, the bot carries on and tells the owner.

## Status
- 2026-10-28: test board created in the **wrong workspace** (Captain Scarlet Content Hub) for testing only. Delete it once the real one exists.
- Real Stairpay workspace: not connected yet.

## Connect the real one (about 10 minutes)
1. In Stairpay's Notion: Settings > Connections > Develop or manage integrations > **New integration** ("Stairpay Content", internal). Copy the secret.
2. Create a page "Founder content" where the team can see it. On that page: ••• > Connections > add "Stairpay Content".
3. Set `NOTION_TOKEN` (secret store), then run `founder-engine notion-setup --parent-page <page id>`. It creates the database with the right columns and prints `NOTION_DATABASE_ID`.
4. Set `NOTION_DATABASE_ID`. The bot now syncs after every scan, digest and pick; `founder-engine notion-sync` pushes everything on demand.
5. In Notion, add a **Board** view grouped by Status, sorted by Score (descending). Optional: a "This week" view filtered on Week.

Alternative without the API: import `mockups/board-sample.csv` (or `founder-engine board-export --csv board.csv`) via Notion's Import > CSV.

## Columns
Name · Status · Score · Type · Source · Why now · Week · Urgent · Idea · Draft · Link · Post URL · Floris edited · Engine ID

## Not verified
Notion API version `2022-06-28` is used in `notion_sync.py`; Notion has newer versions that change databases into data sources. Check the current docs before go-live and update `NOTION_VERSION` if needed.
