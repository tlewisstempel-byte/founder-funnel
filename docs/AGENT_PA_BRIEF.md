# Founder Funnel: brief for my agent PA

**Owner:** Tristram Lewis-Stempel, B2B marketing lead, Stairpay
**Last updated:** 2026-10-30
**Full detail:** GitHub repo `tlewisstempel-byte/founder-funnel`, mirrored in Obsidian at `Documents/Obsidian/founder-funnel`. Start with `START_HERE.md`.

---

## 1. What it is, in one paragraph

The Founder Funnel is a content engine. It turns Stairpay's news, anonymised data, team input and a weekly 30-minute chat with Floris into **4-5 LinkedIn posts a week** on Floris's own profile, aimed at B2B buyers in Shared Ownership (housing associations, for-profit providers, developers, lenders, policy people). It is built so that **Floris does almost nothing** (one chat a week, plus approving drafts in Slack), **I do a little** (picking, editing, logging numbers), and the rest of the team do a few minutes of comments or reposts. A Slack bot and a Notion board run the admin.

## 2. Who's who

| Person | Role | What they do in the funnel |
|---|---|---|
| **Floris ten Nijenhuis** | Founder and CEO, Stairpay | Wednesday chat (30 min). Approves drafts in Slack within 24h. Posts himself. Replies to early comments. |
| **Tristram (me)** | B2B marketing lead, owns the system | Runs the board, edits drafts, runs the Wednesday chat, logs metrics, triages comment targets. |
| **Tim Otto** | CPO | Product and workflow angles; comments or reposts when tasked. |
| **Sinead** | B2C marketing | Shared Owner and resident angles; comments or reposts when tasked. |

**About Stairpay:** software for Shared Ownership in England (staircasing, resales, compliance, resident portal). VC-backed since December 2022. **Never call it bootstrapped.** Its one real competitor is KPRO.

## 3. The weekly cycle

| When | What happens | Who |
|---|---|---|
| **Wednesday morning** | The bot posts the **ideas board digest** in Slack: top 10 scored ideas from news scans, the team, meetings and data, plus last week's results. I pre-pick 4-5. | Bot, me |
| **Wednesday** | **Founder content chat** (30 min, recorded): last week's results → pick next week's posts → sector news → inside Stairpay → quick-fire opinions. | Me + Floris |
| **Wednesday after** | Confirm the picks in Slack. The bot drafts them. The transcript is turned into new ideas for the board. | Me, bot |
| **T-48h per post** | Draft and visual ready, every number checked against its source. | Bot, me |
| **T-24h** | Floris gets the draft in Slack (Approve / Edit / Reject). | Floris |
| **Post day** | Floris posts (link in the first comment). The team comments or reposts within 60 minutes, as the playbook says. | Floris, team |
| **T+24h and T+7d** | The bot asks me to log reactions, comments, reposts and impressions (about 30 seconds). | Me |
| **Daily** | Comment routine: I check target people's posts and triage them with the AI, and Floris gets 3-5 ready-to-post comments. | Me, Floris |

**Rhythm:** Tuesday data post (flagship), Wednesday policy take (moves to whenever news breaks), Thursday story, Monday or Friday a product, partner or second data post. Publish on UK weekday mornings.

## 4. Post types

| Type | Per week | Team funnel |
|---|---|---|
| Data post | 1-2 | Me, Tim and Sinead each comment with a different angle |
| Policy / market take | 1 | I comment (provider angle) |
| Story / behind the scenes | 1 | None |
| Product / launch | 0-1 | Tim, me and Sinead repost with our own 2-3 lines |
| Partner / customer proof | 0-1 | I comment |

Each type has its own playbook in `playbooks/` (template, SOP and team funnel).

## 5. Floris's voice (short version)

Full file: `voice/floris.md`, built from his 23 own-voice LinkedIn posts.
- Warm, direct, a bit cheeky. Sounds like a founder talking over coffee, not a brand.
- Long, flowing sentences joined with commas and "but". No punchy one-line reveals.
- Real numbers early. Names and thanks people specifically. Self-deprecating jokes.
- Ends with an invitation ("drop me a line", "coffee's on me"), a next step or a simple sign-off.
- **Banned AI patterns:** "Here's the thing", "Fair question", "The real problem is", "Not X. Y." reveals, strings of short fragments, tricolons, crafted parallel closing lines, needless repeated "the".
- Hashtags: 0-3 specific ones (#SharedOwnership #Housing). British English.

## 6. Where things live

| Thing | Where |
|---|---|
| Source of truth (all docs, code, decisions) | GitHub `founder-funnel`, synced to Obsidian on every change |
| Ideas board | Notion. **The current one is a TEST board in the wrong workspace**; the real Stairpay one is still to connect. |
| Approvals, digests, metrics | Slack bot (built and tested; not yet live) |
| Drafts | `drafts/` in the repo |
| Visuals (stat cards, charts) | `brand/visuals/`, LinkedIn portrait 1080x1350 rendered at 2x |
| Voice files | `voice/` |
| People to comment on (100 list) | `trends/target-people.md` and `.csv` |
| Decisions log | `decisions/DECISIONS.md` |

## 7. Hard rules (never break these)

1. Nothing is published without Floris's approval.
2. Floris's LinkedIn is never automated or scraped. He posts himself. No shared passwords.
3. No customer, partner or person is named without written OK.
4. Data is anonymised and aggregated before it reaches us.
5. No secrets (API keys, tokens) in documents or the repo.
6. Never invent a number, quote or opinion for Floris. Leave a placeholder and ask.
7. Never describe Stairpay as bootstrapped.

## 8. Where things stand (30 Oct 2026)

**Done:**
- Repo, playbooks, voice file v1, weekly meeting kit, intake note for Tim and Sinead, one-pager for Floris.
- Slack bot code (31 tests passing), news scanner, metrics logging, Notion board mock-up.
- First draft: income-caps post with a stat card.
- Target list of 100 people (68 named, 32 role slots).

**Open, on me:**
- [ ] Send Floris the income-caps draft, stat card and one-pager
- [ ] Send Tim and Sinead the intake message
- [ ] Get Floris's `Shares.csv` and `Comments.csv` exports (UTF-8) to finish the voice file
- [ ] Set up a test Slack workspace, tokens and an Anthropic key with a spending limit
- [ ] Reconnect Notion to the Stairpay workspace and delete the TEST board
- [ ] Confirm Tier A target people and follow them with notifications on
- [ ] Fill gaps in the target list: CEOs and home ownership leads at Peabody, Hyde, Guinness, A2Dominion, MTVH, Notting Hill Genesis and Riverside, plus large non-G15 providers (Sanctuary, Home Group, Orbit and others) and for-profits (SO Resi, M&G)
- [ ] Next week: Stairpay Slack, cloud project, data contract with engineering

## 9. How my PA can help

- **Wednesdays:** remind me to pre-pick from the digest before the chat, book and record the chat, and chase the transcript afterwards.
- **Approvals:** chase Floris if a draft has waited more than 20 hours.
- **Metrics:** remind me at 24h and 7 days after each post if I haven't logged numbers.
- **Team:** remind Tim and Sinead of their comment tasks on post days.
- **Comments:** flag new posts from Tier A people that are worth a comment from Floris.
- **Tracking:** keep the open list above current and tell me what's slipping.
- **When drafting anything for Floris:** follow section 5 and section 7, and send it to me first, never straight to him.
