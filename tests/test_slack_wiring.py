"""Checks the Bolt wiring: Slack payloads reach the right Engine step, and only the right people can click."""

import json
from urllib.parse import urlencode

from slack_bolt import App, BoltRequest
from slack_bolt.authorization import AuthorizeResult

from founder_engine import blocks
from founder_engine.app import parse_type, register
from founder_engine.models import Post


def make_app(engine, team):
    def authorize(enterprise_id, team_id, logger):  # no network: pretend Slack confirmed the token
        return AuthorizeResult(enterprise_id=enterprise_id, team_id=team_id, bot_token="xoxb-test",
                               bot_user_id="UBOT", bot_id="B1")

    app = App(signing_secret="test", authorize=authorize, request_verification_enabled=False,
              process_before_response=True)
    register(app, engine, team)
    return app


def action_payload(action_id, value, user):
    payload = {"type": "block_actions", "user": {"id": user}, "team": {"id": "T1"}, "api_app_id": "A1",
               "trigger_id": "trig", "response_url": "https://hooks.slack.invalid/x",
               "container": {"type": "message"}, "channel": {"id": "D1"}, "message": {"ts": "1.0"},
               "actions": [{"action_id": action_id, "value": value, "type": "button", "block_id": "b"}]}
    return BoltRequest(body=urlencode({"payload": json.dumps(payload)}),
                       headers={"content-type": ["application/x-www-form-urlencoded"]})


def view_payload(callback_id, metadata, values, user):
    payload = {"type": "view_submission", "user": {"id": user}, "team": {"id": "T1"}, "api_app_id": "A1",
               "view": {"type": "modal", "callback_id": callback_id, "private_metadata": metadata, "state": {"values": values}}}
    return BoltRequest(body=urlencode({"payload": json.dumps(payload)}),
                       headers={"content-type": ["application/x-www-form-urlencoded"]})


def test_send_button_only_works_for_owner(engine, team):
    app = make_app(engine, team)
    post = engine.fast_lane("idea")
    assert app.dispatch(action_payload("review_send", post.id, "U_TIM")).status == 200
    assert engine.store.get(Post, post.id).status == "in_review"  # Tim can't send
    app.dispatch(action_payload("review_send", post.id, "U_OWNER"))
    assert engine.store.get(Post, post.id).status == "sent_to_floris"


def test_floris_approve_and_edit_modal(engine, team):
    app = make_app(engine, team)
    post = engine.fast_lane("idea")
    engine.send_to_floris(post.id)
    app.dispatch(action_payload("floris_approve", post.id, "U_OWNER"))  # owner can't approve for Floris
    assert engine.store.get(Post, post.id).status == "sent_to_floris"
    values = {"text": {"value": {"type": "plain_text_input", "value": "Floris's own words."}}}
    assert app.dispatch(view_payload("floris_edit_modal", post.id, values, "U_FLORIS")).status == 200
    post = engine.store.get(Post, post.id)
    assert post.status == "approved" and post.approved_text == "Floris's own words."


def test_posted_modal_requires_linkedin_link(engine, team):
    app = make_app(engine, team)
    post = engine.fast_lane("idea")
    engine.send_to_floris(post.id)
    engine.floris_approve(post.id)
    bad = {"url": {"value": {"value": "not a link"}}, "live_text": {"value": {"value": None}}}
    resp = app.dispatch(view_payload("floris_posted_modal", post.id, bad, "U_FLORIS"))
    assert "errors" in resp.body
    good = {"url": {"value": {"value": "https://www.linkedin.com/posts/abc"}}, "live_text": {"value": {"value": None}}}
    app.dispatch(view_payload("floris_posted_modal", post.id, good, "U_FLORIS"))
    assert engine.store.get(Post, post.id).status == "published"


def test_parse_type():
    assert parse_type("policy-take: caps rose") == ("policy-take", "caps rose")
    assert parse_type("just an idea: with a colon") == ("", "just an idea: with a colon")


def test_blocks_respect_slack_limits(engine):
    post = engine.fast_lane("idea")
    post.versions[-1]["text"] = "x" * 5000
    for block in blocks.owner_review(post, "idea") + blocks.floris_approval(post):
        if block["type"] == "section":
            assert len(block["text"]["text"]) <= 3000
    assert len(blocks.edit_modal("m", post)["blocks"][0]["element"]["initial_value"]) <= 3000


def test_confirm_picks_reads_ticked_boxes(engine, team):
    from founder_engine.models import Idea

    app = make_app(engine, team)
    a, b = engine.add_idea("idea a"), engine.add_idea("idea b")
    req = action_payload("board_confirm", "2026-W45", "U_OWNER")
    import json as _j
    from urllib.parse import parse_qs, urlencode
    payload = _j.loads(parse_qs(req.raw_body)["payload"][0])
    payload["state"] = {"values": {
        f"pick_{a.id}": {"board_tick": {"type": "checkboxes", "selected_options": [{"value": a.id}]}},
        f"pick_{b.id}": {"board_tick": {"type": "checkboxes", "selected_options": []}},
    }}
    req2 = BoltRequest(body=urlencode({"payload": _j.dumps(payload)}),
                       headers={"content-type": ["application/x-www-form-urlencoded"]})
    app.dispatch(req2)
    assert engine.store.get(Idea, a.id).status == "picked" and engine.store.get(Idea, a.id).week == "2026-W45"
    assert engine.store.get(Idea, b.id).status == "new"
