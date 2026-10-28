"""Build the ideas-board mock-ups from sample data, using the bot's real code paths.

Outputs (mockups/): board-sample.csv (import into Notion), board-sample.md (Obsidian),
slack/*.json (exact Block Kit payloads the bot sends) and slack/README.md (preview links).
News items are real (scanned 2026-10-28); items marked EXAMPLE are invented to show other sources.
Run: PYTHONPATH=src python3 scripts/make_mockups.py
"""

import csv
import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from founder_engine import blocks, board  # noqa: E402
from founder_engine.models import CommentCandidate, Idea, Post, TeamTask  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "mockups"
WEEK = "2026-W45"

ideas = [
    Idea(raw_text="Government raises shared ownership income caps: £80k to £90k outside London, £90k to £110k in London, from the new year. First change since 2016.",
         source="trend", post_type="policy-take", title="Shared ownership income caps raised", urgent=True, score=9,
         why_now="Announced 26 Oct; sector reacting this week", score_notes="timely 3, data 2, fit 2, fresh 2",
         source_url="https://www.insidehousing.co.uk/news/government-announces-increase-to-shared-ownership-income-caps-99295"),
    Idea(raw_text="Older people's specialist housing association adopts the Shared Ownership Code; adoption keeps growing after L&Q became the first G15 in July.",
         source="trend", post_type="policy-take", title="Shared Ownership Code adoption keeps growing", score=6,
         why_now="Another provider signed up last week", score_notes="timely 2, data 1, fit 2, fresh 1",
         source_url="https://www.insidehousing.co.uk/news/specialist-older-peoples-housing-association-adopts-shared-ownership-code-99224"),
    Idea(raw_text="US affordable housing investor enters the UK with a £100m target (Inside Housing Living, 28 Oct).",
         source="trend", post_type="policy-take", title="US investor brings £100m to UK affordable housing", score=5,
         why_now="New capital entering the sector", score_notes="timely 2, data 0, fit 2, fresh 1",
         source_url="https://news.google.com/rss/search?q=%22affordable+housing+investor%22+%C2%A3100m+UK"),
    Idea(raw_text="EXAMPLE (meeting): Floris on what providers get wrong about resales: 'most of the delay is waiting, not work'.",
         source="meeting", post_type="policy-take", title="EXAMPLE: What providers get wrong about resales", score=7,
         why_now="Strong line from the weekly chat", score_notes="timely 1, data 2, fit 2, fresh 2"),
    Idea(raw_text="EXAMPLE (data): [DATA NEEDED] median time from staircasing enquiry to completion, by quarter.",
         source="sql", post_type="data-post", title="EXAMPLE: How long staircasing really takes", score=8,
         why_now="Pairs with the income caps news", score_notes="timely 2, data 3, fit 2, fresh 1"),
    Idea(raw_text="EXAMPLE (team inbox, Tim): new resales module goes live next month.",
         source="inbox", post_type="product-launch", title="EXAMPLE: Resales module launch", score=6,
         why_now="Launch date set", score_notes="timely 2, data 1, fit 2, fresh 1", status="picked", week=WEEK),
    Idea(raw_text="Team board game night (19 Oct post).", source="meeting", post_type="story-bts",
         title="Team board game night", score=5, status="drafted"),
]
caps, code, investor, resales, data, launch, games = ideas
draft = Path(__file__).resolve().parents[1] / "drafts" / "2026-10-28_income-caps.md"
caps_text = draft.read_text().split("## Variant A")[1].split("---")[0].split("\n", 1)[1].strip()
caps.status = "drafted"
caps_post = Post(idea_id=caps.id, post_type="policy-take", status="in_review",
                 variants=[{"angle": "door and hallway", "text": caps_text}],
                 hooks=["£80k in 2016 is not £80k in 2026.", "The shared ownership income cap just moved for the first time in a decade."],
                 claims=[{"claim": "Caps rise to £90k / £110k from the new year", "source": "Written statement, 26 Oct 2026"},
                         {"claim": "First change since 2016", "source": "Inside Housing, 27 Oct 2026"}])
caps_post.add_version(caps_text, "llm")
games_post = Post(idea_id=games.id, post_type="story-bts", status="published", post_url="https://www.linkedin.com/in/floris-ten-nijenhuis/recent-activity/",
                  live_text="Any board game fans out here? (EXAMPLE of a published row)", published_at="2026-10-19T09:00:00+00:00")
games_post.add_version(games_post.live_text, "live")

rows = board.build_rows(ideas, [caps_post, games_post])
OUT.mkdir(exist_ok=True)
with open(OUT / "board-sample.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=board.CSV_FIELDS)
    w.writeheader()
    w.writerows(board.to_csv_rows(rows))
(OUT / "board-sample.md").write_text(board.to_markdown(rows, WEEK))

counts = {c: sum(1 for r in rows if r.column == c) for c in board.COLUMNS}
task = TeamTask(post_id=caps_post.id, person_key="b2b_lead", action="comment", due_at="",
                text="Wider eligibility is welcome. The next bottleneck for providers is moving people up the ladder, not just onto it.")
comments = [CommentCandidate(url="https://www.linkedin.com/posts/example-1", text="", author="EXAMPLE: Head of home ownership, large HA",
                             score=5, why="Tier A provider voice on the income caps", suggested_comment="Agree the caps were overdue. What we see next is a staircasing bottleneck: entry is easier, moving up still takes months."),
            CommentCandidate(url="https://www.linkedin.com/posts/example-2", text="", author="EXAMPLE: Shared Ownership Council",
                             score=4, why="Code adoption update; Floris can add the resident-experience angle", suggested_comment="Good to see adoption growing. The Code works best when providers can actually show residents their costs and options in one place.")]
payloads = {
    "1_news_alert": blocks.news_alert(caps),
    "2_board_digest_wednesday": blocks.board_digest(board.top_candidates(rows), WEEK, counts),
    "3_picks_confirmed": blocks.picks_confirmed([launch.title, resales.title, data.title, code.title], WEEK),
    "4_owner_review_card": blocks.owner_review(caps_post, caps.raw_text),
    "5_floris_approval_dm": blocks.floris_approval(caps_post),
    "6_team_task_dm": blocks.team_task(task, "https://www.linkedin.com/posts/example", "10:15", "Add a provider-side angle"),
    "7_floris_comment_list": blocks.floris_comment_list(comments),
}
(OUT / "slack").mkdir(exist_ok=True)
lines = ["# Slack mock-ups", "",
         "Exact Block Kit payloads the bot sends (generated by `scripts/make_mockups.py` from the bot's own code).",
         "Open a link while signed in to Slack to see it rendered in Slack's Block Kit Builder (buttons are inert there).", ""]
for name, b in payloads.items():
    (OUT / "slack" / f"{name}.json").write_text(json.dumps({"blocks": b}, indent=2))
    url = "https://app.slack.com/block-kit-builder/#" + urllib.parse.quote(json.dumps({"blocks": b}, separators=(",", ":")))
    lines.append(f"- [{name.split('_', 1)[1].replace('_', ' ')}]({url}) · `{name}.json`")
(OUT / "slack" / "README.md").write_text("\n".join(lines) + "\n")
print(f"{len(rows)} board rows; {len(payloads)} Slack payloads -> {OUT}")
