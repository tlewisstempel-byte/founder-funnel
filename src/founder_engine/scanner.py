"""Daily news scan: RSS/Atom feeds -> keyword filter -> model triage -> ideas on the board.

Only reads public feeds (config/sources.yaml); never scrapes LinkedIn or paywalled pages.
Items are remembered (SeenItem) so nothing is suggested twice.
"""

from __future__ import annotations

import email.utils
import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import yaml

from .config import REPO_ROOT

ATOM = "{http://www.w3.org/2005/Atom}"
TAG_RE = re.compile(r"<[^>]+>")


@dataclass
class NewsItem:
    title: str
    url: str
    published: str = ""
    summary: str = ""
    source: str = ""


def load_sources(path: Path | None = None) -> dict:
    return yaml.safe_load((path or REPO_ROOT / "config" / "sources.yaml").read_text())


def http_get(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "StairpayContentBot/0.1 (+news digest)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def _clean(text: str) -> str:
    return " ".join(html.unescape(TAG_RE.sub(" ", text or "")).split())


def _iso(date_text: str) -> str:
    if not date_text:
        return ""
    try:
        return email.utils.parsedate_to_datetime(date_text).date().isoformat()  # RSS format
    except (TypeError, ValueError):
        return date_text[:10]  # Atom is already ISO


def parse_feed(xml_text: str, source: str = "") -> list[NewsItem]:
    root = ET.fromstring(xml_text)
    items = []
    if root.tag == f"{ATOM}feed":
        for e in root.findall(f"{ATOM}entry"):
            link = e.find(f"{ATOM}link")
            items.append(NewsItem(
                title=_clean(e.findtext(f"{ATOM}title", "")),
                url=link.get("href", "") if link is not None else "",
                published=_iso(e.findtext(f"{ATOM}updated", "") or e.findtext(f"{ATOM}published", "")),
                summary=_clean(e.findtext(f"{ATOM}summary", ""))[:500],
                source=source))
    else:
        for i in root.iter("item"):
            items.append(NewsItem(
                title=_clean(i.findtext("title", "")),
                url=(i.findtext("link", "") or "").strip(),
                published=_iso(i.findtext("pubDate", "")),
                summary=_clean(i.findtext("description", ""))[:500],
                source=_clean(i.findtext("source", "")) or source))
    return [x for x in items if x.title and x.url]


def keyword_match(item: NewsItem, keywords: list[str]) -> bool:
    text = f"{item.title} {item.summary}".lower()
    return any(k.lower() in text for k in keywords)


def fetch_all(sources: dict, getter: Callable[[str], str] = http_get, log=print) -> list[NewsItem]:
    out, seen_urls = [], set()
    for feed in sources.get("feeds", []):
        try:
            items = parse_feed(getter(feed["url"]), feed.get("name", ""))
        except Exception as e:  # one broken feed must not stop the scan
            log(f"Feed failed: {feed.get('name')}: {e}")
            continue
        for it in items:
            if it.url not in seen_urls and keyword_match(it, sources.get("keywords", [])):
                seen_urls.add(it.url)
                out.append(it)
    return out
