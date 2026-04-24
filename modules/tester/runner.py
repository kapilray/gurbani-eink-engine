import os
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from playwright.sync_api import sync_playwright
from modules.tester.device_profiles import DeviceProfile, ALL_DEVICES

PAGES_TO_CAPTURE = 3
ZOOM_FRACTION = 0.45


@dataclass
class Scenario:
    slug: str
    name: str
    description: str
    css_override: str
    font_scale: float = 1.0


SCENARIOS = [
    Scenario(
        slug='standard',
        name='Standard (Publisher Default)',
        description='Publisher CSS at device default font size — baseline render',
        css_override='',
        font_scale=1.0,
    ),
    Scenario(
        slug='large_font',
        name='Large Font',
        description='Font at 2× device default — stress-tests reflow and word atomicity',
        css_override='',
        font_scale=2.0,
    ),
    Scenario(
        slug='small_font',
        name='Small Font',
        description='Font at 0.7× device default — verifies legibility at compact sizes',
        css_override='',
        font_scale=0.7,
    ),
    Scenario(
        slug='dark_mode',
        name='Dark Mode / Night Mode',
        description='Simulates device dark mode — catches hardcoded colors that vanish on dark backgrounds',
        css_override='''
            html { background: #1a1a1a !important; }
            body { background: #1a1a1a !important; color: #e8e8e8 !important; }
        ''',
        font_scale=1.0,
    ),
    Scenario(
        slug='font_override',
        name='Font Override (Publisher Default Lock)',
        description='Forces system sans-serif — reveals exactly what breaks without embedded TiroGurmukhi',
        css_override='''
            * { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif !important; }
        ''',
        font_scale=1.0,
    ),
]


def extract_epub(epub_path: str, extract_dir: str) -> str:
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    os.makedirs(extract_dir)
    with zipfile.ZipFile(epub_path, 'r') as z:
        z.extractall(extract_dir)
    skip = {'nav.xhtml', 'cover.xhtml', 'credits.xhtml'}
    for root, _, files in os.walk(extract_dir):
        for f in sorted(files):
            if f.endswith('.xhtml') and f not in skip:
                return os.path.join(root, f)
    raise FileNotFoundError('No content XHTML found in EPUB')


def _device_css(device: DeviceProfile, scenario: Scenario) -> str:
    grayscale = '' if device.color else 'html { filter: grayscale(100%) contrast(120%); }'
    font_size = int(device.font_size_px * scenario.font_scale)
    base = f"""
    body {{
        font-size: {font_size}px !important;
        margin: 0 !important;
        padding: {device.margin_px}px !important;
        max-width: {device.width - device.margin_px * 2}px !important;
        background: white !important;
        color: black !important;
        text-align: center !important;
    }}
    {grayscale}
    """
    return base + '\n' + scenario.css_override


def _render_device(
    page,
    device: DeviceProfile,
    scenario: Scenario,
    file_url: str,
    out_dir: str,
) -> list[str]:
    page.set_viewport_size({'width': device.width, 'height': device.height})
    page.goto(file_url, wait_until='networkidle')
    page.add_style_tag(content=_device_css(device, scenario))
    page.wait_for_timeout(400)

    saved = []

    for n in range(PAGES_TO_CAPTURE):
        scroll_y = device.height * n
        page.evaluate(f'window.scrollTo(0, {scroll_y})')
        page.wait_for_timeout(100)
        out_path = os.path.join(out_dir, f'p{n + 1}.png')
        page.screenshot(path=out_path, full_page=False)
        saved.append(out_path)

    page.evaluate('window.scrollTo(0, 0)')
    page.wait_for_timeout(100)
    clip_w = int(device.width  * ZOOM_FRACTION * 2)
    clip_h = int(device.height * ZOOM_FRACTION)
    clip_x = (device.width  - clip_w) // 2
    clip_y = device.margin_px + int(device.font_size_px * 2)
    zoom_path = os.path.join(out_dir, 'zoom.png')
    page.screenshot(
        path=zoom_path,
        full_page=False,
        clip={'x': clip_x, 'y': clip_y, 'width': clip_w, 'height': clip_h},
    )
    saved.append(zoom_path)

    return saved


def render_all(
    epub_path: str,
    version_dir: str,
    devices: list[DeviceProfile] = None,
    scenarios: list[Scenario] = None,
) -> list[tuple[str, str, list[str]]]:
    if devices is None:
        devices = ALL_DEVICES
    if scenarios is None:
        scenarios = SCENARIOS

    extract_dir = os.path.join(version_dir, '_epub_extracted')
    xhtml_path = extract_epub(epub_path, extract_dir)
    file_url   = Path(xhtml_path).as_uri()

    results = []
    with sync_playwright() as p:
        browser = p.webkit.launch()
        page    = browser.new_page()

        for device in devices:
            for scenario in scenarios:
                shot_dir = os.path.join(version_dir, device.slug, scenario.slug)
                os.makedirs(shot_dir, exist_ok=True)
                shots = _render_device(page, device, scenario, file_url, shot_dir)
                results.append((device.name, scenario.slug, shots))

        browser.close()

    shutil.rmtree(extract_dir, ignore_errors=True)

    return results
