"""
CSS structure assertions.

Catches CSS specificity/inheritance bugs — the class of bug that caused
TiroIkonkar not to apply to the .ikonkar element because .word had an
explicit font-family rule that overrode the inherited value.
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS_PATH = os.path.join(ROOT, 'assets', 'gurbani_base.css')


def _parse_rules(css: str) -> list[tuple[str, dict]]:
    """Return [(selector_string, {property: value})] for each rule block."""
    rules = []
    # Strip comments
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
    for block in re.finditer(r'([^{]+)\{([^}]*)\}', css):
        selector = block.group(1).strip()
        declarations = {}
        for decl in block.group(2).split(';'):
            if ':' in decl:
                prop, _, val = decl.partition(':')
                declarations[prop.strip().lower()] = val.strip().lower()
        if declarations:
            rules.append((selector, declarations))
    return rules


def _selectors_with_property(rules, prop: str) -> list[str]:
    """Return all selectors that explicitly declare the given property."""
    return [sel for sel, decls in rules if prop in decls]


@pytest.fixture(scope='module')
def css_rules():
    with open(CSS_PATH, encoding='utf-8') as f:
        return _parse_rules(f.read())


class TestCSSFontInheritance:
    def test_word_has_no_font_family(self, css_rules):
        """
        .word must NOT declare font-family.
        It is a structural wrapper that inherits font-family from its parent
        (.pankti → NotoSansGurmukhi, .ikonkar → TiroIkonkar, etc.).
        An explicit font-family on .word overrides the parent and breaks the
        dual-font ikonkar scheme — this is the bug from v1.2.9.
        """
        offending = [
            sel for sel, decls in css_rules
            if 'font-family' in decls
            and re.search(r'\bword\b', sel)
        ]
        assert not offending, (
            f".word declares font-family in these selectors: {offending}\n"
            "Remove .word from font-family rules — it must inherit from its parent."
        )

    def test_g_has_no_font_family(self, css_rules):
        """.g must NOT declare font-family for the same reason."""
        offending = [
            sel for sel, decls in css_rules
            if 'font-family' in decls
            and re.search(r'\b\.g\b', sel)
        ]
        assert not offending, (
            f".g declares font-family in: {offending}"
        )

    def test_ikonkar_uses_tiro_font(self, css_rules):
        """
        .ikonkar (and related ikonkar classes) must use GurmukhiIkonkar, not
        the main GurmukhiMain family.  This is what keeps ੴ rendering
        correctly on Kobo Clara Color at maximum font size.
        """
        ikonkar_fonts = {
            decls['font-family']
            for sel, decls in css_rules
            if 'font-family' in decls and 'ikonkar' in sel.lower()
        }
        assert ikonkar_fonts, "No font-family found for any .ikonkar selector"
        for family in ikonkar_fonts:
            assert 'gurmukhiikonkar' in family.lower(), (
                f"Ikonkar selectors use '{family}' — expected 'GurmukhiIkonkar'"
            )

    def test_pankti_uses_noto_font(self, css_rules):
        """Main text must use GurmukhiMain — not the ikonkar font."""
        pankti_fonts = {
            decls['font-family']
            for sel, decls in css_rules
            if 'font-family' in decls and 'pankti' in sel.lower()
        }
        assert pankti_fonts, "No font-family found for .pankti"
        for family in pankti_fonts:
            assert 'gurmukhimain' in family.lower(), (
                f".pankti uses '{family}' — should use 'GurmukhiMain'"
            )

    def test_ikonkar_and_pankti_use_different_fonts(self, css_rules):
        """The whole point of the dual-font scheme is that ikonkar and pankti
        use different font families."""
        ikonkar_fonts = {
            decls['font-family']
            for sel, decls in css_rules
            if 'font-family' in decls and 'ikonkar' in sel.lower()
        }
        pankti_fonts = {
            decls['font-family']
            for sel, decls in css_rules
            if 'font-family' in decls and 'pankti' in sel.lower()
        }
        assert ikonkar_fonts and pankti_fonts
        assert ikonkar_fonts != pankti_fonts, (
            "ikonkar and pankti use the same font-family — dual-font scheme broken"
        )


class TestCSSWordBreaking:
    def test_g_has_white_space_nowrap(self, css_rules):
        """
        .g must have white-space: nowrap to prevent line breaks within a
        grapheme cluster (base consonant + its combining marks).
        """
        g_rules = {
            decls.get('white-space', '')
            for sel, decls in css_rules
            if re.search(r'(?<![a-z-])\.g(?![a-z-])', sel)
        }
        assert any('nowrap' in v for v in g_rules), (
            ".g does not have white-space: nowrap — combining marks can split "
            "from base consonants at line breaks"
        )

    def test_word_has_hyphens_manual(self, css_rules):
        """
        .word must have hyphens: manual (or -webkit-hyphens: manual) so that
        the soft hyphens inserted by the shaper are the only allowed break
        points within a word.
        """
        word_hyphens = [
            decls
            for sel, decls in css_rules
            if re.search(r'\bword\b', sel)
        ]
        has_manual = any(
            decls.get('hyphens') == 'manual'
            or decls.get('-webkit-hyphens') == 'manual'
            for decls in word_hyphens
        )
        assert has_manual, (
            ".word does not have hyphens: manual — word breaks will not use "
            "the soft hyphens inserted by the shaper"
        )


class TestCSSCover:
    def test_cover_page_has_zero_margin(self, css_rules):
        """
        cover.xhtml must override @page margin to 0 so the SVG fills
        the full viewport with no whitespace border.
        """
        # This is inline CSS in the cover XHTML — check the architect template
        import zipfile
        epub_path = os.path.join(ROOT, 'output', 'Japji_Sahib.epub')
        if not os.path.exists(epub_path):
            pytest.skip('EPUB not built yet')
        with zipfile.ZipFile(epub_path, 'r') as z:
            cover_names = [n for n in z.namelist() if 'cover.xhtml' in n]
            assert cover_names, "cover.xhtml not in EPUB"
            cover_html = z.read(cover_names[0]).decode('utf-8')
        assert 'margin: 0' in cover_html or 'margin:0' in cover_html, (
            "cover.xhtml does not set @page { margin: 0 } — "
            "cover image will have whitespace border on some devices"
        )

    def test_cover_uses_svg_not_img(self, css_rules):
        """
        Full-bleed cover must use SVG <image> not <img>.
        <img width:100%; height:auto> splits across pages on Libra Color
        when the image height exceeds the viewport after proportional scaling.
        """
        import zipfile
        epub_path = os.path.join(ROOT, 'output', 'Japji_Sahib.epub')
        if not os.path.exists(epub_path):
            pytest.skip('EPUB not built yet')
        with zipfile.ZipFile(epub_path, 'r') as z:
            cover_names = [n for n in z.namelist() if 'cover.xhtml' in n]
            cover_html = z.read(cover_names[0]).decode('utf-8')
        assert '<svg' in cover_html, (
            "cover.xhtml uses <img> instead of SVG — "
            "image will split across pages on Libra Color"
        )
        assert 'viewBox' in cover_html, (
            "SVG in cover.xhtml has no viewBox — will not scale correctly"
        )
