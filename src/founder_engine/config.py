"""Settings, team and funnel configuration.

Secrets come from environment variables only. Everything else comes from
YAML files in `config/`. Nothing environment-specific is hard-coded, so
moving from a test workspace to Stairpay's Slack is a config change.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO_ROOT = Path(os.environ.get("REPO_ROOT", Path(__file__).resolve().parents[2]))


@dataclass
class Person:
    key: str
    name: str
    slack_id: str
    role: str = ""


@dataclass
class Team:
    owner: Person  # B2B marketing lead: reviews every draft first
    founder: Person  # Floris: approves and posts
    amplifiers: dict[str, Person] = field(default_factory=dict)
    inbox_channel: str = ""  # channel ID for the team idea inbox
    comment_queue_channel: str = ""  # channel ID for posts Floris could comment on

    def person(self, key: str) -> Person | None:
        if key == self.owner.key:
            return self.owner
        if key == self.founder.key:
            return self.founder
        return self.amplifiers.get(key)


@dataclass
class FunnelStep:
    who: str  # person key
    action: str  # comment | repost_with_comment | none
    window_minutes: int = 60
    note: str = ""


@dataclass
class Settings:
    slack_bot_token: str = ""
    slack_signing_secret: str = ""
    slack_app_token: str = ""  # only for Socket Mode (local testing)
    llm_provider: str = "anthropic"
    llm_model: str = ""
    anthropic_api_key: str = ""
    storage: str = "sqlite"  # sqlite | firestore
    sqlite_path: str = "founder_engine.db"
    gcp_project: str = ""
    port: int = 3000
    timezone: str = "Europe/London"
    notion_token: str = ""
    notion_database_id: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        e = os.environ.get
        return cls(
            slack_bot_token=e("SLACK_BOT_TOKEN", ""),
            slack_signing_secret=e("SLACK_SIGNING_SECRET", ""),
            slack_app_token=e("SLACK_APP_TOKEN", ""),
            llm_provider=e("LLM_PROVIDER", "anthropic"),
            llm_model=e("LLM_MODEL", ""),
            anthropic_api_key=e("ANTHROPIC_API_KEY", ""),
            storage=e("STORAGE", "sqlite"),
            sqlite_path=e("SQLITE_PATH", "founder_engine.db"),
            gcp_project=e("GCP_PROJECT_ID", ""),
            port=int(e("PORT", "3000")),
            timezone=e("TIMEZONE", "Europe/London"),
            notion_token=e("NOTION_TOKEN", ""),
            notion_database_id=e("NOTION_DATABASE_ID", ""),
        )


def _person(d: dict) -> Person:
    return Person(key=d["key"], name=d.get("name", d["key"]), slack_id=d.get("slack_id", ""), role=d.get("role", ""))


def load_team(path: Path | None = None) -> Team:
    path = path or REPO_ROOT / "config" / "team.yaml"
    if not path.exists():
        path = REPO_ROOT / "config" / "team.example.yaml"
    data = yaml.safe_load(path.read_text())
    return Team(
        owner=_person(data["owner"]),
        founder=_person(data["founder"]),
        amplifiers={p["key"]: _person(p) for p in data.get("amplifiers", [])},
        inbox_channel=data.get("channels", {}).get("inbox", ""),
        comment_queue_channel=data.get("channels", {}).get("comment_queue", ""),
    )


def load_funnels(path: Path | None = None) -> dict[str, list[FunnelStep]]:
    path = path or REPO_ROOT / "config" / "funnels.yaml"
    data = yaml.safe_load(path.read_text())
    return {
        post_type: [FunnelStep(**step) for step in (steps or [])]
        for post_type, steps in data["funnels"].items()
    }


POST_TYPES = ["data-post", "policy-take", "story-bts", "product-launch", "partner-customer"]
