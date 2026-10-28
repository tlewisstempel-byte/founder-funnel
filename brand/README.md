# Brand assets for generated visuals

Source of truth: the Stairpay design kit, https://claude.ai/artifact/CF5UhbgmPgd5BbA8Jha4cA. This folder holds a copy of the machine-readable parts so code and other LLMs can use them without access to the kit.

## Files
- `tokens.json`: colours, type, spacing, radius and shadows (copied as published; keep in sync with the kit)
- `design-kit-README.md`: the kit's written guidelines (voice, colour, type, shape, patterns, logos, slides)
- `logos/`: wordmark and mark in indigo and white (SVG)

## Essentials for visuals
- Fonts: Poppins (400 body, 500 buttons, 600 labels, 700 headlines and figures). Poppins is an open-source Google font; download the files for rendering.
- Ground `neutral-50` (#f9f9fb), cards white with a 1px `neutral-200` hairline, ink `iris-600` (#1f0b56), single accent `iris-400` (#7847ff), body `neutral-700`.
- Logo: indigo on light grounds, white on `iris-600`; never recolour, stretch, outline or add effects. Clear space on every side.
- Nothing is square: cards `radius-lg` (20px) or more, pills `radius-full`.
- One accent moment per view. No gradients, no pure black, no colour-only meaning. Figures carry £ or %, thousands separators and a caption.
- Chart series: use the powder, rice and slate scales (the kit reserves them for charts); iris-600 for the main series, iris-400 as the one highlight. Run a contrast check on any new chart palette.
- Photography: warm, natural, real people at home or at work. No stock handshakes, no house-and-coin illustrations.

## Gaps
- No icon set, no component code and no chart template in the kit yet. Chart and card templates will be built here from the tokens.
- The kit's voice rules are consumer-facing; see `voice/company-page.md`.
