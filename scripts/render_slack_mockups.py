"""Render mockups/slack/*.json (real Block Kit payloads) as Slack-style PNG previews.

An approximation of Slack's look for review only; Slack's Block Kit Builder links in
mockups/slack/README.md show the exact rendering. Run after scripts/make_mockups.py.
"""

import html
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

D = Path(__file__).resolve().parents[1] / "mockups" / "slack"


def md(text: str) -> str:
    t = html.escape(text)
    t = re.sub(r"&lt;(https?://[^|&]+)\|([^&]+?)&gt;", r'<a>\2</a>', t)
    t = re.sub(r"&lt;(https?://[^&]+?)&gt;", r'<a>\1</a>', t)
    t = re.sub(r"\*([^*\n]+)\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w/])_([^_\n]+)_(?!\w)", r"<i>\1</i>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    lines = []
    for line in t.split("\n"):
        if line.startswith("&gt; ") or line == "&gt;":
            lines.append(f'<div class="q">{line[5:] or "&nbsp;"}</div>')
        else:
            lines.append(line + "<br>")
    return "".join(lines)


def render_block(b: dict) -> str:
    t = b["type"]
    if t == "section":
        acc = ""
        if b.get("accessory", {}).get("type") == "checkboxes":
            acc = '<label class="cb"><span class="box"></span>Pick</label>'
        return f'<div class="sec"><div class="txt">{md(b["text"]["text"])}</div>{acc}</div>'
    if t == "context":
        return f'<div class="ctx">{"".join(md(e.get("text", "")) for e in b["elements"])}</div>'
    if t == "divider":
        return '<hr>'
    if t == "actions":
        btns = "".join(f'<span class="btn {e.get("style", "")}">{html.escape(e["text"]["text"])}</span>' for e in b["elements"])
        return f'<div class="acts">{btns}</div>'
    return ""


CSS = """
body{margin:0;background:#fff;font-family:-apple-system,'Segoe UI',Lato,Helvetica,Arial,sans-serif;color:#1d1c1d;font-size:15px}
.msg{display:flex;gap:10px;padding:16px 20px;width:640px}
.av{width:36px;height:36px;border-radius:6px;background:#1f0b56;color:#fff;font-weight:700;display:flex;align-items:center;justify-content:center;flex:none}
.name{font-weight:900}.app{font-size:10px;background:#e8e8e8;color:#616061;padding:1px 4px;border-radius:3px;margin-left:4px;font-weight:700}
.time{color:#616061;font-size:12px;margin-left:6px}
.sec{display:flex;justify-content:space-between;gap:12px;margin:6px 0;line-height:1.46}
.ctx{color:#616061;font-size:13px;margin:4px 0}
.q{border-left:4px solid #dddddd;padding-left:10px;color:#1d1c1d}
hr{border:0;border-top:1px solid #e8e8e8;margin:10px 0}
.acts{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}
.btn{border:1px solid #bbb;border-radius:4px;padding:4px 12px;font-weight:700;font-size:14px}
.btn.primary{background:#007a5a;border-color:#007a5a;color:#fff}.btn.danger{color:#e01e5a;border-color:#e01e5a}
.cb{display:flex;gap:6px;align-items:flex-start;font-size:14px;white-space:nowrap}.box{width:14px;height:14px;border:1px solid #888;border-radius:3px;margin-top:2px}
a{color:#1264a3}code{background:#f6f6f6;border:1px solid #ddd;border-radius:3px;padding:0 3px;font-size:12px;color:#e01e5a}
"""

with sync_playwright() as p:
    br = p.chromium.launch()
    page = br.new_page(viewport={"width": 680, "height": 400}, device_scale_factor=2)
    for f in sorted(D.glob("*.json")):
        blocks = json.loads(f.read_text())["blocks"]
        body = "".join(render_block(b) for b in blocks)
        doc = (f"<html><head><style>{CSS}</style></head><body><div class='msg'><div class='av'>S</div><div>"
               f"<div><span class='name'>Stairpay Content</span><span class='app'>APP</span><span class='time'>9:02</span></div>"
               f"{body}</div></div></body></html>")
        page.set_content(doc)
        page.locator(".msg").screenshot(path=str(f.with_suffix(".png")))
        print("rendered", f.with_suffix(".png").name)
    br.close()
