"""
Unit tests for the atomic shaper.

Regression coverage for every class of bug we've hit:
  - combining marks splitting from base consonants (kepubify koboSpan injection)
  - virama conjuncts (ਪ੍ਰ) splitting across .g spans
  - soft hyphens present between clusters, absent within them
  - NFC normalisation
  - no combining mark as the first character of any .g span
"""
import sys, os, re, unicodedata
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from modules.shaper.shaper import atomic_shaper, _grapheme_clusters

COMBINING = frozenset({'Mn', 'Mc', 'Me'})
SOFT_HYPHEN = '­'


# ── _grapheme_clusters ────────────────────────────────────────────────────────

class TestGraphemeClusters:
    def test_base_with_sihari(self):
        # ਤਿ = ta + sihari (Mn) — must stay in one cluster
        clusters = _grapheme_clusters('ਤਿ')
        assert clusters == ['ਤਿ'], f"Expected ['ਤਿ'], got {clusters}"

    def test_base_with_bihari(self):
        clusters = _grapheme_clusters('ਨੀ')
        assert clusters == ['ਨੀ']

    def test_conjunct_virama(self):
        # ਪ੍ਰ = pa + virama + ra — all three must stay together
        clusters = _grapheme_clusters('ਪ੍ਰ')
        assert clusters == ['ਪ੍ਰ'], f"Expected ['ਪ੍ਰ'], got {clusters}"

    def test_manglacharan_conjunct(self):
        # ਪ੍ਰਸਾਦਿ — the conjunct ਪ੍ਰ must stay together
        clusters = _grapheme_clusters('ਪ੍ਰਸਾਦਿ')
        assert clusters[0] == 'ਪ੍ਰ', f"Conjunct split: {clusters}"
        assert clusters == ['ਪ੍ਰ', 'ਸਾ', 'ਦਿ']

    def test_nirvair(self):
        clusters = _grapheme_clusters('ਨਿਰਵੈਰੁ')
        # No cluster should start with a combining mark
        for c in clusters:
            assert unicodedata.category(c[0]) not in COMBINING, \
                f"Cluster '{c}' starts with combining mark"

    def test_no_cluster_starts_with_combining(self):
        # Broad check across common Gurbani words
        words = ['ਸਤਿ', 'ਨਾਮੁ', 'ਕਰਤਾ', 'ਪੁਰਖੁ', 'ਅਕਾਲ', 'ਮੂਰਤਿ', 'ਅਜੂਨੀ']
        for word in words:
            for cluster in _grapheme_clusters(word):
                assert unicodedata.category(cluster[0]) not in COMBINING, \
                    f"In '{word}': cluster '{cluster}' starts with combining mark"

    def test_ik_onkar_single_cluster(self):
        # ੴ (U+0A74) is a single character — must be one cluster
        clusters = _grapheme_clusters('ੴ')
        assert clusters == ['ੴ']


# ── atomic_shaper HTML output ─────────────────────────────────────────────────

class TestAtomicShaper:
    def _g_spans(self, html: str) -> list[str]:
        return re.findall(r'<span class="g">(.*?)</span>', html)

    def _words(self, html: str) -> list[str]:
        # Non-greedy stops at the first inner </span> so we parse manually.
        results = []
        search = '<span class="word">'
        close  = '</span>'
        pos = 0
        while True:
            start = html.find(search, pos)
            if start == -1:
                break
            content_start = start + len(search)
            depth, i = 1, content_start
            while i < len(html) and depth:
                if html[i:i+6] == '<span ':
                    depth += 1; i += 6
                elif html[i:i+7] == close:
                    depth -= 1
                    if depth == 0:
                        break
                    i += 7
                else:
                    i += 1
            results.append(html[content_start:i])
            pos = i + len(close)
        return results

    def test_output_has_word_spans(self):
        html = atomic_shaper('ਸਤਿ ਨਾਮੁ')
        assert '<span class="word">' in html

    def test_output_has_g_spans(self):
        html = atomic_shaper('ਸਤਿ')
        assert '<span class="g">' in html

    def test_soft_hyphen_between_clusters(self):
        # ਨਿਰਵੈਰੁ has 4 clusters — 3 soft hyphens between them
        html = atomic_shaper('ਨਿਰਵੈਰੁ')
        words = self._words(html)
        assert len(words) == 1
        inner = words[0]
        assert inner.count(SOFT_HYPHEN) == 3, \
            f"Expected 3 soft hyphens, got {inner.count(SOFT_HYPHEN)}"

    def test_no_soft_hyphen_inside_g_span(self):
        html = atomic_shaper('ਸਤਿ ਨਾਮੁ ਕਰਤਾ')
        for g_content in self._g_spans(html):
            assert SOFT_HYPHEN not in g_content, \
                f"Soft hyphen found inside .g span: '{g_content}'"

    def test_combining_marks_not_in_own_span(self):
        html = atomic_shaper('ਸਤਿ ਨਿਰਵੈਰੁ ਮੂਰਤਿ')
        for g_content in self._g_spans(html):
            if g_content:
                assert unicodedata.category(g_content[0]) not in COMBINING, \
                    f"Combining mark starts a .g span: U+{ord(g_content[0]):04X}"

    def test_conjunct_in_single_g_span(self):
        # ਪ੍ਰਸਾਦਿ — ਪ੍ਰ must be in one span
        html = atomic_shaper('ਪ੍ਰਸਾਦਿ')
        spans = self._g_spans(html)
        assert 'ਪ੍ਰ' in spans, f"Conjunct ਪ੍ਰ not in a single .g span: {spans}"

    def test_nfc_normalization(self):
        # Input with decomposed characters should produce NFC output
        decomposed = unicodedata.normalize('NFD', 'ਸਤਿ')
        html = atomic_shaper(decomposed)
        for g_content in self._g_spans(html):
            assert unicodedata.normalize('NFC', g_content) == g_content, \
                f"Non-NFC text in .g span: {repr(g_content)}"

    def test_ik_onkar_single_g_span(self):
        html = atomic_shaper('ੴ')
        spans = self._g_spans(html)
        assert spans == ['ੴ'], f"ੴ split into multiple spans: {spans}"

    def test_multiple_words_separated_by_space(self):
        html = atomic_shaper('ਸਤਿ ਨਾਮੁ')
        words = self._words(html)
        assert len(words) == 2, f"Expected 2 word spans, got {len(words)}"

    def test_single_soft_hyphen_for_two_cluster_word(self):
        # ਸਤਿ = ਸ + ਤਿ → 1 soft hyphen
        html = atomic_shaper('ਸਤਿ')
        words = self._words(html)
        assert words[0].count(SOFT_HYPHEN) == 1
