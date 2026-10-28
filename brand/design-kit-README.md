Stairpay is a free service for shared owners in England: it helps residents understand their home, track its costs, buy a bigger share (staircasing) or sell. The brand is calm, clear and reassuring: deep indigo on a light ground, generous space, Poppins throughout, soft rounded cards and pill-shaped buttons.

## Voice

- Write in plain English, to the reader: "your home", "your share", "your costs".
- Keep sentences short. Explain a term the first time it appears (staircasing = buying a bigger share of your home).
- Headlines are sentence case and short; a full stop is fine on a statement ("Shared ownership, simplified.").
- British English and pounds: £129,850, 45%, "per month".
- Reassure, never hype: no exclamation marks, no emoji, no urgency, no superlatives.
- Stay factual. Stairpay gives information, not financial or legal advice; never promise outcomes.

## Colour

- Ground: `color-bg-page` (neutral-50). Cards: `color-bg-surface` (white) with a 1px `color-border-default` hairline.
- Ink: `color-text-primary` (iris-600) for headlines, figures and labels; `neutral-700` for body copy; `color-text-secondary` for captions and meta.
- Brand panel: `iris-600` as a full-bleed band or a `radius-3xl` panel. On it use `color-text-on-brand` for headlines, `powder-200` for body copy and `iris-200` or `iris-300` for accents. `iris-400` on `iris-600` only at 24px and up.
- Accent: `iris-400` is the single accent: links, progress fills, a highlight figure, the focus ring, the offset shadow. One accent moment per view.
- Tints: `color-bg-tint-brand` (iris-100) behind eyebrow pills (`iris-500` text) and highlighted stat cards (1px `iris-200` border).
- Status: pair each tint with its text token (green-100 + green-500, blue-100 + blue-500, yellow-100 + yellow-600, red-100 + red-500). Always say the status in words too: red-400 and green-500 differ by hue, not lightness.
- The powder, rice and slate scales are defined but barely used on the site. Keep them for chart series, never as new brand colours.
- No gradients, no pure black, no colour-only meaning.

## Type

- One family: Poppins, in four weights. 400 body, 500 buttons, 600 sub-heads and labels, 700 headlines and figures.
- Headlines are tight: tracking -0.02em to -0.03em, line height 1.05 to 1.2 (`display`, `heading-xl`, `heading-lg`, `heading`). Body text breathes at 1.55 to 1.6 (`lead`, `body`).
- One `display` per page or slide. Section titles use `heading`; card titles `card-title` or `heading-sm`.
- Figures use `stat` or `figure`: always with £ or %, thousands separators and a `caption` label above or below.
- Eyebrows: the `eyebrow` style in a pill (`iris-500` on `iris-100`, padding `space-6` `space-14`, `radius-full`), above a headline.

## Shape, space and depth

- Nothing is square. Buttons, eyebrows and progress bars are pills (`radius-full`); cards and photos `radius-lg`; list cards and soft panels `radius-xl`; large indigo panels `radius-3xl`.
- Cards are padded `space-24` (list cards `space-28`); cards in a grid sit `space-16` apart. Sections breathe: `space-56` to `space-80` top and bottom, `space-48` side gutters.
- Shadows are soft and indigo-tinted: `shadow-xs` for list cards, `shadow-md` for floating stat cards, `shadow-pill` for primary buttons.
- The signature move is `shadow-offset`: one white featured card (`radius-2xl`) on an `iris-600` panel, with a solid `iris-400` block offset 12px down and right. Use it once per view at most.
- Keyboard focus uses `color-border-focus` (iris-400), 5.1:1 on white.

## Patterns

There is no component code in this system yet; these are the site's recurring pieces, described so they can be rebuilt exactly.

- Primary button: `radius-full`, `color-accent-brand` fill, `color-text-on-brand` label in `button`, padding 14px 26px, `shadow-pill`. On an iris-600 panel the button flips to a white fill with an iris-600 label at weight 600.
- Eyebrow pill: see Type.
- Stat card: white, 1px `color-border-default`, `radius-lg`, padding 16px 20px, `shadow-md`. A `caption` label, then the value in `figure`.
- Highlighted stat card: `iris-100` fill, 1px `iris-200` border, `radius-lg`; an uppercase `caption` label, the value in `stat`, a progress bar under it.
- Progress bar: a `radius-full` track in `neutral-100`, filled with `iris-400` to the share owned.
- List card: white, 1px border, `radius-xl`, padding `space-28`, `shadow-xs`; an icon tile on the left, a `heading-sm` title and a `body` line.

## Logos

- On light grounds use `stairpay-wordmark-indigo.svg`; on `iris-600` use `stairpay-wordmark-white.svg`. Where space is tight, use the mark alone (`stairpay-mark-indigo.svg` or `stairpay-mark-white.svg`).
- Never recolour the logo beyond indigo and white, stretch it, outline it or add effects. Give it clear space on every side.
- `stairpay-staircase-icon.svg` is the site's favicon silhouette (ink #0a0118).
- `stairpay-wordmark-on-indigo.png` and `stairpay-staircase-3d.jpg` are low-resolution originals; use them only small, never as the main logo.

## Iconography

- The site uses simple single-colour line icons sitting in small rounded lilac tiles. Those icons are not included here; substitute a plain line icon in `iris-600` on an `iris-100` tile (`radius-sm`), and never use emoji.

## Imagery

- Warm, natural photography of residents at home: real rooms, daylight, people doing everyday things. Crop photos to `radius-lg` corners. No staged office handshakes, no illustrations of houses with coins.

## Slides (1920 × 1080)

- Grounds: `color-bg-page` for content slides; `iris-600` for the cover, section dividers and one statement slide. White cards on the light ground.
- Type scale: 120px `display`-style headline for the cover only; 72px slide titles (700, -0.03em); 44px sub-heads (600 or 700, -0.02em); 32px body (400, neutral-700); 24px captions and footers (400, `color-text-secondary`). Nothing smaller than 24px.
- One eyebrow pill above a slide title, at 24px. One `iris-400` accent moment per slide.
- Big numbers: 120 to 160px Poppins 700, `iris-600` (or `iris-400` on light grounds), with a 24px caption label.
- Logo: white wordmark on `iris-600` slides, indigo wordmark on light slides, small, in the footer row.
- Cards on slides use `radius-xl` or larger; panels `radius-3xl`. Use `shadow-offset` on at most one slide.
