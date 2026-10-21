"""
NEBULA EYE — cinematic ASCII eye animation
Requirements:
    py -3.13 -m pip install pygame pillow numpy

Put a close-up eye photo named eye.jpg next to this file.
Run:
    py -3.13 nebula_eye.py

Controls:
    SPACE  pause/resume
    R      restart animation
    F      toggle fullscreen
    ESC    quit
"""

import math
import random
import sys
import time
from pathlib import Path

import numpy as np
import pygame
from PIL import Image, ImageEnhance, ImageOps

# --------------------------- CONFIG ---------------------------
IMAGE_PATH = Path(__file__).resolve().parent / "eye.jpg"
# Pupil center measured from eye.jpg as normalized (x, y) image coordinates.
PUPIL_CENTER = (0.502, 0.397)
WINDOW_SIZE = (1100, 760)
GRID_COLS = 112                 # higher = more detail, lower = faster
CELL_W = 9
CELL_H = 14
FPS = 30
LOOP_SECONDS = 12.0
FONT_NAME = "consolas"

# Dense characters give the image its shading; punctuation keeps highlights crisp.
RAMP = "  ..,:;irsXA253hMHGS#9B&@"
BG = (4, 5, 10)
WHITE = (235, 241, 247)
ORANGE = (255, 133, 45)
GOLD = (255, 184, 76)
PINK = (255, 58, 174)
CYAN = (65, 214, 255)
VIOLET = (166, 112, 255)

# --------------------------- IMAGE ----------------------------
def load_eye(path):
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(
            f"Couldn't find {path}. Put a close-up eye photo named eye.jpg "
            "in the same folder as nebula_eye.py."
        )

    with Image.open(path) as source:
        im = source.convert("RGB")
    # Increase contrast and detail without hard-clipping highlights.
    im = ImageOps.autocontrast(im, cutoff=1)
    im = ImageEnhance.Contrast(im).enhance(1.28)
    im = ImageEnhance.Color(im).enhance(1.22)
    im = ImageEnhance.Sharpness(im).enhance(1.5)
    return im


