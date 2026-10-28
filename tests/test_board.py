from datetime import date

from founder_engine import board
from founder_engine.models import Idea, Post, SeenItem
from founder_engine.notion_sync import DryRunTransport, NotionClient, database_schema
from founder_engine.scanner import keyword_match, parse_feed, NewsItem

ATOM = """<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">
<entry><title>Shared ownership income caps raised</title><link href="https://www.gov.uk/a"/><updated>2026-10-26T10:00:00Z</updated><summary>Caps rise</summary></entry>
<entry><title>Landfill tax guide</title><link href="https://www.gov.uk/b"/><updated>2026-10-28T10:00:00Z</updated></entry>
</feed>"""
RSS = """<?xml version="1.0"?><rss><channel>
<item><title>Staircasing slows at large provider</title><link>https://news.example/c</link><pubDate>Tue, 27 Oct 2026 08:00:00 GMT</pubDate><description>&lt;b&gt;Shared ownership&lt;/b&gt; staircasing down</description><source>Housing Today</source></item>
<item><title>Shared owner service charges rise</title><link>https://news.example/d</link><pubDate>Mon, 26 Oct 2026 08:00:00 GMT</pubDate></item>
</channel></rss>"""
SOURCES = {"feeds": [{"name": "gov", "url": "atom"}, {"name": "news", "url": "rss"}, {"name": "broken", "url": "x"}],
           "keywords": ["shared ownership", "staircasing", "shared owner"]}


def getter(url):
    if url == "x":
        raise OSError("feed down")
    return ATOM if url == "atom" else RSS


def test_parse_atom_and_rss():
    a = parse_feed(ATOM, "gov")
    assert a[0].title == "Shared ownership income caps raised" and a[0].published == "2026-10-26"
    r = parse_feed(RSS, "news")
    assert r[0].published == "2026-10-27" and r[0].summary == "Shared ownership staircasing down" and r[0].source == "Housing Today"
    assert keyword_match(r[0], ["staircasing"]) and not keyword_match(NewsItem("Landfill", "u"), ["staircasing"])


def test_scan_adds_relevant_ideas_alerts_urgent_and_never_repeats(engine, slack):
    added = engine.scan_news(SOURCES, getter)
    # 3 keyword matches (landfill filtered out); item 1 judged irrelevant by the model
    assert len(added) == 2
    assert sum(1 for i in added if i.urgent) == 1
    assert any("Timely" in m["text"] for m in slack.sent_to("U_OWNER"))
    assert len(engine.store.find(SeenItem)) == 3
    assert engine.scan_news(SOURCES, getter) == []  # nothing new second time


def test_board_digest_pick_and_draft(engine, slack):
    engine.scan_news(SOURCES, getter)
    engine.add_idea("Floris on hiring our first analyst", "meeting")
    assert engine.send_board_digest() == 3
    digest = slack.sent_to("U_OWNER")[-1]
    assert sum(1 for b in digest["blocks"] if b.get("accessory", {}).get("type") == "checkboxes") == 3
    meeting = engine.store.find(Idea, source="meeting")[0]
    assert meeting.score == 6 and meeting.title == "Scored idea"  # scored before the digest

    picked = engine.pick_ideas([meeting.id], "2026-W45")
    assert picked[0].status == "picked" and picked[0].week == "2026-W45"
    rows = {r.engine_id: r for r in engine.board_rows()}
    assert rows[meeting.id].column == "Picked"
    posts = engine.draft_picked()
    assert len(posts) == 1 and engine.board_rows()[0].column in board.COLUMNS
    assert {r.engine_id: r for r in engine.board_rows()}[meeting.id].column == "Drafting"


def test_board_columns_follow_post_status(engine):
    post = engine.fast_lane("idea")
    engine.send_to_floris(post.id)
    assert {r.engine_id: r for r in engine.board_rows()}[post.idea_id].column == "With Floris"
    engine.floris_approve(post.id)
    engine.mark_posted(post.id, "https://www.linkedin.com/posts/x")
    row = {r.engine_id: r for r in engine.board_rows()}[post.idea_id]
    assert row.column == "Published" and row.post_url.endswith("/x")
    md = board.to_markdown(engine.board_rows(), "2026-W45")
    assert "## Published (1)" in md


def test_next_cycle_week_from_wednesday():
    assert board.next_cycle_week(date(2026, 10, 28)) == "2026-W45"  # Wed 28 Oct -> week of Mon 2 Nov


def test_notion_sync_creates_then_updates(engine):
    engine.add_idea("An idea", "inbox")
    t = DryRunTransport()
    client = NotionClient("secret", transport=t)
    db = client.create_database("page-123")
    assert set(t.requests[0]["body"]["properties"]) == set(database_schema())
    engine.notion = (client, db)
    assert engine.sync_notion() == 1
    methods = [r["method"] + " " + r["path"].split("/")[1] for r in t.requests[1:]]
    assert methods == ["POST databases", "POST pages"]  # query (no match) then create
    props = t.requests[-1]["body"]["properties"]
    assert props["Status"]["select"]["name"] == "New" and props["Engine ID"]["rich_text"][0]["text"]["content"].startswith("idea_")


def test_notion_failure_never_blocks(engine, slack):
    def broken(method, path, body):
        raise OSError("notion down")
    engine.notion = (NotionClient("s", transport=broken), "db")
    engine.add_idea("x")
    assert engine.sync_notion() == 0
    assert "Notion sync failed" in slack.sent_to("U_OWNER")[-1]["text"]
