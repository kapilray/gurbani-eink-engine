import sys, os
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.getcwd())
from modules.tester.device_profiles import ALL_DEVICES

clara = [d for d in ALL_DEVICES if d.slug == 'kobo-clara-bw-2024'][0]
EPUB_PATH = 'output/Japji_Sahib.epub'

with sync_playwright() as p:
    browser = p.webkit.launch()
    page = browser.new_page()
    page.set_viewport_size({'width': clara.width, 'height': clara.height})
    
    import zipfile, shutil
    extract_dir = 'output/_debug_extract'
    shutil.rmtree(extract_dir, ignore_errors=True)
    os.makedirs(extract_dir)
    with zipfile.ZipFile(EPUB_PATH, 'r') as z:
        z.extractall(extract_dir)
        
    cover_path = os.path.abspath(os.path.join(extract_dir, 'EPUB/cover.xhtml'))
    page.goto(Path(cover_path).as_uri())
    
    sh = page.evaluate('document.body.scrollHeight')
    oh = page.evaluate('document.documentElement.offsetHeight')
    wh = page.evaluate('window.innerHeight')
    
    print(f'ScrollHeight: {sh}')
    print(f'OffsetHeight: {oh}')
    print(f'InnerHeight:  {wh}')
    print(f'DeviceHeight: {clara.height}')
    
    if sh > clara.height:
        print('FAIL: Cover overflows!')
    else:
        print('PASS: Cover fits.')
        
    browser.close()
    shutil.rmtree(extract_dir)
