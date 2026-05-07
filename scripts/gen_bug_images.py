#!/usr/bin/env python3
"""
Generate illustrative images for the Kobo lagaan clipping bug report.
Produces clara_clipping.jpg and libra_clipping.jpg in output/bug-report/.
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.path.join(ROOT, 'assets', 'fonts', 'TiroGurmukhi-Regular.ttf')
OUT_DIR   = os.path.join(ROOT, 'output', 'bug-report')

# ── layout constants ─────────────────────────────────────────────────────────
W, H       = 600, 360
FONT_SIZE  = 46
LINE_H     = 100       # px between line starts
PAGE_TOP   = 68        # px from image top — simulated page content boundary

# TiroGurmukhi font metrics at FONT_SIZE px (UPM = 1000)
ASCENT_PX  = round(755 / 1000 * FONT_SIZE)   # 34 px — hhea content area top
LAGAAN_PX  = round(884 / 1000 * FONT_SIZE)   # 41 px — sihari/bihari actual yMax
# lagaan extend LAGAAN_PX - ASCENT_PX = 7 px above the hhea content area

BORDER_TOP_PX = round(0.25 * FONT_SIZE)       # 11 px — .line-wrap border-top


# ── Gurbani lines with many sihari / bihari marks ────────────────────────────
LINES = [
    "ਸਤਿ ਨਾਮੁ ਕਰਤਾ ਪੁਰਖੁ",   # ਸਤਿ, ਨਿ in next line
    "ਨਿਰਭਉ ਨਿਰਵੈਰੁ",
    "ਅਕਾਲ ਮੂਰਤਿ ਅਜੂਨੀ",
]


# ── helpers ──────────────────────────────────────────────────────────────────
def load_fonts():
    gfont = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    try:
        lf12 = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 12)
        lf10 = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 10)
        lf11 = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 11)
    except OSError:
        lf12 = lf10 = lf11 = ImageFont.load_default()
    return gfont, lf12, lf10, lf11


def cx(draw, text, font):
    """Return x offset to center text."""
    b = draw.textbbox((0, 0), text, font=font)
    return (W - (b[2] - b[0])) // 2


def draw_lines(draw, gfont, baseline_y):
    """Draw LINES with the first line's baseline at baseline_y."""
    y = baseline_y
    for line in LINES:
        x = cx(draw, line, gfont)
        draw.text((x, y), line, font=gfont, fill='#1a1a1a', anchor='ls')
        y += LINE_H


def frame(draw):
    """Simple e-reader screen frame."""
    draw.rectangle([0, 0, W-1, H-1], fill='#f6f6f2')
    draw.rectangle([0, 0, W-1, H-1], outline='#aaaaaa', width=3)
    draw.rectangle([4, 4, W-5, H-5], outline='#dddddd', width=1)


def page_boundary_line(draw, y, lf10):
    draw.line([(6, y), (W-6, y)], fill='#bbbbbb', width=1)
    draw.text((8, y - 14), "page top", font=lf10, fill='#aaaaaa')


# ── Clara ─────────────────────────────────────────────────────────────────────
def make_clara(gfont, lf12, lf10, lf11):
    img = Image.new('RGB', (W, H), '#f6f6f2')
    draw = ImageDraw.Draw(img)
    frame(draw)

    # On Clara the half-leading above the first line is stripped entirely.
    # The page boundary IS the content-area top (hhea.ascent line).
    # baseline = PAGE_TOP + ASCENT_PX  →  content area top is exactly at PAGE_TOP.
    # sihari/bihari yMax is LAGAAN_PX above baseline, so they sit
    # LAGAAN_PX - ASCENT_PX px ABOVE PAGE_TOP and get cut off.
    baseline_y = PAGE_TOP + ASCENT_PX

    draw_lines(draw, gfont, baseline_y)

    # Clip: white rectangle masks everything above PAGE_TOP
    draw.rectangle([5, 5, W-5, PAGE_TOP - 1], fill='#f6f6f2')

    # Page boundary
    page_boundary_line(draw, PAGE_TOP, lf10)

    # Red "clipped" zone indicator
    clip_h = LAGAAN_PX - ASCENT_PX   # px clipped (≈7)
    draw.rectangle([5, PAGE_TOP - clip_h - 1, W-5, PAGE_TOP - 1],
                   fill='#ffe8e8', outline='#ff8888', width=1)
    draw.text((8, PAGE_TOP - clip_h - 1),
              f"▲ {clip_h}px of sihari ਿ · bihari ੀ · dulavaa ੈ  clipped here",
              font=lf10, fill='#cc2222')

    # Header label (device name)
    draw.text((cx(draw, "Kobo Clara Color", lf12), 12),
              "Kobo Clara Color", font=lf12, fill='#333333')
    draw.text((cx(draw, "border-top stripped · leading stripped · clipping persists", lf10),
               28),
              "border-top stripped · leading stripped · clipping persists",
              font=lf10, fill='#888888')

    # Bottom caption
    cap = "All pages: sihari ਿ  bihari ੀ  dulavaa ੈ  clipped at page boundary"
    draw.text((cx(draw, cap, lf11), H - 22), cap, font=lf11, fill='#cc2222')

    path = os.path.join(OUT_DIR, 'clara_clipping.jpg')
    img.save(path, 'JPEG', quality=93)
    print(f"Saved {path}")


# ── Libra ─────────────────────────────────────────────────────────────────────
def make_libra(gfont, lf12, lf10, lf11):
    img = Image.new('RGB', (W, H), '#f6f6f2')
    draw = ImageDraw.Draw(img)
    frame(draw)

    # On Libra, border-top: 0.25em is preserved → text starts BORDER_TOP_PX below
    # the page boundary.  All lagaan fit comfortably above the hhea line.
    baseline_y = PAGE_TOP + BORDER_TOP_PX + ASCENT_PX

    draw_lines(draw, gfont, baseline_y)

    # Page boundary
    page_boundary_line(draw, PAGE_TOP, lf10)

    # Green bracket showing the preserved border-top gap
    bx = 12
    gap_top    = PAGE_TOP + 1
    gap_bottom = PAGE_TOP + BORDER_TOP_PX - 1
    draw.line([(bx, gap_top), (bx, gap_bottom)], fill='#2a8a2a', width=2)
    draw.line([(bx-4, gap_top),    (bx+4, gap_top)],    fill='#2a8a2a', width=2)
    draw.line([(bx-4, gap_bottom), (bx+4, gap_bottom)], fill='#2a8a2a', width=2)
    draw.text((bx + 8, gap_top + 1),
              f"border-top: 0.25em\n({BORDER_TOP_PX}px gap)",
              font=lf10, fill='#2a8a2a')

    # Header
    draw.text((cx(draw, "Kobo Libra Color", lf12), 12),
              "Kobo Libra Color", font=lf12, fill='#333333')
    draw.text((cx(draw, "border-top: 0.25em preserved · lagaan fully visible", lf10), 28),
              "border-top: 0.25em preserved · lagaan fully visible",
              font=lf10, fill='#888888')

    # Bottom caption
    cap = "All marks intact — sihari ਿ  bihari ੀ  dulavaa ੈ  fully visible"
    draw.text((cx(draw, cap, lf11), H - 22), cap, font=lf11, fill='#2a8a2a')

    path = os.path.join(OUT_DIR, 'libra_clipping.jpg')
    img.save(path, 'JPEG', quality=93)
    print(f"Saved {path}")


# ── main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    os.makedirs(OUT_DIR, exist_ok=True)
    fonts = load_fonts()
    make_clara(*fonts)
    make_libra(*fonts)
    print("Done.")
