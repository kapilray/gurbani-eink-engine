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

For each device, captures **4 screenshots**:
| File | What it shows |
|------|---------------|
| `{slug}_p1.png` | First viewport — what the reader sees on opening |
| `{slug}_p2.png` | Second viewport (scrolled 1 device-height) |
| `{slug}_p3.png` | Third viewport (scrolled 2 device-heights) |
| `{slug}_zoom.png` | Native-resolution crop of the text body — catches glyph/break issues invisible at full scale |

## Running

```bash
# Full suite: validate + 64 screenshots across 16 devices
.venv/bin/python3 scripts/test_devices.py
```

Output goes to `output/previews/`.

## Why WebKit

Both Kindle (Amazon's reader) and Kobo (Nickel firmware) use WebKit-based rendering engines. Playwright's `webkit` engine is the same Apple WebKit — a significantly closer proxy than Chromium for predicting how these devices will actually render the EPUB.

## Rendering Engine Note

Kobo's default renderer for standard `.epub` files is technically closer to Adobe Digital Editions (ADE) than pure WebKit. Only `.kepub` (Kobo's proprietary format) gets the full WebKit renderer. For standard EPUB testing, WebKit remains the best available headless proxy — no ADE headless renderer exists.

## Adding a New Device

Add a `DeviceProfile` entry to `device_profiles.py`:
```python
DeviceProfile('slug', 'Human Name', width, height, ppi, size_in, 'kindle'|'kobo', color=False)
```
It will automatically be included in the next test run.

## Adding a New Publication

Point `test_devices.py` at a different EPUB path. The validator and runner work on any EPUB built by the architect module — they check for Tiro Gurmukhi font embedding, `<span class="word">` elements, NFC integrity, and correct XHTML structure regardless of which Bani the content is.
