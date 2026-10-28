"""Everything the model writes. Prompts are built from the repo's Markdown files,
so improving the voice file or a playbook improves the output with no code change.
"""

from __future__ import annotations

from pathlib import Path

from .config import REPO_ROOT
from .llm import LLM

HOUSE_RULES = """You write for Floris ten Nijenhuis, founder of Stairpay (software for shared ownership in England).
Audience: B2B (housing providers, developers, lenders, people shaping shared ownership policy). British English.
Hard rules:
- Never invent a number, quote, opinion, customer or event. If something is missing, write [PLACEHOLDER: what is needed].
- Never name a customer or partner unless the input says written OK was given.
- No financial or legal advice. No hype. No engagement bait.
- Follow the voice file and the playbook exactly."""


def read_repo_file(rel: str, root: Path = REPO_ROOT) -> str:
    p = root / rel
    return p.read_text() if p.exists() else ""


def draft_post(llm: LLM, idea_text: str, post_type: str, recent_posts: list[str], root: Path = REPO_ROOT) -> dict:
    system = "\n\n".join(
        [
            HOUSE_RULES,
            "## Voice file\n" + read_repo_file("voice/floris.md", root),
            f"## Playbook ({post_type})\n" + read_repo_file(f"playbooks/{post_type}.md", root),
        ]
    )
    recent = "\n---\n".join(recent_posts[-5:]) or "(none yet)"
    user = f"""Raw material for the post:
{idea_text}

Floris's most recent posts (avoid repeating their angle or hook):
{recent}

Return JSON with:
- "variants": two objects {{"angle": short label, "text": full post}} with genuinely different angles
- "hooks": three alternative opening lines
- "visual_brief": one line, or "none"
- "claims": every factual claim as {{"claim": ..., "source": where it comes from or "UNVERIFIED"}}"""
    out = llm.complete_json(system, user, max_tokens=4000)
    out.setdefault("variants", [])
    out.setdefault("hooks", [])
    out.setdefault("claims", [])
    out.setdefault("visual_brief", "none")
    if not out["variants"]:
        raise ValueError("Model returned no variants")
    return out


def classify_idea(llm: LLM, idea_text: str, post_types: list[str]) -> str:
    system = "You sort LinkedIn post ideas for a B2B founder into one post type."
    user = f"Post types: {', '.join(post_types)}\n\nIdea:\n{idea_text}\n\nReturn JSON: {{\"post_type\": one of the types}}"
    try:
        pt = llm.complete_json(system, user, max_tokens=100).get("post_type", "")
    except Exception:
        pt = ""
    return pt if pt in post_types else "story-bts"


def team_comments(llm: LLM, post_text: str, tasks: list[dict], root: Path = REPO_ROOT) -> dict[str, str]:
    """tasks: [{person_key, name, role, action}] -> {person_key: text}"""
    if not tasks:
        return {}
    system = "\n\n".join(
        [
            "You write short LinkedIn comments or repost captions for Stairpay team members to support their founder's post.",
            "Rules: 1-3 lines; each person sounds like themselves and adds a different angle; never identical wording; "
            "never praise-only ('great post'); no invented facts; British English.",
            "## Team voice profiles\n" + read_repo_file("voice/team.md", root),
        ]
    )
    who = "\n".join(f"- {t['person_key']} ({t['name']}, {t['role']}): {t['action']}" for t in tasks)
    user = f"Floris's post:\n{post_text}\n\nWrite one text per person:\n{who}\n\nReturn JSON {{person_key: text}}."
    out = llm.complete_json(system, user, max_tokens=1500)
    return {t["person_key"]: str(out.get(t["person_key"], "")).strip() for t in tasks}


def triage_comments(llm: LLM, candidates: list[dict], root: Path = REPO_ROOT, top_n: int = 5) -> dict:
    """candidates: [{id, url, author, text}] -> {"ranked": [{id, score, why, comment}]}"""
    system = "\n\n".join(
        [
            HOUSE_RULES,
            read_repo_file("playbooks/daily-comments.md", root),
            "## Voice file\n" + read_repo_file("voice/floris.md", root),
            "## Watchlist\n" + read_repo_file("trends/watchlist.md", root),
        ]
    )
    posts = "\n\n".join(f"[{c['id']}] {c.get('author','?')} | {c['url']}\n{c['text']}" for c in candidates)
    user = f"""Candidate LinkedIn posts for Floris to comment on today:

{posts}

Score each 1-5 (author priority, relevance, freshness, whether Floris can add something real).
Return JSON {{"ranked": [{{"id", "score", "why" (one line), "comment" (2-4 lines in Floris's voice, or "" if skip)}}]}},
best first, top {top_n} with comments, the rest with comment "" and a reason to skip."""
    out = llm.complete_json(system, user, max_tokens=3000)
    out.setdefault("ranked", [])
    return out


def summarise_edits(llm: LLM, pairs: list[dict], month: str) -> str:
    """pairs: [{before, after}] -> Markdown for voice/edits/YYYY-MM.md"""
    system = (
        "You study how a founder edits ghost-written LinkedIn drafts, to improve his voice file. "
        "Find patterns, not one-offs. Quote short examples. Be concrete: words cut, words added, structure, length, tone."
    )
    body = "\n\n".join(f"### Edit {i+1}\nBEFORE:\n{p['before']}\n\nAFTER:\n{p['after']}" for i, p in enumerate(pairs))
    user = f"""Edits from {month}:

{body}

Write Markdown with sections: "Patterns" (bullets, each with an example), "Proposed changes to voice/floris.md" (bullets),
"One-offs to ignore". Start with a title line '# Floris's edits: {month}'."""
    return llm.complete(system, user, max_tokens=2500)
