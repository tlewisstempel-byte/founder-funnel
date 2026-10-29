# Floris's LinkedIn history: LLM-pattern check (before full import)

Source: LinkedIn export `Rich_Media.csv`, shared 2026-10-29. 49 items: 28 with text (Mar 2023 to Oct 2026), 14 videos with no caption in the export, the rest image-only.

**Gaps:** this file holds only posts with media. Text-only posts (including the 28 Sep 2026 equity loan post) are in `Shares.csv`; comments are in `Comments.csv`. Emoji, £ and curly quotes arrived as "?" (export encoding), so emoji habits can't be read from this file.

## Verdict per post

| Date | Post | Read | Why |
|---|---|---|---|
| 18 May 2026 | Lease extraction vs ChatGPT/Claude | **Strongly LLM-shaped** | "Fair question."; "But that's not the real problem… The real problem is…"; "the real unlock isn't X. It's what happens next."; four "Can…?" questions in a row; "Not just scanning documents."; "Reading them once. Extracting what matters. Then…"; "Upload it once. Scan it once."; "Not AI as a demo. AI as infrastructure." |
| 11 May 2026 | New website and modules | **Strongly LLM-shaped** | "At the beginning, that sounded exciting. / Then reality hit."; one-word paragraph reveal ("Staircasing"); "Teams don't just need point solutions. / They need better infrastructure."; "The right information, in the right place, at the right time."; "Not X, but purpose-built Y"; module list with dash-separated benefit slogans; "There's a lot more coming." |
| 28 Sep 2026 | Equity loan (from screenshot, not in this file) | **Partly** | Strong human analysis and real numbers, but LLM scaffolding: "Here's the one nobody's asking:", "It's the decade afterwards. 📃", the parallel closer "We are very good at… We are still terrible at…" |
| 17 Dec 2025 | "A little pinch me moment" | **Mostly human, a few assisted lines** | Human: "so I'm knackered", "I closed every one of those contracts", Emilia "still a terrible sleeper". LLM-ish: "No pointless metrics, no silly marketing spend, no pleasing anyone"; "Not a one-off data exercise. A live platform anyone can query"; the "--- fast forward ---" divider with four "I want…" lines |
| 25 Feb 2026 | AI roundtable with nsg | **Mostly human, light** | "My response?" Q&A and "Closing a sale on the phone? Human job" are a little formulaic, but the content and tone are his |
| 12 Aug 2026 | "Any hockey fans out here?" | **Mostly human, light** | "Simple, transparent and expert answers on their journey. And much more…" reads like a tagline |
| All others (22) | Together for Homes, events, UKREiiF, awards, office move, Easter, New Year, offsite (18 Oct), roundtables, podcast, Compliance email | **Human** | See markers below |

## His authentic voice (from the human posts)

- **Run-on, conversational sentences** joined with commas and "but", sometimes slightly ungrammatical ("both him and Claude believe", "astoundment", "deals 6 new Housing Association customers"). Keep the rhythm; fix the slips.
- **Self-deprecating humour and asides:** Catan win, "come on you gunners", "terrible dad dancing", "Sweaty picture of Flors", "Dutch people are too direct", "a much better look than me in a suit", "watch me win a piece of glass".
- **Name-checks people generously**, often many per post, each with a small specific thanks or joke.
- **Personal life appears naturally:** his daughter's first steps, Japan trip, needing R&R.
- **Plain founder-speak:** "obvs", "knackered", "Not gonna lie", "I must admit", "Call me sad but", "pinch me moment".
- **Story with concrete detail:** the coffee shop, ordering a drink every two hours, WeWork backpacks, name on the lift.
- **Pride in running lean (VC-backed since Dec 2022, careful with money) and in the team**, numbers stated plainly (£10k MRR took 3 years, £20k took a month; 1 in 3 homes; 75,000 homes; tripled ARR).
- **Exclamation marks and emoji** in celebratory and event posts; calmer in business posts.
- **Endings:** an invitation ("drop me a line", "DM me, coffee's on me!", "Want to be involved? Let me know!") or a simple sign-off ("See you in 2026", "2026, let's go!").
- **Hashtags:** inline #SharedOwnership or 2-3 at the end, inconsistent case.

## LLM patterns to keep OUT of his drafts (seen in the flagged posts)
- "Fair question." / "Here's the thing" / "Here's the one nobody's asking"
- "The real problem is…", "the real unlock", "what happens next"
- "Not X. Y." and "Not X, but Y" reveals; "Not AI as a demo. AI as infrastructure."
- Strings of fragments: "Upload it once. Scan it once."; "Reading them once. Extracting what matters."
- One-word or one-line reveal paragraphs ("Staircasing"; "Then reality hit.")
- Stacks of rhetorical questions ("Can…? Can…? Can…?")
- Tricolons and slogans ("The right information, in the right place, at the right time.")
- Crafted parallel closers ("We are very good at… We are still terrible at…")
- "There's a lot more coming." / "That feels much closer to the real opportunity."

## Recommendation for the full import
1. Get `Shares.csv` (all text posts) and `Comments.csv` (his most natural writing) from the same export, ideally in a UTF-8 copy so emoji and £ survive.
2. Train the voice file on the **human** posts and comments only; use the flagged posts as **anti-examples**.
3. Keep the *analytical* structure of the equity loan post (debate → overlooked question → hard numbers → what it means for people → Stairpay proof) but write it in his conversational voice, without the scaffolding phrases above.
4. Ask Floris, lightly, whether he used AI on the May posts. Not to judge, just so we know which voice he wants to sound like going forward.
