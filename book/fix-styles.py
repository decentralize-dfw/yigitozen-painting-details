# -*- coding: utf-8 -*-
"""Her elemani kendi paragraf stiline ve kendi yazi tipine ayirir.

Kitapta tek bir 'm g' stili uc yuz yirmi dokuz yerde kullaniliyordu:
bolum alt basligi da, malzeme satiri da, renk notu da, kesit kunyesi de,
karsi sayfa satiri da ayni stilde. Birini secip degistirmek mumkun
degildi — hepsi birden degisirdi.

Iki is birden yapilir. Birincisi: her eleman kendi stiline ayrilir, ve o
stile kendi yazi tipi verilir; stili degistirmek kitabin her yerinde o
elemani degistirir, baskasina dokunmaz.

Ikincisi, ve daha onemlisi: stillerin yazi tipleri kirikti. 'Inter (TT)'
ve 'Newsreader (TT)' diye iki aile yaziliydi ve ikisi de kullanicinin
makinesinde YOK. Sayfa dogru gorunuyordu cunku her paragrafin icine ayri
ayri 'Inter' yazilmisti — bin uc yuz altmis yerde. Bu yuzden stili
degistirmek hicbir ise yaramiyordu: yerel atama stili eziyordu. Yerel
atamalar kaldirilir ve yazi tipi stile konur.

    python3 fix-styles.py girdi.idml cikti.idml [--rapor]
"""
import os, sys, re, zipfile, shutil, collections
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from place import transform
from roles import role_of

if len(sys.argv) < 3:
    sys.exit('kullanim: fix-styles.py girdi.idml cikti.idml [--rapor]')
SRC, DST = sys.argv[1], sys.argv[2]

# rol -> (stil adi, aile, kesim). Aileler kullanicinin makinesinde kurulu:
# Inter ve Newsreader kitabin kendi aileleri; kalan dordu icin yine kurulu
# olan Myriad Pro, Helvetica ve Helvetica Light kullanilir, boylece hicbir
# yazi eksik yazi tipi diye kirmizi gelmez.
ROL = {
    'yil':               ('d yr',   'Inter',           'Bold'),
    'baslik':            ('d',      'Inter',           'Regular'),
    'is numarasi':       ('m wn',   'Inter',           'SemiBold'),
    'malzeme':           ('m med',  'Inter',           'Medium'),
    'bolum alt basligi': ('m sub',  'Inter',           'Italic'),
    'metin':             ('t',      'Newsreader',      'Regular'),
    'not':               ('m note', 'Newsreader',      'Medium'),
    'karsi sayfa':       ('m opp',  'Newsreader',      'Italic'),
    'kunye':             ('m cap',  'Myriad Pro',      'Regular'),
    'asama':             ('m stg',  'Myriad Pro',      'Bold'),
    # Folyo sol ve sag sayfada ayri hizalanir; iki stil kalir, ikisine de
    # ayni yazi tipi verilir.
    'folyo':             (None,     'Helvetica',       'Regular'),
    'folyo yili':        ('f yr',   'Helvetica Light', 'Regular'),
}
# Yeni acilacak stiller: hangi stilden kopyalanacaklari
KOPYA = {'m med': 'm g', 'm sub': 'm g', 'm note': 'm g', 'm opp': 'm g',
         'm cap': 'm g', 'm cap rt': 'm g rt', 'm stg': 'm g', 'f yr': 'f rt'}
# Sagda duran iki kunye icin ayni stilin saga dayali ikizi
IKIZ = {'m cap': {'m g rt': 'm cap rt'}}
# Stili degismeyen roller icin yazi tipi dogrudan bu stillere yazilir
AYNI = {'folyo': ('f', 'f rt')}

# Yeni kesim eskisinden ne kadar genis. Serif buyuk harf Inter'den
# genistir; oturtma bunu bilmezse yeni satir sayfanin altina tasar.
GENIS = {'m note': 1.08, 'd yr': 1.06, 'm opp': 1.04, 'm sub': 1.02}

# Kirik ya da yerine baskasi konmus adlari kurulu olanlarla degistir
DUZELT = {'Inter (TT)': ('Inter', 'Regular'),
          'Newsreader (TT)': ('Newsreader', 'Regular'),
          'Inter Medium': ('Inter', 'Medium'),
          'Inter SemiBold': ('Inter', 'SemiBold')}
# Paragrafin icinde kesim degistiren karakter stilleri
KARAKTER = {'bold': ('Inter', 'Bold'), 'italic': ('Newsreader', 'Italic'),
            'italic s': ('Inter', 'Italic')}

Z = zipfile.ZipFile(SRC)
raw = {n: (Z.read(n).decode('utf-8')
           if n.startswith(('Spreads/', 'Stories/', 'Resources/'))
           or n == 'designmap.xml' else Z.read(n)) for n in Z.namelist()}


