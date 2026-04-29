import unicodedata

_COMBINING = frozenset({'Mn', 'Mc', 'Me'})


_GURMUKHI_VIRAMA = '੍'  # U+0A4D — virama binds the following consonant into a conjunct

def _grapheme_clusters(word: str) -> list[str]:
    """Split a word into grapheme clusters: each base letter + all its combining marks.

    Virama (੍) is kept with its following consonant so conjuncts like ਪ੍ਰ stay
    in one span — splitting them would break subscript shaping in the renderer.
    """
    clusters: list[str] = []
    current: list[str] = []
    for ch in word:
        if current and unicodedata.category(ch) not in _COMBINING:
            if current[-1] == _GURMUKHI_VIRAMA:
                # Following consonant belongs to same conjunct — keep together
                current.append(ch)
            else:
                clusters.append(''.join(current))
                current = [ch]
        else:
            current.append(ch)
    if current:
        clusters.append(''.join(current))
    return clusters


def atomic_shaper(text: str) -> str:
    """NFC-normalize and wrap: each word in .word, each grapheme cluster in .g.

    Two-layer protection against kepubify koboSpan injection splitting
    Gurmukhi combining marks (sihari, bihari, hora …) from their base consonants:
    - Inner .g spans: each span is one complete grapheme cluster — kepubify can
      only split between .g spans, never inside one
    - Outer .word spans: white-space: nowrap prevents line breaks between clusters
      within a word
    """
    normalized = unicodedata.normalize('NFC', text)
    parts: list[str] = []
    for word in normalized.split():
        clusters = _grapheme_clusters(word)
        inner = ''.join(f'<span class="g">{c}</span>' for c in clusters)
        parts.append(f'<span class="word">{inner}</span>')
    return ' '.join(parts)
