"""
Shaper Stress Tests.

Tests the atomic shaper against the most complex Gurmukhi clusters found
in Gurbani to ensure that no combining marks are ever orphaned.
"""
import sys, os, unicodedata
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from modules.shaper.shaper import atomic_shaper, _grapheme_clusters

# Tricky words with multiple subscripts, bindi/tippi, or rare combinations
STRESS_WORDS = [
    "ਪ੍ਰੇਮ",      # Pa + Virama + Ra + Lanv + Tippa
    "ਕ੍ਰਿਪਾ",     # Ka + Virama + Ra + Sihari + Pa + Kanna
    "ਤ੍ਰੈ",       # Ta + Virama + Ra + Dulayv
    "ਦ੍ਵਾਰ",      # Da + Virama + Va + Kanna + Ra
    "ਸ੍ਵਾਮੀ",     # Sa + Virama + Va + Kanna + Ma + Bihari
    "ਅੰਮ੍ਰਿਤ",    # A + Tippa + Ma + Virama + Ra + Sihari + Ta
    "ਪ੍ਰਗਟੁ",     # Pa + Virama + Ra + Ga + Ta + Aunkar
    "ਬ੍ਰਹਮਾ",     # Ba + Virama + Ra + Haha + Virama + Ma + Kanna
    "ਗ੍ਰਿਹ",      # Ga + Virama + Ra + Sihari + Haha
    "ਪ੍ਰਥਮੇ",     # Pa + Virama + Ra + Tha + Ma + Lanv
    "ਸਤਿਗੁਰੂ",   # Sa + Ta + Sihari + Ga + Ra + Dulankar
    "ਨਿਰਭਉ",     # Na + Sihari + Ra + Bha + Hora
    "ਨਿਰਵੈਰੁ",    # Na + Sihari + Ra + Va + Dulayv + Ra + Aunkar
    "ੴ",         # Ik Onkar
    "ਸੰਸਾਰੁ",     # Sa + Tippa + Sa + Kanna + Ra + Aunkar
    "ਭ੍ਰਮੁ",       # Bha + Virama + Ra + Ma + Aunkar
]

COMBINING = frozenset({'Mn', 'Mc', 'Me'})

@pytest.mark.parametrize("word", STRESS_WORDS)
def test_complex_word_shaping(word):
    clusters = _grapheme_clusters(word)
    
    # 1. No cluster should be empty
    assert all(clusters), f"Empty cluster found in '{word}'"
    
    # 2. Re-joining clusters must equal original (NFC normalized)
    assert "".join(clusters) == unicodedata.normalize('NFC', word)
    
    # 3. No cluster should start with a combining mark
    for c in clusters:
        assert unicodedata.category(c[0]) not in COMBINING, \
            f"Cluster '{c}' in '{word}' starts with combining mark"

    # 4. Atomic shaper output check
    html = atomic_shaper(word)
    assert '<span class="g">' in html
    # Ensure all original characters are present in the HTML (minus tags/sh)
    clean_html = html.replace('<span class="word">', '').replace('<span class="g">', '').replace('</span>', '').replace('­', '')
    assert clean_html == unicodedata.normalize('NFC', word)
