import io
import os
import re
from PIL import Image, ImageDraw, ImageFont
from ebooklib import epub
from modules.shaper.shaper import atomic_shaper


def _read(path: str, mode='r', encoding='utf-8'):
    if mode == 'rb':
        with open(path, 'rb') as f:
            return f.read()
    with open(path, encoding=encoding) as f:
        return f.read()


def _cover_to_jpeg(cover_path: str, version: str = '', quality: int = 85) -> bytes:
    """Convert cover image to JPEG, optionally stamping a version string."""
    with Image.open(cover_path) as img:
        if img.mode not in ('RGB',):
            img = img.convert('RGB')
        if version:
            draw = ImageDraw.Draw(img)
            W, H = img.size
            try:
                font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', max(18, H // 60))
            except OSError:
                font = ImageFont.load_default()
            label = f'v{version}'
            bbox = draw.textbbox((0, 0), label, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            pad = 12
            x = W - tw - pad
            y = H - th - pad
            draw.rectangle([x - 4, y - 4, x + tw + 4, y + th + 4], fill='#000000aa')
            draw.text((x, y), label, font=font, fill='#ffffff')
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=quality, optimize=True)
        return buf.getvalue()


_IK_ONKAR = 'ੴ'


def _build_content_xhtml(pauris: list[dict]) -> str:
    parts = []
    for pauri in pauris:
        has_manglacharan = any(l['type'] == 'manglacharan' for l in pauri['lines'])
        parts.append('<div class="pauri">')
        prev_was_salok_end = False

        for line in pauri['lines']:
            text      = line['text']
            line_type = line['type']

            # Ik Onkar gets its own full line at 2× size for any Bani that opens with it
            if line_type == 'manglacharan' and text.startswith(_IK_ONKAR):
                # ikonkar-wrap overrides line-wrap's padding-top to 0 — body padding
                # is sufficient on page 1, and if break-inside moves it to a new page
                # the @page margin-top provides the ascender buffer
                parts.append(f'  <div class="line-wrap ikonkar-wrap"><p class="line ikonkar"><span class="word">{_IK_ONKAR}</span></p></div>')
                rest = text[len(_IK_ONKAR):].strip()
                if rest:
                    parts.append(f'  <div class="line-wrap"><p class="line manglacharan">{atomic_shaper(rest)}</p></div>')
                prev_was_salok_end = False
            else:
                # In a pauri with manglacharan, insert a visual break after the salok
                # closing verse (ending ॥੧॥) before the first main pankti begins
                extra_class = ''
                if prev_was_salok_end and line_type == 'pankti' and has_manglacharan:
                    extra_class = ' pauri-start'
                parts.append(f'  <div class="line-wrap"><p class="line {line_type}{extra_class}">{atomic_shaper(text)}</p></div>')
                prev_was_salok_end = (line_type == 'pankti' and
                                      bool(re.search(r'॥\d+॥\s*$', text)))

        parts.append('</div>')

    body = '\n'.join(parts)
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="pa" lang="pa">
<head>
  <meta charset="utf-8"/>
  <title>Japji Sahib</title>
  <link rel="stylesheet" type="text/css" href="styles/gurbani_base.css"/>
