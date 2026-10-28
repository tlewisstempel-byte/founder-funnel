"""Slack Block Kit layouts: every card and form the bot shows. No logic here."""

from __future__ import annotations

MAX_TEXT = 2900  # Slack section text limit is 3000 characters


def _clip(text: str, limit: int = MAX_TEXT) -> str:
    return text if len(text) <= limit else text[: limit - 20] + "\n…(truncated)"


def _section(text: str) -> dict:
    return {"type": "section", "text": {"type": "mrkdwn", "text": _clip(text) or " "}}


def _context(text: str) -> dict:
    return {"type": "context", "elements": [{"type": "mrkdwn", "text": _clip(text, 1900)}]}


def _quote(text: str) -> str:
    return "\n".join("> " + line if line.strip() else ">" for line in text.splitlines())


def _button(text: str, action_id: str, value: str, style: str | None = None) -> dict:
    b = {"type": "button", "text": {"type": "plain_text", "text": text, "emoji": True}, "action_id": action_id, "value": value}
    if style:
        b["style"] = style
    return b


def _actions(*buttons: dict) -> dict:
    return {"type": "actions", "elements": list(buttons)}


DIVIDER = {"type": "divider"}


# ---------------------------------------------------------------- owner review
def owner_review(post, idea_text: str) -> list[dict]:
    variant = post.variants[post.variant_index] if post.variants else {"angle": "edited"}
    blocks = [
        _section(f"*New draft for review* · `{post.post_type}` · variant {post.variant_index + 1}/{max(len(post.variants), 1)}: _{variant.get('angle', '')}_"),
        _context(f"Idea: {idea_text[:300]}"),
        DIVIDER,
        _section(_quote(post.current_text)),
        DIVIDER,
    ]
    if post.hooks:
        blocks.append(_section("*Alternative hooks*\n" + "\n".join(f"• {h}" for h in post.hooks)))
    if post.claims:
        lines = [f"• {c.get('claim','')} — _{c.get('source','UNVERIFIED')}_" for c in post.claims]
        blocks.append(_section("*Check these claims before sending*\n" + "\n".join(lines)))
    if post.visual_brief and post.visual_brief.lower() != "none":
        blocks.append(_context(f"Visual: {post.visual_brief}"))
    buttons = [
        _button("Send to Floris", "review_send", post.id, "primary"),
        _button("Edit", "review_edit", post.id),
    ]
    if len(post.variants) > 1:
        buttons.append(_button("Other variant", "review_variant", post.id))
    buttons += [_button("Redraft", "review_regen", post.id), _button("Drop", "review_reject", post.id, "danger")]
    blocks.append(_actions(*buttons))
    return blocks


def status_card(title: str, text: str, note: str = "") -> list[dict]:
    blocks = [_section(title), _section(_quote(text))]
    if note:
        blocks.append(_context(note))
    return blocks


# ---------------------------------------------------------------- Floris
def floris_approval(post) -> list[dict]:
    return [
        _section(f"*Draft ready for your approval* · `{post.post_type}`\nPlease approve, edit or reject within 24h."),
        DIVIDER,
        _section(_quote(post.current_text)),
        DIVIDER,
        _actions(
            _button("Approve", "floris_approve", post.id, "primary"),
            _button("Edit", "floris_edit", post.id),
            _button("Reject", "floris_reject", post.id, "danger"),
        ),
    ]


def floris_approved(post) -> list[dict]:
    return [
        _section("*Approved* ✅  Post it on LinkedIn when ready (put any link in the first comment), then press the button and paste the post link."),
        _section(_quote(post.approved_text)),
        _actions(_button("I've posted it", "floris_posted", post.id, "primary")),
    ]


def floris_comment_list(items: list) -> list[dict]:
    blocks = [_section(f"*{len(items)} posts worth a comment today*\nCopy, tweak, post. Tap ✅ when done so we can track it."), DIVIDER]
    for i, c in enumerate(items, 1):
        blocks.append(_section(f"*{i}. {c.author or 'Post'}* · <{c.url}|open post>\n_{c.why}_\n\n{_quote(c.suggested_comment)}"))
        blocks.append(_actions(_button("✅ Commented", "comment_posted", c.id, "primary"), _button("Skip", "comment_skip", c.id)))
    return blocks


