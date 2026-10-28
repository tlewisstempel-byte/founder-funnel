"""Slack wiring (Bolt). Thin: it checks who is clicking, then calls `Engine`.

Commands
  /idea <text>                  save an idea to the bank (anyone)
  /draft [type:] <text>         fast lane: draft now (owner). Types: data-post, policy-take, story-bts,
                                product-launch, partner-customer. With no text, drafts the oldest waiting idea.
  /comments                     triage today's #comment-queue into a list for Floris (owner)
  /buffer                       what's in the pipeline (anyone)
  /board                        send the ideas board digest now (owner; normally Wednesday morning)
  /scan                         run the news scan now (owner; normally daily)
  /metrics                      list posts whose 24h/7d numbers are due, with a button to log each (owner)
Channels
  #content-inbox                every message becomes an idea (💡 reaction confirms)
  #comment-queue                paste a LinkedIn link + the post text (👀 confirms)
"""

from __future__ import annotations

import logging
import traceback

from slack_bolt import App

from . import blocks
from .config import POST_TYPES, Settings, Team, load_funnels, load_team
from .flows import Engine
from .llm import LLM, make_llm
from .models import Idea, Post
from .store import Store, make_store

log = logging.getLogger("founder_engine")


def parse_type(text: str) -> tuple[str, str]:
    """'policy-take: caps rose' -> ('policy-take', 'caps rose')"""
    head, _, rest = text.partition(":")
    if head.strip() in POST_TYPES and rest.strip():
        return head.strip(), rest.strip()
    return "", text.strip()


