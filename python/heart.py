"""A little universe of love. Requires Python 3, Tkinter and Pillow."""
import math
import random
import time
import tkinter as tk
import unicodedata
from bisect import bisect_right
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from tkinter import font as tkfont
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageTk

BACKGROUND = "#080611"
BODY_FONT = "Sukhumvit Set"
DISPLAY_FONT = "Avenir Next"
NAME_FONT = "Times New Roman"
HEART_SCALE = 18.5
DRAW_SECONDS = 14.0
FILL_START = DRAW_SECONDS + .5
FILL_SECONDS = 10.0
FILL_END = FILL_START + FILL_SECONDS
BURST_START = FILL_END + 1.5
GATHER_START = BURST_START + 8.0
GATHER_END = GATHER_START + 4.0
RETURN_START = GATHER_END + 7.0
RETURN_END = RETURN_START + 6.0
TARGET_FPS = 60
PERSONAL_MESSAGE = "จากทุกดวงดาวในจักรวาล ดีใจที่สุดที่ได้เจออัง 𑣲◡̈"
PERSONAL_MESSAGE_START = RETURN_END + 3.4


def ease(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


def cubic_point(start, control1, control2, end, progress):
    remaining = 1 - progress
    return tuple(remaining ** 3 * a + 3 * remaining ** 2 * progress * b
                 + 3 * remaining * progress ** 2 * c + progress ** 3 * d
                 for a, b, c, d in zip(start, control1, control2, end))


def writing_progress(elapsed):
    """Brief soft start/stop with a steady writing speed in between."""
    elapsed = max(0.0, min(FILL_SECONDS, elapsed))
    ramp = 1.2
    distance = FILL_SECONDS - ramp
    if elapsed < ramp:
        return elapsed * elapsed / (2 * ramp * distance)
    if elapsed > FILL_SECONDS - ramp:
        remaining = FILL_SECONDS - elapsed
        return 1 - remaining * remaining / (2 * ramp * distance)
    return (elapsed - ramp / 2) / distance

# Keep the Thai vowel attached to its consonant when drawing letters.
NAME_LETTERS = (
    ["อั", "ง", " ", "♥︎", " "]
    + list("Ang ")
    + ["𑣲◡̈", " "]
    + list("Nathaiinee ")
    + ["ᯓᰔ", " "]
    + list("Samomoeton ")
    + ["ᰔᩚ", " ", "อั", "ง", " ", "𑣲𝑨", " "]
)
PHRASES = [
    "รักอังนะ", "I love you, Ang", "Je t'aime, Ang", "Te amo, Ang",
    "Ti amo, Ang", "Ich liebe dich, Ang", "愛してる, Ang", "사랑해, Ang",
    "我爱你，Ang", "Eu te amo, Ang", "Я тебя люблю, Ang", "Seni seviyorum, Ang",
    "Aku cinta kamu, Ang", "Mahal kita, Ang", "Tôi yêu bạn, Ang",
    "Ik hou van jou, Ang", "Jag älskar dig, Ang", "Kocham cię, Ang",
    "Te iubesc, Ang", "Miluji tě, Ang",
]


@lru_cache(maxsize=1024)
def rgb(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def blend(color, amount, base=BACKGROUND):
    """Fade an RGB color into the night."""
    if amount <= 0:
        return base
    if amount >= 1:
        return color
    a, b = rgb(color), rgb(base)
    return "#" + "".join(f"{int(y + (x - y) * amount):02x}" for x, y in zip(a, b))


def heart(t):
    return (16 * math.sin(t) ** 3,
            13 * math.cos(t) - 5 * math.cos(2 * t)
            - 2 * math.cos(3 * t) - math.cos(4 * t))


class GalaxyTexture:
    """Rotate the entire dusty stellar disc before projecting its inclination."""
    INCLINATION = .36
    TILT = -.27
    ROTATION_SPEED = .21

    def __init__(self, root):
        self.root = root
        self.width = 640
        self.face_radius = self.width * .43
        rng = random.Random(932)
        size = self.width
        # Several noise scales make mottled clouds, rather than clean spiral lines.
        noise = Image.new("L", (size, size), 0)
        for resolution, strength in [(12, .37), (30, .30), (80, .21), (190, .12)]:
            layer = Image.frombytes("L", (resolution, resolution),
                                    bytes(rng.randrange(256) for _ in range(resolution ** 2)))
            layer = layer.resize((size, size), Image.Resampling.BICUBIC)
            noise = ImageChops.add(noise, layer.point(lambda v: round(v * strength)))
        clouds = noise.tobytes()
        pixels = bytearray()
        for y in range(size):
            for x in range(size):
                gx, gy = (x - size / 2) / self.face_radius, (y - size / 2) / self.face_radius
                r = math.hypot(gx, gy)
                theta = math.atan2(gy, gx)
                cloud = clouds[y * size + x] / 255
                turbulence = .11 * math.sin(theta * 7 + r * 18) + (cloud - .5) * .65
                spiral = theta - r * 4.8 + turbulence
                arm = (.5 + .5 * math.cos(spiral * 2)) ** 3
                dust = (.5 + .5 * math.cos((spiral - .4) * 2)) ** 14
                core = math.exp(-(r / .16) ** 1.5)
                bulge = math.exp(-r * 5)
                disc = math.exp(-r * r / .8)
                light = .065 * disc + .35 * arm * math.exp(-r * 1.5) + .95 * core + .20 * bulge
                light *= (1 - .84 * dust * ease(r / .22)) * (.30 + 1.35 * cloud)
                light *= 1 - ease((r - .95) / .24)
                pale = min(1, core * 1.5 + bulge * .4)
                pixels.extend((min(255, round(light * 255)),
                               min(255, round(light * (105 + 140 * pale))),
                               min(255, round(light * (195 + 60 * pale)))))
        emission = Image.frombytes("RGB", (size, size), bytes(pixels))
        stars = Image.new("RGB", (size, size))
        draw = ImageDraw.Draw(stars)
        for i in range(18000):
            r = rng.random() ** .60 * 1.13
            theta = ((i % 2) * math.pi + r * 4.8 + rng.gauss(0, .20)
                     if i % 4 else rng.uniform(0, math.tau))
            x = round(size / 2 + math.cos(theta) * r * self.face_radius)
            y = round(size / 2 + math.sin(theta) * r * self.face_radius)
            strength = min(1, .025 * rng.paretovariate(1.65)) * (1 - ease((r - .93) / .2))
            tint = rng.choice([(255, 235, 250), (255, 161, 210), (191, 181, 255)])
            color = tuple(round(channel * strength) for channel in tint)
            draw.point((x, y), fill=color)
        emission = ImageChops.add(emission, stars)
        emission = ImageChops.add(emission, stars.filter(ImageFilter.GaussianBlur(1.1)))
        rgba = bytearray()
        for color in emission.get_flattened_data():
            alpha = min(1, max(color) / 255)
            if alpha < .004:
                rgba.extend((0, 0, 0, 0))
            else:
                rgba.extend([min(255, round(c / alpha)) for c in color] + [round(alpha * 255)])
        # Premultiplied alpha avoids dark fringes when rotating and resampling.
        self.face = Image.frombytes("RGBA", (size, size), bytes(rgba)).convert("RGBa")
        self.radius = 0
        self.frame_key = None
        self.photo = None
        self.worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="galaxy")
        self.pending = None

    def reset(self):
        if self.pending is not None:
            self.pending[0].cancel()
        self.pending = None
        self.frame_key = None
        self.photo = None

    def resize(self, radius):
        radius = round(radius)
        if radius == self.radius:
            return
        self.radius = radius
        # The inclined disc fits this tighter rectangle; avoid uploading empty pixels.
        self.output_size = (max(1, round(radius * 2.4)), max(1, round(radius * 1.12)))
        self.reset()

    def render(self, age, alpha, geometry=None):
        # Rotate in the galaxy's own plane; keep the camera tilt fixed.
        phase = age * self.ROTATION_SPEED
        cp, sp = math.cos(phase), math.sin(phase)
        ct, st = math.cos(self.TILT), math.sin(self.TILT)
        output_size, radius = geometry or (self.output_size, self.radius)
        scale = self.face_radius / radius
        a = scale * (cp * ct - sp * st / self.INCLINATION)
        b = scale * (cp * st + sp * ct / self.INCLINATION)
        d = scale * (-sp * ct - cp * st / self.INCLINATION)
        e = scale * (-sp * st + cp * ct / self.INCLINATION)
        w, h = output_size
        c = self.width / 2 - a * w / 2 - b * h / 2
        f = self.width / 2 - d * w / 2 - e * h / 2
        frame = self.face.transform(output_size, Image.Transform.AFFINE,
                                    (a, b, c, d, e, f), Image.Resampling.BILINEAR).convert("RGBA")
        if alpha < 1:
            frame.putalpha(frame.getchannel("A").point(lambda v: round(v * alpha)))
        return frame

    def draw(self, canvas, x, y, alpha, age):
        if alpha <= 0:
            return
        # Pillow runs off the UI thread. Only the completed frame's Tk upload
        # happens here; never wait for an unfinished render in the event loop.
        key = (round(age * TARGET_FPS), self.output_size)
        if self.pending is not None and self.pending[0].done():
            future, completed_key = self.pending
            frame = future.result()
            self.pending = None
            if self.photo is None:
                self.photo = ImageTk.PhotoImage(frame, master=self.root)
            else:
                self.photo.paste(frame)
            self.frame_key = completed_key
        if self.pending is None and key != self.frame_key:
            geometry = (self.output_size, self.radius)
            self.pending = (self.worker.submit(self.render, key[0] / TARGET_FPS, alpha, geometry), key)
        if self.photo is not None:
            canvas.create_image(x, y, image=self.photo, tags="frame")


class LoveUniverse:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("For Ang — Nathaiinee Samoeton")
        self.root.geometry("1000x900")
        self.root.minsize(600, 640)
        self.canvas = tk.Canvas(self.root, bg=BACKGROUND, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.rng = random.Random(14)
        self.width, self.height = 1000, 900
        self.elapsed = 0.0
        self.last_frame = time.perf_counter()
        self.next_frame = self.last_frame
        self.paused = False
        self.fullscreen = False
        self.bursts = []
        self.rings = []
        self.last_beat = -1
        self.scene_alpha = 1.0
        self.stars = [(self.rng.random(), self.rng.random(),
                       self.rng.uniform(.6, 1.7), self.rng.random() * math.tau)
                      for _ in range(125)]
        self.dust = []
        for _ in range(670):
            angle = self.rng.uniform(0, math.tau)
            radial = self.rng.random() ** .44
            x, y = heart(angle)
            self.dust.append((x * radial, y * radial,
                              self.rng.uniform(.7, 1.9), self.rng.random() * math.tau))
        self.outline = [heart(i / 200 * math.tau) for i in range(201)]
        # Equal spacing keeps individual letters legible around the curve.
        curve = [heart(i / 1200 * math.tau) for i in range(1201)]
        distances = [0.0]
        for previous, point in zip(curve, curve[1:]):
            distances.append(distances[-1] + math.hypot(
                point[0] - previous[0], point[1] - previous[1]))
        self.name_letters = []
        total = len(NAME_LETTERS) * 4
        cursor = 0
        for i in range(total):
            distance = (i / total) * distances[-1]
            while cursor < len(curve) - 1 and distances[cursor] < distance:
                cursor += 1
            x, y = curve[cursor]
            self.name_letters.append((x, y, NAME_LETTERS[i % len(NAME_LETTERS)]))
        self.galaxy_texture = GalaxyTexture(self.root)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.prepare_fill()
        self.canvas.bind("<Configure>", self.resize)
        self.canvas.bind("<Button-1>", self.spark)
        self.root.bind("<space>", self.toggle_pause)
        self.root.bind("r", self.replay)
        self.root.bind("R", self.replay)
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)
        # Let the window manager map the window before requesting foreground.
        self.root.after(150, self.show_window)

    def show_window(self):
        self.root.deiconify()
        self.fullscreen = True
        self.root.attributes("-fullscreen", True)
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.focus_force()
        # Raise only at startup; afterwards other apps can cover it normally.
        self.root.after(500, lambda: self.root.attributes("-topmost", False))
        self.last_frame = time.perf_counter()
        self.next_frame = self.last_frame
        self.draw_frame()

    def close(self):
        self.galaxy_texture.worker.shutdown(wait=False, cancel_futures=True)
        self.root.destroy()

    def resize(self, event):
        self.width, self.height = event.width, event.height
        self.prepare_fill()

    def prepare_fill(self):
        """Pack measured names and all 20 love notes inside the heart."""
        unit = min(self.width / 1000, self.height / 900)
        scale = max(.1, HEART_SCALE * unit)
        self.fill_size = max(6, int(9 * unit))
        font = tkfont.Font(root=self.root, family=BODY_FONT,
                           size=self.fill_size, weight="bold")
        half_height = font.metrics("linespace") / scale / 2

        def spans(y):
            crossings = []
            for (x1, y1), (x2, y2) in zip(self.outline, self.outline[1:]):
                if (y1 <= y < y2) or (y2 <= y < y1):
                    crossings.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
            crossings.sort()
            return list(zip(crossings[::2], crossings[1::2]))

        self.fill_words = []
        self.fill_widths = []
        phrase_index = 0
        name_index = 0
        names = ["อัง", "Ang", "Nathaiinee Samoeton", "Ang", "อัง"]
        y = max(py for _, py in self.outline) - half_height - .5
        while y > -17 + half_height + .5:
            for left, right in spans(y):
                # At the notch the row can split into two lobes. Keep all
                # safe intersections rather than dropping the shorter lobe.
                segments = [(left, right)]
                for edge_y in (y - half_height, y + half_height):
                    segments = [(max(left, a), min(right, b))
                                for left, right in segments for a, b in spans(edge_y)
                                if max(left, a) < min(right, b)]
                for left, right in segments:
                    x = left + .55
                    right -= .55
                    while x < right:
                        phrase = PHRASES[phrase_index % len(PHRASES)]
                        want_phrase = len(self.fill_words) % 2 == 0
                        value = phrase if want_phrase else names[name_index % len(names)]
                        width = font.measure(value) / scale
                        if x + width > right:
                            value = "อัง" if name_index % 2 == 0 else "Ang"
                            width = font.measure(value) / scale
                        if x + width > right:
                            break
                        self.fill_words.append((x + width / 2, y, value))
                        self.fill_widths.append(width)
                        if value == phrase:
                            phrase_index += 1
                        else:
                            name_index += 1
                        x += width + .45
            y -= half_height * 2 + .28

        # Measure a continuous pen path, including travel between lines.
        self.fill_starts = []
        self.fill_ends = []
        self.fill_prefixes = []
        distance = 0.0
        previous = None
        for (x, y, value), width in zip(self.fill_words, self.fill_widths):
            left = x - width / 2
            if previous is not None:
                distance += math.hypot(left - previous[0], y - previous[1])
            self.fill_starts.append(distance)
            distance += width
            self.fill_ends.append(distance)
            previous = (left + width, y)
            # Keep Thai vowels/tone marks attached; render whole prefixes so
            # the font can still shape each script correctly.
            clusters = []
            for char in value:
                if clusters and unicodedata.category(char).startswith("M"):
                    clusters[-1] += char
                else:
                    clusters.append(char)
            prefixes = []
            prefix = ""
            for cluster in clusters:
                prefix += cluster
                prefixes.append((prefix, font.measure(prefix) / scale))
            self.fill_prefixes.append(prefixes)
        self.fill_length = distance
        self.prepare_finale()
        self.galaxy_texture.resize(min(self.width * .42, 470 * unit))

    def prepare_finale(self):
        """Give each heart letter a stable star destination and name destination."""
        sources = [(x, y, char, 13) for x, y, char in self.name_letters if not char.isspace()]
        origins = [("outline", index) for index, (_, _, char) in enumerate(self.name_letters)
                   if not char.isspace()]
        for word_index, ((x, y, _), width, prefixes) in enumerate(zip(self.fill_words, self.fill_widths, self.fill_prefixes)):
            previous_width = 0
            previous_text = ""
            for prefix, prefix_width in prefixes:
                char = prefix[len(previous_text):]
                if not char.isspace():
                    sources.append((x - width / 2 + (previous_width + prefix_width) / 2,
                                    y, char, self.fill_size))
                    origins.append(("word", word_index))
                previous_width, previous_text = prefix_width, prefix

        # Curved letter strokes for the constellation's A, n and g.
        strokes = [
            [(0, 60), (22, 0), (44, 60)], [(9, 37), (35, 37)],
            [(58, 60), (58, 24)],
            [cubic_point((58, 42), (58, 17), (94, 17), (94, 42), i / 50)
             for i in range(51)] + [(94, 60)],
            [(124 + 18 * math.cos(i / 70 * math.tau),
              42 + 19 * math.sin(i / 70 * math.tau)) for i in range(71)],
            [(142, 24), (142, 65)],
            [(124 + 18 * math.cos(i / 50 * math.pi),
              65 + 17 * math.sin(i / 50 * math.pi)) for i in range(51)],
        ]
        # Add Love before Ang so the gathered stars spell the complete message.
        love_strokes = [
            [(0, 0), (0, 60), (28, 60)],
            [(49 + 15 * math.cos(i / 60 * math.tau),
              43 + 18 * math.sin(i / 60 * math.tau)) for i in range(61)],
            [(70, 25), (85, 60), (100, 25)],
            # Lowercase e: crossbar joins the upper loop, with its opening
            # below the bar on the right (the reverse arc looked like G).
            [(108, 42), (138, 42)]
            + [(123 + 15 * math.cos(-i / 60 * math.pi * 1.8),
                42 + 18 * math.sin(-i / 60 * math.pi * 1.8)) for i in range(61)],
        ]
        strokes = love_strokes + [[(x + 160, y) for x, y in stroke] for stroke in strokes]
        targets = []
        for stroke in strokes:
            for (x1, y1), (x2, y2) in zip(stroke, stroke[1:]):
                count = max(1, math.ceil(math.hypot(x2 - x1, y2 - y1) / 1.6))
                for i in range(count):
                    u = i / count
                    targets.append((x1 + (x2 - x1) * u, y1 + (y2 - y1) * u))
        rng = random.Random(81)
        step = max(1, math.ceil(len(sources) / 560))
        selected_sources = sources[::step]
        self.finale_origins = origins[::step]
        self.finale_particles = []
        for i, (x, y, char, size) in enumerate(selected_sources):
            # Cover the whole phrase even when there are fewer stars than
            # sampled stroke points; sequential assignment cut off its end.
            target_index = round(i * (len(targets) - 1) / max(1, len(selected_sources) - 1))
            tx, ty = targets[target_index]
            self.finale_particles.append((x, y, char, size,
                                          rng.uniform(.07, .93), rng.uniform(.17, .78),
                                          (tx - 151) * 1.5 + rng.uniform(-.7, .7),
                                          (ty - 41) * 1.8 + rng.uniform(-.7, .7),
                                          rng.uniform(0, math.tau)))

    def return_delay(self, kind, index):
        if kind == "outline":
            return .015 + .10 * index / max(1, len(self.name_letters))
        x, y, _ = self.fill_words[index]
        edge = min(1, math.hypot(x / 16, y / 17))
        return .14 + .16 * (1 - edge)

    def landing_alpha(self, t, kind, index):
        progress = (t - RETURN_START) / (RETURN_END - RETURN_START)
        return ease((progress - self.return_delay(kind, index) - .60) / .10)

    def draw_meteors(self, t, unit):
        if t < 3:
            return
        index = int((t - 3) / 6)
        age = (t - 3) % 6
        if age > 1.5:
            return
        start_x = self.width * (.12 + ((index * .271) % .45))
        start_y = self.height * (.08 + ((index * .137) % .19))
        brightness = math.sin(math.pi * age / 1.5) * .55
        for segment in range(10):
            a = max(0, age - segment * .024)
            b = max(0, age - (segment + 1) * .024)
            self.canvas.create_line(start_x + b * 320 * unit, start_y + b * 135 * unit,
                                    start_x + a * 320 * unit, start_y + a * 135 * unit,
                                    fill=blend("#ffb9dd", brightness * (1 - segment / 10)),
                                    width=max(.5, (1.6 - segment * .1) * unit), tags="frame")

    def draw_constellation(self, t, cx, cy, scale, unit):
        if t < BURST_START:
            return
        age = t - BURST_START
        scatter = ease(age / 3)
        gather = ease((t - GATHER_START) / 4)
        return_time = (t - RETURN_START) / (RETURN_END - RETURN_START)
        # Keep the gathered name as stars until those same stars return home.
        alpha = ease(age / .35) if t < RETURN_END else 0

        # A textured disc supplies dust lanes and a dense, softly glowing core.
        # Let the original heart fade before uploading the large nebula image.
        galaxy_alpha = ease((age - .75) / 2.25) * (1 - gather)
        galaxy_radius = self.galaxy_texture.radius
        self.galaxy_texture.draw(self.canvas, cx, cy, galaxy_alpha, age)
        if alpha > 0:
            for i, (x, y, char, size, dx, dy, tx, ty, phase) in enumerate(self.finale_particles):
                sx, sy = cx + x * scale, cy - y * scale
                radius = math.sqrt(dx)
                theta = ((i % 2) * math.pi + radius * 4.8
                         + age * self.galaxy_texture.ROTATION_SPEED + (dy - .475) * .7)
                gx = math.cos(theta) * radius * galaxy_radius
                gy = math.sin(theta) * radius * galaxy_radius * self.galaxy_texture.INCLINATION
                tilt = self.galaxy_texture.TILT
                star_x = cx + gx * math.cos(tilt) - gy * math.sin(tilt)
                star_y = cy + gx * math.sin(tilt) + gy * math.cos(tilt)
                # A curved outward journey becomes a slow orbit, then gathers.
                orbit = math.sin(math.pi * scatter) * 28 * unit
                px = sx + (star_x - sx) * scatter + math.cos(phase + age) * orbit
                py = sy + (star_y - sy) * scatter + math.sin(phase + age) * orbit
                arc = math.sin(math.pi * gather) * 55 * unit
                px += (cx + tx * unit - px) * gather + math.sin(phase + gather * math.tau) * arc
                py += (cy - 25 * unit + ty * unit - py) * gather + math.cos(phase + gather * math.tau) * arc
                if t >= RETURN_START:
                    # Follow a curved flight to the exact letter, then settle.
                    kind, source_index = self.finale_origins[i]
                    delay = self.return_delay(kind, source_index)
                    progress = ease((return_time - delay) / .60)
                    landed = self.landing_alpha(t, kind, source_index)
                    if landed >= 1:
                        continue
                    start = (cx + tx * unit, cy - 25 * unit + ty * unit)
                    delta_x, delta_y = sx - start[0], sy - start[1]
                    length = max(1, math.hypot(delta_x, delta_y))
                    bend = (24 + 32 * math.sin(phase)) * unit
                    normal_x, normal_y = -delta_y / length * bend, delta_x / length * bend
                    control1 = (start[0] + delta_x * .28 + normal_x,
                                start[1] + delta_y * .28 + normal_y)
                    control2 = (sx - delta_x * .12 - normal_x * .2,
                                sy - delta_y * .12 - normal_y * .2)
                    px, py = cubic_point(start, control1, control2, (sx, sy), progress)
                    if i % 3 == 0 and 0 < progress < 1:
                        tail = cubic_point(start, control1, control2, (sx, sy), max(0, progress - .025))
                        self.canvas.create_line(*tail, px, py,
                                                fill=blend("#f99bcb", .30 * (1 - landed)),
                                                width=max(.5, unit), tags="frame")
                    particle_alpha = alpha * (1 - landed)
                else:
                    particle_alpha = alpha
                twinkle = .65 + .35 * math.sin(age * 2 + phase) ** 2
                color = blend(["#ff82bd", "#ffd4eb", "#f9a1d2"][i % 3], particle_alpha * twinkle)
                radius = (1.1 + .6 * math.sin(phase) ** 2) * unit
                self.dot(px, py, radius, color)
                if age < .7 and i % 4 == 0:
                    self.text(px, py, char, max(6, round(size * unit)),
                              blend("#ffb7dd", alpha * (1 - ease(age / .7))), weight="bold")
                elif i % 25 == 0:
                    arm = 3 * unit * particle_alpha
                    self.canvas.create_line(px - arm, py, px + arm, py,
                                            fill=color, tags="frame")
                    self.canvas.create_line(px, py - arm, px, py + arm,
                                            fill=color, tags="frame")

    def replay(self, _event=None):
        self.elapsed = 0.0
        self.paused = False
        self.rings.clear()
        self.bursts.clear()
        self.last_beat = -1
        self.galaxy_texture.reset()

    def toggle_pause(self, _event=None):
        self.paused = not self.paused

    def toggle_fullscreen(self, _event=None):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)

    def exit_fullscreen(self, _event=None):
        self.fullscreen = False
        self.root.attributes("-fullscreen", False)

    def spark(self, event):
        for _ in range(46):
            angle = self.rng.uniform(0, math.tau)
            speed = self.rng.uniform(35, 190)
            self.bursts.append([event.x, event.y, math.cos(angle) * speed,
                                math.sin(angle) * speed, self.elapsed,
                                self.rng.choice(["#ff6ca8", "#ffb5dc", "#ffe6f4"])])

    def dot(self, x, y, radius, color):
        color = blend(color, self.scene_alpha)
        self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius,
                                fill=color, outline="", tags="frame")

    def text(self, x, y, value, size, color, family=BODY_FONT, weight="normal"):
        color = blend(color, self.scene_alpha)
        self.canvas.create_text(x, y, text=value, fill=color,
                                font=(family, size, weight), tags="frame")

    def draw_frame(self):
        now = time.perf_counter()
        dt = min(now - self.last_frame, .05)
        self.last_frame = now
        if not self.paused:
            self.elapsed += dt
        t = self.elapsed
        w, h = self.width, self.height
        unit = min(w / 1000, h / 900)
        cx, cy = w / 2, h * .47
        scale = HEART_SCALE * unit
        intro = ease(t / DRAW_SECONDS)
        fade = min(1, max(0, (t - 1.5) / 2))
        fill_progress = writing_progress(t - FILL_START)
        finale = ease((t - RETURN_END - .6) / 1.8)
        personal_fade = ease((t - PERSONAL_MESSAGE_START) / 2)
        title_fade = fade * (1 - ease((t - DRAW_SECONDS + 1) / 1))
        # Start the heartbeat clock only after the outline has closed.
        beat_time = max(0, t - DRAW_SECONDS)
        phase = (beat_time % 2.4) / 2.4
        pulse = (math.exp(-((phase - .12) / .055) ** 2)
                 + .55 * math.exp(-((phase - .27) / .07) ** 2))
        pulse *= ease(beat_time / 1.2)
        filling = ease((t - FILL_START) / 1.2)
        amplitude = .045 * (1 - filling) + .012 * filling + .010 * finale
        beat_scale = 1 + amplitude * pulse + .085 * math.exp(-((t - BURST_START + .18) / .17) ** 2)
        if t >= RETURN_START:
            beat_scale = 1 + amplitude * pulse * ease((t - RETURN_END) / 1.2)
        c = self.canvas
        c.delete("frame")
        self.scene_alpha = 1.0

        # A few opaque glow layers are cheaper than a large translucent image
        # on the macOS Tk canvas, while retaining the soft pink atmosphere.
        for i in range(6, 0, -1):
            r = (120 + i * 46.7) * unit
            c.create_oval(cx-r, cy-r*.93, cx+r, cy+r*.93,
                          fill=blend("#39102e", (1 - i / 7) * .42 * fade),
                          outline="", tags="frame")

        for sx, sy, radius, offset in self.stars:
            x, y = sx * w, (sy * h - t * (3 + radius) * unit) % h
            brightness = .22 + .55 * (.5 + .5 * math.sin(t * .8 + offset))
            color = blend("#d6c9eb", brightness)
            self.dot(x, y, radius * unit, color)
            if radius > 1.6:
                c.create_line(x - 4 * unit, y, x + 4 * unit, y,
                              fill=blend("#d6c9eb", brightness * .4), tags="frame")

        self.draw_meteors(t, unit)

        heart_alpha = max(1 - ease((t - BURST_START) / .65),
                          ease((t - RETURN_END + .5) / .5))
        if heart_alpha > 0 or t >= RETURN_START:
            self.scene_alpha = heart_alpha
            if heart_alpha > 0:
                # Heartbeat waves slowly dissolve into the surrounding sky.
                beat = int(beat_time / 2.4) if t >= DRAW_SECONDS else -1
                if beat != self.last_beat and beat >= 0:
                    self.rings.append(t)
                self.last_beat = beat
                self.rings = [born for born in self.rings if t - born < 3]
                for born in self.rings:
                    age = (t - born) / 3
                    coords = []
                    for x, y in self.outline:
                        coords.extend((cx + x * scale * (1 + age * .58),
                                       cy - y * scale * (1 + age * .58)))
                    c.create_line(*coords, fill=blend("#ef6ca7", .21 * (1 - age) * self.scene_alpha),
                                  width=1, smooth=True, tags="frame")

                # A cloud of light fills the heart without obscuring its silhouette.
                for x, y, radius, offset in self.dust:
                    drift = math.sin(t * 1.3 + offset) * .1
                    px = cx + (x + drift) * scale * beat_scale
                    py = cy - y * scale * beat_scale
                    intensity = (.08 + .20 * (.5 + .5 * math.sin(offset + t * 1.7))) * fade
                    color = "#ffb8e0" if radius > 1.7 else "#ff4b93"
                    self.dot(px, py, radius * unit * (1 + pulse * .25), blend(color, intensity))

                coords = []
                count = max(2, int(len(self.outline) * intro))
                for x, y in self.outline[:count]:
                    coords.extend((cx + x * scale * beat_scale, cy - y * scale * beat_scale))
                for width, color in [(8, "#150a1b"), (1, "#39102e")]:
                    c.create_line(*coords, fill=blend(color, self.scene_alpha), width=max(.5, width * unit),
                                  smooth=True, capstyle="round", tags="frame")

            # Write the names one letter at a time, tracing one continuous heart.
            if t >= RETURN_START:
                self.scene_alpha = 1.0
            draw_cursor = intro * len(self.name_letters)
            visible = min(len(self.name_letters), math.ceil(draw_cursor))
            for i, (x, y, letter) in enumerate(self.name_letters[:visible]):
                reveal = ease(draw_cursor - i)
                if t >= RETURN_START:
                    reveal *= self.landing_alpha(t, "outline", i)
                if reveal <= 0:
                    continue
                highlight = max(0, 1 - (draw_cursor - i) / 4) * (1 - ease((t - DRAW_SECONDS) / .5))
                color = blend("#ffe0f2", highlight, "#ff9cc8")
                color = blend(color, reveal)
                self.text(cx + x * scale * beat_scale,
                          cy - y * scale * beat_scale, letter,
                          max(7, int(13 * unit)), color, weight="bold")
            if intro < 1:
                pen = min(len(self.name_letters) - 1, int(draw_cursor))
                x1, y1, _ = self.name_letters[pen]
                x2, y2, _ = self.name_letters[(pen + 1) % len(self.name_letters)]
                fraction = draw_cursor - pen
                x, y = x1 + (x2 - x1) * fraction, y1 + (y2 - y1) * fraction
                for radius, strength in [(9, .12), (5, .3), (2, 1)]:
                    self.dot(cx + x * scale * beat_scale,
                             cy - y * scale * beat_scale, radius * unit,
                             blend("#ffd6ee", strength))

            # A moving pink highlight paints each word, then settles into a gradient.
            fill_cursor = fill_progress * self.fill_length
            fill_visible = bisect_right(self.fill_starts, fill_cursor) if t >= FILL_START else 0
            for i, (x, y, value) in enumerate(self.fill_words[:fill_visible]):
                landed = self.landing_alpha(t, "word", i) if t >= RETURN_START else 1
                if landed <= 0:
                    continue
                age = ((fill_cursor - self.fill_starts[i]) * FILL_SECONDS / max(1, self.fill_length)
                       + max(0, t - FILL_END))
                pink_mix = (1 + math.sin(y * .15 + x * .07)) / 2
                color = blend("#ffb3db", pink_mix, "#ed4d9e")
                highlight = math.exp(-max(0, age) * 4)
                color = blend("#ffe3f3", highlight, color)
                color = blend(color, ease(age / .25))
                color = blend(color, landed)
                if fill_cursor < self.fill_ends[i]:
                    written = max(0, fill_cursor - self.fill_starts[i])
                    prefixes = self.fill_prefixes[i]
                    prefix_index = bisect_right([width for _, width in prefixes], written)
                    if prefix_index < len(prefixes):
                        next_value, next_width = prefixes[prefix_index]
                        previous_width = prefixes[prefix_index - 1][1] if prefix_index else 0
                        letter_fade = ease((written - previous_width)
                                           / max(.0001, next_width - previous_width))
                        self.text(cx + (x + (next_width - self.fill_widths[i]) / 2) * scale * beat_scale,
                                  cy - y * scale * beat_scale, next_value, self.fill_size,
                                  blend(color, letter_fade), weight="bold")
                    if not prefix_index:
                        continue
                    value, prefix_width = prefixes[prefix_index - 1]
                    x += (prefix_width - self.fill_widths[i]) / 2
                self.text(cx + x * scale * beat_scale, cy - y * scale * beat_scale,
                          value, self.fill_size, color, weight="bold")

            # Sparks follow the writing point; deterministic timing also respects pause.
            if FILL_START <= t < FILL_END and self.fill_words:
                pen = min(len(self.fill_words) - 1, bisect_right(self.fill_ends, fill_cursor))
                x, y, _ = self.fill_words[pen]
                x -= self.fill_widths[pen] / 2
                writing = fill_cursor >= self.fill_starts[pen]
                if writing:
                    x += fill_cursor - self.fill_starts[pen]
                elif pen:
                    previous_x, previous_y, _ = self.fill_words[pen - 1]
                    previous_x += self.fill_widths[pen - 1] / 2
                    travel = max(.0001, self.fill_starts[pen] - self.fill_ends[pen - 1])
                    fraction = ease((fill_cursor - self.fill_ends[pen - 1]) / travel)
                    x = previous_x + (x - previous_x) * fraction
                    y = previous_y + (y - previous_y) * fraction
                px, py = cx + x * scale * beat_scale, cy - y * scale * beat_scale
                for radius, strength in [(11, .10), (6, .24), (2, 1)]:
                    self.dot(px, py, radius * unit,
                             blend("#ffd1ec", strength * (1 if writing else .2)))
            for i in range(max(0, fill_visible - 12), fill_visible):
                age = ((fill_cursor - self.fill_starts[i]) * FILL_SECONDS / max(1, self.fill_length)
                       + max(0, t - FILL_END))
                if not 0 <= age < .75:
                    continue
                x, y, _ = self.fill_words[i]
                for ray in range(3):
                    angle = i * 2.399 + ray * math.tau / 3
                    distance = (4 + 28 * age) * unit
                    px = cx + x * scale * beat_scale + math.cos(angle) * distance
                    py = cy - y * scale * beat_scale + math.sin(angle) * distance - age * 13 * unit
                    color = blend("#ffd9f0", (1 - age / .75) * .85)
                    radius = (1.2 + .6 * math.sin(i + ray)) * unit
                    self.dot(px, py, radius, color)
                    if ray == 0:
                        arm = 3 * unit * (1 - age / .75)
                        c.create_line(px - arm, py, px + arm, py, fill=color, tags="frame")
                        c.create_line(px, py - arm, px, py + arm, fill=color, tags="frame")

        self.scene_alpha = 1.0
        self.draw_constellation(t, cx, cy, scale, unit)

        self.text(cx, h * .105, "F O R  Y O U,  A N G", max(10, int(12 * unit)),
                  blend("#d5b3c8", min(1, t / 2)), DISPLAY_FONT)
        if title_fade > 0:
            self.text(cx, cy - 24 * unit, "Ang", max(26, int(66 * unit)),
                      blend("#ffe0f2", title_fade), NAME_FONT, "italic")
            self.text(cx, cy + 34 * unit, "อัง", max(16, int(24 * unit)),
                      blend("#ffcfdf", title_fade))
            self.text(cx, cy + 77 * unit, "every beat, always you.", max(10, int(12 * unit)),
                      blend("#ffc3d8", title_fade))

        if finale > 0:
            self.text(cx, h * .87 + (1 - finale) * 9 * unit,
                      "ทุกภาษาแปลว่ารักอัง", max(15, int(25 * unit)),
                      blend("#ffc9e8", finale), weight="bold")
        if personal_fade > 0:
            self.text(cx, h * .924 + (1 - personal_fade) * 6 * unit,
                      PERSONAL_MESSAGE, max(9, round(12 * unit)),
                      blend("#ffd8ed", personal_fade))
        self.text(cx, h * .98,
                  "SPACE  resume   ·   R  replay   ·   CLICK  spark   ·   F11  fullscreen" if self.paused else
                  "SPACE  pause   ·   R  replay   ·   CLICK  spark   ·   F11  fullscreen",
                  max(8, int(10 * unit)), "#796b85")

        self.bursts = [p for p in self.bursts if t - p[4] < 1.6]
        for x, y, vx, vy, born, color in self.bursts:
            age = t - born
            px, py = x + vx * age, y + vy * age + 35 * age * age
            tail = max(0, age - .06)
            c.create_line(x + vx * tail, y + vy * tail + 35 * tail * tail,
                          px, py, fill=blend(color, (1 - age / 1.6) * .7),
                          width=max(1, 1.5 * unit), tags="frame")
            self.dot(px, py, 1.8 * unit, blend(color, 1 - age / 1.6))
        finished = time.perf_counter()
        self.next_frame = max(self.next_frame + 1 / TARGET_FPS, finished)
        self.root.after(max(1, round((self.next_frame - finished) * 1000)), self.draw_frame)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    LoveUniverse().run()
