# -*- coding: utf-8 -*-
"""
Duzenlenmis kitabin IDML'ini onarir, baglarina dokunmadan.

Sayfa eklenip cikarilinca icindekiler kendiliginden guncellenmez: her
satirin sayfa numarasi kendi kucuk yazi cercevesinde durur ve orada
kalir. Bu betik her isin gercekte hangi sayfada actigini bulur ve o
numaralari yeniden yazar. Ayrica kunyedeki yer adinin buyuk harfi geri
gelir — bunu IDML'e cevirirken atlamisim: stil sayfasinda .f span hem
buyuk harf hem 7,2 punto, karakter stiline yalniz rengi koymusum.

Gorseller icin: Spreads/ hic acilmaz. Dolayisiyla hicbir Link kaydi
degismez, hicbir gorsel yeniden baglanmaz. Betik yazmadan once butun
bag kayitlarini once-sonra karsilastirir; bir tanesi bile oynamissa
durur ve dosyayi yazmaz.

    python3 fix-book-idml.py girdi.idml render.pdf cikti.idml

render.pdf, ayni belgenin herhangi bir PDF ciktisidir; sayfa numaralari
oradan okunur, cozunurlugunun onemi yoktur.
"""
import os, sys, re, zipfile, shutil
import xml.etree.ElementTree as ET

if len(sys.argv) < 4:
    sys.exit('kullanim: fix-book-idml.py girdi.idml render.pdf cikti.idml')
SRC, PDF, DST = sys.argv[1], sys.argv[2], sys.argv[3]

import pymupdf

# Icindekiler satirlarinin sutun konumlari, punto cinsinden.
COL_TITLE, COL_PAGE, COL_NO = 105.8, 597.2, 56.7
TOL = 4.0

# Is olmayan satirlar: bolum adi -> sayfada aranacak isaret
# Bolum satirlari. Isaretler bolumun ACILDIGI sayfada bulunan, baska
# yerde gecmeyen dizelerdir: 'What comes back' govde yazisinda da gecer,
# o yuzden bolumun kendi baslik dizesi aranir.
SECTIONS = {
    'On the work': ['ON THE WORK'],
    'Biography': ['BIOGRAPHY'],
    'Index': ['THE THIRTY-FIVE, AT ONE WIDTH'],
    'What comes back': ['SIX THINGS THAT COME BACK'],
    'Colophon': ['COLOPHON'],
}

z = zipfile.ZipFile(SRC)


def links_of(zf):
    out = []
    for n in sorted(zf.namelist()):
        if not n.startswith('Spreads/'): continue
        for el in ET.fromstring(zf.read(n)).iter('Link'):
            out.append((n, el.get('LinkResourceURI'), el.get('LinkResourceFormat')))
    return out


def story_text(sid):
    p = 'Stories/Story_%s.xml' % sid
    if p not in z.namelist(): return ''
    return ''.join((c.text or '')
                   for c in ET.fromstring(z.read(p)).iter('Content'))


def box(el):
    pts = [p.get('Anchor').split() for p in el.iter('PathPointType')]
    xs = [float(p[0]) for p in pts]; ys = [float(p[1]) for p in pts]
    return min(xs), min(ys)


# ── icindekiler yapragini bul ───────────────────────────────────────
toc = None
for n in z.namelist():
    if not n.startswith('Spreads/'): continue
    t = ET.fromstring(z.read(n))
    fr = t.findall('.//TextFrame')
    if len(fr) < 30: continue
    if any(story_text(f.get('ParentStory')).strip() == '7 fam board game' for f in fr):
        toc = (n, t, fr); break
if not toc: sys.exit('icindekiler yapragi bulunamadi')
tocname, toctree, frames = toc

items = []
for f in frames:
    x, y = box(f)
    sid = f.get('ParentStory')
    items.append((y, x, sid, story_text(sid).strip()))

titles = [i for i in items if abs(i[1] - COL_TITLE) < TOL and i[3]]
pagenos = [i for i in items if abs(i[1] - COL_PAGE) < TOL
           and re.fullmatch(r'\d{1,3}', i[3] or '')]

# ── gercek sayfalar, PDF ciktisindan ────────────────────────────────
doc = pymupdf.open(PDF)
pages = [re.sub(r'\s+', ' ', p.get_text()) for p in doc]


def opening_of(title):
    """Isin acilis sayfasi: baslik ile kunye satiri ayni sayfada."""
    key = title.lower()[:26]
    for i in range(9, len(pages)):
        low = pages[i].lower()
        if key in low and 'acrylic on' in low: return i + 1
    for i in range(9, len(pages)):
        if key in pages[i].lower(): return i + 1
    return None


def section_of(title):
    for name, marks in SECTIONS.items():
        if title.lower().startswith(name.lower()):
            for i in range(3, len(pages)):
                up = pages[i].upper()
                if any(m in up for m in marks) and i + 1 != 9:
                    return i + 1
    return None


