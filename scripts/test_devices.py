import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from modules.tester.validator import validate_epub
from modules.tester.runner import render_all, SCENARIOS, PAGES_TO_CAPTURE
from modules.tester.device_profiles import ALL_DEVICES

EPUB_PATH = os.path.join(ROOT, 'output', 'Japji_Sahib.epub')


def _read_version() -> str:
    version_file = os.path.join(ROOT, 'VERSION')
    if os.path.exists(version_file):
        with open(version_file) as f:
            return f.read().strip()
    return 'unversioned'


if __name__ == '__main__':
    version = _read_version()
    version_dir = os.path.join(ROOT, 'output', f'v{version}')
    shots_per_device = len(SCENARIOS) * (PAGES_TO_CAPTURE + 1)
    total_shots = len(ALL_DEVICES) * shots_per_device

    print('=' * 60)
    print('Gurbani EInk Engine — Device Test Suite')
    print(f'EPUB version : {version}')
    print(f'Output       : output/v{version}/')
    print(f'Devices      : {len(ALL_DEVICES)}')
    print(f'Scenarios    : {len(SCENARIOS)}')
    print(f'Total shots  : {total_shots}')
    print('=' * 60)

    print()
    print('STEP 1 — EPUB Validation')
    print('-' * 40)
    issues = validate_epub(EPUB_PATH)
    for issue in issues:
        print(f'  {issue}')

    print()
    print('STEP 2 — Scenarios')
    print('-' * 40)
    for s in SCENARIOS:
        print(f'  [{s.slug}]')
        print(f'    {s.name}')
        print(f'    {s.description}')
    print()
    print('  [kepub_vs_epub] — MANUAL TEST ONLY')
    print('    Kobo handles standard EPUBs differently from its native KePub format.')
    print('    Sideload the EPUB to a physical Kobo and compare page-turn performance')
    print('    with a KePub conversion. No headless ADE renderer exists for automation.')

    print()
    print('STEP 3 — Rendering (WebKit)')
    print('-' * 40)
    results = render_all(EPUB_PATH, version_dir)

    current_device = None
    for device_name, scenario_slug, shots in results:
        if device_name != current_device:
            print(f'  {device_name}')
            current_device = device_name
        labels = [f'p{i+1}' for i in range(PAGES_TO_CAPTURE)] + ['zoom']
        print(f'    [{scenario_slug:<14}] {" · ".join(labels)}')

    total = sum(len(s) for _, _, s in results)
    print(f'\nDone. {total} screenshots saved to output/v{version}/')
