"""
Cover art preparation for Gurbani EPUB.

Usage:
  python cover_prep.py --input path/to/art.webp [--guides]

  --input   Source artwork file (omit for placeholder)
  --guides  Overlay safe-zone guide markers on output

Outputs (in assets/branding/):
  cover_color.png      — 1600×2560, colour, with title overlay
  cover_grayscale.png  — grayscale version for B&W Kindle/Kobo test
"""

import argparse
import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat

# ── Constants ────────────────────────────────────────────────────────────────
COVER_W, COVER_H = 1600, 2560
SAFE_ZONE_INSET  = 75          # px — store safe zone boundary
TITLE_TEXT  = 'ਜਪੁਜੀ ਸਾਹਿਬ'
AUTHOR_TEXT = 'ਗੁਰੂ ਨਾਨਕ ਦੇਵ ਜੀ'
ARTIST_NAME = 'RAVINARTOOR'
ARTIST_NOTE = 'Art: RAVINARTOOR'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT       = os.path.dirname(os.path.dirname(SCRIPT_DIR))
FONT_PATH  = os.path.join(ROOT, 'assets', 'fonts', 'TiroGurmukhi-Regular.ttf')
OUT_DIR    = SCRIPT_DIR

TEXT_BAND_COLOR  = (245, 237, 218)   # warm parchment — matches art palette
TEXT_COLOR       = (28, 18,  8)
ACCENT_COLOR     = (120, 80, 40)
CREDIT_COLOR     = (60,  40, 20)     # dark enough to pass contrast check


def _font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except OSError:
        print(f'Warning: Tiro Gurmukhi not found at {FONT_PATH}', file=sys.stderr)
        return ImageFont.load_default()


def _cx(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    bb = draw.textbbox((0, 0), text, font=font)
    return (COVER_W - (bb[2] - bb[0])) // 2


def _make_canvas(input_path: str | None) -> tuple[Image.Image, int]:
    """Return (canvas, art_bottom_y) — the y where art ends."""
    canvas = Image.new('RGB', (COVER_W, COVER_H), TEXT_BAND_COLOR)

    if input_path:
        art = Image.open(input_path).convert('RGB')
        src_w, src_h = art.size

        # Scale to fit full width, keep aspect ratio
        scale   = COVER_W / src_w
        new_h   = int(src_h * scale)
        art     = art.resize((COVER_W, new_h), Image.LANCZOS)
        art_h   = min(new_h, COVER_H)

        # Paste art at top
        canvas.paste(art.crop((0, 0, COVER_W, art_h)), (0, 0))

        # Soft gradient blend where art meets text band (bottom 60px of art zone)
        blend_h = 60
        blend_start = max(0, art_h - blend_h)
        for i in range(blend_h):
            y      = blend_start + i
            if y >= COVER_H:
                break
            alpha  = i / blend_h          # 0 = art, 1 = text band
            strip  = canvas.crop((0, y, COVER_W, y + 1))
            solid  = Image.new('RGB', (COVER_W, 1), TEXT_BAND_COLOR)
            blended = Image.blend(strip, solid, alpha)
            canvas.paste(blended, (0, y))

        return canvas, art_h
    else:
        # Placeholder: two-tone canvas with border + art zone label
        draw   = ImageDraw.Draw(canvas)
        art_h  = int(COVER_H * 0.68)
        label_font = _font(52)

        # Art zone fill
        canvas.paste(Image.new('RGB', (COVER_W, art_h), (235, 228, 210)), (0, 0))

        # Art zone label
        label = '[ ART ZONE — 1600 × {:,}px ]'.format(art_h)
        lx    = _cx(draw, label, label_font)
        draw.text((lx, art_h // 2 - 30), label, font=label_font, fill=(180, 160, 130))

        # Inset border
        inset = 40
        draw.rectangle([inset, inset, COVER_W - inset, art_h - inset],
                        outline=ACCENT_COLOR, width=2)

        return canvas, art_h


def _overlay_text(canvas: Image.Image, art_bottom: int, guides: bool) -> Image.Image:
    canvas = canvas.copy()
    draw   = ImageDraw.Draw(canvas)

    title_font  = _font(130)
    author_font = _font(76)
    credit_font = _font(46)

    # Text band starts at art_bottom, but we work within safe zone
    band_top    = art_bottom
    band_h      = COVER_H - band_top
    band_center = band_top + band_h // 2

    # Rule line at top of text band
    rule_y = band_top + 28
    draw.line([(SAFE_ZONE_INSET + 20, rule_y),
               (COVER_W - SAFE_ZONE_INSET - 20, rule_y)],
              fill=ACCENT_COLOR, width=2)

    # Title
    title_y = rule_y + 40
    draw.text((_cx(draw, TITLE_TEXT, title_font), title_y),
              TITLE_TEXT, font=title_font, fill=TEXT_COLOR)
    title_h = draw.textbbox((0, 0), TITLE_TEXT, font=title_font)
    title_h = title_h[3] - title_h[1]

    # Author
    author_y = title_y + title_h + 28
    draw.text((_cx(draw, AUTHOR_TEXT, author_font), author_y),
              AUTHOR_TEXT, font=author_font, fill=ACCENT_COLOR)

    # Artist credit — bottom right, inside safe zone, dark enough to read
    credit_x = COVER_W - SAFE_ZONE_INSET - 20
    credit_y = COVER_H - SAFE_ZONE_INSET - 20
    credit_bb = draw.textbbox((0, 0), ARTIST_NOTE, font=credit_font)
    credit_w  = credit_bb[2] - credit_bb[0]
    draw.text((credit_x - credit_w, credit_y - (credit_bb[3] - credit_bb[1])),
              ARTIST_NOTE, font=credit_font, fill=CREDIT_COLOR)

    # Safe-zone guides (dashed rectangle) — debug only
    if guides:
        sz = SAFE_ZONE_INSET
        guide_color = (255, 0, 100)
        dash = 20
        for x in range(sz, COVER_W - sz, dash * 2):
            draw.line([(x, sz), (min(x + dash, COVER_W - sz), sz)],
                      fill=guide_color, width=2)
            draw.line([(x, COVER_H - sz), (min(x + dash, COVER_W - sz), COVER_H - sz)],
                      fill=guide_color, width=2)
        for y in range(sz, COVER_H - sz, dash * 2):
            draw.line([(sz, y), (sz, min(y + dash, COVER_H - sz))],
                      fill=guide_color, width=2)
            draw.line([(COVER_W - sz, y), (COVER_W - sz, min(y + dash, COVER_H - sz))],
                      fill=guide_color, width=2)

    return canvas


def generate(input_path: str | None = None, guides: bool = False) -> tuple[str, str]:
    canvas, art_bottom = _make_canvas(input_path)
    color = _overlay_text(canvas, art_bottom, guides)

    color_path = os.path.join(OUT_DIR, 'cover_color.png')
    gray_path  = os.path.join(OUT_DIR, 'cover_grayscale.png')

    color.save(color_path, 'PNG')
    color.convert('L').save(gray_path, 'PNG')

    return color_path, gray_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input',  metavar='IMAGE', help='Source artwork file')
    parser.add_argument('--guides', action='store_true', help='Show safe-zone guide markers')
    args = parser.parse_args()

    c, g = generate(args.input, args.guides)
    print(f'Color cover     → {c}')
    print(f'Grayscale cover → {g}')
