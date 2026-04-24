# tester

Automated multi-device rendering and validation for any Gurbani or Gurbani-related EPUB produced by this pipeline. The test suite is publication-agnostic — it validates and renders any EPUB that follows the engine's structural conventions.

## Modules

### `device_profiles.py`
Registry of all 16 supported Kindle and Kobo devices with exact pixel dimensions, PPI, and color capability. Each profile computes a proportional `font_size_px` and `margin_px` for the test render.

### `validator.py`
Runs structural checks on the EPUB before rendering:
- Font files present in the archive
- Font declared in the OPF manifest
- Content XHTML is well-formed XML
- `<span class="word">` elements exist (shaper ran)
- No U+2060 Word Joiner characters in content (renders as circles in some readers)
- NFC normalization integrity on sampled spans

### `runner.py`
Uses **Playwright WebKit** (the same engine Kindle and Kobo use) to render the content XHTML at exact device pixel dimensions and capture screenshots.

For each device × scenario, captures **4 screenshots** inside `output/v{version}/{device_slug}/{scenario}/`:

| File | What it shows |
|------|---------------|
| `p1.png` | First viewport — what the reader sees on opening |
| `p2.png` | Second viewport (scrolled 1 device-height) |
| `p3.png` | Third viewport (scrolled 2 device-heights) |
| `zoom.png` | Native-resolution crop of the text body — catches glyph/break issues invisible at full scale |

## Scenarios

| Slug | Name | Goal |
|------|------|------|
| `standard` | Standard (Publisher Default) | Baseline render at device default font size |
| `large_font` | Large Font | Font at 2× device default — stress-tests word atomicity and reflow |
| `small_font` | Small Font | Font at 0.7× device default — verifies legibility at compact sizes |
| `dark_mode` | Dark Mode / Night Mode | Catches hardcoded CSS colors that become invisible on dark backgrounds |
| `font_override` | Font Override (Publisher Default Lock) | Forces system sans-serif — reveals exactly what breaks without embedded TiroGurmukhi |

### Manual test: KePub vs EPUB

Kobo handles standard `.epub` files differently from its native `.kepub` format — only KePub gets the full WebKit renderer; standard EPUBs go through a closer-to-ADE path. No headless ADE renderer exists, so this cannot be automated.

**How to run manually:**
1. Sideload `Japji_Sahib.epub` onto a Kobo device
2. Note page-turn speed and rendering quality
3. Convert to KePub using Calibre + KePub Output plugin
4. Sideload the KePub and compare

## Output structure

```
output/
  v1.0.0/
    kindle-11-2024/
      standard/
        p1.png  p2.png  p3.png  zoom.png
      large_font/
        p1.png  p2.png  p3.png  zoom.png
      dark_mode/
        ...
    kobo-clara-bw-2024/
      ...
```

Versioned output directories (`output/v*/`) are in `.gitignore` — screenshots are build artifacts, not source. Commit the `VERSION` file; run the suite locally or in CI to regenerate.

## Running

```bash
# Full suite: validate + render all 16 devices × 5 scenarios = 320 screenshots
.venv/bin/python3 scripts/test_devices.py
```

## Why WebKit

Both Kindle (Amazon's AZW3 reader) and Kobo KePub use WebKit-based rendering engines. Playwright's `webkit` engine is the same Apple WebKit — a significantly closer proxy than Chromium for predicting how these devices will actually render the EPUB.

## Adding a new device

Add a `DeviceProfile` entry to `device_profiles.py`:
```python
DeviceProfile('slug', 'Human Name', width, height, ppi, size_in, 'kindle'|'kobo', color=False)
```
It will automatically be included in the next test run.

## Adding a new scenario

Add a `Scenario` entry to the `SCENARIOS` list in `runner.py`:
```python
Scenario(
    slug='my_scenario',
    name='Human Name',
    description='What this tests and why',
    css_override='/* CSS injected on top of device CSS */',
    font_scale=1.0,
)
```

## Adding a new publication

Point `test_devices.py` at a different EPUB path. The validator and runner work on any EPUB built by the architect module — they check for Tiro Gurmukhi font embedding, `<span class="word">` elements, NFC integrity, and correct XHTML structure regardless of which Bani the content is.
