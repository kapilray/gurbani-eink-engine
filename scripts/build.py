import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from modules.fetcher.fetcher import load_japji
from modules.architect.architect import build_epub

COVER_PATH  = os.path.join(ROOT, 'assets', 'branding', 'cover_color.png')
FONT_PATH   = os.path.join(ROOT, 'assets', 'fonts', 'TiroGurmukhi-Regular.ttf')
CSS_PATH    = os.path.join(ROOT, 'assets', 'gurbani_base.css')
OUTPUT_PATH = os.path.join(ROOT, 'output', 'Japji_Sahib.epub')

if __name__ == '__main__':
    print('Loading Japji Sahib from Shabad OS database...')
    pauris = load_japji()
    total_lines = sum(len(p['lines']) for p in pauris)
    print(f'  {len(pauris)} pauris, {total_lines} lines')

    print('Building EPUB...')
    out = build_epub(pauris, COVER_PATH, FONT_PATH, CSS_PATH, OUTPUT_PATH)
    print(f'Done → {out}')