</head>
<body>
{body}
</body>
</html>'''


def _build_reader_note_xhtml(css_href: str = 'styles/gurbani_base.css') -> str:
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
  <meta charset="utf-8"/>
  <title>Before You Begin</title>
  <link rel="stylesheet" type="text/css" href="{css_href}"/>
</head>
<body>
<div class="reader-note">
  <p class="reader-note-ikonkar" lang="pa" xml:lang="pa">ੴ</p>
  <p class="reader-note-heading">Before You Begin</p>
  <p class="reader-note-body">This book uses the Tiro Gurmukhi font to ensure every word of Gurbani renders correctly &#8212; with all ligatures and vowel signs intact, at any font size.</p>
  <p class="reader-note-body">Please take a moment to set your font to <strong>Publisher Default</strong> before starting paath:</p>
  <p class="reader-note-device"><strong>Kindle:</strong> Tap the top of the screen &#8594; Aa &#8594; Font &#8594; Publisher Default</p>
  <p class="reader-note-device"><strong>Kobo:</strong> Tap the centre of the screen &#8594; Aa &#8594; Font &#8594; Publisher Default</p>
  <p class="reader-note-body">Once set, you may change font size freely at any time.</p>
  <p class="reader-note-closing" lang="pa" xml:lang="pa">ਵਾਹਿਗੁਰੂ ਜੀ ਕਾ ਖਾਲਸਾ &#8212; ਵਾਹਿਗੁਰੂ ਜੀ ਕੀ ਫਤਹਿ</p>
</div>
</body>
</html>'''


def _build_credits_xhtml(css_href: str = 'styles/gurbani_base.css') -> str:
    return f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
  <meta charset="utf-8"/>
  <title>Acknowledgements</title>
  <link rel="stylesheet" type="text/css" href="{css_href}"/>
</head>
<body>
<div class="credits-page">
  <p class="credits-ikonkar" lang="pa" xml:lang="pa">ੴ</p>
  <p class="credits-invocation" lang="pa" xml:lang="pa">ਸਤਿਗੁਰ ਪ੍ਰਸਾਦਿ ॥</p>
  <p class="credits-heading">Acknowledgements</p>

  <div class="credit-person">
    <span class="credit-person-name">Ravina Toor</span>
    <span class="credit-person-link">ravinartoor.com</span>
    <span class="credit-person-role">Cover Art <em>(permission pending)</em></span>
  </div>

  <div class="credit-person">
    <span class="credit-person-name">Maneetpaul Singh</span>
    <span class="credit-person-link">youtube.com/@Maneetpaul</span>
    <span class="credit-person-role">Device Testing Sewa</span>
    <span class="credit-person-note">Maneetpaul&#8217;s videos inspired so many members of the Sangat &#8212; including this sewadar &#8212; to discover the e-ink reader. He very kindly gave his time to test this publication across his devices. Shukariya.</span>
  </div>

  <div class="credit-person">
    <span class="credit-person-name">Shabad OS</span>
    <span class="credit-person-link">shabados.com</span>
    <span class="credit-person-role">Open Gurbani Database</span>
    <span class="credit-person-note">The contributors behind Shabad OS &#8212; including harjot1singh, bhajneet, saihaj, and the wider open-source community &#8212; built the versioned, meticulously maintained Gurbani database this engine is built upon. Their dedication to making Gurbani digitally accessible is seva at its finest.</span>
  </div>

  <div class="credit-person">
    <span class="credit-person-name">Khalis Foundation</span>
    <span class="credit-person-link">khalisfoundation.org</span>
    <span class="credit-person-role">Two Decades of Digital Sewa</span>
    <span class="credit-person-note">For over 20 years, the Khalis Foundation has quietly and persistently built the digital infrastructure that lets projects like this one exist &#8212; from BaniDB to tools that bring Gurbani to contemporary Sikh life. Their work is the ground this project stands on.</span>
  </div>

  <div class="credits-technical">
    <p><strong>Gurbani:</strong> Sri Guru Granth Sahib Ji, Ang 1&#8211;8 &#183; Shabadaarth SGGS (Vols. 1&#8211;4), SGPC, Sri Amritsar, 2009&#8211;2012 &#183; Shabad OS Database v4.8.7 &#8212; github.com/shabados/database</p>
    <p><strong>Font:</strong> Tiro Gurmukhi &#8212; Tiro Typeworks (OFL)</p>
  </div>

  <div class="disclaimer">
    <p>Every effort has been made to accurately represent the Gurbani. If you find an error, the sewadar asks for forgiveness and requests you to kindly inform 1guru.rakha@gmail.com.</p>
    <p class="bhul-chuk" lang="pa" xml:lang="pa">ਭੁੱਲ ਚੁੱਕ ਮਾਫ਼</p>
  </div>
