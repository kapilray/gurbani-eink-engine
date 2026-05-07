# Building Indic Script EPUBs for Kobo E-ink Devices

Lessons learned building the Japji Sahib e-ink EPUB — a Gurmukhi publication
targeting Kobo Clara Color and Kobo Libra Color. Every problem here was
discovered the hard way. The fixes are real and tested on physical hardware.

Most of these lessons apply to any Indic script (Devanagari, Bengali, Tamil,
etc.), not just Gurmukhi.

---

## 1. Always embed a Gurmukhi font

Kobo e-ink devices are **not Android-based** and do not ship Noto fonts.
Their built-in fonts cover Latin, CJK, and some Devanagari/Tamil — but
**Gurmukhi is absent**. If you do not embed a font, users see blank squares
and the "missing letters" dialog regardless of device model.

Embed the font via `@font-face` in your CSS and add it to the EPUB manifest.
Use class-based CSS selectors rather than `:lang()` — Kobo's renderer does not
honour `:lang()`:

```css
/* Works on all Kobo renderers */
.pankti, .word, .g { font-family: 'YourGurmukhi', serif; }

/* Does NOT work reliably on Kobo */
:lang(pa) { font-family: 'YourGurmukhi', serif; }
```

Use `font/ttf` as the manifest media type for TrueType fonts:

```python
epub.EpubItem(
    uid='font-gurmukhi',
    file_name='fonts/NotoSansGurmukhi-Regular.ttf',
    media_type='font/ttf',   # NOT application/vnd.ms-opentype
    content=font_bytes,
)
```

`application/vnd.ms-opentype` is for CFF/OpenType. Using it for a TTF causes
some Kobo devices (Libra Color observed) to silently ignore the font and show
nothing after the title page.

---

## 2. Choose a font where all lagaan fit within `hhea.ascent`

Gurmukhi vowel marks (lagaan) — sihari ਿ, bihari ੀ, dulavaa ੈ, tippi ੰ, and
others — extend well above the main text body. If those glyphs' `yMax` values
exceed the font's declared `hhea.ascent`, Kobo KEPUB clips them at the top of
every new page.

Use fontTools to check before committing to a font:

```python
from fontTools.ttLib import TTFont

LAGAAN = {
    'sihari ਿ':    0x0A3F,
    'bihari ੀ':    0x0A40,
    'dulavaa ੈ':   0x0A48,
    'tippi ੰ':     0x0A70,
    'bindi ਂ':     0x0A02,
    'adda-bindi ਁ': 0x0A01,
}

font = TTFont('YourFont.ttf')
cmap = font.getBestCmap()
hhea = font['hhea'].ascent
upm  = font['head'].unitsPerEm

for label, cp in LAGAAN.items():
    gname = cmap.get(cp)
    if gname:
        ymax = font['glyf'][gname].yMax
        status = '✓' if ymax <= hhea else f'✗ overflows by {ymax - hhea}u'
        print(f'{label}: yMax={ymax}  hhea={hhea}  {status}')
```

**Font comparison for Gurmukhi EPUB use (tested May 2026):**

| Font | UPM | hhea.ascent | Highest lagaan yMax | Overflows? |
|---|---|---|---|---|
| TiroGurmukhi | 1000 | 755u (75.5%) | 947u (adda-bindi) | ✗ +192u |
| OpenSatlujUni | 1000 | 701u (70.1%) | 909u (adda-bindi) | ✗ +208u |
| **NotoSansGurmukhi** | **2048** | **1836u (89.6%)** | **1836u** | **✓ 0u** |
| AnmolLipi\* | 2048 | 1901u | — | n/a |
| GurbaniHindi\* | 2000 | 1828u | — | n/a |

\* AnmolLipi and GurbaniHindi do not have Gurmukhi glyphs mapped to standard
Unicode codepoints (U+0A00–U+0A7F) and cannot render Unicode Gurbani text.

