import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from modules.tester.validator import validate_epub
from modules.tester.runner import render_all, SCENARIOS, PAGES_TO_CAPTURE
from modules.tester.device_profiles import ALL_DEVICES
from modules.tester.differ import compute_diff

EPUB_PATH = os.path.join(ROOT, 'output', 'Japji_Sahib.epub')


def _read_version() -> str:
    version_file = os.path.join(ROOT, 'VERSION')
    if os.path.exists(version_file):
        with open(version_file) as f:
            return f.read().strip()
    return 'unversioned'


def _find_baseline(current_version: str) -> str | None:
    output_dir = os.path.join(ROOT, 'output')
    versions = [d for d in os.listdir(output_dir) if d.startswith('v') and os.path.isdir(os.path.join(output_dir, d))]
    versions.sort(key=lambda x: [int(p) for p in re.findall(r'\d+', x)])
    
    baseline = None
    for v in versions:
        if v == f'v{current_version}':
            break
        baseline = v
    return os.path.join(output_dir, baseline) if baseline else None


if __name__ == '__main__':
    import re
    version = _read_version()
    version_dir = os.path.join(ROOT, 'output', f'v{version}')
    baseline_dir = _find_baseline(version)
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

    print()
    print('STEP 4 — Visual Regression (Diff)')
    print('-' * 40)
    if not baseline_dir:
        print('  [SKIP] No baseline version found for comparison.')
    else:
        print(f'  Baseline: {os.path.basename(baseline_dir)}')
        regressions = []
        for device_name, scenario_slug, shots in results:
            # Reconstruct device slug from shots path if needed, but results has device name
            # Actually, the results gives (device_name, scenario_slug, [shots])
            # Let's get the device slug from the first shot's path
            if not shots: continue
            device_slug = os.path.basename(os.path.dirname(os.path.dirname(shots[0])))
            
            for shot_path in shots:
                rel_path = os.path.relpath(shot_path, version_dir)
                base_shot = os.path.join(baseline_dir, rel_path)
                
                if os.path.exists(base_shot):
                    diff_score = compute_diff(shot_path, base_shot)
                    if diff_score > 0.001: # 0.1% threshold
                        regressions.append((rel_path, diff_score))
        
        if regressions:
            print(f'  [FAIL] {len(regressions)} screenshots deviated from baseline!')
            for rel, score in regressions[:10]:
                print(f'    {rel:<40} diff: {score:.2%}')
            if len(regressions) > 10:
                print(f'    ... and {len(regressions) - 10} more')
        else:
            print('  [PASS] No visual regressions detected.')

    print()
    print('Summary')
    print('-' * 40)
    current_device = None
    for device_name, scenario_slug, shots in results:
        if device_name != current_device:
            print(f'  {device_name}')
            current_device = device_name
        labels = [f'p{i+1}' for i in range(PAGES_TO_CAPTURE)] + ['zoom']
        print(f'    [{scenario_slug:<14}] {" · ".join(labels)}')

    total = sum(len(s) for _, _, s in results)
    print(f'\nDone. {total} screenshots saved to output/v{version}/')
