# Playbook: daily comments for Floris

**Why:** commenting on the right people's posts is often a bigger reach lever than posting, and it builds relationships with buyers and policy voices. LinkedIn has no feed API and we don't scrape it, so a human picks the posts and the system does the rest.

**Target:** 3-5 comments a day, weekdays. Quality over volume.

## Who does what

| Step | Who | Time |
|---|---|---|
| 1. Follow every account in `trends/watchlist.md` and turn on post notifications (the bell) | B2B lead | once, then as the list grows |
| 2. Each morning, scan notifications and the "shared ownership" post search (past 24h); shortlist 5-8 posts | B2B lead | ~10 min |
| 3. Triage with an LLM: paste each post's link, author and full text; the LLM ranks them and drafts comments (prompt: `prompts/triage-comments.md`) | B2B lead + LLM | ~5 min |
| 4. Send Floris the top 3-5 in one Slack message: post link, one-line why, suggested comment | B2B lead (later: the bot) | 1 min |
| 5. Floris copies, edits, posts, ideally before noon | Floris | ~5 min |
| 6. Log which ones he posted (react ✅ in Slack) | Floris | seconds |

Later, the Slack bot replaces steps 3-4: the B2B lead drops posts into `#comment-queue` and Floris receives the finished list.

## What makes a post worth it
- Author is Tier A or B on the watchlist, or a new buyer-side voice worth adding
- Fresh (under 24h) and gaining early comments
- Floris can add something real: a data point, a provider-side view, a lesson from Stairpay
- Skip: KPro, politicians (comment on issues, not people), pile-ons, anything where a comment would read as a pitch

## What a good comment looks like
- 2-4 lines, in Floris's voice
- Adds a fact, a number, a counterpoint or a sharp question; never just praise
- No product pitch, no links
- Never reveals customer data or names a customer without written OK

## Weekly
Friday: add new names worth following to the watchlist; note which comments led to replies, connections or DMs.
