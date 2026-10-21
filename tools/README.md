# Tools for the weekly content pack

- `render.py slides.json OUTDIR FONTDIR`: renders 1080×1350 PNG slides with the Albanian with Elisa logo.
  Slide types: `hook` {title, sub}, `phrase` {when, sq, say, en, tip}, `word` {when, sq, say, en, tip} (word of the day), `cta` {title, sub, small}.
  FONTDIR needs: playfair-display-latin-600-normal.woff2, playfair-display-latin-400-italic.woff2, inter-latin-500-normal.woff2,
  inter-latin-600-normal.woff2, pinyon-script-latin-400-normal.woff2, jost-latin-500-normal.woff2
  (npm pack @fontsource/playfair-display @fontsource/inter @fontsource/pinyon-script @fontsource/jost).
- `build_approval.py week.json OUTDIR`: builds the weekly review page (see the docstring for week.json).

## story.py (added 21 Oct 2026)
`python3 tools/story.py FRAMES.json OUTDIR FONTDIR` renders 1080x1920 story frames (photo, count, phone, art, text). Frame fields are documented at the top of the file. Backgrounds: `bank/` (see `bank/bank.json`; e01–e04 are Elisa, b01–b26 places and moods).

## motion.py (added 21 Oct 2026)
`python3 tools/motion.py SPEC.json OUT.mp4 FONTDIR` renders short vertical videos (30 fps) frame by frame: photo scenes with a slow zoom, a phone mockup scrolling a full-page screenshot or showing slides, and a red end card. Spec format at the top of the file.
