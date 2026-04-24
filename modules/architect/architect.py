import io
import os
import re
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
                parts.append(f'  <p class="line ikonkar"><span class="word">{_IK_ONKAR}</span></p>')
                rest = text[len(_IK_ONKAR):].strip()
                if rest:
                    parts.append(f'  <p class="line manglacharan">{atomic_shaper(rest)}</p>')
                prev_was_salok_end = False
            else:
                # In a pauri with manglacharan, insert a visual break after the salok
                # closing verse (ending ॥੧॥) before the first main pankti begins
                extra_class = ''
                if prev_was_salok_end and line_type == 'pankti' and has_manglacharan:
                    extra_class = ' pauri-start'
                parts.append(f'  <p class="line {line_type}{extra_class}">{atomic_shaper(text)}</p>')
                prev_was_salok_end = (line_type == 'pankti' and
                                      bool(re.search(r'॥\d+॥\s*$', text)))

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

    # Cover image — register with create_page=False so ebooklib does NOT generate its
    # own bare cover.xhtml (which renders partially on Kobo due to missing viewport CSS).
    book.set_cover('images/cover.jpg', cover_bytes, create_page=False)

    # Cover HTML — our own page with explicit viewport-filling CSS
    cover_ch = epub.EpubHtml(uid='cover', title='Cover', file_name='cover.xhtml', lang='pa')
    cover_ch.content = b'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="pa" lang="pa">
<head>
  <meta charset="utf-8"/>
  <title>Cover</title>
</head>
<body style="margin: 0; padding: 0;">
  <img src="images/cover.jpg" alt="Cover" style="width: 100%; height: 100%; display: block;"/>
</body>
</html>'''
    book.add_item(cover_ch)

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
    content_ch = epub.EpubHtml(title='Japji Sahib', file_name='japji_sahib.xhtml', lang='pa')
    content_ch.content = content_xhtml.encode('utf-8')
    content_ch.add_item(css_item)
    book.add_item(content_ch)

    # Reader note chapter
    note_xhtml = _build_reader_note_xhtml()
    note_ch = epub.EpubHtml(title='Before You Begin', file_name='reader_note.xhtml', lang='en')
    note_ch.content = note_xhtml.encode('utf-8')
    note_ch.add_item(css_item)
    book.add_item(note_ch)

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
        epub.Link('reader_note.xhtml', 'Before You Begin', 'note'),
        epub.Link('japji_sahib.xhtml', 'Japji Sahib',      'japji'),
        epub.Link('credits.xhtml',     'Contributions',    'credits'),
    )
    # Spine: cover → reader note → content → credits. Nav is not a reading document.
    book.spine = ['cover', note_ch, content_ch, credits_ch]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    epub.write_epub(output_path, book, {})
    return output_path