def links_of(zf):
    out = []
    for n in sorted(zf.namelist()):
        if not n.startswith('Spreads/'): continue
        for el in ET.fromstring(zf.read(n)).iter('Link'):
            out.append((n, el.get('LinkResourceURI'), el.get('LinkResourceFormat')))
    return out


# ── kurulu yazi tipleri: uydurma ad kabul edilmez ───────────────────
kurulu = set()
for f in ET.fromstring(raw['Resources/Fonts.xml']).iter('Font'):
    if f.get('Status') == 'Installed':
        kurulu.add((f.get('FontFamily'), f.get('FontStyleName')))
eksik = [(a, b) for _, a, b in ROL.values() if (a, b) not in kurulu]
eksik += [v for v in KARAKTER.values() if v not in kurulu]
if eksik:
    sys.exit('DURDU: bu yazi tipleri makinede kurulu degil: %s' % eksik)

# ── sayfalar ve roller ──────────────────────────────────────────────
loc, chapter, stage = {}, set(), set()
for n in sorted(raw):
    if not n.startswith('Spreads/'): continue
    sp = ET.fromstring(raw[n]).find('.//Spread')
    if sp is None: continue
    pg = {}
    for p in sp.findall('Page'):
        g = [float(v) for v in p.get('GeometricBounds').split()]
        it = [float(v) for v in (p.get('ItemTransform') or '1 0 0 1 0 0').split()]
        if p.get('Name', '').isdigit():
            pg[int(p.get('Name'))] = (g[1] + it[4], g[3] + it[4])
    for f in sp.iter('TextFrame'):
        b = transform(f)
        if not b: continue
        loc[f.get('ParentStory')] = next(
            (k for k, (a1, a2) in pg.items() if a1 - 1 <= (b[0] + b[2]) / 2 <= a2 + 1), None)


def oyku(sid):
    s = raw['Stories/Story_%s.xml' % sid]
    t = re.sub(r'\s+', ' ', ''.join(
        (c.text or '') for c in ET.fromstring(s).iter('Content'))).strip()
    m = re.search(r'AppliedParagraphStyle="ParagraphStyle/([^"]+)"', s)
    return t, (m.group(1) if m else '')


for n in sorted(raw):
    m = re.match(r'Stories/Story_(\w+)\.xml$', n)
    if not m: continue
    t, sty = oyku(m.group(1))
    if sty == 'd yr': chapter.add(loc.get(m.group(1)))
    if re.match(r'^(of \d+ stages|stage \d)', t, re.I): stage.add(loc.get(m.group(1)))

sayim = collections.Counter()
degis = {}
for n in sorted(raw):
    m = re.match(r'Stories/Story_(\w+)\.xml$', n)
    if not m: continue
    sid = m.group(1)
    t, sty = oyku(sid)
    r = role_of(t, sty, loc.get(sid), sid, chapter, stage)
    if r is None: continue
    ad = ROL[r][0]
    if ad is None:
        sayim[r] += 1; continue          # stili degismez, yalniz yazi tipi
    degis[n] = IKIZ.get(ad, {}).get(sty, ad)
    sayim[r] += 1

print('%s' % os.path.basename(SRC))
print('  ayrilan eleman:')
for r in sorted(sayim, key=lambda x: -sayim[x]):
    s, fam, kes = ROL[r]
    ad = s or ' + '.join(AYNI.get(r, ()))
    print('     %-18s %4d  ->  stil %-10s %s %s' % (r, sayim[r], ad, fam, kes))
if '--rapor' in sys.argv: sys.exit(0)

# ── 1 · stil dosyasi ────────────────────────────────────────────────
st = raw['Resources/Styles.xml']


def set_font(block, fam, kes):
    b = re.sub(r'<AppliedFont type="string">[^<]*</AppliedFont>',
               '<AppliedFont type="string">%s</AppliedFont>' % fam, block)
    if '<AppliedFont' not in b:
        b = b.replace('<Properties>',
                      '<Properties><AppliedFont type="string">%s</AppliedFont>' % fam, 1)
    if re.search(r'\sFontStyle="[^"]*"', b):
        b = re.sub(r'\sFontStyle="[^"]*"', ' FontStyle="%s"' % kes, b, count=1)
    else:
        b = b.replace('>', ' FontStyle="%s">' % kes, 1)
    return b


# yeni stilleri ac
yeni = []
for ad, kaynak in KOPYA.items():
    m = re.search(r'<ParagraphStyle Self="ParagraphStyle/%s"[\s\S]*?</ParagraphStyle>'
                  % re.escape(kaynak), st)
    if not m: sys.exit('DURDU: %s stili bulunamadi' % kaynak)
    b = m.group(0)
    b = b.replace('Self="ParagraphStyle/%s"' % kaynak, 'Self="ParagraphStyle/%s"' % ad)
    b = re.sub(r'\sName="[^"]*"', ' Name="%s"' % ad, b, count=1)
    b = b.replace('NextStyle="ParagraphStyle/%s"' % kaynak,
                  'NextStyle="ParagraphStyle/%s"' % ad)
    b = re.sub(r'\sStyleUniqueId="[^"]*"', '', b)
    yeni.append(b)
