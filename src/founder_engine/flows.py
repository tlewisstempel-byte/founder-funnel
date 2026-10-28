"""The pipeline's steps, independent of Slack's plumbing.

Each method does one step of the flow in ARCHITECTURE.md:
idea -> draft -> owner review -> Floris approval -> posted -> team tasks,
plus the daily comment list. `client` is anything with Slack WebClient's
method names (the real client in production, a fake one in tests).
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from . import blocks, board, metrics, scanner, writer
from .config import POST_TYPES, REPO_ROOT, FunnelStep, Team
from .diffing import change_ratio, word_diff
from .llm import LLM
from .models import CommentCandidate, Idea, Post, SeenItem, TeamTask, now
from .store import Store

URL_RE = re.compile(r"<?(https?://[^\s|>]+)(?:\|[^>]*)?>?")


class Engine:
    def __init__(self, store: Store, llm: LLM, team: Team, funnels: dict[str, list[FunnelStep]],
                 client, root: Path = REPO_ROOT, tz: str = "Europe/London"):
        self.store, self.llm, self.team, self.funnels = store, llm, team, funnels
        self.client, self.root, self.tz = client, root, ZoneInfo(tz)
        self.notion = None  # (NotionClient, database_id) once Notion is connected

    # ------------------------------------------------------------ helpers
    def _dm(self, user_id: str, blocks_: list[dict], text: str) -> dict:
        r = self.client.chat_postMessage(channel=user_id, blocks=blocks_, text=text)
        return {"channel": r["channel"], "ts": r["ts"]}

    def _update(self, msg: dict, blocks_: list[dict], text: str) -> None:
        if msg:
            self.client.chat_update(channel=msg["channel"], ts=msg["ts"], blocks=blocks_, text=text)

    def _tell_owner(self, text: str) -> None:
        self.client.chat_postMessage(channel=self.team.owner.slack_id, text=text)

    def _post(self, post_id: str) -> Post:
        post = self.store.get(Post, post_id)
        if not post:
            raise KeyError(f"No post {post_id}")
        return post

    def _idea_text(self, post: Post) -> str:
        idea = self.store.get(Idea, post.idea_id)
        return idea.raw_text if idea else ""

    def _recent_posts(self) -> list[str]:
        done = self.store.find(Post, status="published")
        return [p.live_text or p.approved_text for p in done]

    # ------------------------------------------------------------ ideas
    def add_idea(self, text: str, source: str = "inbox", user: str = "", post_type: str = "") -> Idea:
        idea = Idea(raw_text=text.strip(), source=source, created_by=user,
                    post_type=post_type if post_type in POST_TYPES else "")
        self.store.put(idea)
        return idea

    # ------------------------------------------------------------ drafting
    def draft_idea(self, idea_id: str) -> Post:
        idea = self.store.get(Idea, idea_id)
        if not idea:
            raise KeyError(f"No idea {idea_id}")
        if not idea.post_type:
            idea.post_type = writer.classify_idea(self.llm, idea.raw_text, POST_TYPES)
        out = writer.draft_post(self.llm, idea.raw_text, idea.post_type, self._recent_posts(), self.root)
        post = Post(idea_id=idea.id, post_type=idea.post_type, variants=out["variants"], hooks=out["hooks"],
                    claims=out["claims"], visual_brief=out["visual_brief"], model=self.llm.model, status="in_review")
        post.add_version(out["variants"][0]["text"], "llm", note=out["variants"][0].get("angle", ""))
        post.review_msg = self._dm(self.team.owner.slack_id, blocks.owner_review(post, idea.raw_text), "New draft for review")
        idea.status = "drafted"
        self.store.put(idea)
        self.store.put(post)
        return post

    def fast_lane(self, text: str, user: str = "", post_type: str = "") -> Post:
        return self.draft_idea(self.add_idea(text, "fast_lane", user, post_type).id)

    # ------------------------------------------------------------ owner review
    def owner_edit(self, post_id: str, text: str) -> Post:
        post = self._post(post_id)
        post.add_version(text, "owner")
        self.store.put(post)
        self._update(post.review_msg, blocks.owner_review(post, self._idea_text(post)), "Draft updated")
        return post

    def switch_variant(self, post_id: str) -> Post:
        post = self._post(post_id)
        if len(post.variants) > 1:
            post.variant_index = (post.variant_index + 1) % len(post.variants)
            v = post.variants[post.variant_index]
            post.add_version(v["text"], "llm", note=v.get("angle", ""))
            self.store.put(post)
            self._update(post.review_msg, blocks.owner_review(post, self._idea_text(post)), "Switched variant")
        return post

    def regenerate(self, post_id: str) -> Post:
        post = self._post(post_id)
        post.status = "rejected"
        post.rejection_reason = "owner asked for a redraft"
        self.store.put(post)
        self._update(post.review_msg, blocks.status_card("*Redrafting…* a new card is on its way.", post.current_text), "Redrafting")
        return self.draft_idea(post.idea_id)

    def drop(self, post_id: str) -> Post:
        post = self._post(post_id)
        post.status, post.rejection_reason = "rejected", "dropped by owner"
        self.store.put(post)
        self._update(post.review_msg, blocks.status_card("*Dropped* 🗑", post.current_text), "Dropped")
        return post

    def send_to_floris(self, post_id: str) -> Post:
        post = self._post(post_id)
        post.status, post.sent_to_floris_at = "sent_to_floris", now()
        post.floris_msg = self._dm(self.team.founder.slack_id, blocks.floris_approval(post), "Draft ready for your approval")
        self.store.put(post)
        self._update(post.review_msg, blocks.status_card("*Sent to Floris* ⏳ waiting for approval", post.current_text), "Sent to Floris")
        return post

    # ------------------------------------------------------------ Floris
    def floris_approve(self, post_id: str, edited_text: str | None = None) -> Post:
        post = self._post(post_id)
        sent = post.current_text
        if edited_text is not None and edited_text.strip() != sent.strip():
            post.add_version(edited_text, "floris")
            post.floris_edited = True
        post.status, post.approved_at, post.approved_text = "approved", now(), post.current_text
        self.store.put(post)
        self._update(post.floris_msg, blocks.floris_approved(post), "Approved")
        note = "approved as sent"
        if post.floris_edited:
            note = f"approved with edits (changed {int(change_ratio(sent, post.approved_text) * 100)}%):\n{word_diff(sent, post.approved_text)[:2500]}"
        self._update(post.review_msg, blocks.status_card("*Floris approved* ✅", post.approved_text, note), "Floris approved")
        return post

    def floris_reject(self, post_id: str, reason: str = "") -> Post:
        post = self._post(post_id)
        post.status, post.rejection_reason = "rejected", reason or "no reason given"
        self.store.put(post)
        self._update(post.floris_msg, blocks.status_card("*Rejected* — thanks, noted.", post.current_text), "Rejected")
        self._update(post.review_msg, blocks.status_card("*Floris rejected this draft*", post.current_text, f"Reason: {post.rejection_reason}"), "Floris rejected")
        return post

    def mark_posted(self, post_id: str, url: str, live_text: str = "") -> Post:
        post = self._post(post_id)
        post.status, post.published_at, post.post_url = "published", now(), url.strip()
        post.live_text = live_text.strip() or post.approved_text
        if live_text.strip() and live_text.strip() != post.approved_text.strip():
            post.add_version(post.live_text, "live", note="changed on LinkedIn before posting")
            post.floris_edited = True
        self.store.put(post)
        self._update(post.floris_msg, blocks.status_card(f"*Live* 🚀 <{post.post_url}|view post>", post.live_text,
                                                         "The team has been asked to engage in the next hour."), "Posted")
        tasks = self._create_team_tasks(post)
        who = ", ".join(t.person_key for t in tasks) or "nobody (no funnel for this post type)"
        self._tell_owner(f"🚀 Floris posted: {post.post_url}\nTeam tasks sent to: {who}")
        return post

    # ------------------------------------------------------------ team funnel
    def _create_team_tasks(self, post: Post) -> list[TeamTask]:
        steps = [s for s in self.funnels.get(post.post_type, []) if s.action != "none"]
        people = [(s, self.team.person(s.who)) for s in steps]
        people = [(s, p) for s, p in people if p and p.slack_id]
        if not people:
            return []
        texts = writer.team_comments(
            self.llm, post.live_text,
            [{"person_key": p.key, "name": p.name, "role": p.role, "action": s.action} for s, p in people], self.root)
        published = datetime.fromisoformat(post.published_at)
        tasks = []
        for step, person in people:
            due = published + timedelta(minutes=step.window_minutes)
            task = TeamTask(post_id=post.id, person_key=person.key, action=step.action,
                            text=texts.get(person.key, ""), due_at=due.isoformat(timespec="seconds"))
            due_label = due.astimezone(self.tz).strftime("%H:%M")
            task.msg = self._dm(person.slack_id, blocks.team_task(task, post.post_url, due_label, step.note),
                                f"Please engage with Floris's new post by {due_label}")
            self.store.put(task)
            tasks.append(task)
        return tasks

    def task_status(self, task_id: str, status: str) -> TeamTask:
        task = self.store.get(TeamTask, task_id)
        if not task:
            raise KeyError(f"No task {task_id}")
        task.status = status
        self.store.put(task)
        label = "Done ✅ thank you" if status == "done" else "Skipped"
        self._update(task.msg, blocks.status_card(f"*{label}*", task.text), label)
        return task

    # ------------------------------------------------------------ daily comments
    def add_comment_candidate(self, message_text: str, user: str = "") -> CommentCandidate | None:
        m = URL_RE.search(message_text or "")
        if not m:
            return None
        url = m.group(1)
        text = URL_RE.sub("", message_text, count=1).strip()
        author = ""
        first = text.splitlines()[0] if text else ""
        if first.lower().startswith(("by ", "author:")):
            author = first.split(" ", 1)[1].strip() if " " in first else ""
            text = "\n".join(text.splitlines()[1:]).strip()
        cand = CommentCandidate(url=url, text=text, author=author, added_by=user)
        self.store.put(cand)
        return cand

    def triage_comments(self, top_n: int = 5) -> str | None:
        queued = self.store.find(CommentCandidate, status="queued")
        if not queued:
            self._tell_owner("Nothing in #comment-queue yet. Paste a post link plus its text there first.")
            return None
        out = writer.triage_comments(self.llm, [c.to_dict() for c in queued], self.root, top_n)
        by_id = {c.id: c for c in queued}
        batch_id = "batch_" + uuid.uuid4().hex[:8]
        picked, skipped = [], []
        for r in out["ranked"]:
            c = by_id.get(r.get("id"))
            if not c:
                continue
            c.score, c.why = float(r.get("score", 0) or 0), r.get("why", "")
            c.suggested_comment, c.batch_id = (r.get("comment") or "").strip(), batch_id
            if c.suggested_comment and len(picked) < top_n:
                c.status = "ranked"
                picked.append(c)
            else:
                c.status = "skipped"
                skipped.append(c)
            self.store.put(c)
        self._dm(self.team.owner.slack_id, blocks.owner_comment_preview(picked, batch_id, skipped), "Comment list ready to review")
        return batch_id

    def send_comment_batch(self, batch_id: str) -> int:
        items = [c for c in self.store.find(CommentCandidate, batch_id=batch_id) if c.status == "ranked"]
        items.sort(key=lambda c: -c.score)
        if not items:
            return 0
        self._dm(self.team.founder.slack_id, blocks.floris_comment_list(items), f"{len(items)} posts worth a comment today")
        for c in items:
            c.status = "sent"
            self.store.put(c)
        return len(items)

    def comment_status(self, cand_id: str, status: str) -> CommentCandidate:
        c = self.store.get(CommentCandidate, cand_id)
        if not c:
            raise KeyError(f"No comment candidate {cand_id}")
        c.status = status
        self.store.put(c)
        return c

    # ------------------------------------------------------------ reporting and learning
    def buffer_report(self) -> str:
        posts = self.store.all_raw(Post.collection)
        ideas = self.store.all_raw(Idea.collection)
        count = lambda rows, s: sum(1 for r in rows if r.get("status") == s)
        lines = [
            "*Content buffer*",
            f"• Ideas waiting: {count(ideas, 'new')}",
            f"• Drafts in your review: {count(posts, 'in_review')}",
            f"• With Floris: {count(posts, 'sent_to_floris')}",
            f"• Approved, not yet posted: {count(posts, 'approved')}",
            f"• Published: {count(posts, 'published')}",
        ]
        edited = [r for r in posts if r.get("status") in ("approved", "published")]
        if edited:
            clean = sum(1 for r in edited if not r.get("floris_edited"))
            lines.append(f"• Approved without Floris edits: {clean}/{len(edited)} (the lift metric)")
        return "\n".join(lines)

    def edit_pairs(self, month: str) -> list[dict]:
        """month 'YYYY-MM' -> [{before, after}] for drafts Floris changed that month."""
        pairs = []
        for p in self.store.find(Post):
            if not p.floris_edited or not (p.approved_at or "").startswith(month):
                continue
            before = next((v["text"] for v in reversed(p.versions) if v["author"] in ("llm", "owner")), "")
            after = p.live_text or p.approved_text
            if before and after and before.strip() != after.strip():
                pairs.append({"before": before, "after": after})
        return pairs

    def write_edit_summary(self, month: str) -> Path | None:
        pairs = self.edit_pairs(month)
        if not pairs:
            return None
        path = self.root / "voice" / "edits" / f"{month}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(writer.summarise_edits(self.llm, pairs, month))
        return path

    # ------------------------------------------------------------ news scan (daily)
    def scan_news(self, sources: dict | None = None, getter=None) -> list[Idea]:
        """Fetch feeds, keep unseen relevant items, add them to the board; alert the owner only for urgent ones."""
        sources = sources or scanner.load_sources()
        items = scanner.fetch_all(sources, getter or scanner.http_get)
        fresh = [it for it in items if not self.store.get(SeenItem, it.url)][:40]
        if not fresh:
            return []
        listing = [{"i": i, "title": it.title, "url": it.url, "summary": it.summary, "source": it.source,
                    "published": it.published} for i, it in enumerate(fresh)]
        verdicts = {v.get("i"): v for v in writer.triage_news(self.llm, listing, self._recent_posts(), self.root)}
        added = []
        for i, it in enumerate(fresh):
            v = verdicts.get(i, {})
            relevant = bool(v.get("relevant"))
            self.store.put(SeenItem(id=it.url, title=it.title, relevant=relevant))
            if not relevant:
                continue
            idea = Idea(raw_text=f"{it.title}\n{it.summary}\nSource: {it.source}, {it.published}", source="trend",
                        post_type=v.get("post_type") if v.get("post_type") in POST_TYPES else "",
                        title=v.get("title") or it.title[:80], source_url=it.url, why_now=v.get("why_now", ""),
                        score=float(v.get("score", 0) or 0), score_notes=v.get("notes", ""), urgent=bool(v.get("urgent")))
            self.store.put(idea)
            added.append(idea)
            if idea.urgent:
                self._dm(self.team.owner.slack_id, blocks.news_alert(idea), f"Timely: {idea.title}")
        self.sync_notion()
        return added

    # ------------------------------------------------------------ weekly board (Wednesday)
    def board_rows(self) -> list:
        return board.build_rows(self.store.find(Idea), self.store.find(Post))

    def score_new_ideas(self) -> int:
        """Score ideas that arrived without a score (inbox, meeting, data); news items are scored at scan time."""
        todo = [i for i in self.store.find(Idea, status="new") if not i.score_notes]
        if not todo:
            return 0
        results = {r.get("id"): r for r in writer.score_ideas(
            self.llm, [{"id": i.id, "text": i.raw_text, "source": i.source, "post_type": i.post_type} for i in todo],
            self._recent_posts())}
        for idea in todo:
            r = results.get(idea.id)
            if not r:
                continue
            idea.score, idea.score_notes = float(r.get("score", 0) or 0), r.get("notes", "") or "scored"
            idea.title = idea.title or r.get("title", "")
            idea.why_now = idea.why_now or r.get("why_now", "")
            if not idea.post_type and r.get("post_type") in POST_TYPES:
                idea.post_type = r["post_type"]
            self.store.put(idea)
        return len(todo)

    def send_board_digest(self, n: int = 10) -> int:
        """Wednesday morning: top ideas from every source, ranked, with checkboxes to pick next week's posts."""
        self.score_new_ideas()
        rows = self.board_rows()
        top = board.top_candidates(rows, n)
        counts = {c: sum(1 for r in rows if r.column == c) for c in board.COLUMNS}
        results = blocks.last_week_results(metrics.last_week(self.store.find(Post)))
        self._dm(self.team.owner.slack_id, blocks.board_digest(top, board.next_cycle_week(), counts, results),
                 f"Ideas board: {len(top)} candidates for the Wednesday review")
        self.sync_notion()
        return len(top)

    def pick_ideas(self, idea_ids: list[str], week: str | None = None) -> list[Idea]:
        week = week or board.next_cycle_week()
        picked = []
        for iid in idea_ids:
            idea = self.store.get(Idea, iid)
            if idea and idea.status == "new":
                idea.status, idea.week = "picked", week
                self.store.put(idea)
                picked.append(idea)
        self.sync_notion()
        return picked

    def draft_picked(self) -> list[Post]:
        return [self.draft_idea(i.id) for i in self.store.find(Idea, status="picked")]

    def drop_idea(self, idea_id: str) -> None:
        idea = self.store.get(Idea, idea_id)
        if idea:
            idea.status = "dropped"
            self.store.put(idea)
            self.sync_notion()

    # ------------------------------------------------------------ metrics (24h and 7d, logged by hand)
    def request_metrics(self, quiet_if_none: bool = True) -> int:
        items = metrics.due(self.store.find(Post))
        if items:
            self._dm(self.team.owner.slack_id, blocks.metrics_request(items), f"{len(items)} post(s) need numbers")
        elif not quiet_if_none:
            self._tell_owner("All caught up: no post numbers due.")
        return len(items)

    def log_metrics(self, post_id: str, checkpoint: str, values: dict, note: str = "") -> Post:
        if checkpoint not in metrics.CHECKPOINTS:
            raise ValueError(f"Unknown checkpoint {checkpoint}")
        post = self._post(post_id)
        post.metrics = dict(post.metrics or {})
        post.metrics[checkpoint] = {**{k: values.get(k) for k in metrics.FIELDS}, "note": note, "logged_at": now()}
        self.store.put(post)
        self.sync_notion()
        return post

    def sync_notion(self) -> int:
        if not self.notion:
            return 0
        client, database_id = self.notion
        try:
            return client.sync(database_id, self.board_rows())
        except Exception as e:  # Notion is a view: never block the pipeline on it
            self._tell_owner(f"⚠️ Notion sync failed: {e}")
            return 0


def default_month() -> str:
    first = datetime.now(timezone.utc).replace(day=1)
    return (first - timedelta(days=1)).strftime("%Y-%m")
