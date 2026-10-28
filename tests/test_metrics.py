from datetime import datetime, timedelta, timezone

import pytest

from founder_engine import metrics
from founder_engine.models import Post


def publish(engine, text="idea", days_ago=0.0):
    post = engine.fast_lane(text)
    engine.send_to_floris(post.id)
    engine.floris_approve(post.id)
    engine.mark_posted(post.id, "https://www.linkedin.com/posts/x")
    post = engine.store.get(Post, post.id)
    post.published_at = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
    engine.store.put(post)
    return post


def test_parse_count():
    assert metrics.parse_count("1,234") == 1234
    assert metrics.parse_count("1.2k") == 1200
    assert metrics.parse_count("") is None
    with pytest.raises(ValueError):
        metrics.parse_count("lots")


def test_due_checkpoints(engine):
    fresh = publish(engine, days_ago=0.5)
    day_old = publish(engine, days_ago=1.5)
    week_old = publish(engine, days_ago=8)
    due = {(p.id, cp) for p, cp in metrics.due(engine.store.find(Post))}
    assert (fresh.id, "24h") not in due
    assert (day_old.id, "24h") in due and (day_old.id, "7d") not in due
    assert {(week_old.id, "24h"), (week_old.id, "7d")} <= due


def test_request_log_and_digest_results(engine, slack):
    a = publish(engine, "post a", days_ago=2)
    b = publish(engine, "post b", days_ago=3)
    assert engine.request_metrics() == 2
    assert "need numbers" in slack.sent_to("U_OWNER")[-1]["text"]
    engine.log_metrics(a.id, "24h", {"reactions": 30, "comments": 2, "reposts": 0, "impressions": None})
    engine.log_metrics(b.id, "24h", {"reactions": 20, "comments": 8, "reposts": 1, "impressions": 2400}, "Head of HO at a G15 commented")
    assert engine.request_metrics() == 0
    assert engine.store.get(Post, b.id).metrics["24h"]["note"].startswith("Head of HO")
    ranked = metrics.last_week(engine.store.find(Post))
    assert ranked[0].id == b.id  # comments and reposts weigh more than reactions
    engine.send_board_digest()
    digest = str(slack.sent_to("U_OWNER")[-1]["blocks"])
    assert "Last week's results" in digest and "2,400 impressions" in digest
    row = {r.engine_id: r for r in engine.board_rows()}[b.idea_id]
    assert row.comments == 8 and row.impressions == 2400


def test_metrics_modal_validation(engine, team):
    from tests.test_slack_wiring import make_app, view_payload

    app = make_app(engine, team)
    post = publish(engine, days_ago=2)
    bad = {"reactions": {"value": {"value": "lots"}}, "comments": {"value": {"value": ""}},
           "reposts": {"value": {"value": "0"}}, "impressions": {"value": {"value": None}}, "note": {"value": {"value": None}}}
    resp = app.dispatch(view_payload("metrics_modal", f"{post.id}|24h", bad, "U_OWNER"))
    assert "errors" in resp.body and "reactions" in resp.body and "comments" in resp.body
    good = {"reactions": {"value": {"value": "41"}}, "comments": {"value": {"value": "4"}},
            "reposts": {"value": {"value": "2"}}, "impressions": {"value": {"value": "3.1k"}}, "note": {"value": {"value": None}}}
    app.dispatch(view_payload("metrics_modal", f"{post.id}|24h", good, "U_OWNER"))
    m = engine.store.get(Post, post.id).metrics["24h"]
    assert (m["reactions"], m["comments"], m["reposts"], m["impressions"]) == (41, 4, 2, 3100)
