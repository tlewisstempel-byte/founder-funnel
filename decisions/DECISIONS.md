# Decisions log

Newest at the bottom of each section. Add a date to every entry.

## Decided

| Date | Decision | Notes |
|---|---|---|
| 2026-10-28 | Goal: build Floris's brand and credibility; convert gradually. Staying top of mind is the mechanism. | |
| 2026-10-28 | Audience focus: B2B. | Working assumption: housing providers and developers (Stairpay's CRM for shared ownership, per Floris's 7 Oct post). **Confirm.** |
| 2026-10-28 | Language: English (British). | |
| 2026-10-28 | Cadence: 4-5 posts a week, alternating 4- and 5-post weeks. | |
| 2026-10-28 | Floris posts himself, initially. Approval via Slack, within 24h always. | |
| 2026-10-28 | Primary input is SQL insights. Also team inbox, weekly Floris meeting (15-30 min, recorded, Google Meet), company calendar, trends. | |
| 2026-10-28 | Data is anonymised upstream by production/engineering before it reaches this workflow. | Engineer to supply the feed. Floris signs off what is safe to publish. |
| 2026-10-28 | Stack: Python on Cloud Run, small database, Slack as main interface, Notion as read-only mirror. | |
| 2026-10-28 | LLM: Claude via API by default; must stay swappable via config. | |
| 2026-10-28 | Visuals: rendered by code from the Stairpay design kit; real photos for people moments. | Kit: https://claude.ai/artifact/CF5UhbgmPgd5BbA8Jha4cA |
| 2026-10-28 | Company page: used for key posts only; otherwise Floris's profile leads. | |
| 2026-10-28 | Team: 7 people, 4 focus on LinkedIn: Floris, Tim (CPO, product), B2B marketing lead, Sinead (B2C angles). | |
| 2026-10-28 | Daily list of high-impact posts for Floris to comment on, with suggested comments. | |
| 2026-10-28 | Policy commentary defaults to issues and schemes, not named politicians. Naming customers or partners needs written OK. | Floris's view to be discussed. |
| 2026-10-28 | Scaffold in the owner's company cloud account for now, dummy data only; move to Stairpay's project later via config. | |
| 2026-10-28 | Only real competitor: KPro Software (Keaze Ltd). Monitor, never comment on. | Owner |
| 2026-10-28 | Daily comments: B2B lead is the human in the loop (follow + bell, curate 3-5 posts a day, triage with an LLM); system drafts; Floris posts. Target 3-5 a day, not 10. | `playbooks/daily-comments.md` |
| 2026-10-28 | Bot flow, Phase 1: every draft goes to the B2B lead first (edit, then "Send to Floris"); Floris receives drafts and the comment list as DMs from the bot. | Owner |
| 2026-10-28 | Bot storage: SQLite locally for testing, Firestore on Cloud Run; swappable in `store.py`. | Claude, owner agreed |
| 2026-10-28 | Owner creates a free test Slack workspace this week; bot is tested there before Stairpay's Slack. | |
| 2026-10-28 | Team voices: ask Tim and Sinead for their full LinkedIn exports as well as a short intake form. | Owner |
| 2026-10-28 | Founder content review is every Wednesday. The ideas board digest lands Wednesday morning, before the review; posts picked there fill the next weekly cycle. | Owner. Open: is this the same session as the weekly Floris meeting? |
| 2026-10-28 | One ideas board for all sources (inbox, meeting, news scanner, data, calendar). The scanner adds ideas daily but only pings for urgent, fast-lane items. | Board home (Notion vs Obsidian/Slack) to confirm |
| 2026-10-28 | Sync model: one git repo is both the GitHub source of truth and the Obsidian vault on each device. Multiple LLMs work in parallel via branches/worktrees. | See `COLLABORATION.md` |

## Open items (next week unless noted)

- [ ] Floris: request LinkedIn data export (Settings > Data privacy > Get a copy of your data, full archive incl. posts and comments) for `voice/floris.md`
- [ ] Engineer: agree data contract (`data/DATA_CONTRACT.md`) and anonymised feed format
- [ ] Discover what metrics exist in the database
- [ ] Tim and Sinead: full LinkedIn data exports (all posts) + short intake form, for `voice/team.md`
- [ ] Slack admin and bot installation
- [ ] Cloud project ownership and admin access
- [ ] Which voice rules apply where: Floris's own (emoji, exclamation marks) vs Stairpay brand kit (neither). Proposed: Floris voice for his posts, kit voice for company page.
- [ ] Off-limits topics and strong opinions for Floris (not yet known)
- [ ] Policy-commentary stance and naming rules (discussion)
- [ ] Watchlist: which accounts, competitors and newsletters define the vertical
- [ ] LLM API cost check; third-party analytics tool shortlist
- [ ] Image model: decide only if abstract imagery is wanted
- [ ] How to get post metrics (verify LinkedIn options)
- [ ] GitHub: personal account or a Stairpay organisation (org survives staff changes)

## Observations from Floris's recent posts (screenshots, 2026-10-28)

| Date | Type | Reactions / comments / reposts |
|---|---|---|
| 19 Oct | Team moment (photo, board game night) | 30 / 1 / - |
| 7 Oct | Product video (end-to-end shared ownership CRM) | 41 / 4 / 2 |
| 28 Sep | Policy take (equity loan scheme) | 37 / - / 1 |
| 17 Sep | Cause / event (#TogetherForHomes 2026, video) | not visible |
| 13 Aug | Data chart (growth over time) | 37 / 4 / 1 |
| 4 Aug | Podcast with Southern Housing | not visible |

Small sample, no impressions data. Pattern: policy and data posts perform at least as well as product posts; frequency is about once every 10 days.