</div>
</body>
</html>'''


def build_epub(
    pauris:      list[dict],
    font_path:   str,
    css_path:    str,
    cover_path:  str,
    output_path: str,
    version:     str = '',
) -> str:
    css_content = _read(css_path)
    font_bytes  = _read(font_path, mode='rb')
    cover_bytes = _cover_to_jpeg(cover_path, version)
    with Image.open(cover_path) as _cimg:
        cover_w, cover_h = _cimg.size

    book = epub.EpubBook()
    book.set_identifier('japji-sahib-eink-001')
    book.set_title('Japji Sahib')
    book.set_language('pa')
    book.add_author('Guru Nanak Dev Ji')
    book.add_metadata('DC', 'description',
                      'The complete Japji Sahib in Unicode Gurmukhi, formatted for e-ink devices.')

    # Cover image thumbnail — registered first so ebooklib sets the cover metadata.
    # create_page=False prevents ebooklib generating its own bare cover.xhtml.
    book.set_cover('images/cover.jpg', cover_bytes, create_page=False)

    book.add_item(epub.EpubItem(
        uid='font-gurmukhi-regular',
        file_name='fonts/NotoSansGurmukhi-Regular.ttf',
        media_type='font/ttf',
        content=font_bytes,
    ))
    book.add_item(epub.EpubItem(
        uid='font-tiro-ikonkar',
        file_name='fonts/TiroGurmukhi-Regular.ttf',
        media_type='font/ttf',
        content=_read(
            os.path.join(os.path.dirname(font_path), 'TiroGurmukhi-Regular.ttf'),
            mode='rb',
        ),
    ))

    # CSS — must be created before cover_ch so cover_ch.add_item() can reference it
    css_item = epub.EpubItem(
        uid='style-gurbani',
        file_name='styles/gurbani_base.css',
        media_type='text/css',
        content=css_content.encode('utf-8'),
    )
    book.add_item(css_item)

    # Cover — use EpubItem (not EpubHtml) so ebooklib does not reserialise the
    # content via lxml's HTML parser, which would lowercase SVG attribute names
    # (viewBox → viewbox, preserveAspectRatio → preserveaspectratio) and strip
    # the <style> tag.  Raw bytes are written to the EPUB zip unchanged.
    ver_label = f' v{version}' if version else ''
    cover_bytes_xhtml = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
  <meta charset="utf-8"/>
  <title>Japji Sahib{ver_label}</title>
  <style type="text/css">
    @page {{ margin: 0; }}
    html, body {{ margin: 0; padding: 0; width: 100%; height: 100%; }}
    svg {{ display: block; width: 100%; height: 100%; }}
  </style>
</head>
<body>
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     version="1.1" width="100%" height="100%"
     viewBox="0 0 {cover_w} {cover_h}"
     preserveAspectRatio="xMidYMid meet">
  <image width="{cover_w}" height="{cover_h}" xlink:href="images/cover.jpg"/>
</svg>
</body>
</html>'''.encode('utf-8')
    cover_ch = epub.EpubItem(
        uid='cover',
        file_name='cover.xhtml',
        media_type='application/xhtml+xml',
        content=cover_bytes_xhtml,
    )
    book.add_item(cover_ch)

    # Content chapter
    content_xhtml = _build_content_xhtml(pauris)
    content_ch = epub.EpubHtml(title='Japji Sahib', file_name='japji_sahib.xhtml', lang='pa')
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
        epub.Link('japji_sahib.xhtml', 'Japji Sahib',   'japji'),
        epub.Link('credits.xhtml',     'Contributions', 'credits'),
    )
    # Spine: cover → content → credits. Nav is not a reading document.
    book.spine = ['cover', content_ch, credits_ch]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    epub.write_epub(output_path, book, {})
    return output_path
