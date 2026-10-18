"""Bake the web galaxy's clouds, dust lanes and stars once, never per frame.

Run with the Pillow environment used for the original Python animation.
The transparent disc rotates in its own plane before the browser projects it.
"""
import math
from pathlib import Path
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter


SIZE = 1536
FACE_RADIUS = SIZE * .43
rng = random.Random(932)


def smooth(value):
    value = max(0, min(1, value))
    return value * value * (3 - 2 * value)


def noise(scales):
    result = Image.new("L", (SIZE, SIZE))
    for resolution, strength in scales:
        layer = Image.frombytes("L", (resolution, resolution),
                                bytes(rng.randrange(256) for _ in range(resolution ** 2)))
        layer = layer.resize((SIZE, SIZE), Image.Resampling.BICUBIC)
        result = ImageChops.add(result, layer.point(lambda value: round(value * strength)))
    return result.tobytes()


clouds = noise([(15, .36), (38, .27), (95, .20), (240, .12), (620, .05)])
filaments = noise([(24, .35), (70, .30), (200, .23), (500, .12)])
pixels = bytearray()
for y in range(SIZE):
    for x in range(SIZE):
        gx, gy = (x - SIZE / 2) / FACE_RADIUS, (y - SIZE / 2) / FACE_RADIUS
        radius, theta = math.hypot(gx, gy), math.atan2(gy, gx)
        i = y * SIZE + x
        cloud, fine = clouds[i] / 255, filaments[i] / 255
        turbulence = .10 * math.sin(theta * 7 + radius * 18) + (cloud - .5) * .75
        spiral = theta - radius * 4.8 + turbulence
        arm = (.5 + .5 * math.cos(spiral * 2)) ** 5
        branches = (.5 + .5 * math.cos(spiral * 4 + radius * 7)) ** 12
        lane = (.5 + .5 * math.cos((spiral - .34 + (fine - .5) * .3) * 2)) ** 24
        threads = (.5 + .5 * math.cos((spiral - .53) * 4)) ** 22
        core = math.exp(-(radius / .12) ** 1.35)
        bulge = math.exp(-(radius / .29) ** 1.6)
        disc = math.exp(-radius * radius / .65)
        fade = 1 - smooth((radius - .91) / .23)
        attenuation = 1 - .92 * lane * smooth(radius / .23)
        attenuation *= 1 - .40 * threads * smooth(radius / .32)
        structure = (.05 * disc + .48 * arm * math.exp(-radius * 1.25)
                     + .08 * branches * disc) * (.18 + 1.7 * cloud)
        light = (structure + .88 * core + .24 * bulge) * attenuation * fade
        pale = min(1, core * 2 + bulge * .7)
        pixels.extend((min(255, round(light * 255)),
                       min(255, round(light * (117 + 138 * pale))),
                       min(255, round(light * (201 + 54 * pale)))))

emission = Image.frombytes("RGB", (SIZE, SIZE), bytes(pixels))
stars = Image.new("RGB", (SIZE, SIZE))
draw = ImageDraw.Draw(stars)
for i in range(95000):
    radius = rng.random() ** .60 * 1.12
    theta = ((i % 2) * math.pi + radius * 4.8 + rng.gauss(0, .17)
             if i % 5 else rng.uniform(0, math.tau))
    x = round(SIZE / 2 + math.cos(theta) * radius * FACE_RADIUS)
    y = round(SIZE / 2 + math.sin(theta) * radius * FACE_RADIUS)
    strength = min(.85, .026 * rng.paretovariate(1.65)) * (1 - smooth((radius - .92) / .20))
    tint = rng.choice([(255, 239, 250), (255, 157, 211), (212, 193, 255)])
    draw.point((x, y), fill=tuple(round(channel * strength) for channel in tint))

# Uneven star-forming knots follow the arms; their glow is baked into the disc.
knots = Image.new("RGB", (SIZE, SIZE))
draw = ImageDraw.Draw(knots)
for i in range(240):
    radius = rng.uniform(.28, .94)
    theta = (i % 2) * math.pi + radius * 4.8 + rng.gauss(0, .10)
    x = SIZE / 2 + math.cos(theta) * radius * FACE_RADIUS
    y = SIZE / 2 + math.sin(theta) * radius * FACE_RADIUS
    spread = rng.uniform(1.1, 4.5)
    draw.ellipse((x - spread, y - spread, x + spread, y + spread),
                 fill=rng.choice([(44, 19, 38), (35, 29, 45), (47, 31, 42)]))
emission = ImageChops.add(emission, knots.filter(ImageFilter.GaussianBlur(3)))
emission = ImageChops.add(emission, stars.filter(ImageFilter.GaussianBlur(1.2)))
emission = ImageChops.add(emission, stars)

# Store straight alpha so compositing over the night sky preserves faint light.
rgba = bytearray()
for color in emission.get_flattened_data():
    alpha = max(color)
    rgba.extend([round(channel * 255 / alpha) if alpha else 0 for channel in color] + [alpha])
output = Path(__file__).resolve().parents[1] / "dist/assets/galaxy.png"
Image.frombytes("RGBA", (SIZE, SIZE), bytes(rgba)).save(output, optimize=True)
print(f"Exported {SIZE}×{SIZE} galaxy: {output.stat().st_size:,} bytes")