def owner_comment_preview(items: list, batch_id: str, skipped: list) -> list[dict]:
    blocks = [_section(f"*Today's comment list for Floris* ({len(items)} picked, {len(skipped)} skipped)"), DIVIDER]
    for i, c in enumerate(items, 1):
        blocks.append(_section(f"*{i}. {c.author or 'Post'}* (score {c.score}) · <{c.url}|open>\n_{c.why}_\n{_quote(c.suggested_comment)}"))
    if skipped:
        blocks.append(_context("Skipped: " + "; ".join(f"{c.author or c.url}: {c.why}" for c in skipped)[:1800]))
    blocks.append(_actions(_button("Send to Floris", "comments_send", batch_id, "primary")))
    return blocks


# ---------------------------------------------------------------- team
ACTION_LABEL = {"comment": "Comment on", "repost_with_comment": "Repost (with your own comment)"}


def team_task(task, post_url: str, due_label: str, note: str = "") -> list[dict]:
    action = ACTION_LABEL.get(task.action, task.action)
    return [
        _section(f"*{action} Floris's new post* by {due_label}\n<{post_url}|Open the post>" + (f"\n_{note}_" if note else "")),
        _section("*Suggested text* (edit so it sounds like you):\n" + _quote(task.text)),
        _context("LinkedIn doesn't let tools post for you, so copy, tweak, post. ~30 seconds."),
        _actions(_button("Done", "task_done", task.id, "primary"), _button("Skip", "task_skip", task.id)),
    ]


# ---------------------------------------------------------------- modals
def _text_input(block_id: str, label: str, initial: str = "", multiline: bool = True, optional: bool = False, placeholder: str = "") -> dict:
    el = {"type": "plain_text_input", "action_id": "value", "multiline": multiline, "max_length": 3000}
    if initial:
        el["initial_value"] = initial[:3000]
    if placeholder:
        el["placeholder"] = {"type": "plain_text", "text": placeholder}
    return {"type": "input", "block_id": block_id, "label": {"type": "plain_text", "text": label}, "element": el, "optional": optional}


def _modal(callback_id: str, title: str, submit: str, blocks: list[dict], metadata: str) -> dict:
    return {
        "type": "modal",
        "callback_id": callback_id,
        "title": {"type": "plain_text", "text": title[:24]},
        "submit": {"type": "plain_text", "text": submit},
        "close": {"type": "plain_text", "text": "Cancel"},
        "private_metadata": metadata,
        "blocks": blocks,
    }


def edit_modal(callback_id: str, post) -> dict:
    return _modal(callback_id, "Edit draft", "Save", [_text_input("text", "Post text", post.current_text)], post.id)


def reject_modal(post) -> dict:
    return _modal("floris_reject_modal", "Reject draft", "Reject",
                  [_text_input("reason", "Why? (helps the next draft)", multiline=True, optional=True)], post.id)


def posted_modal(post) -> dict:
    return _modal("floris_posted_modal", "Posted", "Done", [
        _text_input("url", "Link to the LinkedIn post", multiline=False, placeholder="https://www.linkedin.com/posts/..."),
        _text_input("live_text", "Did you change the text before posting? Paste the final version here (optional)",
                    multiline=True, optional=True),
    ], post.id)


# ---------------------------------------------------------------- news scan and ideas board
def news_alert(idea) -> list[dict]:
    return [
        _section(f"⚡ *Timely post idea* · score {idea.score:g}/10\n*{idea.title}*\n_{idea.why_now}_"),
        _context(f"<{idea.source_url}|Source> · {idea.post_type or 'type tbc'} · {idea.score_notes}"),
        _actions(_button("Draft now (fast lane)", "news_draft", idea.id, "primary"),
                 _button("Keep for Wednesday", "news_keep", idea.id),
                 _button("Drop", "news_drop", idea.id)),
    ]


