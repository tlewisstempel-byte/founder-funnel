"""On-brand LinkedIn visuals rendered from real numbers: column chart, line chart,
stat card, quote card. Output: 1080x1350 PNG (LinkedIn's 4:5 feed format) + alt text.

Charts are drawn as SVG here (exact numbers, exact labels: never an image model),
placed in an HTML card using brand/tokens.json and Poppins, then screenshotted
with Playwright. Every visual carries its source line (period, sample).

Colour rules (validated with the dataviz palette checker, 2026-10-28):
- One series: iris-600 columns/line, iris-400 for the single highlight.
- Several series, in this fixed order: iris-400, rice-500, powder-400, slate-300.
  Passes lightness, chroma, colour-blind separation and contrast checks on white.
  More than 4 series: fold into "Other" or split the chart.
"""

from __future__ import annotations

import base64
import html
import json
import math
from dataclasses import dataclass
from pathlib import Path

from .config import REPO_ROOT

W, H = 1080, 1350
CATEGORICAL = ["iris-400", "rice-500", "powder-400", "slate-300"]


# ------------------------------------------------------------------ tokens
def load_tokens(root: Path = REPO_ROOT) -> dict[str, str]:
    data = json.loads((root / "brand" / "tokens.json").read_text())
    raw = {t["name"]: t["value"] for t in data["color"]["tokens"]}
    resolve = lambda v: resolve(raw[v[1:-1]]) if v.startswith("{") else v
    return {k: resolve(v) for k, v in raw.items()}


@dataclass
class Card:
    eyebrow: str = ""
    headline: str = ""
    subhead: str = ""
    source: str = ""  # e.g. "Anonymised, aggregated Stairpay data · Jan-Sep 2026 · n = 1,240 homes"


def fmt_value(v: float, unit: str = "") -> str:
    """£1,250 · 45% · 12.9K · 3.4M"""
    if unit == "%":
        return f"{v:.0f}%" if abs(v - round(v)) < 0.05 else f"{v:.1f}%"
    prefix = "£" if unit == "£" else ""
    suffix = unit if unit not in ("£", "%") else ""
    a = abs(v)
    if a >= 1_000_000:
        s = f"{v/1_000_000:.1f}M".replace(".0M", "M")
    elif a >= 10_000:
        s = f"{v/1_000:.1f}K".replace(".0K", "K")
    elif a >= 1000 and prefix:
        s = f"{v:,.0f}"
    elif a >= 1000:
        s = f"{v:,.0f}"
    else:
        s = f"{v:.0f}" if abs(v - round(v)) < 0.05 else f"{v:.1f}"
    return f"{prefix}{s}{suffix}"


def nice_ticks(vmax: float, target: int = 4) -> list[float]:
    if vmax <= 0:
        return [0, 1]
    raw = vmax / target
    mag = 10 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
    top = math.ceil(vmax / step) * step
    return [round(i * step, 10) for i in range(int(round(top / step)) + 1)]


def _esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def _column_path(x: float, y: float, w: float, h: float, r: float) -> str:
    """Column with rounded top (data end) and square base."""
    r = min(r, w / 2, h)
    return (f"M{x:.1f},{y+h:.1f} V{y+r:.1f} Q{x:.1f},{y:.1f} {x+r:.1f},{y:.1f} "
            f"H{x+w-r:.1f} Q{x+w:.1f},{y:.1f} {x+w:.1f},{y+r:.1f} V{y+h:.1f} Z")