def ease_in_out(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def zoom_crop(image, zoom, center_x=0.5, center_y=0.5):
    w, h = image.size
    cw = max(2, int(w / zoom))
    ch = max(2, int(h / zoom))
    cx = int(center_x * w)
    cy = int(center_y * h)
    left = max(0, min(w - cw, cx - cw // 2))
    top = max(0, min(h - ch, cy - ch // 2))
    return image.crop((left, top, left + cw, top + ch)), left, top


# --------------------------- COLOR / ASCII -------------------
def classify_color(r, g, b, lum, x, y, t):
    # Keep the iris warm and the sclera cool-white, with a subtle neon edge.
    if r > g * 1.22 and r > b * 1.25 and r > 75:
        return ORANGE if lum < 185 else GOLD
    if b > r * 1.10 and b > g * 0.95 and b > 85:
        return CYAN
    if lum > 185:
        return WHITE
    if lum < 30:
        return (10, 12, 19)
    return (105, 116, 133)


def make_ascii(image, cols, rows, t):
    # Correct for the tall proportions of terminal-style characters.
    small = image.resize((cols, rows), Image.Resampling.LANCZOS)
    pixels = np.asarray(small, dtype=np.float32)
    lum = (
        0.2126 * pixels[:, :, 0]
        + 0.7152 * pixels[:, :, 1]
        + 0.0722 * pixels[:, :, 2]
    )

    # Slight animated glow on warm iris pixels.
    out = []
    for y in range(rows):
        row = []
        for x in range(cols):
            r, g, b = pixels[y, x]
            brightness = lum[y, x]

            # Darken edges for a cinematic vignette.
            nx = (x / max(1, cols - 1) - 0.5) * 2
            ny = (y / max(1, rows - 1) - 0.5) * 2
            vignette = max(0.38, 1.0 - 0.34 * (nx * nx + ny * ny))
            brightness *= vignette

            # Use more solid glyphs for bright/high-detail areas.
            idx = int(np.clip(brightness / 255 * (len(RAMP) - 1), 0, len(RAMP) - 1))
            char = RAMP[idx]
            color = classify_color(r, g, b, brightness, x, y, t)

            # Fine, breathing highlight around the center during the portal phase.
            if t > 0.72:
                pulse = 0.5 + 0.5 * math.sin(t * 28 + x * 0.13 + y * 0.17)
                dx = (x - cols * 0.5) / (cols * 0.22)
                dy = (y - rows * 0.52) / (rows * 0.22)
                radius = dx * dx + dy * dy
                if radius < 1.0 and pulse > 0.66:
                    color = PINK
                    if pulse > 0.91:
                        char = random.choice("{}[]<>/\\01")

            # Let the whole image resolve into a pink ASCII portal at the end.
            if t > 0.90 and char != " ":
                color = PINK
            elif t > 0.80 and char != " ":
                sparkle = math.sin(x * 12.9898 + y * 78.233 + int(t * 30) * 0.37)
                if sparkle > 0.998:
                    char = "+"
                    color = PINK

            row.append((char, color))
        out.append(row)
    return out


# --------------------------- EFFECTS -------------------------
def draw_scanlines(surface, alpha=18):
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    for y in range(0, surface.get_height(), 4):
        pygame.draw.line(overlay, (0, 0, 0, alpha), (0, y), (surface.get_width(), y))
    surface.blit(overlay, (0, 0))


def draw_soft_glow(surface, center, radius, color, strength):
    """Composite a compact radial glow with a gently fading edge."""
    radius = max(1, int(radius))
    glow = pygame.Surface((radius * 2 + 1, radius * 2 + 1), pygame.SRCALPHA)
    for ring_radius in range(radius, 0, -1):
        falloff = 1.0 - ring_radius / radius
        alpha = int(strength * falloff ** 1.8)
        if alpha:
            pygame.draw.circle(glow, (*color, alpha), (radius, radius), ring_radius)
    surface.blit(glow, (center[0] - radius, center[1] - radius))


def draw_energy_core(surface, center, elapsed):
    """Draw the pupil-locked core, pulse rings, sparks, and fading aura."""
    width, height = surface.get_size()
    period = 3.0
    cycle = elapsed % period
    pulse_duration = 0.48
    pulse = math.sin(math.pi * cycle / pulse_duration) ** 2 if cycle < pulse_duration else 0.0
    afterglow = math.exp(-cycle / 0.72)

    effects = pygame.Surface((width, height), pygame.SRCALPHA)
    glow_strength = int(34 + 40 * afterglow + 38 * pulse)
    draw_soft_glow(effects, center, 28, CYAN, glow_strength)

    ring_lifetime = 1.55
    max_radius = int(min(width, height) * 0.46)
    ring_delays = (0.0, 0.18, 0.38)
    ring_colors = (CYAN, VIOLET, CYAN)

    for delay, color in zip(ring_delays, ring_colors):
        age = cycle - delay
        if 0.0 <= age < ring_lifetime:
            progress = age / ring_lifetime
            radius = int(10 + progress * max_radius)
            alpha = int(105 * (1.0 - progress) ** 1.25)
            pygame.draw.circle(effects, (*color, alpha), center, radius, 2)

    # A small set of deterministic sparks travel outward from each pulse.
    spark_age = cycle - 0.08
    spark_lifetime = 0.78
    if 0.0 <= spark_age < spark_lifetime:
        progress = spark_age / spark_lifetime
        distance = 8 + int(progress * min(width, height) * 0.34)
        tail_distance = max(3, int(min(width, height) * 0.035 * (1.0 - progress)))
        alpha = int(220 * (1.0 - progress) ** 1.6)
        spark_count = 8
        for index in range(spark_count):
            angle = math.tau * index / spark_count + 0.17
            dx, dy = math.cos(angle), math.sin(angle)
            point = (round(center[0] + dx * distance), round(center[1] + dy * distance))
            tail = (round(point[0] - dx * tail_distance), round(point[1] - dy * tail_distance))
            color = CYAN if index % 2 == 0 else VIOLET
            pygame.draw.line(effects, (*color, alpha), tail, point, 2)
            pygame.draw.circle(effects, (*color, alpha), point, 2)

    core_radius = 3 + int(2 * pulse)
    core_alpha = min(255, 218 + int(37 * pulse))
    pygame.draw.circle(effects, (238, 251, 255, core_alpha), center, core_radius)
    pygame.draw.circle(effects, (255, 255, 255, min(255, core_alpha)), center, max(1, core_radius - 1))
    surface.blit(effects, (0, 0))


def draw_particles(surface, particles, t, dt):
    w, h = surface.get_size()
    for p in particles:
        p["y"] -= p["speed"] * dt * FPS
        p["x"] += math.sin(t * 2 + p["phase"]) * 0.22 * dt * FPS
        if p["y"] < -5:
            p["y"] = h + random.randrange(5, 80)
            p["x"] = random.randrange(w)
        brightness = int(75 + 90 * (0.5 + 0.5 * math.sin(t * 3 + p["phase"])))
        pygame.draw.circle(surface, (brightness, brightness, brightness + 15),
                           (int(p["x"]), int(p["y"])), p["size"])


def draw_ascii(surface, art, font, cell_w, cell_h, start_x, start_y, t):
    # Font surfaces are cached by glyph + color so the animation stays responsive.
    if not hasattr(draw_ascii, "cache"):
        draw_ascii.cache = {}
    cache = draw_ascii.cache

    for gy, row in enumerate(art):
        y = start_y + gy * cell_h
        for gx, (char, color) in enumerate(row):
            if char == " ":
                continue
            key = (char, color)
            glyph = cache.get(key)
            if glyph is None:
                glyph = font.render(char, True, color)
                cache[key] = glyph
            x = start_x + gx * cell_w
            surface.blit(glyph, (x, y))


# --------------------------- MAIN ----------------------------
def main():
    eye = load_eye(IMAGE_PATH)

    pygame.init()
    pygame.display.set_caption("NEBULA EYE  |  ASCII VISUALIZER")
    screen = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(FONT_NAME, CELL_H, bold=False)
    title_font = pygame.font.SysFont(FONT_NAME, 16, bold=True)
    small_font = pygame.font.SysFont(FONT_NAME, 12)

    started = time.perf_counter()
    paused = False
    pause_at = 0.0
    elapsed_before_pause = 0.0
    fullscreen = False

    particles = [
        {
            "x": random.randrange(WINDOW_SIZE[0]),
            "y": random.randrange(WINDOW_SIZE[1]),
            "speed": random.uniform(0.25, 1.1),
            "size": random.choice((1, 1, 2)),
            "phase": random.random() * math.tau,
        }
        for _ in range(90)
    ]

    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    if not paused:
                        paused = True
                        pause_at = time.perf_counter()
                    else:
                        elapsed_before_pause += time.perf_counter() - pause_at
                        paused = False
                elif event.key == pygame.K_r:
                    started = time.perf_counter()
                    elapsed_before_pause = 0.0
                    paused = False
                elif event.key == pygame.K_f:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)
            elif event.type == pygame.VIDEORESIZE and not fullscreen:
                screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)

        now = pause_at if paused else time.perf_counter()
        elapsed = now - started - elapsed_before_pause
        phase = (elapsed % LOOP_SECONDS) / LOOP_SECONDS

        sw, sh = screen.get_size()
        screen.fill(BG)

        # Header / footer are part of the finished presentation.
        header = title_font.render("N E B U L A   /   E Y E", True, (206, 216, 230))
        screen.blit(header, (22, 16))
        sub = small_font.render("LIVE ASCII CONVERSION   •   CHROMATIC IRIS   •   PROCEDURAL GLOW",
                                True, (94, 111, 132))
        screen.blit(sub, (22, 39))

        # Three-act animation: reveal, dramatic iris zoom, then pink portal transition.
        if phase < 0.12:
            reveal = ease_in_out(phase / 0.12)
            zoom = 1.0 + reveal * 0.18
            brightness = 0.18 + reveal * 0.82
        elif phase < 0.76:
            q = (phase - 0.12) / 0.64
            zoom = 1.18 + ease_in_out(q) * 3.3
            brightness = 1.0
        else:
            q = (phase - 0.76) / 0.24
            zoom = 4.48 + ease_in_out(q) * 1.35
            brightness = 1.0 - ease_in_out(q) * 0.68

        # Center the crop on the pupil and map the actual focal position after edge clamping.
        cropped, crop_left, crop_top = zoom_crop(eye, zoom, *PUPIL_CENTER)
        if brightness != 1.0:
            cropped = ImageEnhance.Brightness(cropped).enhance(brightness)

        # Keep the character grid proportional to the available window.
        cols = max(1, min(GRID_COLS, int(max(1, sw - 44) / CELL_W)))
        rows = max(1, int(max(1, sh - 105) / CELL_H))
        art = make_ascii(cropped, cols, rows, phase)

        grid_w = cols * CELL_W
        grid_h = rows * CELL_H
        start_x = (sw - grid_w) // 2
        start_y = 70 + max(0, (sh - 105 - grid_h) // 2)

        # Glow behind the ASCII iris.
        pupil_x = (PUPIL_CENTER[0] * eye.width - crop_left) / cropped.width
        pupil_y = (PUPIL_CENTER[1] * eye.height - crop_top) / cropped.height
        pupil_center = (
            round(start_x + pupil_x * grid_w),
            round(start_y + pupil_y * grid_h),
        )
        draw_particles(screen, particles, elapsed, 0.0 if paused else dt)
        draw_ascii(screen, art, font, CELL_W, CELL_H, start_x, start_y, phase)
        draw_energy_core(screen, pupil_center, elapsed)

        # Final portal ring and small status line.
        if phase > 0.76:
            q = (phase - 0.76) / 0.24
            ring_radius = int(18 + 70 * q)
            ring_alpha = int(90 * (1 - q * 0.5))
            ring = pygame.Surface((sw, sh), pygame.SRCALPHA)
            pygame.draw.circle(ring, (*PINK, ring_alpha), pupil_center, ring_radius, 1)
            pygame.draw.circle(ring, (*ORANGE, max(20, ring_alpha // 2)),
                               pupil_center, max(2, ring_radius - 8), 1)
            screen.blit(ring, (0, 0))

        draw_scanlines(screen, alpha=13)

        footer_text = "SPACE pause   R restart   F fullscreen   ESC exit"
        footer = small_font.render(footer_text, True, (91, 105, 124))
        screen.blit(footer, (22, sh - 25))

        if paused:
            label = title_font.render("PAUSED", True, PINK)
            screen.blit(label, (sw - label.get_width() - 22, 18))

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nNEBULA EYE ERROR: {exc}\n")
        print("Check that eye.jpg is in the same folder and install dependencies:")
        print("    py -3.13 -m pip install pygame pillow numpy")
        input("Press Enter to close...")