fixes = {}
report = []
bywork = {}          # is numarasi -> gercek sayfa
for ty, tx, tsid, title in sorted(titles):
    cand = [p for p in pagenos if abs(p[0] - ty) < TOL]
    if not cand: continue
    said = cand[0][3]
    real = section_of(title) or opening_of(title)
    if real is None:
        report.append((title, said, None, 'bulunamadi')); continue
    cno = [p for p in items if abs(p[1] - COL_NO) < TOL and abs(p[0] - ty) < TOL
           and re.fullmatch(r'\d{2}', p[3] or '')]
    if cno: bywork[cno[0][3]] = real
    if str(real) != said:
        fixes[cand[0][2]] = str(real)
        report.append((title, said, real, 'duzeltildi'))
    else:
        report.append((title, said, real, 'zaten dogru'))

# Dizin: '01 · 10' bicimindeki otuz bes satir. Her biri kendi hikayesinde
# ve uc kosuya bolunmus durur — '01 ', '·', ' 10' — cunku ortadaki nokta
# gri. Bu yuzden ham metinde arama ise yaramaz; hikaye cozumlenir, sayfa
# numarasini tasiyan son kosu yeniden yazilir. Duzeltilmezse icindekiler
# dogruyu, dizin eskisini gosterirdi.
index_fix = {}
for n2 in z.namelist():
    if not n2.startswith('Stories/'): continue
    raw = z.read(n2).decode('utf-8')
    t2 = ET.fromstring(raw)
    txt2 = ''.join((c.text or '') for c in t2.iter('Content')).strip()
    mm = re.fullmatch(r'(\d{2})\s*·\s*(\d{1,3})', txt2)
    if not mm: continue
    no, pg = mm.group(1), mm.group(2)
    real2 = bywork.get(no)
    if not real2 or str(real2) == pg: continue
    # Noktadan SONRAKI ilk Content sayfa numarasini tasir.
    dot = raw.find('>·<')
    if dot < 0: dot = raw.find('·')
    head, tail = raw[:dot], raw[dot:]
    tail2, cnt = re.subn(r'(<Content>\s*)%s(\s*</Content>)' % re.escape(pg),
                         lambda g: g.group(1) + str(real2) + g.group(2), tail, count=1)
    if cnt: index_fix[n2] = head + tail2

# ── parcalari yaz ───────────────────────────────────────────────────
before = links_of(z)
changed_toc = changed_caps = changed_idx = 0
parts = []
for info in z.infolist():
    data = z.read(info.filename)
    m = re.match(r'Stories/Story_(\w+)\.xml$', info.filename)
    if m and m.group(1) in fixes:
        s = data.decode('utf-8')
        new = re.sub(r'(<Content>)\s*\d{1,3}\s*(</Content>)',
                     lambda mm: mm.group(1) + fixes[m.group(1)] + mm.group(2), s, count=1)
        if new != s:
            data = new.encode('utf-8'); changed_toc += 1
    if info.filename in index_fix and info.filename not in [
            'Stories/Story_%s.xml' % k for k in fixes]:
        data = index_fix[info.filename].encode('utf-8'); changed_idx += 1
    if info.filename == 'Resources/Styles.xml':
        s = data.decode('utf-8')
        # .f span: gri, 7,2 punto ve BUYUK HARF. Cevirirken yalniz rengi
        # koymusum, punto ile buyuk harfi atlamisim; folyodaki yer adi bu
        # yuzden yazildigi gibi cikiyor.
        new = re.sub(
            r'(<CharacterStyle Self="CharacterStyle/place"(?:(?!/?>)[\s\S])*?)>',
            r'\1 PointSize="7.2" Capitalization="AllCaps" Tracking="70">', s, count=1)
        if new != s:
            data = new.encode('utf-8'); changed_caps = 1
    parts.append((info, data))

tmp = DST + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for info, data in parts:
        if info.filename == 'mimetype':
            zi = zipfile.ZipInfo('mimetype'); zi.compress_type = zipfile.ZIP_STORED
            zo.writestr(zi, data)
        else:
            zo.writestr(info.filename, data)

zo2 = zipfile.ZipFile(tmp)
after = links_of(zo2)
same = z.namelist() == zo2.namelist()
zo2.close()
if before != after:
    os.remove(tmp); sys.exit('DURDU: bag kaydi degismis, dosya yazilmadi')
if not same:
    os.remove(tmp); sys.exit('DURDU: paket girisleri degismis, dosya yazilmadi')
shutil.move(tmp, DST)

ok = sum(1 for r in report if r[3] == 'zaten dogru')
fx = sum(1 for r in report if r[3] == 'duzeltildi')
nf = sum(1 for r in report if r[3] == 'bulunamadi')
print('%s -> %s' % (os.path.basename(SRC), os.path.basename(DST)))
print('  icindekiler: %d satir · %d duzeltildi · %d zaten dogru · %d bulunamadi'
      % (len(report), fx, ok, nf))
for t, s, r, st in report:
    if st == 'duzeltildi': print('     %-42s %s -> %s' % (t[:42], s, r))
    elif st == 'bulunamadi': print('     %-42s %s -> ? (elle bak)' % (t[:42], s))
print('  dizin satiri duzeltilen hikaye: %d' % changed_idx)
print('  kunye yer adi buyuk harfe alindi: %s' % ('evet' if changed_caps else 'GEREK VARDI AMA OLMADI'))
print('  bag kaydi %d · hepsi birebir ayni · paket girisleri ayni' % len(before))
