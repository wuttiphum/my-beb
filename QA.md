# Verification — Tk typography and sizing correction

Browser: headed Chromium through Playwright CLI (IAB unavailable).
Reference: the current python/heart.py on the original Mac, with Tk scaling
1.000750469043152. Python source was not modified.

## Reproduced problems

The first browser port substituted Sarabun for Sukhumvit Set/Avenir Next,
used regular instead of bold lettering, measured text in the substitute font,
and fitted the heart to a grid cell after header/footer space was removed.
Those choices changed typography, packing, heart scale and placement.

## Corrections checked

- Fixed animation text rasterized with CoreText using Sukhumvit Set,
  Avenir Next and italic Times New Roman, at four times the reference size.
  No proprietary font files are shipped. Sarabun remains only as a fallback
  for browser controls, which have no original Tk counterpart.
- Desktop canvas uses the full window, unit=min(width/1000,height/900),
  heart scale=18.5*unit, center=(width/2,height*.47), and original copy anchors.
- Native Tk bold font measurements and line spacing drive word packing.
- Original seeded stars, dust, glow layers and pink word gradient restored.
- Small/short screens retain a proportional fit and visible touch controls.
  Landscape closing text was visually checked after fixing an overlap.

## Original viewport-dependent baseline (before fixed layout)

All word strings, positions, widths and integer font sizes compared against
LoveUniverse.prepare_fill(), called directly in the original Tk interpreter.

| Window | Words (both implementations) | Fill point size |
| --- | ---: | ---: |
| 1000x900 | 193 | 9 |
| 1280x720 | 191 | 7 |
| 1920x1080 | 222 | 10 |
| 1998x1588 | 215 | 15 |
| 768x1024 | 242 | 6 |

Maximum coordinate difference: 3.56e-15 heart units (floating point rounding).
All 20 languages present at every size above.

## Browser checks

- 320x568, 390x844 and 844x390: no page overflow, all controls fit, all 20
  languages present; checked intro, writing, galaxy, name, return and finale.
- Visually inspected desktop intro, galaxy, Love Ang, return, final heart,
  and portrait/landscape phone final states.
- Forcing a different CSS font leaves paused canvas pixels unchanged.
- Pause freezes playback; replay restarts and unpauses.
- No page errors in the checked flows; node --check dist/app.js passes.
- On this Mac, 180 requestAnimationFrame intervals sampled across the galaxy
  transition: median 8.3ms, p95 8.4ms, maximum 9.3ms. This is a local observation,
  not a frame-rate guarantee for other hardware.

The original 1000x900 reference geometry is matched numerically. CoreText/Tk antialiasing and
raster scaling can still differ slightly. Phones intentionally use an adapted
fit; accessible DOM copies remain available to screen readers.

## Consistent interior layout

The interior now uses the native 1000x900 layout at a 9-point reference size
for all viewports. Word widths, line spacing, and pen distances are computed in
heart coordinates; font size is 9*unit with no integer rounding. This replaces
the viewport-dependent counts in the historical table above. The expected
current count is 193 words at every viewport, with the same normalized word
positions, order, writing path and timing. Heart projection still fits the
viewport, and small screens retain their existing fit and touch controls.

Verified fixed layout at 1000x900, 1512x950, 1512x840, 1920x1080,
1280x720, 768x1024, 600x840, 599x840, 390x844, 320x568 and 844x390.
All had identical normalized word arrays (193 words, 20 languages), a constant
9-point reference font ratio, and the same pen position at t=20. Resizing during
playback preserved progress. Fullscreen entry through the real button and exit
with Escape preserved both layout and progress; Escape is handled even while
that button retains focus.
