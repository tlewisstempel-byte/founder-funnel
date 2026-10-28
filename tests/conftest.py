import itertools
import json
import re

import pytest

from founder_engine.config import Person, Team, load_funnels
from founder_engine.flows import Engine
from founder_engine.llm import FakeLLM
from founder_engine.store import SQLiteStore


class FakeSlack:
    """Records every call; returns what Slack would (channel + ts)."""

    def __init__(self):
        self.calls = []
        self._ts = itertools.count(1)

    def _record(self, method, **kw):
        self.calls.append((method, kw))
        return {"ok": True, "channel": "D_" + str(kw.get("channel", "")), "ts": f"{next(self._ts)}.0"}

    def chat_postMessage(self, **kw):
        return self._record("chat_postMessage", **kw)

    def chat_update(self, **kw):
        return self._record("chat_update", **kw)

    def views_open(self, **kw):
        return self._record("views_open", **kw)

    def reactions_add(self, **kw):
        return self._record("reactions_add", **kw)

    def sent_to(self, user_id):
        return [kw for m, kw in self.calls if m == "chat_postMessage" and kw["channel"] == user_id]

    def updates(self):
        return [kw for m, kw in self.calls if m == "chat_update"]


def fake_responder(system: str, user: str) -> str:
    if "sort LinkedIn post ideas" in system:
        return json.dumps({"post_type": "policy-take"})
    if '"variants"' in user:
        return "```json\n" + json.dumps({
            "variants": [
                {"angle": "door and hallway", "text": "Income caps are up.\n\nNow fix staircasing."},
                {"angle": "short", "text": "Caps rise to £90k / £110k. Good. Next: resales."},
            ],
            "hooks": ["£80k in 2016 is not £80k in 2026."],
            "visual_brief": "none",
            "claims": [{"claim": "Caps rise to £90k", "source": "Written statement 26 Oct 2026"}],
        }) + "\n```"
    if "Write one text per person" in user:
        keys = re.findall(r"^- (\w+) \(", user, re.M)
        return json.dumps({k: f"{k}'s angle on this." for k in keys})
    if "Candidate LinkedIn posts" in user:
        ids = re.findall(r"\[(cmt_\w+)\]", user)
        ranked = [{"id": i, "score": 5 - n, "why": f"reason {n}", "comment": f"comment {n}" if n < 2 else ""}
                  for n, i in enumerate(ids)]
        return json.dumps({"ranked": ranked})
    if "Edits from" in user:
        return "# Floris's edits\n\n## Patterns\n- Cuts the opening question."
    raise AssertionError("Unexpected prompt: " + user[:200])


@pytest.fixture
def team():
    return Team(
        owner=Person("b2b_lead", "B2B lead", "U_OWNER", "B2B marketing"),
        founder=Person("floris", "Floris", "U_FLORIS", "Founder"),
        amplifiers={
            "tim": Person("tim", "Tim", "U_TIM", "CPO"),
            "sinead": Person("sinead", "Sinead", "U_SINEAD", "B2C marketing"),
            "b2b_lead": Person("b2b_lead", "B2B lead", "U_OWNER", "B2B marketing"),
        },
        inbox_channel="C_INBOX",
        comment_queue_channel="C_QUEUE",
    )


@pytest.fixture
def slack():
    return FakeSlack()


@pytest.fixture
def llm():
    return FakeLLM(fake_responder)


@pytest.fixture
def engine(team, slack, llm):
    return Engine(SQLiteStore(":memory:"), llm, team, load_funnels(), slack)