def last_week_results(posts: list) -> list[dict]:
    from . import metrics as m

    if not posts:
        return [_section("*Last week's results*\nNothing published last week."), DIVIDER]
    lines = []
    for i, p in enumerate(posts):
        first = (p.live_text or p.approved_text or "").strip().splitlines()[0][:70] if (p.live_text or p.approved_text) else p.id
        tag = " 🏆" if i == 0 and m.best_numbers(p) else ""
        lines.append(f"• <{p.post_url}|{first}> · `{p.post_type}`{tag}\n   {m.fmt(m.best_numbers(p))}")
    missing = sum(1 for p in posts if not p.metrics)
    note = f"\n_{missing} post(s) still need numbers: use `/metrics`._" if missing else ""
    return [_section("*Last week's results* (best first)\n" + "\n".join(lines) + note), DIVIDER]


def board_digest(rows: list, week: str, counts: dict, results: list | None = None) -> list[dict]:
    summary = " · ".join(f"{k}: {v}" for k, v in counts.items() if v)
    blocks_ = [
        _section(f"*Ideas board for the Wednesday review* · posts for {week}\nTick the ones to post next week (aim for 4-5), then confirm."),
        _context(summary or "Board is empty"),
        DIVIDER,
    ] + (results or [])
    if not rows:
        blocks_.append(_section("No new ideas. Drop some in #content-inbox or use `/idea`."))
        return blocks_
    for r in rows:
        link = f" · <{r.source_url}|source>" if r.source_url else ""
        flag = "⚡ " if r.urgent else ""
        text = f"{flag}*{r.title}* · {r.score:g}/10\n_{r.why_now or r.idea_text[:120]}_\n{r.post_type or 'type tbc'} · {r.source}{link}"
        blocks_.append({
            "type": "section", "block_id": f"pick_{r.engine_id}",
            "text": {"type": "mrkdwn", "text": _clip(text, 2900)},
            "accessory": {"type": "checkboxes", "action_id": "board_tick",
                          "options": [{"text": {"type": "mrkdwn", "text": "Pick"}, "value": r.engine_id}]},
        })
    blocks_ += [DIVIDER, _actions(_button("Confirm picks", "board_confirm", week, "primary"))]
    return blocks_


def picks_confirmed(titles: list[str], week: str) -> list[dict]:
    listing = "\n".join(f"• {t}" for t in titles) or "Nothing picked."
    return [_section(f"*Picked for {week}* ✅\n{listing}"),
            _actions(_button("Draft all picked now", "board_draft_picked", week, "primary"))]


# ---------------------------------------------------------------- metrics
def metrics_request(items: list) -> list[dict]:
    """items: [(post, checkpoint)]"""
    blocks_ = [_section(f"*Numbers to log* ({len(items)})\nOpen each post, then tap the button and type what you see. ~30 seconds each.")]
    for post, cp in items:
        first = (post.live_text or post.approved_text or "").strip().splitlines()[0][:80] if (post.live_text or post.approved_text) else post.id
        blocks_.append(_section(f"*{cp}* · <{post.post_url}|{first}>"))
        blocks_.append(_actions(_button(f"Log {cp} numbers", "metrics_log", f"{post.id}|{cp}", "primary")))
    return blocks_


def metrics_modal(post, checkpoint: str) -> dict:
    from .metrics import FIELDS, LABELS

    existing = (post.metrics or {}).get(checkpoint, {})
    inputs = [_text_input(f, LABELS[f], str(existing.get(f, "") or ""), multiline=False,
                          optional=(f == "impressions"), placeholder="e.g. 42") for f in FIELDS]
    inputs.append(_text_input("note", "Anything notable? (optional: who commented, DMs, leads)", multiline=True, optional=True))
    return _modal("metrics_modal", f"Post numbers {checkpoint}", "Save", inputs, f"{post.id}|{checkpoint}")
