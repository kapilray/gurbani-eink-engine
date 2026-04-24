import zipfile
from lxml import etree

XHTML_NS = 'http://www.w3.org/1999/xhtml'

def validate_epub(epub_path: str) -> list[str]:
    issues = []

    with zipfile.ZipFile(epub_path, 'r') as z:
        names = z.namelist()

        # 1. Font embedded
        font_files = [n for n in names if n.endswith('.ttf') or n.endswith('.otf')]
        if not font_files:
            issues.append('FAIL [font-embed] No font files found inside EPUB')

        # 2. OPF declares the font
        opf_files = [n for n in names if n.endswith('.opf')]
        if not opf_files:
            issues.append('FAIL [opf] No OPF/package file found')
        else:
            opf_content = z.read(opf_files[0])
            if b'font' not in opf_content.lower():
                issues.append('FAIL [opf-font] Font not declared in OPF manifest')

        # 3. Content XHTML checks
        # Only validate Gurmukhi content files — skip nav, cover, credits
        skip = {'nav', 'cover', 'credits'}
        content_xhtml = [
            n for n in names
            if n.endswith('.xhtml')
            and not any(s in n.lower() for s in skip)
        ]
        for xhtml_name in content_xhtml:
            content = z.read(xhtml_name)

            # 3a. Well-formed XML
            try:
                root = etree.fromstring(content)
            except etree.XMLSyntaxError as e:
                issues.append(f'FAIL [xhtml-wellformed] {xhtml_name}: {e}')
                continue

            # 3b. Word spans present (shaper ran)
            spans = root.findall(f'.//{{{XHTML_NS}}}span[@class="word"]')
            if not spans:
                issues.append(f'FAIL [word-spans] {xhtml_name}: no <span class="word"> elements — shaper may not have run')

            # 3c. No U+2060 Word Joiner in text (invisible char rendering bug)
            if '⁠' in content.decode('utf-8', errors='ignore'):
                issues.append(f'FAIL [word-joiner] {xhtml_name}: U+2060 Word Joiner found — renders as visible circles in some readers')

            # 3d. NFC normalization check (sample first span)
            import unicodedata
            for span in spans[:5]:
                text = ''.join(span.itertext())
                if unicodedata.normalize('NFC', text) != text:
                    issues.append(f'FAIL [nfc] {xhtml_name}: text is not NFC-normalized')
                    break

        if not issues:
            issues.append('PASS — all checks passed')

    return issues
