#!/usr/bin/env python3
"""Binary-earth brand mark: SVG (light+dark) plus apple-touch PNG."""
from __future__ import annotations

import math
import os

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # PNG icons need Pillow; SVG still writes
    Image = ImageDraw = ImageFont = None

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DESK = os.path.join(HERE, "desk")

# Deterministic 0/1 field: denser 1s over a crude land mask (Americas / Afro-Eurasia / Oz).
def land(lat, lon):
    # lat -90..90, lon -180..180
    if -55 < lat < 72 and -168 < lon < -52:
        if lat > 15 and lon < -80:
            return lon > -140 or lat > 45
        if lat < 12 and lon > -82:
            return lon < -35 and lat > -55
        return True
    if -36 < lat < 72 and -18 < lon < 150:
        if lat < 0 and lon < 20:
            return lat > -36 and lon > 8
        if lat < -10 and lon > 110:
            return False
        return True
    if -45 < lat < -10 and 112 < lon < 155:
        return True
    return False


def digits():
    """Front-hemisphere only (lon −80…80) so digits do not stack into a solid disk."""
    rows = []
    for i, lat in enumerate(range(-48, 52, 12)):
        clat = math.radians(lat)
        # Width of the visible parallel; keep glyphs from colliding at 28–32px.
        n = max(7, int(12 * math.cos(clat) + 0.5))
        row = []
        for j in range(n):
            lon = -80 + (j + 0.5) * (160 / n)
            on_land = land(lat, lon)
            bit = "1" if on_land else "0"
            if bit == "0" and ((i + j) % 4 == 0):
                bit = "1"
            if bit == "1" and not on_land and ((i * 3 + j) % 6 == 0):
                bit = "0"
            x = 32 + 24.2 * math.cos(clat) * math.sin(math.radians(lon))
            y = 32 - 24.2 * math.sin(clat)
            row.append((x, y, bit))
        rows.append(row)
    return rows


def svg_mark():
    glyphs = []
    for row in digits():
        for x, y, bit in row:
            glyphs.append(
                f'<text x="{x:.1f}" y="{y:.1f}">{bit}</text>'
            )
    body = "\n    ".join(glyphs)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="compute.world binary earth">
  <title>compute.world</title>
  <style>
    .bg {{ fill: #F3F5F2; }}
    .fg {{ fill: #1B222A; stroke: #1B222A; }}
    text {{ fill: #1B222A; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 6.2px; font-weight: 700; text-anchor: middle; dominant-baseline: middle; }}
    @media (prefers-color-scheme: dark) {{
      .bg {{ fill: #0F1216; }}
      .fg {{ fill: #E9EDF1; stroke: #E9EDF1; }}
      text {{ fill: #E9EDF1; }}
    }}
  </style>
  <defs><clipPath id="disc"><circle cx="32" cy="32" r="26.2"/></clipPath></defs>
  <rect class="bg" width="64" height="64" rx="14"/>
  <circle class="fg" cx="32" cy="32" r="27" fill="none" stroke-width="1.6"/>
  <ellipse class="fg" cx="32" cy="32" rx="13" ry="27" fill="none" stroke-width="0.55" opacity=".45"/>
  <ellipse class="fg" cx="32" cy="32" rx="22" ry="27" fill="none" stroke-width="0.45" opacity=".32"/>
  <line class="fg" x1="5.2" y1="32" x2="58.8" y2="32" stroke-width="0.45" opacity=".32"/>
  <g clip-path="url(#disc)">
  {body}
  </g>
</svg>
'''


def write_svg(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg_mark())


def write_png(path, size=180, dark=False):
    if Image is None:
        print("skip png (no Pillow):", path)
        return
    paper = (15, 18, 22) if dark else (243, 245, 242)
    ink = (233, 237, 241) if dark else (27, 34, 42)
    img = Image.new("RGB", (size, size), paper)
    d = ImageDraw.Draw(img)
    # Try a monospaced face; fall back to default.
    font = None
    for cand in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ):
        if os.path.isfile(cand):
            font = ImageFont.truetype(cand, max(9, size // 11))
            break
    if font is None:
        font = ImageFont.load_default()
    cx = cy = size / 2
    r = size * 0.42
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=ink, width=max(2, size // 90))
    scale = r / 27
    for row in digits():
        for x, y, bit in row:
            px = cx + (x - 32) * scale
            py = cy + (y - 32) * scale
            d.text((px, py), bit, font=font, fill=ink, anchor="mm")
    img.save(path, optimize=True)


def main():
    svg_desk = os.path.join(DESK, "mark.svg")
    svg_root = os.path.join(ROOT, "mark.svg")
    write_svg(svg_desk)
    write_svg(svg_root)
    write_png(os.path.join(ROOT, "apple-touch-icon.png"), 180, dark=False)
    write_png(os.path.join(ROOT, "favicon-32.png"), 32, dark=False)
    print("wrote mark.svg, apple-touch-icon.png, favicon-32.png")


if __name__ == "__main__":
    main()
