# Architecture: Stairpay Founder Content Engine

Version 0.1 · 2026-10-28 · Status: design agreed in principle, nothing built

## 1. Goal and constraints

Build Floris's brand and credibility with Stairpay's B2B audience, so that Stairpay is top of mind when buyers are ready. Conversion is gradual and indirect.

- Cadence: 4-5 posts a week from Floris's personal profile (alternating 4- and 5-post weeks), plus company-page posts for key moments only.
- Lift: Floris approves in Slack within 24h and posts himself. The B2B lead starts hands-on. Tim and Sinead only copy-paste ready-written comments or reposts.
- Starting point (from his profile, 2026-10-28): about 4.8k followers, roughly one post every 10 days, typical 30-40 reactions. The company page has about 1k followers.
- Constraint: everything must be portable, so another LLM or tool can take it over from the repo alone.

## 2. Design principles

1. **Files are the brain, code is plumbing.** Voice, playbooks, SOPs, prompts and decisions are Markdown in this repo. Code only moves data and calls models.
2. **Everything at the edges is an adapter.** Inputs (SQL, Slack inbox, transcripts) and outputs (Slack, Notion, Docs) are swappable plug-ins.
3. **A human approves everything public.**
4. **Anonymise before entry.** Production produces anonymised, aggregated views. This system never touches raw customer data.
5. **Log everything, learn from edits.** Floris's edits are the training signal for his tone file.
6. **Provider-agnostic.** One module calls the model. Claude is the default.
7. **Manual first where automation is risky.** Automate once the manual version works.

## 3. Overview

```
INPUTS                      IDEA BANK       DRAFTING            APPROVAL            PUBLISH & AMPLIFY          LEARN
SQL (anonymised views) ──┐
Team inbox (Slack) ──────┤
Weekly Floris meeting ───┼─► scored ideas ─► draft engine ─► Floris approves ─► Floris posts ─► team tasks ─► metrics ─► log
Company calendar ────────┤   (+ buffer)      voice + playbook   in Slack, 24h     himself         (Slack DMs)   (24h, 7d)    │
Trends / watchlist ──────┘        ▲                                                                                        ▼
                                  └── fast lane: meeting notes and timely news skip the bank ──────────── monthly edit summary → tone file
```

## 4. Components

### 4.1 Inputs
| Input | How it arrives | Lift |
|---|---|---|
| SQL insights | Weekly job runs saved queries against anonymised views (see `data/DATA_CONTRACT.md`) and proposes ideas ("what changed, what is notable") | Zero for the team once built |
| Team inbox | A Slack channel or form: anyone drops an observation, quote, win | Seconds |
| Floris meeting | Weekly 15-30 min recording, transcribed, split into ideas and draft angles | Zero extra for Floris |
| Company calendar | Launches, hires, events, partner dates in a simple file or sheet | Low |
| Trends | See section 9 | Zero once built |

### 4.2 Idea bank and draft buffer
- Every input becomes an **idea** record with type, pillar, source and a score (timeliness, data strength, fit with pillars, freshness vs recent posts).
- Each week the top ideas are drafted into a **buffer** of 8-10 approved-or-ready drafts. The buffer is what absorbs Floris's irregularity: if he misses a day, the next buffered post goes out.
- **Fast lane:** meeting material and breaking policy news go straight to drafting.

### 4.3 Draft engine
Inputs to each draft: the idea, `voice/floris.md`, the playbook for that post type, recent posts (to avoid repeats) and any approved data. Output: two variants, three alternative hooks, a visual brief, and a list of claims that need checking against the data.

### 4.4 Approval
Slack message to Floris with Approve / Edit / Reject. Edit opens a pre-filled text box. Target response within 24h. If not approved by publish time, the next buffer post is swapped in and the missed one is re-queued.

### 4.5 Publish
Floris posts himself. He pastes the live link into the Slack thread; the system stores the live text and compares it to the approved text. Company-page versions (key posts only) are posted manually at first.

### 4.6 Amplification
On publish, the system DMs the relevant teammates with the action, the deadline and ready-written text in their voice. Rules per post type are in `playbooks/`.

### 4.7 Learn
Metrics are logged at 24h and 7 days. Each month the system summarises Floris's before/after edits into `voice/edits/YYYY-MM.md` and proposes updates to `voice/floris.md`. The owner reviews before anything changes.

## 5. Data model (log)

**Idea:** id · created_at · source (sql, inbox, meeting, calendar, trend) · raw_text · pillar · post_type · score · status (new, selected, drafted, dropped) · anonymised_confirmed (bool)

**Post:** id · idea_id · post_type · slot · drafts[] (version, text, model, prompt_version) · visual_ref · status (drafted, sent, approved, edited, rejected, published) · floris_final_text · diff · approved_at · published_at · post_url · company_page_flag · team_tasks[] (person, action, text, due, done) · metrics_24h · metrics_7d

Start storage: Firestore or Postgres in the cloud project, whichever the owner finds easier. Notion is a read-only mirror for browsing. The repo stores the lessons (`voice/edits/`), the database stores the evidence.

## 6. Weekly rhythm (hypothesis, to be tested)

See `playbooks/README.md`. Four slots every week (data, policy take, story/people, product or partner proof), plus an optional fifth (light/community) in 5-post weeks. Floris posted about every 10 days recently, so go-live needs a buffer of 8-10 ready drafts first.

## 7. How Floris's lift trends to zero

| Phase | Floris does | Owner does |
|---|---|---|
| 1 | Weekly meeting, approves every draft in Slack, edits freely | Reviews and edits every draft before it reaches Floris |
| 2 | Weekly meeting, one-tap approve on most drafts | Spot-checks, fixes data and facts |
| 3 | Meeting (shorter), weekly digest approval | Monthly tone-file update, strategy |

