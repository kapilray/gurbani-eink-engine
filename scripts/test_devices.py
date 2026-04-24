import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from modules.tester.validator import validate_epub
from modules.tester.runner import render_all, PAGES_TO_CAPTURE
from modules.tester.device_profiles import ALL_DEVICES

EPUB_PATH  = os.path.join(ROOT, 'output', 'Japji_Sahib.epub')
OUTPUT_DIR = os.path.join(ROOT, 'output')

if __name__ == '__main__':
    print('=' * 60)
    print('STEP 1 — EPUB Validation')
    print('=' * 60)
    issues = validate_epub(EPUB_PATH)
    for issue in issues:
        print(f'  {issue}')

    print()
    print('=' * 60)
    print(f'STEP 2 — Device Rendering ({len(ALL_DEVICES)} devices × {PAGES_TO_CAPTURE} pages + zoom, WebKit)')
    print('=' * 60)
    results = render_all(EPUB_PATH, OUTPUT_DIR)
    for name, shots in results:
        labels = [f'p{i+1}' for i in range(PAGES_TO_CAPTURE)] + ['zoom']
        print(f'  ✓  {name}')
        for label, path in zip(labels, shots):
            print(f'      [{label}] {os.path.basename(path)}')

    total = sum(len(s) for _, s in results)
    print(f'\nDone. {total} screenshots in output/previews/')
