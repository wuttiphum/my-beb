# Love Ang ♡

A pink universe for Ang: names trace a heart, fill it with love in 20 languages,
become a rotating galaxy, gather into **Love Ang**, then return to the heart.

## Web version

The deployed website is the static content in `dist/`. It requires no build,
package install, backend, or environment variables.

```sh
python3 -m http.server 4173 --directory dist
```

Open http://localhost:4173. Use the buttons or Space to pause, R to replay,
and touch/click for sparks. Small screens adapt the layout; desktop geometry
and text measurements follow the original Tk animation. Interior lettering uses
one fixed 1000x900 reference layout, so resizing/fullscreen preserves word order,
spacing, and writing progress while scaling the heart as a whole.

`vercel.json` configures **Other**, an empty build/install command, and `dist`
as the output directory. Import this repository into Vercel with the repository
root as Root Directory and `main` as the production branch.

## Original Python version

```sh
python3 -m pip install -r python/requirements.txt
python3 python/heart.py
```

Requires a Python installation with Tkinter support and Pillow. On the original
Mac, the Tk-capable interpreter is
`/Library/Frameworks/Python.framework/Versions/3.13/bin/python3`.

## Typography

The web animation uses transparent text artwork rendered from Sukhumvit Set,
Avenir Next and italic Times New Roman on the original Mac, plus measured Tk
text widths and line spacing. Visitors do not need those system fonts. No
proprietary font files are included. Sarabun is an OFL fallback for touch controls.
The web galaxy uses a 1536px procedural texture with baked spiral dust lanes,
star-forming knots and 95,000 stars. Only 96 accent stars twinkle dynamically,
keeping the finer detail out of the animation's per-frame generation work.
Regenerate it with the same Pillow environment:

```sh
python3 scripts/export-galaxy.py
```

After changing fixed text, regenerate the artwork on the original Mac:

```sh
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 scripts/export-tk-typography.py
```

Also update `dist/assets/animation-data.json` when animation copy changes.
See `QA.md` for the native layout comparison and browser verification.

## Layout regression checks

```sh
node --test tests/heart-layout.test.mjs
```

These checks use the actual heart geometry and exported font measurements to
catch skipped interior regions, words crossing the notch or border, overlap,
and missing languages. The clipper fills both lobes when a text band splits
at the notch. It keeps the same fixed layout when the viewport changes.
