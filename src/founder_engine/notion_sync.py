"""Mirror the ideas board into a Notion database (one-way: bot -> Notion).

The bot's store stays the source of truth; Notion is the browsable view for the team.
Each row is matched on "Engine ID", so syncing twice updates rather than duplicates.

Setup next week (docs/NOTION.md):
  1. Notion > Settings > Connections > Develop or manage integrations > New integration ("Stairpay Content").
     Copy the secret into NOTION_TOKEN.
  2. Create a page "Founder content", share it with the integration (••• > Connections).
  3. founder-engine notion-setup --parent-page <page id>   -> prints NOTION_DATABASE_ID
  4. founder-engine notion-sync (or let the bot sync after each change)

Uses Notion API version 2022-06-28 (databases). Verify against Notion's current docs before go-live.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Callable

from .board import COLUMNS, BoardRow

API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
POST_TYPES = ["data-post", "policy-take", "story-bts", "product-launch", "partner-customer"]
SOURCES = ["Team inbox", "Floris meeting", "Stairpay data", "Calendar", "News scan", "Fast lane"]
COLUMN_COLOURS = {"New": "gray", "Picked": "blue", "Drafting": "yellow", "With Floris": "orange",
                  "Approved": "purple", "Published": "green", "Dropped": "red"}


def database_schema() -> dict:
    sel = lambda names, colours=None: {"select": {"options": [
        {"name": n, **({"color": colours[n]} if colours else {})} for n in names]}}
    return {
        "Name": {"title": {}},
        "Status": sel(COLUMNS, COLUMN_COLOURS),
        "Score": {"number": {"format": "number"}},
        "Type": sel(POST_TYPES),
        "Source": sel(SOURCES),
        "Why now": {"rich_text": {}},
        "Week": {"rich_text": {}},
        "Urgent": {"checkbox": {}},
        "Idea": {"rich_text": {}},
        "Draft": {"rich_text": {}},
        "Link": {"url": {}},
        "Post URL": {"url": {}},
        "Floris edited": {"checkbox": {}},
        "Reactions": {"number": {"format": "number"}},
        "Comments": {"number": {"format": "number"}},
        "Reposts": {"number": {"format": "number"}},
        "Impressions": {"number": {"format": "number_with_commas"}},
        "Engine ID": {"rich_text": {}},
    }


def _text(s: str, limit: int = 1900) -> dict:
    return {"rich_text": [{"type": "text", "text": {"content": (s or "")[:limit]}}]}


def row_properties(r: BoardRow) -> dict:
    props = {
        "Name": {"title": [{"type": "text", "text": {"content": r.title[:200] or "(untitled)"}}]},
        "Status": {"select": {"name": r.column}},
        "Score": {"number": r.score},
        "Why now": _text(r.why_now),
        "Week": _text(r.week),
        "Urgent": {"checkbox": r.urgent},
        "Idea": _text(r.idea_text),
        "Draft": _text(r.draft_excerpt),
        "Link": {"url": r.source_url or None},
        "Post URL": {"url": r.post_url or None},
        "Floris edited": {"checkbox": r.floris_edited},
        "Engine ID": _text(r.engine_id),
        "Reactions": {"number": r.reactions},
        "Comments": {"number": r.comments},
        "Reposts": {"number": r.reposts},
        "Impressions": {"number": r.impressions},
    }
    if r.post_type in POST_TYPES:
        props["Type"] = {"select": {"name": r.post_type}}
    if r.source in SOURCES:
        props["Source"] = {"select": {"name": r.source}}
    return props


class NotionClient:
    def __init__(self, token: str, transport: Callable[[str, str, dict | None], dict] | None = None):
        self.token = token
        self._transport = transport or self._http

    def _http(self, method: str, path: str, body: dict | None) -> dict:
        req = urllib.request.Request(
            API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
            headers={"Authorization": f"Bearer {self.token}", "Notion-Version": NOTION_VERSION,
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())

    def call(self, method: str, path: str, body: dict | None = None) -> dict:
        return self._transport(method, path, body)

    def create_database(self, parent_page_id: str, title: str = "Founder content board") -> str:
        res = self.call("POST", "/databases", {
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": title}}],
            "properties": database_schema(),
        })
        return res["id"]

    def find_page(self, database_id: str, engine_id: str) -> str | None:
        res = self.call("POST", f"/databases/{database_id}/query", {
            "filter": {"property": "Engine ID", "rich_text": {"equals": engine_id}}, "page_size": 1})
        hits = res.get("results", [])
        return hits[0]["id"] if hits else None

    def upsert(self, database_id: str, row: BoardRow) -> str:
        props = row_properties(row)
        page_id = self.find_page(database_id, row.engine_id)
        if page_id:
            self.call("PATCH", f"/pages/{page_id}", {"properties": props})
            return page_id
        return self.call("POST", "/pages", {"parent": {"database_id": database_id}, "properties": props})["id"]

    def sync(self, database_id: str, rows: list[BoardRow]) -> int:
        for r in rows:
            self.upsert(database_id, r)
        return len(rows)


class DryRunTransport:
    """Records every request instead of sending it. Used in tests and to preview payloads."""

    def __init__(self):
        self.requests: list[dict] = []
        self._n = 0

    def __call__(self, method: str, path: str, body: dict | None) -> dict:
        self.requests.append({"method": method, "path": path, "body": body})
        self._n += 1
        if path.endswith("/query"):
            return {"results": []}
        return {"id": f"dry-{self._n}"}

    def dump(self, path: Path) -> None:
        Path(path).write_text(json.dumps(self.requests, indent=2))
