# -*- coding: utf-8 -*-
"""Sayfadaki her yazinin ne oldugunu soyler.

Kitapta bir tek 'm g' stili uc yuz yirmi dokuz yerde kullaniliyor: bolum
alt basligi da, malzeme satiri da, renk notu da, kesit kunyesi de, karsi
sayfa satiri da ayni stille dizilmis. Boyle olunca birini secip
degistirmek mumkun degil — hepsi birden degisir.

Burada her yazi kendi isine gore ayrilir. Ayrim yaziyla ve yeriyle
yapilir; bir sonraki betik her role kendi paragraf stilini verir.
"""
import re

# Kitabin islerinden birinin malzeme satiri boyle baslar.
MED = re.compile(r'^(acrylic|charcoal|pencil|ink|oil|gouache|mixed)\b', re.I)
NOTE = re.compile(r'^(colour|color|composition|hand)\s*[—–-]', re.I)
NUM = re.compile(r'^\d{1,3}$')


def role_of(text, style, page, story_id, chapter_pages, stage_pages):
    """Yazinin rolu. Bilinmiyorsa None doner; o zaman stili degismez."""
    t = (text or '').strip()
    # Folyo once bakilir: sayfa numarasi otomatik alandir, oykude yazi
    # olarak durmaz, dolayisiyla metni bostur.
    if style in ('f', 'f rt'):
        return 'folyo yili' if t and not NUM.match(t) else 'folyo'
    if not t: return None
    if style == 'm wn': return 'is numarasi'
    if style.startswith('d'):
        return 'yil' if style == 'd yr' else 'baslik' if style == 'd' else None
    if style == 't': return 'metin'
    if not style.startswith('m'): return None

    if ' · Opposite · ' in t: return 'karsi sayfa'
    if NOTE.match(t): return 'not'
    if MED.match(t) and re.search(r'\d', t): return 'malzeme'
    if re.match(r'^(cn|cw|cs|cr)', story_id or ''): return 'kunye'
    if page in stage_pages and (NUM.match(t) or
                                re.match(r'^(stage \d|of \d+ stages|first frame)', t, re.I)):
        return 'asama'
    if page in chapter_pages and len(t) < 60: return 'bolum alt basligi'
    if page is not None and (page <= 9 or page >= 126): return None   # on ve arka bolum
    if style in ('m', 'm rt', 'm rt g', 'm wh', 'm rt wh'): return None
    return 'kunye'
