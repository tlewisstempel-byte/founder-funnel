"""Records the bot keeps. One record per idea, post, team task and comment candidate.

These map to the data model in ARCHITECTURE.md section 5. Every record is a
plain dict in storage, so the backend (SQLite, Firestore, Postgres) is swappable.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field, fields
from datetime import datetime, timezone


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class Record:
    collection = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict):
        names = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in names})


@dataclass
class Idea(Record):
    collection = "ideas"
    raw_text: str
    source: str = "inbox"  # inbox | meeting | sql | calendar | trend | fast_lane
    post_type: str = ""
    created_by: str = ""
    status: str = "new"  # new | drafted | dropped
    score: float = 0.0
    id: str = field(default_factory=lambda: new_id("idea"))
    created_at: str = field(default_factory=now)


@dataclass
class DraftVersion:
    text: str
    author: str  # llm | owner | floris | live
    created_at: str = field(default_factory=now)
    note: str = ""


@dataclass
class Post(Record):
    collection = "posts"
    idea_id: str
    post_type: str
    status: str = "drafting"
    # drafting | in_review | sent_to_floris | approved | published | rejected
    variants: list[dict] = field(default_factory=list)  # [{angle, text}] from the model
    variant_index: int = 0
    versions: list[dict] = field(default_factory=list)  # DraftVersion dicts, full history
    hooks: list[str] = field(default_factory=list)
    visual_brief: str = ""
    claims: list[dict] = field(default_factory=list)  # [{claim, source}]
    approved_text: str = ""
    live_text: str = ""
    floris_edited: bool = False
    rejection_reason: str = ""
    post_url: str = ""
    company_page: bool = False
    model: str = ""
    review_msg: dict = field(default_factory=dict)  # {channel, ts} of the owner's card
    floris_msg: dict = field(default_factory=dict)  # {channel, ts} of Floris's card
    sent_to_floris_at: str = ""
    approved_at: str = ""
    published_at: str = ""
    id: str = field(default_factory=lambda: new_id("post"))
    created_at: str = field(default_factory=now)

    @property
    def current_text(self) -> str:
        return self.versions[-1]["text"] if self.versions else ""

    def add_version(self, text: str, author: str, note: str = "") -> None:
        self.versions.append(asdict(DraftVersion(text=text, author=author, note=note)))


@dataclass
class TeamTask(Record):
    collection = "team_tasks"
    post_id: str
    person_key: str
    action: str  # comment | repost_with_comment
    text: str
    due_at: str
    status: str = "open"  # open | done | skipped
    msg: dict = field(default_factory=dict)
    id: str = field(default_factory=lambda: new_id("task"))
    created_at: str = field(default_factory=now)


@dataclass
class CommentCandidate(Record):
    collection = "comment_candidates"
    url: str
    text: str
    author: str = ""
    added_by: str = ""
    status: str = "queued"  # queued | ranked | sent | posted | skipped
    score: float = 0.0
    why: str = ""
    suggested_comment: str = ""
    batch_id: str = ""
    id: str = field(default_factory=lambda: new_id("cmt"))
    created_at: str = field(default_factory=now)