def register(app: App, engine: Engine, team: Team) -> None:
    owner, founder = team.owner.slack_id, team.founder.slack_id

    def guard(user_id: str, allowed: set[str], respond_fn=None) -> bool:
        if user_id in allowed:
            return True
        msg = "Sorry, that button isn't for you."
        if respond_fn:
            respond_fn(msg)
        return False

    def safely(fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:  # tell the owner instead of failing silently
            log.error("Error in %s: %s\n%s", fn.__name__, e, traceback.format_exc())
            try:
                engine.client.chat_postMessage(channel=owner, text=f"⚠️ Something went wrong in `{fn.__name__}`: {e}")
            except Exception:
                pass

    # -------------------------------------------------------- commands
    @app.command("/idea")
    def cmd_idea(ack, command, respond):
        ack()
        text = (command.get("text") or "").strip()
        if not text:
            respond("Usage: `/idea <your idea>`")
            return
        post_type, text = parse_type(text)
        idea = engine.add_idea(text, "inbox", command["user_id"], post_type)
        respond(blocks=[blocks._section(f"💡 Saved to the idea bank (`{idea.id}`)."),
                        blocks._actions(blocks._button("Draft it now", "idea_draft", idea.id))] if command["user_id"] == owner
                else None, text=f"💡 Saved to the idea bank (`{idea.id}`).")

    @app.command("/draft")
    def cmd_draft(ack, command, respond):
        ack()
        if not guard(command["user_id"], {owner}, respond):
            return
        post_type, text = parse_type(command.get("text") or "")
        if text:
            respond("✍️ Drafting… the review card will arrive in your DMs in under a minute.")
            safely(engine.fast_lane, text, command["user_id"], post_type)
            return
        waiting = engine.store.find(Idea, status="new")
        if not waiting:
            respond("No ideas waiting. Use `/draft <text>` or `/idea <text>` first.")
            return
        respond(f"✍️ Drafting the oldest waiting idea (`{waiting[0].id}`)…")
        safely(engine.draft_idea, waiting[0].id)

    @app.command("/comments")
    def cmd_comments(ack, command, respond):
        ack()
        if not guard(command["user_id"], {owner}, respond):
            return
        respond("🔎 Ranking today's #comment-queue… the list will arrive in your DMs.")
        safely(engine.triage_comments)

    @app.command("/buffer")
    def cmd_buffer(ack, respond):
        ack()
        respond(engine.buffer_report())

    @app.command("/board")
    def cmd_board(ack, command, respond):
        ack()
        if not guard(command["user_id"], {owner}, respond):
            return
        respond("📋 Building the ideas board… it will arrive in your DMs.")
        safely(engine.send_board_digest)

    @app.command("/scan")
    def cmd_scan(ack, command, respond):
        ack()
        if not guard(command["user_id"], {owner}, respond):
            return
        respond("🔎 Scanning the news feeds…")
        added = safely(engine.scan_news) or []
        respond(f"Added {len(added)} ideas to the board ({sum(1 for i in added if i.urgent)} urgent).")

    # -------------------------------------------------------- channel listeners
    @app.event("message")
    def on_message(event, client):
        if event.get("subtype") or event.get("bot_id") or event.get("thread_ts"):
            return
        channel, text, user = event.get("channel"), event.get("text") or "", event.get("user", "")
        if channel == team.inbox_channel and text.strip():
            engine.add_idea(text, "inbox", user)
            client.reactions_add(channel=channel, timestamp=event["ts"], name="bulb")
        elif channel == team.comment_queue_channel:
            cand = engine.add_comment_candidate(text, user)
            client.reactions_add(channel=channel, timestamp=event["ts"], name="eyes" if cand else "question")

    # -------------------------------------------------------- owner review buttons
    def value(body) -> str:
        return body["actions"][0]["value"]

    def user(body) -> str:
        return body["user"]["id"]

    @app.action("idea_draft")
    def a_idea_draft(ack, body, respond):
        ack()
        if guard(user(body), {owner}):
            respond(text="✍️ Drafting… the review card will arrive in your DMs.", replace_original=True)
            safely(engine.draft_idea, value(body))

    @app.action("review_send")
    def a_send(ack, body):
        ack()
        if guard(user(body), {owner}):
            safely(engine.send_to_floris, value(body))

    @app.action("review_edit")
    def a_owner_edit(ack, body, client):
        ack()
        if guard(user(body), {owner}):
            client.views_open(trigger_id=body["trigger_id"], view=blocks.edit_modal("owner_edit_modal", engine._post(value(body))))

    @app.action("review_variant")
    def a_variant(ack, body):
        ack()
        if guard(user(body), {owner}):
            safely(engine.switch_variant, value(body))

    @app.action("review_regen")
    def a_regen(ack, body):
        ack()
        if guard(user(body), {owner}):
            safely(engine.regenerate, value(body))

    @app.action("review_reject")
    def a_drop(ack, body):
        ack()
        if guard(user(body), {owner}):
            safely(engine.drop, value(body))

    @app.view("owner_edit_modal")
    def v_owner_edit(ack, body, view):
        ack()
        if guard(user(body), {owner}):
            safely(engine.owner_edit, view["private_metadata"], view["state"]["values"]["text"]["value"]["value"])

    # -------------------------------------------------------- Floris buttons
    @app.action("floris_approve")
    def a_approve(ack, body):
        ack()
        if guard(user(body), {founder}):
            safely(engine.floris_approve, value(body))

    @app.action("floris_edit")
    def a_floris_edit(ack, body, client):
        ack()
        if guard(user(body), {founder}):
            client.views_open(trigger_id=body["trigger_id"], view=blocks.edit_modal("floris_edit_modal", engine._post(value(body))))

    @app.view("floris_edit_modal")
    def v_floris_edit(ack, body, view):
        ack()
        if guard(user(body), {founder}):
            safely(engine.floris_approve, view["private_metadata"], view["state"]["values"]["text"]["value"]["value"])

    @app.action("floris_reject")
    def a_reject(ack, body, client):
        ack()
        if guard(user(body), {founder}):
            client.views_open(trigger_id=body["trigger_id"], view=blocks.reject_modal(engine._post(value(body))))

    @app.view("floris_reject_modal")
    def v_reject(ack, body, view):
        ack()
        if guard(user(body), {founder}):
            reason = view["state"]["values"]["reason"]["value"].get("value") or ""
            safely(engine.floris_reject, view["private_metadata"], reason)

    @app.action("floris_posted")
    def a_posted(ack, body, client):
        ack()
        if guard(user(body), {founder, owner}):
            client.views_open(trigger_id=body["trigger_id"], view=blocks.posted_modal(engine._post(value(body))))

    @app.view("floris_posted_modal")
    def v_posted(ack, body, view):
        vals = view["state"]["values"]
        url = (vals["url"]["value"].get("value") or "").strip()
        if "linkedin.com" not in url:
            ack(response_action="errors", errors={"url": "Please paste the LinkedIn post link."})
            return
        ack()
        if guard(user(body), {founder, owner}):
            safely(engine.mark_posted, view["private_metadata"], url, vals["live_text"]["value"].get("value") or "")

    # -------------------------------------------------------- team tasks
    @app.action("task_done")
    def a_task_done(ack, body):
        ack()
        safely(engine.task_status, value(body), "done")

    @app.action("task_skip")
    def a_task_skip(ack, body):
        ack()
        safely(engine.task_status, value(body), "skipped")

    # -------------------------------------------------------- daily comments
    @app.action("comments_send")
    def a_comments_send(ack, body, respond):
        ack()
        if guard(user(body), {owner}):
            n = safely(engine.send_comment_batch, value(body)) or 0
            respond(text=f"📨 Sent {n} posts to Floris.", replace_original=False)

    @app.action("comment_posted")
    def a_comment_posted(ack, body, respond):
        ack()
        c = safely(engine.comment_status, value(body), "posted")
        if c:
            respond(text=f"✅ Logged: commented on {c.author or c.url}", replace_original=False)

    @app.action("comment_skip")
    def a_comment_skip(ack, body):
        ack()
        safely(engine.comment_status, value(body), "skipped")

    _register_board(app, engine, team)


def _register_board(app: App, engine: Engine, team: Team) -> None:
    owner = team.owner.slack_id

    @app.action("board_tick")
    def a_tick(ack):
        ack()  # ticks are read from the message state when "Confirm picks" is pressed

    @app.action("board_confirm")
    def a_confirm(ack, body, respond):
        ack()
        if body["user"]["id"] != owner:
            return
        ids = []
        for block_id, actions in (body.get("state", {}).get("values", {}) or {}).items():
            for a in actions.values():
                ids += [o["value"] for o in (a.get("selected_options") or [])]
        week = body["actions"][0]["value"]
        picked = engine.pick_ideas(ids, week)
        respond(blocks=blocks.picks_confirmed([i.title or i.raw_text[:60] for i in picked], week),
                text=f"Picked {len(picked)} for {week}", replace_original=False)

    @app.action("board_draft_picked")
    def a_draft_picked(ack, body, respond):
        ack()
        if body["user"]["id"] == owner:
            respond(text="✍️ Drafting the picked ideas… review cards will arrive one by one.", replace_original=False)
            try:
                engine.draft_picked()
            except Exception as e:
                respond(text=f"⚠️ Drafting failed: {e}", replace_original=False)

    @app.command("/metrics")
    def cmd_metrics(ack, command, respond):
        ack()
        if command["user_id"] != owner:
            respond("Sorry, only the B2B lead logs numbers.")
            return
        engine.request_metrics(quiet_if_none=False)

    @app.action("metrics_log")
    def a_metrics_log(ack, body, client):
        ack()
        if body["user"]["id"] != owner:
            return
        post_id, cp = body["actions"][0]["value"].split("|")
        client.views_open(trigger_id=body["trigger_id"], view=blocks.metrics_modal(engine._post(post_id), cp))

    @app.view("metrics_modal")
    def v_metrics(ack, body, view):
        from .metrics import FIELDS, parse_count

        vals = view["state"]["values"]
        parsed, errors = {}, {}
        for f in FIELDS:
            try:
                parsed[f] = parse_count(vals[f]["value"].get("value"))
                if parsed[f] is None and f != "impressions":
                    errors[f] = "Please enter a number (0 is fine)."
            except ValueError:
                errors[f] = "Numbers only, e.g. 42 or 1.2k"
        if errors:
            ack(response_action="errors", errors=errors)
            return
        ack()
        post_id, cp = view["private_metadata"].split("|")
        engine.log_metrics(post_id, cp, parsed, vals["note"]["value"].get("value") or "")

    @app.action("news_draft")
    def a_news_draft(ack, body, respond):
        ack()
        if body["user"]["id"] == owner:
            respond(text="✍️ Drafting now (fast lane)…", replace_original=False)
            engine.draft_idea(body["actions"][0]["value"])

    @app.action("news_keep")
    def a_news_keep(ack, body, respond):
        ack()
        respond(text="Kept on the board for Wednesday.", replace_original=False)

    @app.action("news_drop")
    def a_news_drop(ack, body, respond):
        ack()
        if body["user"]["id"] == owner:
            engine.drop_idea(body["actions"][0]["value"])
            respond(text="Dropped.", replace_original=False)


def build(settings: Settings | None = None, store: Store | None = None, llm: LLM | None = None,
          team: Team | None = None) -> tuple[App, Engine]:
    settings = settings or Settings.from_env()
    team = team or load_team()
    app = App(token=settings.slack_bot_token, signing_secret=settings.slack_signing_secret or None,
              token_verification_enabled=bool(settings.slack_bot_token))
    engine = Engine(store or make_store(settings), llm or make_llm(settings), team, load_funnels(), app.client,
                    tz=settings.timezone)
    register(app, engine, team)
    if settings.notion_token and settings.notion_database_id:
        from .notion_sync import NotionClient

        engine.notion = (NotionClient(settings.notion_token), settings.notion_database_id)
    return app, engine


def create_wsgi():
    """Entry point for Cloud Run: gunicorn 'founder_engine.app:create_wsgi()'"""
    from slack_bolt.adapter.wsgi import SlackRequestHandler

    app, _ = build()
    return SlackRequestHandler(app)
