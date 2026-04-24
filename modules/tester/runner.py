import os
import shutil
import zipfile
from pathlib import Path
from playwright.sync_api import sync_playwright
from modules.tester.device_profiles import DeviceProfile, ALL_DEVICES

# How many viewport-height pages to capture per device
PAGES_TO_CAPTURE = 3
# Zoom crop: capture this fraction of the viewport width/height for the zoom shot
ZOOM_FRACTION = 0.45


def extract_epub(epub_path: str, extract_dir: str) -> str:
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    os.makedirs(extract_dir)
    with zipfile.ZipFile(epub_path, 'r') as z:
        z.extractall(extract_dir)
    # Prefer japji_sahib.xhtml; skip nav/cover/credits
    skip = {'nav.xhtml', 'cover.xhtml', 'credits.xhtml'}
    for root, _, files in os.walk(extract_dir):
        for f in sorted(files):
            if f.endswith('.xhtml') and f not in skip:
                return os.path.join(root, f)
    raise FileNotFoundError('No content XHTML found in EPUB')


def _device_css(device: DeviceProfile) -> str:
    grayscale = '' if device.color else 'html { filter: grayscale(100%) contrast(120%); }'
    return f"""
    body {{
        font-size: {device.font_size_px}px !important;
        margin: 0 !important;
        padding: {device.margin_px}px !important;
        max-width: {device.width - device.margin_px * 2}px !important;
        background: white !important;
        color: black !important;
        text-align: center !important;
    }}
    {grayscale}
    """


def _render_device(page, device: DeviceProfile, file_url: str, out_dir: str) -> list[str]:
    page.set_viewport_size({'width': device.width, 'height': device.height})
    page.goto(file_url, wait_until='networkidle')
    page.add_style_tag(content=_device_css(device))
    page.wait_for_timeout(400)

    saved = []

    # Pages 1–N: scroll one viewport-height at a time
    for n in range(PAGES_TO_CAPTURE):
        scroll_y = device.height * n
        page.evaluate(f'window.scrollTo(0, {scroll_y})')
        page.wait_for_timeout(100)
        out_path = os.path.join(out_dir, f'{device.slug}_p{n + 1}.png')
        page.screenshot(path=out_path, full_page=False)
        saved.append(out_path)

    # Zoom crop: capture center of page 1 at full native resolution
    # Clips a ZOOM_FRACTION × ZOOM_FRACTION window from the text area
    page.evaluate('window.scrollTo(0, 0)')
    page.wait_for_timeout(100)
    clip_w = int(device.width  * ZOOM_FRACTION * 2)   # wider crop
    clip_h = int(device.height * ZOOM_FRACTION)
    clip_x = (device.width  - clip_w) // 2
    clip_y = device.margin_px + int(device.font_size_px * 2)  # skip first line, zoom into body
    zoom_path = os.path.join(out_dir, f'{device.slug}_zoom.png')
    page.screenshot(
        path=zoom_path,
        full_page=False,
        clip={'x': clip_x, 'y': clip_y, 'width': clip_w, 'height': clip_h}
    )
    saved.append(zoom_path)

    return saved


def render_all(epub_path: str, output_dir: str, devices: list[DeviceProfile] = None) -> list[tuple[str, list[str]]]:
    if devices is None:
        devices = ALL_DEVICES

    extract_dir = os.path.join(output_dir, '_epub_extracted')
    preview_dir = os.path.join(output_dir, 'previews')
    os.makedirs(preview_dir, exist_ok=True)

    xhtml_path = extract_epub(epub_path, extract_dir)
    file_url   = Path(xhtml_path).as_uri()

    results = []
    # Both Kindle and Kobo use WebKit-based renderers
    with sync_playwright() as p:
        browser = p.webkit.launch()
        page    = browser.new_page()

        for device in devices:
            shots = _render_device(page, device, file_url, preview_dir)
            results.append((device.name, shots))

        browser.close()

    return results
