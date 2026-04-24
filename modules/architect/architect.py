import io
import os
from PIL import Image
from ebooklib import epub
from modules.shaper.shaper import atomic_shaper


def _read(path: str, mode='r', encoding='utf-8'):
    if mode == 'rb':
        with open(path, 'rb') as f:
            return f.read()
    with open(path, encoding=encoding) as f:
        return f.read()


def _cover_to_jpeg(cover_path: str, quality: int = 85) -> bytes:
    with Image.open(cover_path) as img:
        if img.mode not in ('RGB',):
            img = img.convert('RGB')
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=quality, optimize=True)
        return buf.getvalue()


def _build_content_xhtml(pauris: list[dict]) -> str:
    parts = []
    for pauri in pauris:
        parts.append('<div class="pauri">')
        for line in pauri['lines']:
            shaped = atomic_shaper(line['text'])
            parts.append(f'  <p class="line {line["type"]}">{shaped}</p>')
        parts.append('</div>')

    body = '\n'.join(parts)
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="pa" lang="pa">
<head>
  <meta charset="utf-8"/>
  <title>ਜਪੁਜੀ ਸਾਹਿਬ</title>
  <link rel="stylesheet" type="text/css" href="styles/gurbani_base.css"/>
</head>
<body>
{body}
</body>
</html>'''


def _build_credits_xhtml(css_href: str = 'styles/gurbani_base.css') -> str:
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
  <meta charset="utf-8"/>
  <title>Contributions</title>
  <link rel="stylesheet" type="text/css" href="{css_href}"/>
</head>
<body>
<div class="credits-page">
  <p class="credits-heading">Contributions</p>

  <div class="credit-row">
    <span class="credit-label">Cover Art</span>
    <span class="credit-value"><a href="https://ravinartoor.com">RAVINARTOOR</a></span>
  </div>

  <div class="credit-row">
    <span class="credit-label">Gurbani Data</span>
    <span class="credit-value">Shabad OS — <a href="https://shabados.com">shabados.com</a></span>
  </div>

  <div class="credit-row">
    <span class="credit-label">Font</span>
    <span class="credit-value">Tiro Gurmukhi — Tiro Typeworks (OFL)</span>
  </div>

  <div class="credit-row">
    <span class="credit-label">Development</span>
    <span class="credit-value">Gurbani-EInk Team</span>
  </div>

  <div class="credit-row">
    <span class="credit-label">Source Text</span>
    <span class="credit-value">Sri Guru Granth Sahib Ji — Public Domain</span>
  </div>
</div>
</body>
</html>'''


def build_epub(
    pauris:      list[dict],
    cover_path:  str,
    font_path:   str,
    css_path:    str,
    output_path: str,
) -> str:
    css_content = _read(css_path)
    font_bytes  = _read(font_path, mode='rb')
    # Always embed cover as JPEG regardless of source format — keeps file size small
    cover_bytes = _cover_to_jpeg(cover_path)

    book = epub.EpubBook()
    book.set_identifier('japji-sahib-eink-001')
    book.set_title('ਜਪੁਜੀ ਸਾਹਿਬ — Japji Sahib')
    book.set_language('pa')
    book.add_author('Guru Nanak Dev Ji')
    book.add_metadata('DC', 'description',
                      'The complete Japji Sahib in Unicode Gurmukhi, formatted for e-ink devices.')

    # Cover — always JPEG in the EPUB; set_cover() adds the item internally
    book.set_cover('images/cover.jpg', cover_bytes)

    # Font
    book.add_item(epub.EpubItem(
        uid='font-tiro-regular',
        file_name='fonts/TiroGurmukhi-Regular.ttf',
        media_type='font/ttf',
        content=font_bytes,
    ))

    # CSS
    css_item = epub.EpubItem(
        uid='style-gurbani',
        file_name='styles/gurbani_base.css',
        media_type='text/css',
        content=css_content.encode('utf-8'),
    )
    book.add_item(css_item)

    # Content chapter
    content_xhtml = _build_content_xhtml(pauris)
    content_ch = epub.EpubHtml(title='ਜਪੁਜੀ ਸਾਹਿਬ', file_name='japji_sahib.xhtml', lang='pa')
    content_ch.content = content_xhtml.encode('utf-8')
    content_ch.add_item(css_item)
    book.add_item(content_ch)

    # Credits chapter
    credits_xhtml = _build_credits_xhtml()
    credits_ch = epub.EpubHtml(title='Contributions', file_name='credits.xhtml', lang='en')
    credits_ch.content = credits_xhtml.encode('utf-8')
    credits_ch.add_item(css_item)
    book.add_item(credits_ch)

    # NCX + Nav
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    book.toc = (
        epub.Link('japji_sahib.xhtml', 'ਜਪੁਜੀ ਸਾਹਿਬ', 'japji'),
        epub.Link('credits.xhtml',     'Contributions',   'credits'),
    )
    # Spine: cover first, then content, then credits. Nav is not a reading document.
    book.spine = ['cover', content_ch, credits_ch]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    epub.write_epub(output_path, book, {})
    return output_path
