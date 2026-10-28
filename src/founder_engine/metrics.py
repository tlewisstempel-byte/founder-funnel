"""Simple post metrics: logged by hand in Slack at 24h and 7d after posting.

LinkedIn gives no API for a personal profile's post stats, and we don't scrape. Reactions,
comments and reposts are public on the post, so the B2B lead logs them in ~30 seconds.
Impressions are only visible to Floris: optional per post, or filled from his monthly
analytics export later.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

CHECKPOINTS = {"24h": timedelta(hours=24), "7d": timedelta(days=7)}
FIELDS = ["reactions", "comments", "reposts", "impressions"]  # impressions optional
LABELS = {"reactions": "Reactions", "comments": "Comments", "reposts": "Reposts",
          "impressions": "Impressions (optional: only Floris can see these)"}


def parse_count(text: str | None) -> int | None:
    """'1,234' -> 1234 · '' -> None · '1.2k' -> 1200. Raises ValueError on anything else."""
    t = (text or "").strip().lower().replace(",", "").replace(" ", "")
    if not t:
        return None
    mult = 1000 if t.endswith("k") else 1
    t = t.rstrip("k")
    n = float(t)
    if n < 0:
        raise ValueError("negative")
    return int(round(n * mult))


def due(posts: list, now: datetime | None = None) -> list[tuple]:
    """Published posts whose checkpoint has passed but has no numbers yet -> [(post, checkpoint)]."""
    now = now or datetime.now(timezone.utc)
    out = []
    for p in posts:
        if p.status != "published" or not p.published_at:
            continue
        published = datetime.fromisoformat(p.published_at)
        for cp, delta in CHECKPOINTS.items():
            if cp not in (p.metrics or {}) and now >= published + delta:
                out.append((p, cp))
    return out


def best_numbers(post) -> dict:
    m = post.metrics or {}
    return m.get("7d") or m.get("24h") or {}


def engagement(nums: dict) -> int:
    """Simple ranking score: comments and reposts count more than reactions (they drive reach)."""
    return (nums.get("reactions") or 0) + 3 * (nums.get("comments") or 0) + 3 * (nums.get("reposts") or 0)


def last_week(posts: list, now: datetime | None = None, days: int = 7) -> list:
    now = now or datetime.now(timezone.utc)
    recent = [p for p in posts if p.status == "published" and p.published_at
              and now - datetime.fromisoformat(p.published_at) <= timedelta(days=days + 1)]
    return sorted(recent, key=lambda p: -engagement(best_numbers(p)))


def fmt(nums: dict) -> str:
    if not nums:
        return "no numbers logged yet"
    parts = [f"{nums.get('reactions') or 0} reactions", f"{nums.get('comments') or 0} comments",
             f"{nums.get('reposts') or 0} reposts"]
    if nums.get("impressions"):
        parts.append(f"{nums['impressions']:,} impressions")
    return " · ".join(parts)
