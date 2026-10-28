"""The ideas board: one view over every idea and post, whatever its source.

Columns: New -> Picked -> Drafting -> With Floris -> Approved -> Published (plus Dropped).
The bot's store is the source of truth; Slack, Notion, CSV and Markdown are views of it.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta

from .models import Idea, Post

COLUMNS = ["New", "Picked", "Drafting", "With Floris", "Approved", "Published", "Dropped"]

POST_STATUS_TO_COLUMN = {
    "drafting": "Drafting", "in_review": "Drafting", "sent_to_floris": "With Floris",
    "approved": "Approved", "published": "Published", "rejected": "Dropped",
}

SOURCE_LABEL = {"inbox": "Team inbox", "meeting": "Floris meeting", "sql": "Stairpay data", "calendar": "Calendar",
                "trend": "News scan", "fast_lane": "Fast lane"}


@dataclass
class BoardRow:
    engine_id: str  # idea id: stable key for upserts into Notion etc.
    title: str
    column: str
    post_type: str
    source: str
    score: float
    why_now: str
    score_notes: str
    week: str
    urgent: bool
    idea_text: str
    source_url: str
    draft_excerpt: str = ""
    post_url: str = ""
    floris_edited: bool = False
    updated: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def iso_week(d: date | None = None) -> str:
    d = d or date.today()
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def next_cycle_week(today: date | None = None) -> str:
    """Posts picked at the Wednesday review run in the following week."""
    today = today or date.today()
    return iso_week(today + timedelta(days=7 - today.weekday()))  # Monday of next week


def _title(idea: Idea) -> str:
    if idea.title:
        return idea.title
    words = idea.raw_text.split()
    return " ".join(words[:8]) + ("…" if len(words) > 8 else "")


def build_rows(ideas: list[Idea], posts: list[Post]) -> list[BoardRow]:
    latest_post: dict[str, Post] = {}
    for p in sorted(posts, key=lambda p: p.created_at):
        latest_post[p.idea_id] = p  # a redraft supersedes the earlier post
    rows = []
    for idea in ideas:
        post = latest_post.get(idea.id)
        if post:
            column = POST_STATUS_TO_COLUMN.get(post.status, "Drafting")
        else:
            column = {"new": "New", "picked": "Picked", "dropped": "Dropped"}.get(idea.status, "New")
        text = (post.live_text or post.approved_text or post.current_text) if post else ""
        rows.append(BoardRow(
            engine_id=idea.id, title=_title(idea), column=column, post_type=(post.post_type if post else idea.post_type),
            source=SOURCE_LABEL.get(idea.source, idea.source), score=round(idea.score, 1), why_now=idea.why_now,
            score_notes=idea.score_notes, week=idea.week, urgent=idea.urgent, idea_text=idea.raw_text,
            source_url=idea.source_url, draft_excerpt=text[:280], post_url=post.post_url if post else "",
            floris_edited=bool(post and post.floris_edited),
            updated=(post.published_at or post.approved_at or post.created_at if post else idea.created_at)))
    order = {c: i for i, c in enumerate(COLUMNS)}
    return sorted(rows, key=lambda r: (order[r.column], -r.score))


def top_candidates(rows: list[BoardRow], n: int = 10) -> list[BoardRow]:
    return [r for r in rows if r.column == "New"][:n]


def to_markdown(rows: list[BoardRow], week: str) -> str:
    lines = [f"# Ideas board · review for {week}", "",
             f"_Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}. Source of truth is the bot's log; this is a snapshot._", ""]
    for col in COLUMNS:
        items = [r for r in rows if r.column == col]
        if not items:
            continue
        lines.append(f"## {col} ({len(items)})")
        lines.append("")
        lines.append("| Score | Idea | Type | Source | Why now |")
        lines.append("|---|---|---|---|---|")
        for r in items:
            title = f"[{r.title}]({r.post_url or r.source_url})" if (r.post_url or r.source_url) else r.title
            flag = " ⚡" if r.urgent else ""
            lines.append(f"| {r.score:g} | {title}{flag} | {r.post_type} | {r.source} | {r.why_now} |")
        lines.append("")
    return "\n".join(lines)


CSV_FIELDS = ["Name", "Status", "Score", "Type", "Source", "Why now", "Week", "Urgent", "Idea", "Draft",
              "Link", "Post URL", "Floris edited", "Engine ID"]


def to_csv_rows(rows: list[BoardRow]) -> list[dict]:
    return [{
        "Name": r.title, "Status": r.column, "Score": r.score, "Type": r.post_type, "Source": r.source,
        "Why now": r.why_now, "Week": r.week, "Urgent": "Yes" if r.urgent else "No", "Idea": r.idea_text[:1900],
        "Draft": r.draft_excerpt, "Link": r.source_url, "Post URL": r.post_url,
        "Floris edited": "Yes" if r.floris_edited else "No", "Engine ID": r.engine_id,
    } for r in rows]