st = st.replace('</RootParagraphStyleGroup>', ''.join(yeni) + '</RootParagraphStyleGroup>', 1)

# her stile yazi tipini yaz
hedef = {s: (fam, kes) for s, fam, kes in ROL.values() if s}
for r, (s0, fam, kes) in ROL.items():
    for a in AYNI.get(r, ()): hedef[a] = (fam, kes)
    for a in IKIZ.get(s0, {}).values(): hedef[a] = (fam, kes)
duzeltilen = 0
def para(m):
    global duzeltilen
    b = m.group(0)
    nm = re.search(r'Self="ParagraphStyle/([^"]+)"', b).group(1)
    if nm in hedef:
        duzeltilen += 1
        return set_font(b, *hedef[nm])
    af = re.search(r'<AppliedFont type="string">([^<]*)</AppliedFont>', b)
    if af and af.group(1) in DUZELT:
        duzeltilen += 1
        return set_font(b, *DUZELT[af.group(1)])
    return b
st = re.sub(r'<ParagraphStyle Self="ParagraphStyle/(?!\$ID)[^"]+"[\s\S]*?</ParagraphStyle>',
            para, st)

# karakter stilleri: yazi tipi tasiyanlar duzeltilir, kalanlardan kaldirilir
def kar(m):
    b = m.group(0)
    nm = re.search(r'Self="CharacterStyle/([^"]+)"', b).group(1)
    if nm in KARAKTER: return set_font(b, *KARAKTER[nm])
    b = re.sub(r'<AppliedFont type="string">[^<]*</AppliedFont>', '', b)
    return re.sub(r'\sFontStyle="[^"]*"', '', b)
st = re.sub(r'<CharacterStyle Self="CharacterStyle/(?!\$ID)[^"]+"[\s\S]*?</CharacterStyle>',
            kar, st)
raw['Resources/Styles.xml'] = st

# ── 2 · oykuler: stil degistir, yerel yazi tipi atamalarini kaldir ──
yerel = 0
for n in sorted(raw):
    if not n.startswith('Stories/'): continue
    s = raw[n]
    if n in degis:
        s = re.sub(r'AppliedParagraphStyle="ParagraphStyle/[^"]+"',
                   'AppliedParagraphStyle="ParagraphStyle/%s"' % degis[n], s)
    a = len(re.findall(r'<AppliedFont type="string">', s)) + \
        len(re.findall(r'\sFontStyle="', s))
    s = re.sub(r'<AppliedFont type="string">[^<]*</AppliedFont>', '', s)
    s = re.sub(r'\sFontStyle="[^"]*"', '', s)
    yerel += a
    raw[n] = s

# ── yaz ─────────────────────────────────────────────────────────────
before = links_of(Z)
tmp = DST + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for info in Z.infolist():
        d = raw[info.filename]
        if isinstance(d, str): d = d.encode('utf-8')
        if info.filename == 'mimetype':
            zi = zipfile.ZipInfo('mimetype'); zi.compress_type = zipfile.ZIP_STORED
            zo.writestr(zi, d)
        else:
            zo.writestr(info.filename, d)

z2 = zipfile.ZipFile(tmp)
ok = True
for nm in z2.namelist():
    if nm.endswith('.xml'):
        try: ET.fromstring(z2.read(nm))
        except Exception as e: ok = False; print('AYRISMADI', nm, e)
after = links_of(z2)
# her paragraf stilinin yazi tipi kurulu olmali
st2 = ET.fromstring(z2.read('Resources/Styles.xml'))
kotu = []
for s in st2.iter('ParagraphStyle'):
    nm = s.get('Name')
    if not nm or nm.startswith('$ID'): continue
    af = next((p.text for p in s.iter('AppliedFont')), None)
    if (af, s.get('FontStyle')) not in kurulu: kotu.append((nm, af, s.get('FontStyle')))
kalan = sum(z2.read(n).count(b'<AppliedFont') for n in z2.namelist()
            if n.startswith('Stories/'))
z2.close()
if before != after: os.remove(tmp); sys.exit('DURDU: bag kaydi degisti')
if not ok: os.remove(tmp); sys.exit('DURDU: XML bozuldu')
if kotu: os.remove(tmp); sys.exit('DURDU: kurulu olmayan yazi tipi: %s' % kotu[:6])
shutil.move(tmp, DST)

import json
gj = os.path.join(os.path.dirname(os.path.abspath(DST)), 'genisleme.json')
json.dump({re.match(r'Stories/Story_(\w+)\.xml$', n).group(1): GENIS[v]
           for n, v in degis.items() if v in GENIS}, open(gj, 'w'))

print('  -> %s' % os.path.basename(DST))
print('  stile yazi tipi yazildi: %d · oykudeki yerel atama kaldirildi: %d '
      '(kalan %d)' % (duzeltilen, yerel, kalan))
print('  bag kaydi %d · hepsi birebir ayni' % len(before))
