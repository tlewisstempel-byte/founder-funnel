from founder_engine.diffing import change_ratio, word_diff
from founder_engine.llm import parse_json
from founder_engine.models import CommentCandidate, Idea, Post, TeamTask


def test_full_post_lifecycle(engine, slack):
    # 1. fast lane: idea -> draft -> owner's review card
    post = engine.fast_lane("Income caps raised to £90k / £110k from the new year.", "U_OWNER")
    assert post.status == "in_review"
    assert post.post_type == "policy-take"  # classified by the model
    assert post.current_text.startswith("Income caps are up")
    assert len(slack.sent_to("U_OWNER")) == 1

    # 2. owner switches variant, then edits
    engine.switch_variant(post.id)
    engine.owner_edit(post.id, "Caps rise to £90k / £110k. Good news. Next: resales.")
    post = engine.store.get(Post, post.id)
    assert [v["author"] for v in post.versions] == ["llm", "llm", "owner"]

    # 3. send to Floris: he gets a DM, owner card updates
    engine.send_to_floris(post.id)
    assert len(slack.sent_to("U_FLORIS")) == 1
    assert engine.store.get(Post, post.id).status == "sent_to_floris"

    # 4. Floris edits on approval: edit is captured as a version + diff shown to owner
    engine.floris_approve(post.id, "Caps rise to £90k / £110k. Good news. Next up: staircasing and resales.")
    post = engine.store.get(Post, post.id)
    assert post.status == "approved" and post.floris_edited
    assert post.versions[-1]["author"] == "floris"
    assert any("approved with edits" in str(u["blocks"]) for u in slack.updates())

    # 5. posted with a last-minute change on LinkedIn -> live version captured, team tasks fired
    engine.mark_posted(post.id, "https://www.linkedin.com/posts/floris-123", "Caps rise to £90k/£110k. Next up: staircasing.")
    post = engine.store.get(Post, post.id)
    assert post.status == "published" and post.versions[-1]["author"] == "live"
    tasks = engine.store.find(TeamTask, post_id=post.id)
    assert [t.person_key for t in tasks] == ["b2b_lead"]  # policy-take funnel: B2B lead comments only
    assert tasks[0].text == "b2b_lead's angle on this."

    # 6. task done
    engine.task_status(tasks[0].id, "done")
    assert engine.store.get(TeamTask, tasks[0].id).status == "done"


def test_approve_without_edits_is_clean(engine):
    post = engine.fast_lane("story: board game night")
    engine.send_to_floris(post.id)
    engine.floris_approve(post.id)
    post = engine.store.get(Post, post.id)
    assert not post.floris_edited and post.approved_text == post.current_text
    assert "Approved without Floris edits: 1/1" in engine.buffer_report()


def test_product_launch_funnel_reaches_whole_team(engine, slack):
    idea = engine.add_idea("New resales module", post_type="product-launch")
    post = engine.draft_idea(idea.id)
    engine.send_to_floris(post.id)
    engine.floris_approve(post.id)
    engine.mark_posted(post.id, "https://www.linkedin.com/posts/x")
    tasks = engine.store.find(TeamTask, post_id=post.id)
    assert sorted(t.person_key for t in tasks) == ["b2b_lead", "sinead", "tim"]
    assert all(t.action == "repost_with_comment" for t in tasks)
    assert slack.sent_to("U_TIM") and slack.sent_to("U_SINEAD")


def test_reject_and_redraft(engine):
    post = engine.fast_lane("idea")
    new = engine.regenerate(post.id)
    assert engine.store.get(Post, post.id).status == "rejected"
    assert new.id != post.id and new.status == "in_review"
    engine.send_to_floris(new.id)
    engine.floris_reject(new.id, "too salesy")
    assert engine.store.get(Post, new.id).rejection_reason == "too salesy"


def test_inbox_idea_and_draft_buffer(engine):
    engine.add_idea("Hiring our first data analyst")
    assert len(engine.store.find(Idea, status="new")) == 1
    engine.draft_idea(engine.store.find(Idea, status="new")[0].id)
    assert engine.store.find(Idea, status="new") == []


def test_comment_queue_triage_and_send(engine, slack):
    engine.add_comment_candidate("<https://www.linkedin.com/posts/a|link>\nBy Jane Doe\nShared ownership code thoughts", "U_OWNER")
    engine.add_comment_candidate("https://www.linkedin.com/posts/b\nStaircasing is slowing", "U_OWNER")
    engine.add_comment_candidate("https://www.linkedin.com/posts/c\nUnrelated post", "U_OWNER")
    assert engine.add_comment_candidate("no link here") is None
    first = engine.store.find(CommentCandidate)[0]
    assert first.author == "Jane Doe" and first.url == "https://www.linkedin.com/posts/a"

    batch = engine.triage_comments()
    cands = engine.store.find(CommentCandidate)
    assert sum(c.status == "ranked" for c in cands) == 2 and sum(c.status == "skipped" for c in cands) == 1

    assert engine.send_comment_batch(batch) == 2
    floris_msgs = slack.sent_to("U_FLORIS")
    assert "2 posts worth a comment" in floris_msgs[-1]["text"]
    engine.comment_status(cands[0].id, "posted")
    assert engine.store.get(CommentCandidate, cands[0].id).status == "posted"


def test_empty_comment_queue_tells_owner(engine, slack):
    assert engine.triage_comments() is None
    assert "Nothing in #comment-queue" in slack.sent_to("U_OWNER")[-1]["text"]


def test_edit_summary_written(engine, tmp_path):
    engine.root = tmp_path
    post = engine.fast_lane("idea")
    engine.send_to_floris(post.id)
    engine.floris_approve(post.id, "Totally different words from Floris.")
    month = engine.store.get(Post, post.id).approved_at[:7]
    path = engine.write_edit_summary(month)
    assert path and path.read_text().startswith("# Floris's edits")
    assert engine.write_edit_summary("1999-01") is None


def test_diff_helpers():
    assert word_diff("a b c", "a x c") == "a [-b-] {+x+} c"
    assert change_ratio("same text", "same text") == 0.0
    assert change_ratio("a b c d", "w x y z") == 1.0


def test_parse_json_tolerates_prose():
    assert parse_json('Sure! Here it is:\n{"a": 1}\nHope that helps') == {"a": 1}