# ------------------------------------------------------------------ chart SVGs
def column_chart_svg(labels: list[str], values: list[float], t: dict, unit: str = "",
                     highlight: int | None = None, width: int = 900, height: int = 760) -> str:
    if len(labels) != len(values) or not values:
        raise ValueError("labels and values must be the same non-zero length")
    if min(values) < 0:
        raise ValueError("column charts here start at zero; use a different form for negative values")
    left, right, top, bottom = 84, 16, 56, 64
    pw, ph = width - left - right, height - top - bottom
    ticks = nice_ticks(max(values))
    vmax = ticks[-1]
    slot = pw / len(values)
    bw = min(slot * 0.62, 64)  # cap thickness; leftover band is air
    hi = highlight if highlight is not None else len(values) - 1
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    for tv in ticks:  # recessive hairline grid
        y = top + ph - tv / vmax * ph
        parts.append(f'<line x1="{left}" x2="{width-right}" y1="{y:.1f}" y2="{y:.1f}" stroke="{t["neutral-200"]}" stroke-width="1"/>')
        parts.append(f'<text x="{left-14}" y="{y+8:.1f}" text-anchor="end" class="tick">{_esc(fmt_value(tv, unit))}</text>')
    label_every = max(1, math.ceil(len(labels) / 12))
    to_label = {hi, len(values) - 1, values.index(max(values))}
    for i, (lab, v) in enumerate(zip(labels, values)):
        x = left + i * slot + (slot - bw) / 2
        h = v / vmax * ph
        y = top + ph - h
        colour = t["iris-400"] if i == hi else t["iris-600"]
        if h > 0:
            parts.append(f'<path d="{_column_path(x, y, bw, h, 8)}" fill="{colour}"/>')
        if i % label_every == 0 or i == len(labels) - 1:
            parts.append(f'<text x="{x+bw/2:.1f}" y="{top+ph+40}" text-anchor="middle" class="xlab">{_esc(lab)}</text>')
        if i in to_label:  # selective direct labels on the cap
            parts.append(f'<text x="{x+bw/2:.1f}" y="{y-14:.1f}" text-anchor="middle" class="{"val hi" if i == hi else "val"}">{_esc(fmt_value(v, unit))}</text>')
    parts.append(f'<line x1="{left}" x2="{width-right}" y1="{top+ph}" y2="{top+ph}" stroke="{t["neutral-300"]}" stroke-width="1.5"/>')
    parts.append("</svg>")
    return "".join(parts)


