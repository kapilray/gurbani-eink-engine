import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from modules.fetcher.fetcher import load_japji
from modules.architect.architect import build_epub

FONT_PATH   = os.path.join(ROOT, 'assets', 'fonts', 'TiroGurmukhi-Regular.ttf')
CSS_PATH    = os.path.join(ROOT, 'assets', 'gurbani_base.css')
COVER_PATH  = os.path.join(ROOT, 'assets', 'branding', 'cover_color.png')
OUTPUT_PATH = os.path.join(ROOT, 'output', 'Japji_Sahib.epub')

def _read_version() -> str:
    try:
        with open(os.path.join(ROOT, 'VERSION')) as f:
            return f.read().strip()
    except OSError:
        return ''

if __name__ == '__main__':
    version = _read_version()
    print(f'Building Japji Sahib EPUB v{version}...')
    pauris = load_japji()
    total_lines = sum(len(p['lines']) for p in pauris)
    print(f'  {len(pauris)} pauris, {total_lines} lines')

    out = build_epub(pauris, FONT_PATH, CSS_PATH, COVER_PATH, OUTPUT_PATH, version=version)
    print(f'Done → {out}')
