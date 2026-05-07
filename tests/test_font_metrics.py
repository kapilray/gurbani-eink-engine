"""
Font metric assertions.

Verifies that every font embedded in the EPUB has lagaan (ascending vowel
marks) whose yMax values fit within hhea.ascent.  This is the root cause
of Kobo KEPUB lagaan clipping at page tops — caught before hardware testing.
"""
import sys, os, zipfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fontTools.ttLib import TTFont

ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EPUB_PATH = os.path.join(ROOT, 'output', 'Japji_Sahib.epub')

# All above-baseline Gurmukhi marks that have caused clipping in practice
LAGAAN = {
    'sihari ਿ':     0x0A3F,
    'bihari ੀ':     0x0A40,
    'dulavaa ੈ':    0x0A48,
    'tippi ੰ':      0x0A70,
    'bindi ਂ':      0x0A02,
    'adda-bindi ਁ': 0x0A01,
    'lanvan ਏ':     0x0A0F,
}

# Fonts in the EPUB that carry Gurmukhi text (not the ikonkar-only font)
GURMUKHI_FONTS = ['NotoSansGurmukhi-Regular.ttf']


def _extract_font(epub_path: str, font_filename: str) -> bytes:
    with zipfile.ZipFile(epub_path, 'r') as z:
        for name in z.namelist():
            if name.endswith(font_filename):
                return z.read(name)
    raise FileNotFoundError(f'{font_filename} not found in EPUB')


class TestFontMetrics:
    @pytest.fixture(scope='class')
    def fonts(self):
        result = {}
        for fname in GURMUKHI_FONTS:
            data = _extract_font(EPUB_PATH, fname)
            import io
            font = TTFont(io.BytesIO(data))
            result[fname] = font
        yield result
        for f in result.values():
            f.close()

    def test_gurmukhi_fonts_present_in_epub(self):
        with zipfile.ZipFile(EPUB_PATH, 'r') as z:
            names = z.namelist()
        for fname in GURMUKHI_FONTS:
            assert any(n.endswith(fname) for n in names), \
                f'{fname} not found in EPUB manifest'

    def test_lagaan_fit_within_hhea_ascent(self, fonts):
        for fname, font in fonts.items():
            cmap  = font.getBestCmap()
            hhea  = font['hhea'].ascent
            for label, cp in LAGAAN.items():
                gname = cmap.get(cp)
                if gname is None:
                    continue
                try:
                    ymax = font['glyf'][gname].yMax
                except Exception:
                    continue
                if ymax is None:
                    continue
                assert ymax <= hhea, (
                    f"{fname}: {label} yMax={ymax} exceeds hhea.ascent={hhea} "
                    f"(overflow +{ymax - hhea}u) — will clip on Kobo KEPUB"
                )

    def test_hhea_sTypo_usWin_consistent(self, fonts):
        # All three ascent metrics should agree so Clara/Libra renderer
        # differences don't produce different clipping behaviour.
        for fname, font in fonts.items():
            hhea = font['hhea'].ascent
            typo = font['OS/2'].sTypoAscender
            win  = font['OS/2'].usWinAscent
            assert hhea == typo == win, (
                f"{fname}: ascent metrics disagree — "
                f"hhea={hhea}, sTypoAscender={typo}, usWinAscent={win}"
            )

    def test_font_has_core_gurmukhi_coverage(self, fonts):
        required = {
            'ੴ (Ik Onkar)': 0x0A74,
            'ਸ (sa)':        0x0A38,
            'ਤ (ta)':        0x0A24,
            'ਿ (sihari)':    0x0A3F,
            'ੀ (bihari)':    0x0A40,
        }
        for fname, font in fonts.items():
            cmap = font.getBestCmap()
            for label, cp in required.items():
                assert cmap.get(cp) is not None, \
                    f"{fname}: missing required glyph {label} (U+{cp:04X})"
