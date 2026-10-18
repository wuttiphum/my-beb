"""Export fixed text artwork and Tk metrics; never copy or distribute font files.

Run on the original Mac using its Tk-capable Python. Fixed text is rasterized
through CoreText at 4x resolution so Windows/Android do not substitute fonts.
"""
import importlib.util
import json
import math
import random
from pathlib import Path
import subprocess
import tempfile
import tkinter as tk
from tkinter import font as tkfont
import unicodedata
from PIL import Image

project = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("original_heart", project / "python/heart.py")
heart = importlib.util.module_from_spec(spec)
spec.loader.exec_module(heart)
root = tk.Tk()
root.withdraw()

def clusters(value):
    result = []
    for char in value:
        if result and unicodedata.category(char).startswith("M"):
            result[-1] += char
        else:
            result.append(char)
    return result

names = ["อัง", "Ang", "Nathaiinee Samoeton"]
prefixes = set()
for value in heart.PHRASES + names:
    prefix = ""
    for cluster in clusters(value):
        prefix += cluster
        prefixes.add(prefix)
        prefixes.add(cluster)

styles = {
    "fill": (heart.BODY_FONT, 9, True, False, sorted(prefixes)),
    "outline": (heart.BODY_FONT, 13, True, False, sorted(set(heart.NAME_LETTERS))),
    "body": (heart.BODY_FONT, 12, False, False, ["อัง", "every beat, always you.", heart.PERSONAL_MESSAGE]),
    "name": (heart.NAME_FONT, 66, False, True, ["Ang"]),
    "display": (heart.DISPLAY_FONT, 12, False, False, ["F O R  Y O U,  A N G"]),
    "promise": (heart.BODY_FONT, 25, True, False, ["ทุกภาษาแปลว่ารักอัง"]),
    "hint": (heart.BODY_FONT, 10, False, False, [
        "SPACE  pause   ·   R  replay   ·   CLICK  spark   ·   F11  fullscreen",
        "SPACE  resume   ·   R  replay   ·   CLICK  spark   ·   F11  fullscreen"]),
}
items = []
for role, (family, size, bold, italic, values) in styles.items():
    font = tkfont.Font(root=root, family=family, size=size,
                       weight="bold" if bold else "normal", slant="italic" if italic else "roman")
    for value in values:
        if value.strip():
            items.append(dict(role=role, text=value, family=family, size=size,
                              bold=bold, italic=italic, **font.metrics()))

metrics = {}
for size in range(6, 65):
    font = tkfont.Font(root=root, family=heart.BODY_FONT, size=size, weight="bold")
    metrics[str(size)] = dict(linespace=font.metrics("linespace"),
                             widths={value: font.measure(value) for value in sorted(prefixes)})

with tempfile.TemporaryDirectory(prefix="love-ang-text-") as temp:
    folder = Path(temp)
    (folder / "text.json").write_text(json.dumps(items, ensure_ascii=False))
    subprocess.run(["swift", str(project / "scripts/render-text.swift"),
                    str(folder / "text.json"), str(folder)], check=True)
    # Shelf packing keeps the atlas small; a single alpha mask serves all colors.
    cells, x, y, row_height = {}, 0, 0, 0
    images = []
    for index, item in enumerate(items):
        image = Image.open(folder / f"{index}.png").convert("RGBA")
        if x + image.width > 2048:
            x, y, row_height = 0, y + row_height + 2, 0
        advance = json.loads((folder / f"{index}.json").read_text())["advance"]
        cells[f"{item['role']}:{item['text']}"] = [x, y, image.width, image.height, item["size"], advance]
        images.append((image, x, y))
        x += image.width + 2
        row_height = max(row_height, image.height)
    atlas = Image.new("RGBA", (2048, y + row_height))
    for image, x, y in images:
        atlas.paste(image, (x, y))
    atlas.save(project / "dist/assets/tk-text.png", optimize=True)

rng = random.Random(14)
stars = [dict(x=rng.random(), y=rng.random(), r=rng.uniform(.6, 1.7), p=rng.random()*math.tau)
         for _ in range(125)]
dust = []
for _ in range(670):
    angle, radial = rng.uniform(0, math.tau), rng.random()**.44
    x, y = heart.heart(angle)
    dust.append(dict(x=x*radial, y=y*radial, r=rng.uniform(.7, 1.9), p=rng.random()*math.tau))
result = dict(density=4, cells=cells, fillMetrics=metrics, stars=stars, dust=dust,
              sourceFonts=dict(body=heart.BODY_FONT, display=heart.DISPLAY_FONT, name=heart.NAME_FONT),
              tkScaling=float(root.tk.call("tk", "scaling")))
(project / "dist/assets/tk-typography.json").write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
root.destroy()
print(f"Exported {len(cells)} fixed text sprites; atlas {atlas.width}x{atlas.height}")
