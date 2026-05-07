"""
Data Integrity (Lossless) Tests.

Ensures that no characters are lost or corrupted during the shaping and
EPUB packaging process. We strip all HTML tags and soft hyphens from the
generated EPUB and compare it against the source JSON from the fetcher.
"""
import sys, os, json, re, unicodedata, zipfile
from lxml import etree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

JSON_PATH = os.path.join(ROOT, 'modules', 'fetcher', 'japji_full.json')
EPUB_PATH = os.path.join(ROOT, 'output', 'Japji_Sahib.epub')
SOFT_HYPHEN = '­'
XHTML_NS = 'http://www.w3.org/1999/xhtml'

def test_no_text_lost_in_shaping():
    if not os.path.exists(EPUB_PATH):
        import pytest
        pytest.skip("EPUB not built yet. Run scripts/build.py first.")

    # 1. Load source text from JSON
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        source_data = json.load(f)
    
    source_text = ""
    for pauri in source_data:
        for line in pauri['lines']:
            source_text += line['text']
    
    # Normalize source
    source_text = unicodedata.normalize('NFC', source_text)
    # Remove whitespace for a robust comparison (shaper might adjust spaces)
    source_clean = re.sub(r'\s+', '', source_text)

    # 2. Extract text from EPUB
    epub_text = ""
    with zipfile.ZipFile(EPUB_PATH, 'r') as z:
        # Only look at content files
        skip = {'nav', 'cover', 'credits'}
        content_files = [
            n for n in z.namelist() 
            if n.endswith('.xhtml') and not any(s in n.lower() for s in skip)
        ]
        
        # Sort files to match source order (assuming file naming follows order)
        content_files.sort()
        
        for name in content_files:
            content = z.read(name)
            tree = etree.fromstring(content)
            # Only get text from <body> to avoid metadata like <title>
            body = tree.find(f".//{{{XHTML_NS}}}body")
            if body is not None:
                text = "".join(body.itertext())
                epub_text += text
            else:
                # Fallback if no body found (shouldn't happen)
                text = "".join(tree.itertext())
                epub_text += text

    # 3. Clean EPUB text
    # Remove soft hyphens
    epub_text = epub_text.replace(SOFT_HYPHEN, '')
    # Normalize
    epub_text = unicodedata.normalize('NFC', epub_text)
    # Remove whitespace
    epub_clean = re.sub(r'\s+', '', epub_text)

    # 4. Compare
    # Note: We use clean (no whitespace) because the shaper/architect might 
    # add structural whitespace or newlines for readability in the XHTML.
    assert source_clean == epub_clean, "Text mismatch: source and EPUB content do not match!"

if __name__ == "__main__":
    # Quick manual run
    try:
        test_no_text_lost_in_shaping()
        print("PASS: Data integrity verified.")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)
