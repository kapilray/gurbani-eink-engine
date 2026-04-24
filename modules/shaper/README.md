# shaper

Reflow-proofs Gurmukhi text for e-ink display. This module operates on any Gurbani or Gurbani-related text — not just Japji Sahib. Any Unicode Gurmukhi string can be passed through `atomic_shaper`.

## `atomic_shaper(text) → str`

1. **NFC normalization** — mandatory for Indic scripts. Ensures combining vowel signs (matras) are in canonical composed form, preventing decomposed diacritics from floating loose.
2. **Split on whitespace** — produces individual words.
3. **Span wrapping** — wraps each word in `<span class="word">`. Combined with `white-space: nowrap` in the CSS, this makes each word an unbreakable typographic atom.

Returns an HTML fragment. The caller wraps it in a block element (`<p>`, `<div>`, etc.).

## Why no U+2060 Word Joiner between characters

An earlier version injected U+2060 between every character inside each word. This caused the character to render as visible circles in Apple Books and other readers that fall back to a system font for format-control characters not present in Tiro Gurmukhi. The CSS `white-space: nowrap` on `.word` spans is sufficient and produces no visual artifacts.

## What the shaper does NOT do

- Script shaping (OpenType GSUB/GPOS) — handled by the font engine
- Vishraam (pause) marker handling — handled by the fetcher before text reaches the shaper
- Unicode normalization of oora/ira forms — handled by the fetcher's `normalizeVowels()` pass

## Scope

The shaper is Bani-agnostic. It works on any normalized Unicode Gurmukhi input — Japji Sahib, Anand Sahib, Sukhmani Sahib, Nitnem, or any text from the Shabad OS database. No changes needed when adding new publications.