Phase moves are decided by data: share of drafts approved unedited, and average edit size.

## 8. Team funnel

Per post type, not fixed. Detailed in `playbooks/`. Principle: amplification should look natural. Reposts are for product and launch moments; substantive comments are for data and policy; personal posts get little or none. Tim, Sinead and the owner each have a voice profile (`voice/team.md`), and the system pre-writes their comment for them to edit. LinkedIn does not let tools post comments for them, so they copy-paste.

## 9. Trend scanning: what is realistic

- **LinkedIn feed scanning is not something to automate.** It breaks LinkedIn's terms and risks restricting accounts. Floris's account must never be used for this.
- **Watchlist + human curation (decided 2026-10-28).** 30-50 accounts across housing providers, trade bodies, policy voices and peers. LinkedIn has no feed API and is not scraped, so the B2B lead is the human in the loop: follows every watchlist account with post notifications on, picks 3-5 posts each morning, triages them with an LLM, and the system turns them into a ready-to-post comment list for Floris. Full SOP: `playbooks/daily-comments.md`. Realistic volume is 3-5 a day, not 10: a 50-account niche watchlist produces only about 7 posts a day in total.
- **Off-LinkedIn signals (automatable, legal).** Trade press, government and Homes England announcements, parliamentary activity, sector newsletters, Reddit threads, podcasts. These usually lead LinkedIn by days.
- **Third-party LinkedIn data tools:** optional and carry terms-of-service risk. Decision deferred; owner to assess risk appetite.

In a niche vertical, "trending" really means "what the few hundred people who matter are reacting to", which the watchlist plus off-LinkedIn sources cover well.

## 10. Visuals

- Charts, stat cards and quote cards are **rendered by code** from the real numbers using `brand/tokens.json` and Poppins (open-source Google font). Image models garble numbers and small text, so they are not used for data visuals.
- Carousels: HTML templates exported to PDF.
- Photos: real photos only, sent to Slack by Floris or the team. His team and event posts are the ones that feel human.
- An image model is optional for abstract imagery only. Model choice sits behind the same swappable layer; not decided.
- Brand rules from the design kit: one accent moment per view, no gradients, no emoji, no pure black, status never by colour alone. Chart series use the powder/rice/slate scales; iris-600 for the main series, iris-400 as a single highlight.
- **Voice split:** visuals follow the Stairpay brand kit; post text follows Floris's voice; company-page text follows `voice/company-page.md`. The kit's voice rules are consumer-facing (no emoji, no exclamation marks), whereas Floris's own posts use both. Decide explicitly which applies where (logged as an open item).

## 11. Hosting and portability

```
GitHub repo (source of truth: files + code)
   │  deploy on merge
   ▼
Cloud Run service   ← Slack buttons and events need a live endpoint
Cloud Run job       ← weekly pipeline, triggered by Cloud Scheduler
   │
Database (Firestore or Postgres) · Secret Manager · Cloud Storage (images, transcripts)
```

- Portability lives in GitHub, not Cloud Run. Cloud Run only runs what the repo says.
- All environment-specific values (project ID, keys, workspace IDs, model name) come from configuration. Moving from a scaffold project to Stairpay's own project means redeploying with new config.
- Scaffold in the owner's company account for now, using dummy data only. Move before any real anonymised data or a production Slack app is connected.
- Switching LLM provider: change `llm.provider` and the key in config; one module changes.
- Switching Slack to Notion or Docs (or adding them): write one output adapter.

## 12. Security and governance

- Anonymised, aggregated inputs only. Proposed minimum cohort size for any published figure, to be agreed with Floris and whoever advises on UK GDPR: see `data/DATA_CONTRACT.md`.
- Floris signs off what data is safe to publish.
- Read-only database credentials. Secrets in the cloud secret store. Least-privilege Slack app.
- Every published number links back to the query that produced it (stored in the log).

## 13. Cost (unverified estimate)

Model usage at about 5 posts plus team comments a week is probably in the tens of pounds a month. Cloud Run and a small database should sit at or near free tiers. Confirm against current pricing before committing. Third-party analytics or scheduling tools are optional extras.

## 14. Risks

| Risk | Mitigation |
|---|---|
| Re-identifiable data in a post | Anonymise upstream, minimum cohort size, owner and Floris review, claims checklist per draft |
| Floris becomes the bottleneck | 24h SLA, buffer of ready drafts, one-tap approval, fast lane only for timely items |
| Posts sound generic or machine-made | Tone file from his full history, monthly edit learning, real photos and meeting material as the raw ingredient |
| Posting frequency jump (about every 10 days to 4-5 a week) | Build buffer first; review reach and fatigue weekly; the 4-5 target is adjustable |
| Metrics blind spot (personal-profile analytics are hard for tools to read) | Verify current options; fall back to a monthly export or a 2-minute weekly paste into Slack |
| Single-person dependency | Everything in files; `START_HERE.md`; adapters |

## 15. Build order

1. **Now (Phase 0):** this repo, decisions log, playbooks, data contract draft.
2. **Next week:** access (Slack admin, cloud project, engineer data feed), Floris's LinkedIn export, first recorded meeting. **Run the first posts by hand** (an LLM chat plus these files, no code) to prove the content before coding.
3. **Phase 1 code:** idea bank, draft engine, Slack approval and logging.
4. **Phase 2:** team tasks, daily comment list for Floris, buffer management.
5. **Phase 3:** automatic SQL ingestion, off-LinkedIn trend scan, chart and carousel rendering.
6. **Phase 4:** metrics logging, monthly tone-file learning, company-page flow.

## 16. Not yet verified

LinkedIn's current options for reading post analytics and posting to company pages via approved apps; current model pricing; which image model, if any, to use. Check each before the relevant build step.
