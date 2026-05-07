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
    target: str = 'content'  # 'content' or 'nav'


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
        slug='font_system_sans',
        name='Font Override — Sans-serif',
        description='Forces Helvetica/Arial — reveals what breaks without embedded TiroGurmukhi (sans fallback)',
        css_override='''
            * { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif !important; }
        ''',
        font_scale=1.0,
    ),
    Scenario(
        slug='font_system_serif',
        name='Font Override — Serif',
        description='Forces Times New Roman/Georgia — reveals what breaks without embedded TiroGurmukhi (serif fallback)',
        css_override='''
            * { font-family: "Times New Roman", Times, Georgia, serif !important; }
        ''',
        font_scale=1.0,
    ),
    Scenario(
        slug='chapter_nav',
        name='Chapter Navigation (TOC)',
        description='Renders nav.xhtml — shows how Gurmukhi and English chapter names display in reader navigation',
        css_override='',
        font_scale=1.0,
        target='nav',
    ),
]


def extract_epub(epub_path: str, extract_dir: str) -> list[str]:
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    os.makedirs(extract_dir)
    with zipfile.ZipFile(epub_path, 'r') as z:
        z.extractall(extract_dir)
    
    xhtml_files = []
    # Important files in priority order
    priority = ['cover.xhtml', 'nav.xhtml', 'japji_sahib.xhtml', 'credits.xhtml']
    
    all_found = []
    for root, _, files in os.walk(extract_dir):
        for f in files:
            if f.endswith('.xhtml'):
                all_found.append(os.path.join(root, f))
    
    # Sort by priority, then by name
    def sort_key(path):
        fname = os.path.basename(path)
        try:
            return (priority.index(fname), fname)
        except ValueError:
            return (len(priority), fname)
            
    all_found.sort(key=sort_key)
    return all_found


def _find_nav(extract_dir: str) -> str | None:
    for root, _, files in os.walk(extract_dir):
        for f in files:
            if f == 'nav.xhtml':
                return os.path.join(root, f)
    return None


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

    extract_dir  = os.path.join(version_dir, '_epub_extracted')
    xhtml_paths  = extract_epub(epub_path, extract_dir)
    
    results = []
    with sync_playwright() as p:
        browser = p.webkit.launch()
        page    = browser.new_page()

        for device in devices:
            for scenario in scenarios:
                for xhtml_path in xhtml_paths:
                    fname = os.path.basename(xhtml_path).replace('.xhtml', '')
                    
                    # Skip nav in non-nav scenarios and vice-versa to keep output manageable
                    if scenario.target == 'nav' and fname != 'nav':
                        continue
                    if scenario.target == 'content' and fname == 'nav':
                        continue
                    
                    url = Path(os.path.abspath(xhtml_path)).as_uri()
                    # Include the filename in the slug if it's not the main content
                    sub_slug = scenario.slug
                    if fname != 'japji_sahib' and scenario.target != 'nav':
                        sub_slug = f"{scenario.slug}_{fname}"
                        
                    shot_dir = os.path.join(version_dir, device.slug, sub_slug)
                    os.makedirs(shot_dir, exist_ok=True)
                    shots = _render_device(page, device, scenario, url, shot_dir)
                    results.append((device.name, sub_slug, shots))

        browser.close()

    shutil.rmtree(extract_dir, ignore_errors=True)

    return results
