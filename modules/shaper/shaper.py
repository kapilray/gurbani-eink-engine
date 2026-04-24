import unicodedata

def atomic_shaper(text):
    # NFC Normalization is mandatory for Indic scripts
    normalized = unicodedata.normalize('NFC', text)
    words = normalized.split()
    # CSS white-space: nowrap on .word handles line-break prevention — no format chars needed
    return ' '.join([f'<span class="word">{w}</span>' for w in words])
