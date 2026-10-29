# On-brand visuals

Charts and cards for Floris's posts, rendered by code from real numbers using `brand/tokens.json` and Poppins (`brand/fonts/`, open font licence). Output: 4:5 portrait PNG (LinkedIn's tallest feed format), laid out at 1080x1350 and rendered at 2x (2160x2700) so text stays sharp; plus alt text to paste into LinkedIn.

```bash
founder-engine visual brand/visuals/examples/column-growth.yaml out.png
```

| Type | Use for | Example |
|---|---|---|
| `column` | One measure over time or across groups (data posts) | `examples/column-growth.png` |
| `line` | Trends; up to 4 series | `examples/line-staircasing.png` |
| `stat` | One number that carries the post | `examples/stat-caps.png` |
| `quote` | Floris's exact words (from a transcript, with his OK) | `examples/quote.png` |

The example charts use **dummy numbers** and say so.

## Spec fields
- All: `eyebrow` (pill above the headline), `headline`, `subhead`, `source` (always state source, period and sample size)
- `column`: `labels`, `values`, `unit` (`£`, `%` or blank), optional `highlight` (index; defaults to the last column)
- `line`: `x_labels`, `series` (name: values), `unit`
- `stat`: `value` (as it should read, e.g. "£110k"), `label`, `context`
- `quote`: `quote`, `who`

## Standards for every asset (owner, 2026-10-29)
1. **Double size, always.** Lay out at the platform size, render at 2x (LinkedIn 4:5: 2160x2700). PNG. Never ship a 1x export.
2. **Breathing room.** Generous space between number, heading and supporting line; balanced line breaks (no single word or "from £90k" stranded on its own line); nothing crowding the edges.
3. **Natural phrasing.** Supporting text reads like a person wrote it: one flowing sentence beats two clipped ones ("Outside London the cap rises from £80k to £90k, the first change since 2016." not "...to £90k. First change since 2016.").
4. **Best design practice.** One message per visual, clear hierarchy (number, then label, then context), brand kit colours and type, and look at the rendered file before it goes out.

## Rules (from the design kit and the data-viz checks)
- One series: indigo (iris-600) with one violet (iris-400) highlight. Several series, in this order: iris-400, rice-500, powder-400, slate-300. This set passed the colour-blind, lightness and contrast checks on 2026-10-28. More than 4 series: fold into "Other" or split the chart.
- Columns start at zero. One axis only. Selective labels (highlight, latest, maximum), not a number on every bar.
- A legend whenever there are 2+ series, plus direct end labels.
- Every published figure must trace to an approved, anonymised query (`data/DATA_CONTRACT.md`). Never use an image model for charts.
