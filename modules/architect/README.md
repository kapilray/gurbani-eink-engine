# architect

Assembles the final EPUB3 from all pipeline outputs. The architect is designed for **any Bani or Gurbani-related text** — not just Japji Sahib. The `build_epub` function accepts any structured list of pauris/sections produced by a fetcher, so adding a new publication requires only a new fetcher and updated metadata.

## `build_epub(pauris, cover_path, font_path, css_path, output_path) → str`

Builds a complete, store-ready EPUB3 file:

1. **Cover image** — embedded via `set_cover()`, appears as the book thumbnail in reader libraries.
2. **Font** — Tiro Gurmukhi Regular embedded at `fonts/TiroGurmukhi-Regular.ttf`.
3. **CSS** — embedded at `styles/gurbani_base.css`; handles font-face, line spacing, word atomicity, center alignment, and line-type styling.
4. **Content chapter** — each Pauri/section is a `<div class="pauri">`, each line is a `<p class="line {type}">` with all words wrapped by the shaper.
5. **Credits chapter** (`credits.xhtml`) — lists cover artist, Gurbani data source, font, and development credits.
6. **Metadata** — Title, Gurmukhi title, author, language (`pa`), description.

## EPUB Internal Structure

```
EPUB/
├── content.opf              # Package manifest
├── nav.xhtml                # Navigation document
├── cover.xhtml              # Cover page
├── japji_sahib.xhtml        # Main Gurbani content
├── credits.xhtml            # Contributions page
├── fonts/
│   └── TiroGurmukhi-Regular.ttf
├── images/
│   └── cover.png
└── styles/
    └── gurbani_base.css
```

## CSS Path Note

The XHTML files sit at `EPUB/*.xhtml`. CSS is at `EPUB/styles/`. The stylesheet link must use `styles/gurbani_base.css` (no leading `../`).

## Credits Template

`credits_template.xhtml` — standalone template for the contributions page. Replace `{{ARTIST_NAME}}` and `{{ARTIST_URL}}` when the final cover art arrives.