def line_chart_svg(x_labels: list[str], series: dict[str, list[float]], t: dict, unit: str = "",
                   width: int = 900, height: int = 760) -> str:
    if not series or len(series) > len(CATEGORICAL):
        raise ValueError(f"1-{len(CATEGORICAL)} series; fold the rest into 'Other' or split the chart")
    n = len(x_labels)
    if any(len(v) != n for v in series.values()):
        raise ValueError("every series needs one value per x label")
    multi = len(series) > 1
    longest = max(len(fmt_value(v[-1], unit) + (f" · {k}" if multi else "")) for k, v in series.items())
    end_label_w = min(int(longest * 17.5) + 40, width // 2)  # measured, so end labels are never clipped
    left, right, top, bottom = 84, end_label_w, 56, 64
    pw, ph = width - left - right, height - top - bottom
    allv = [v for vs in series.values() for v in vs]
    lo = 0 if min(allv) >= 0 else min(allv)
    ticks = nice_ticks(max(allv) - lo)
    ticks = [lo + tv for tv in ticks]
    vmin, vmax = ticks[0], ticks[-1]
    xp = lambda i: left + (pw * i / (n - 1) if n > 1 else pw / 2)
    yp = lambda v: top + ph - (v - vmin) / (vmax - vmin) * ph
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    for tv in ticks:
        parts.append(f'<line x1="{left}" x2="{left+pw}" y1="{yp(tv):.1f}" y2="{yp(tv):.1f}" stroke="{t["neutral-200"]}" stroke-width="1"/>')
        parts.append(f'<text x="{left-14}" y="{yp(tv)+8:.1f}" text-anchor="end" class="tick">{_esc(fmt_value(tv, unit))}</text>')
    every = max(1, math.ceil(n / 8))
    for i, lab in enumerate(x_labels):
        if i % every == 0 or i == n - 1:
            parts.append(f'<text x="{xp(i):.1f}" y="{top+ph+40}" text-anchor="middle" class="xlab">{_esc(lab)}</text>')
    colours = [t["iris-600"]] if not multi else [t[c] for c in CATEGORICAL]
    ends = []
    for (name, vals), colour in zip(series.items(), colours):
        pts = " ".join(f"{xp(i):.1f},{yp(v):.1f}" for i, v in enumerate(vals))
        if not multi:  # 10% wash under a single line
            parts.append(f'<polygon points="{xp(0):.1f},{yp(vmin):.1f} {pts} {xp(n-1):.1f},{yp(vmin):.1f}" fill="{colour}" fill-opacity="0.1"/>')
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{colour}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>')
        ex, ey = xp(n - 1), yp(vals[-1])
        parts.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="9" fill="{colour}" stroke="#ffffff" stroke-width="4"/>')
        ends.append([ey, name, vals[-1], colour])
    # end labels with simple collision avoidance (min 44px apart), leader lines when nudged
    ends.sort(key=lambda e: e[0])
    for i in range(1, len(ends)):
        ends[i].append(ends[i][0])
        if ends[i][0] - ends[i - 1][0] < 44:
            ends[i][0] = ends[i - 1][0] + 44
    for e in ends:
        ly, name, val, colour = e[0], e[1], e[2], e[3]
        orig = e[4] if len(e) > 4 else ly
        lx = left + pw + 22
        if abs(ly - orig) > 1:
            parts.append(f'<line x1="{left+pw+10}" y1="{orig:.1f}" x2="{lx-4}" y2="{ly-8:.1f}" stroke="{t["neutral-300"]}" stroke-width="1.5"/>')
        label = f"{fmt_value(val, unit)}" + (f" · {name}" if multi else "")
        parts.append(f'<text x="{lx}" y="{ly:.1f}" class="val">{_esc(label)}</text>')
    parts.append(f'<line x1="{left}" x2="{left+pw}" y1="{top+ph}" y2="{top+ph}" stroke="{t["neutral-300"]}" stroke-width="1.5"/>')
    parts.append("</svg>")
    return "".join(parts)


# ------------------------------------------------------------------ card HTML
def _font_css(root: Path) -> str:
    out = []
    for w, name in ((400, "Regular"), (500, "Medium"), (600, "SemiBold"), (700, "Bold")):
        f = root / "brand" / "fonts" / f"Poppins-{name}.ttf"
        if f.exists():
            b64 = base64.b64encode(f.read_bytes()).decode()
            out.append(f"@font-face{{font-family:Poppins;font-weight:{w};src:url(data:font/ttf;base64,{b64}) format('truetype');}}")
    return "".join(out)


def card_html(card: Card, body: str, t: dict, root: Path = REPO_ROOT, legend: list[tuple[str, str]] | None = None,
              dark: bool = False) -> str:
    logo_file = "stairpay-wordmark-white.svg" if dark else "stairpay-wordmark-indigo.svg"
    logo = (root / "brand" / "logos" / logo_file).read_text()
    ground = t["iris-600"] if dark else t["neutral-50"]
    legend_html = ""
    if legend:
        legend_html = '<div class="legend">' + "".join(
            f'<span><i style="background:{c}"></i>{_esc(n)}</span>' for n, c in legend) + "</div>"
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{_font_css(root)}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{W}px;height:{H}px;background:{ground};font-family:Poppins,sans-serif;color:{t['neutral-700']}}}
.page{{width:{W}px;height:{H}px;padding:72px 64px 56px;display:flex;flex-direction:column}}
.eyebrow{{align-self:flex-start;font-size:24px;font-weight:600;color:{t['iris-500']};background:{t['iris-100']};padding:8px 22px;border-radius:9999px;margin-bottom:28px}}
h1{{font-size:56px;line-height:1.1;font-weight:700;letter-spacing:-0.025em;color:{t['iris-600']};margin-bottom:18px}}
.sub{{font-size:28px;line-height:1.45;color:{t['neutral-700']};margin-bottom:28px}}
.card{{flex:1;background:#fff;border:1px solid {t['neutral-200']};border-radius:28px;padding:36px 24px 24px;display:flex;flex-direction:column;justify-content:center;align-items:center;overflow:hidden}}
.card svg{{max-width:100%;height:auto}}
.tick,.xlab{{font-family:Poppins;font-size:24px;fill:{t['neutral-500']}}}
.val{{font-family:Poppins;font-size:28px;font-weight:700;fill:{t['iris-600']}}}
.val.hi{{fill:{t['iris-400']}}}
.legend{{display:flex;gap:28px;flex-wrap:wrap;font-size:24px;color:{t['neutral-700']};margin:0 0 16px}}
.legend i{{display:inline-block;width:28px;height:8px;border-radius:9999px;margin-right:10px;vertical-align:middle}}
.foot{{display:flex;justify-content:space-between;align-items:flex-end;gap:32px;margin-top:28px}}
.source{{font-size:24px;line-height:1.4;color:{t['neutral-500']};max-width:720px}}
.logo svg{{height:44px;width:auto;display:block}}
.stat{{font-size:200px;font-weight:700;letter-spacing:-0.04em;line-height:1;color:{t['iris-400']}}}
.stat-label{{font-size:36px;font-weight:600;color:{t['iris-600']};text-align:center;margin-top:24px;max-width:760px;line-height:1.3}}
.stat-context{{font-size:28px;color:{t['neutral-700']};text-align:center;margin-top:20px;max-width:760px;line-height:1.45}}
.quote{{font-size:52px;font-weight:600;line-height:1.3;letter-spacing:-0.02em;color:#fff;padding:0 24px}}
.quote:before{{content:"“";display:block;font-size:160px;line-height:0.8;color:{t['iris-300']}}}
.who{{font-size:28px;color:{t['powder-200']};margin-top:40px;padding:0 24px}}
.dark .source{{color:{t['powder-200']}}}
</style></head><body class="{'dark' if dark else ''}"><div class="page">
{f'<div class="eyebrow">{_esc(card.eyebrow)}</div>' if card.eyebrow else ''}
{f'<h1>{_esc(card.headline)}</h1>' if card.headline else ''}
{f'<div class="sub">{_esc(card.subhead)}</div>' if card.subhead else ''}
{legend_html}
{body}
<div class="foot"><div class="source">{_esc(card.source)}</div><div class="logo">{logo}</div></div>
</div></body></html>"""


def render_png(html_doc: str, out: Path) -> Path:
    from playwright.sync_api import sync_playwright

    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.set_content(html_doc, wait_until="load")
        page.evaluate("document.fonts.ready")
        page.screenshot(path=str(out), full_page=False)
        browser.close()
    return out


# ------------------------------------------------------------------ public API
def column_chart(card: Card, labels: list[str], values: list[float], out: Path, unit: str = "",
                 highlight: int | None = None, root: Path = REPO_ROOT) -> tuple[Path, str]:
    t = load_tokens(root)
    svg = column_chart_svg(labels, values, t, unit, highlight)
    path = render_png(card_html(card, f'<div class="card">{svg}</div>', t, root), out)
    hi = highlight if highlight is not None else len(values) - 1
    alt = (f"Column chart: {card.headline}. " + "; ".join(f"{l}: {fmt_value(v, unit)}" for l, v in zip(labels, values))
           + f". Highlighted: {labels[hi]}. Source: {card.source}")
    return path, alt


def line_chart(card: Card, x_labels: list[str], series: dict[str, list[float]], out: Path, unit: str = "",
               root: Path = REPO_ROOT) -> tuple[Path, str]:
    t = load_tokens(root)
    svg = line_chart_svg(x_labels, series, t, unit)
    legend = [(n, t[c]) for n, c in zip(series, CATEGORICAL)] if len(series) > 1 else None
    path = render_png(card_html(card, f'<div class="card">{svg}</div>', t, root, legend), out)
    alt = f"Line chart: {card.headline}, {x_labels[0]} to {x_labels[-1]}. " + "; ".join(
        f"{n}: {fmt_value(v[0], unit)} to {fmt_value(v[-1], unit)}" for n, v in series.items()) + f". Source: {card.source}"
    return path, alt


def stat_card(card: Card, value: str, label: str, out: Path, context: str = "", root: Path = REPO_ROOT) -> tuple[Path, str]:
    t = load_tokens(root)
    body = (f'<div class="card"><div class="stat">{_esc(value)}</div><div class="stat-label">{_esc(label)}</div>'
            + (f'<div class="stat-context">{_esc(context)}</div>' if context else "") + "</div>")
    path = render_png(card_html(card, body, t, root), out)
    return path, f"{value} {label}. {context} Source: {card.source}".strip()


def quote_card(quote: str, who: str, out: Path, source: str = "", root: Path = REPO_ROOT) -> tuple[Path, str]:
    t = load_tokens(root)
    body = (f'<div style="flex:1;display:flex;flex-direction:column;justify-content:center">'
            f'<div class="quote">{_esc(quote)}</div><div class="who">{_esc(who)}</div></div>')
    path = render_png(card_html(Card(source=source), body, t, root, dark=True), out)
    return path, f"Quote: “{quote}” — {who}"


def render_spec(spec: dict, out: Path, root: Path = REPO_ROOT) -> tuple[Path, str]:
    """Render from a YAML/JSON spec (see brand/visuals/README.md)."""
    card = Card(**{k: spec.get(k, "") for k in ("eyebrow", "headline", "subhead", "source")})
    kind = spec["type"]
    if kind == "column":
        return column_chart(card, spec["labels"], spec["values"], out, spec.get("unit", ""), spec.get("highlight"), root)
    if kind == "line":
        return line_chart(card, spec["x_labels"], spec["series"], out, spec.get("unit", ""), root)
    if kind == "stat":
        return stat_card(card, spec["value"], spec["label"], out, spec.get("context", ""), root)
    if kind == "quote":
        return quote_card(spec["quote"], spec["who"], out, spec.get("source", ""), root)
    raise ValueError(f"Unknown visual type: {kind}")