**NotoSansGurmukhi** (available in the
[Khalis Foundation fonts repo](https://github.com/KhalisFoundation/gurmukhi-fonts))
is the recommended choice. It has a critical additional property: all three
metric tables agree — `hhea.ascent` = `OS/2.sTypoAscender` = `OS/2.usWinAscent`
= **1836u**. This matters because different Kobo device generations use different
metrics for their line-box model, and having all three identical eliminates the
variable entirely.

> **Note on font patching:** Raising `hhea.ascent` and `sTypoAscender` via
> fontTools at build time works in theory but does not fix clipping on Kobo
> Clara Color. Clara's renderer appears to use a different model for the first
> line on a new page. Choosing a font with correct metrics from the start is
> the reliable fix.

---

## 3. Protect grapheme clusters from kepubify koboSpan injection

[kepubify](https://pgaskin.net/kepubify/) — the tool used to convert EPUB3 to
Kobo's KEPUB format — wraps every text node in a `<span class="koboSpan">`
for position tracking. If your Gurmukhi text is a raw string, kepubify splits
it at text-node boundaries, which can land between a consonant and its
combining vowel mark (sihari, bihari, etc.), breaking shaping.

The fix is to wrap every grapheme cluster in its own `<span>` before kepubify
runs, so kepubify can only split *between* clusters, never inside one.

**Grapheme cluster segmentation (Python):**

```python
import unicodedata

_COMBINING      = frozenset({'Mn', 'Mc', 'Me'})
_GURMUKHI_VIRAMA = '੍'  # U+0A4D — binds following consonant into conjunct

def grapheme_clusters(word: str) -> list[str]:
    clusters, current = [], []
    for ch in word:
        if current and unicodedata.category(ch) not in _COMBINING:
            if current[-1] == _GURMUKHI_VIRAMA:
                current.append(ch)   # keep conjunct together: ਪ੍ਰ
            else:
                clusters.append(''.join(current))
                current = [ch]
        else:
            current.append(ch)
    if current:
        clusters.append(''.join(current))
    return clusters
```

**Two-layer HTML wrapping:**

```python
def atomic_shaper(text: str) -> str:
    normalized = unicodedata.normalize('NFC', text)
    parts = []
    for word in normalized.split():
        clusters = grapheme_clusters(word)
        # Soft hyphen (U+00AD) between clusters: invisible normally,
        # renders as '-' at the break point when the word overflows.
        inner = '­'.join(f'<span class="g">{c}</span>' for c in clusters)
        parts.append(f'<span class="word">{inner}</span>')
    return ' '.join(parts)
```

**CSS:**

```css
/* Inner: one grapheme cluster — kepubify cannot split inside this */
.g {
    display: inline;
    white-space: nowrap;
    overflow-wrap: normal;
}

/* Outer: one word — breaks only at soft-hyphen positions between .g spans */
.word {
    display: inline;
    -webkit-hyphens: manual;
    hyphens: manual;
}
```

The virama check (`current[-1] == '੍'`) is critical for conjuncts like ਪ੍ਰਸਾਦਿ.
Without it, ਪ੍ਰ splits into `['ਪ੍', 'ਰ']`, breaking subscript shaping.

---

## 4. Full-bleed cover pages need an SVG wrapper

The natural approach — `<img style="width: 100%; height: auto">` — does not
reliably fill the screen on all Kobo devices. If the image's natural height
(proportionally scaled to screen width) exceeds the viewport height, Kobo
splits it across two pages. The user sees a partial image on the cover page
and the rest on the next page.

The fix is to wrap the cover image in an SVG with a `viewBox` matching the
image dimensions. The SVG scales to fill the viewport exactly, preserving
aspect ratio, on any screen size:

```xml
<!-- cover.xhtml -->
<html>
<head>
  <style>
    @page { margin: 0; }
    html, body { margin: 0; padding: 0; width: 100%; height: 100%; }
    svg { display: block; width: 100%; height: 100%; }
  </style>
</head>
<body>
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     version="1.1" width="100%" height="100%"
     viewBox="0 0 1600 2560"
     preserveAspectRatio="xMidYMid meet">
  <image width="1600" height="2560" xlink:href="images/cover.jpg"/>
</svg>
</body>
</html>
```

Use `xlink:href` (not `href`) for maximum Kobo firmware compatibility.
Set the `viewBox` values from the actual image dimensions at build time.

---

## 5. Complex glyphs fail on Clara Color at large font sizes

The Ik Onkar glyph ੴ (U+0A74) in NotoSansGurmukhi has a complex outline path.
On Kobo Clara Color at the device's maximum user font size, the rasterizer
fails and renders a hatched placeholder box instead of the glyph.

The same glyph renders correctly on Kobo Libra Color at the same or larger
size, suggesting Clara's rasterizer has a lower budget for path complexity.

**Fix:** embed a second font with a simpler ੴ path and scope it only to the
ikonkar element. TiroGurmukhi's ੴ is a simpler serif outline and survives
Clara's rasterizer at maximum size:

```css
@font-face {
    font-family: 'NotoGurmukhi';
    src: url('../fonts/NotoSansGurmukhi-Regular.ttf') format('truetype');
}
@font-face {
    font-family: 'TiroIkonkar';
    src: url('../fonts/TiroGurmukhi-Regular.ttf') format('truetype');
}

/* All Gurmukhi text */
.pankti, .word, .g { font-family: 'NotoGurmukhi', serif; }

/* Ik Onkar only — simpler glyph path for Clara compatibility */
.ikonkar { font-family: 'TiroIkonkar', serif; }
```

This pattern generalises: if a specific glyph fails at large sizes, identify
a font with a simpler rendering for that glyph and scope it via a class.

---

## 6. Kobo KEPUB renderer differences (Clara vs Libra)

The two current Kobo Color devices use different renderer versions with
meaningfully different behaviour:

| Behaviour | Kobo Libra Color | Kobo Clara Color |
|---|---|---|
| `padding-top` on page-first element | stripped | stripped |
| `border-top` on page-first element | **preserved** | stripped |
| `@page { margin-top }` | honoured | ignored |
| Max glyph rasterization | higher budget | lower budget |
| Max user font size | larger | smaller |
| Font: NotoSansGurmukhi lagaan | ✓ no clipping | ✓ no clipping (with correct font) |

The `border-top` difference was our working fix before the font swap: using
`border-top: 0.25em solid transparent` on line wrappers fixed Libra but not
Clara. The root fix — choosing a font where lagaan fit within `hhea.ascent`
— resolved both devices.

---

## 7. Word breaking at very large font sizes

At the maximum user font size on Kobo Libra Color, a long Gurmukhi word (7–9
consonants) can be physically wider than the viewport. `white-space: nowrap`
prevents any break, which causes the text to overflow and be cut off silently.
`overflow-wrap: break-word` breaks at an arbitrary character, which can land
inside a combining mark cluster.

The correct approach is soft hyphens between grapheme clusters (see §3 above).
This gives the renderer explicit, linguistically correct break points — every
`.g` boundary IS a Gurmukhi syllable boundary — and shows a `-` at the break
rather than a silent clip or a mid-cluster split.

---

## 8. Useful tools

| Tool | Use |
|---|---|
| [fontTools](https://github.com/fonttools/fonttools) | Inspect/patch font metrics (`hhea`, `OS/2`, glyph `yMax`) |
| [kepubify](https://pgaskin.net/kepubify/) | EPUB3 → KEPUB conversion (also available at send.djazz.se) |
| [epubcheck](https://github.com/w3c/epubcheck) | Validate EPUB structure before conversion |
| [Kobo EPUB spec](https://github.com/kobolabs/epub-spec) | Kobo's official EPUB guidelines |
| [KhalisFoundation/gurmukhi-fonts](https://github.com/KhalisFoundation/gurmukhi-fonts) | NotoSansGurmukhi + other Gurmukhi fonts (TTF) |
| [Shabad OS database](https://github.com/shabados/database) | Versioned, Unicode-correct Gurbani source data |

---

*This guide is part of the [Japji Sahib e-ink engine](../README.md) project.
Pull requests with corrections or additions welcome.*
