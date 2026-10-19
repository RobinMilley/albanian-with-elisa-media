# Tools for the weekly content pack

- `render.py slides.json OUTDIR FONTDIR`: renders 1080×1350 PNG slides with the Albanian with Elisa logo.
  Slide types: `hook` {title, sub}, `phrase` {when, sq, say, en, tip}, `word` {when, sq, say, en, tip} (word of the day), `cta` {title, sub, small}.
  FONTDIR needs: playfair-display-latin-600-normal.woff2, playfair-display-latin-400-italic.woff2, inter-latin-500-normal.woff2,
  inter-latin-600-normal.woff2, pinyon-script-latin-400-normal.woff2, jost-latin-500-normal.woff2
  (npm pack @fontsource/playfair-display @fontsource/inter @fontsource/pinyon-script @fontsource/jost).
- `build_approval.py week.json OUTDIR`: builds the weekly review page (see the docstring for week.json).
