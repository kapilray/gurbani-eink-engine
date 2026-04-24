# Gurbani-EInk Engine

A purpose-built pipeline for producing pixel-perfect, reflowable EPUBs of Gurbani and Gurbani-related texts — optimized for every major Kindle and Kobo e-ink device.

The first publication is **Japji Sahib** by Guru Nanak Dev Ji, with cover art by [RAVINARTOOR](https://ravinartoor.com) *(permission pending — see [issue #1](https://github.com/kapilray/gurbani-eink-engine/issues/1))*.

> **Found a bug or rendering issue?** [Open an issue →](https://github.com/your-org/gurbani-eink-engine/issues/new) or email [1guru.rakha@gmail.com](mailto:1guru.rakha@gmail.com)

---

## Credits

| Contribution | Credit |
|---|---|
| **Cover Art** | [RAVINARTOOR](https://ravinartoor.com) *(permission pending)* |
| **Gurbani Source** | [Shabad OS Database](https://github.com/shabados/database) |
| **Font** | [Tiro Gurmukhi](https://github.com/TiroTypeworks) — Tiro Typeworks (OFL License) |
| **Source Text** | Sri Guru Granth Sahib Ji — Public Domain |

---

## Why This Exists

E-ink readers are the most peaceful way to read. The low refresh rate, paper-like texture, and distraction-free form factor make them ideal for Gurbani. But standard Gurmukhi text on e-readers breaks constantly — words split mid-character, vowel signs detach from their base consonants, and fonts render diacritics as boxes.

This project solves that at the source: every word is wrapped atomically, every character is NFC-normalized, the font is embedded directly in the file, and the output is tested at the exact pixel dimensions of 16 real devices before anything ships.

This pipeline is built for **all Gurbani and Gurbani-related texts** — not just Japji Sahib. Japji Sahib is the first publication; the architecture is designed to produce any Bani from the Shabad OS database with a single command.

---

## Project Structure

```
gurbani-eink-engine/
├── assets/
│   ├── fonts/                  # Tiro Gurmukhi (Regular + Italic, embedded in EPUB)
│   ├── branding/               # Cover art pipeline (cover_prep.py)
│   └── gurbani_base.css        # Defensive CSS — font, word atomicity, center alignment
│
├── modules/
│   ├── fetcher/                # Pulls Gurbani from Shabad OS SQLite database
│   ├── shaper/                 # NFC normalization + reflow-safe HTML wrapping
│   ├── architect/              # Assembles EPUB with cover, content, credits
│   └── tester/                 # Automated multi-device rendering via Playwright WebKit
│
├── scripts/
│   ├── build.py                # Build the EPUB
│   └── test_devices.py         # Run 16-device render suite (64 screenshots)
│
├── docs/
│   └── publishing_guidelines.md
│
└── output/
    ├── Japji_Sahib.epub
    └── previews/               # 64 PNGs (3 pages + zoom per device)
```

---

## Quick Start

```bash
# 1. Create virtual environment and install Python dependencies
python3 -m venv .venv
.venv/bin/pip install ebooklib pillow playwright lxml

# 2. Install Playwright's WebKit browser
.venv/bin/playwright install webkit

# 3. Install Node.js fetcher dependencies (run once from the fetcher folder)
npm install --prefix modules/fetcher

# 4. Build the EPUB
.venv/bin/python3 scripts/build.py

# 5. Test across all 16 devices (generates 64 screenshots)
.venv/bin/python3 scripts/test_devices.py

# 6. Swap in new cover art and rebuild
.venv/bin/python3 assets/branding/cover_prep.py --input path/to/art.jpg
.venv/bin/python3 scripts/build.py
```

---

## Tech Stack

| Layer | Tool | Why |
|-------|------|-----|
| Data | Shabad OS SQLite DB (v4.8.7) | Authoritative, versioned Gurbani source |
| Fetcher | Node.js + `@shabados/gurmukhi-utils` | Only library with correct ASCII→Unicode Gurmukhi conversion |
| Shaper | Python + `unicodedata` | NFC normalization + atomic word wrapping |
| EPUB | `ebooklib` | EPUB3 packaging with embedded font + cover |
| Font | Tiro Gurmukhi (OFL) | Designed for Gurmukhi — correct glyph shaping at e-ink resolution |
| Testing | Playwright WebKit | WebKit is the actual rendering engine used by both Kindle and Kobo |
| Cover | Pillow | Resize, grayscale conversion, text overlay at 1:1.6 ratio |

---

## Device Coverage

### Kindle
| Device | Screen | PPI |
|--------|--------|-----|
| Kindle 11th gen (2024) | 6" — 1072×1448 | 300 |
| Kindle Paperwhite 11th gen (2021) | 6.8" — 1236×1648 | 300 |
| Kindle Paperwhite 12th gen (2024) | 7" — 1264×1680 | 300 |
| Kindle Colorsoft (2024) | 7" — 1264×1680 | 300 |
| Kindle Colorsoft SE (2025) | 7" — 1264×1680 | 300 |
| Kindle Oasis 10th gen (2019) | 7" — 1264×1680 | 300 |
| Kindle Scribe 2nd gen (2024) | 10.2" — 1860×2480 | 300 |
| Kindle Scribe 3rd gen (2025) | 11" — 1980×2640 | 300 |
| Kindle Scribe Colorsoft (2025) | 11" — 1980×2640 | 300 |

### Kobo
| Device | Screen | PPI |
|--------|--------|-----|
| Kobo Clara BW (2024) | 6" — 1072×1448 | 300 |
| Kobo Clara Colour (2024) | 6" — 1072×1448 | 300 |
| Kobo Libra 2 | 7" — 1264×1680 | 300 |
| Kobo Libra Colour (2024) | 7" — 1264×1680 | 300 |
| Kobo Sage | 8" — 1440×1920 | 300 |
| Kobo Forma | 8" — 1440×1920 | 300 |
| Kobo Elipsa 2E | 10.3" — 1404×1872 | 227 |
