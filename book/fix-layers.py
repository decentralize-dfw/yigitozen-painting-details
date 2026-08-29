# -*- coding: utf-8 -*-
"""Gorselin altinda kalan yaziyi one alir, yerinden kopmus etiketleri
ait olduklari sayfaya geri tasir.

IDML'de yaprakta sonra gelen nesne ustte durur. Kullanicinin dosyasinda
bazi yapraklarda gorseller yazi cercevelerinden sonra yazilmis; orada
yazi hic gorunmuyor — folyo, kunye, hatta bir sayfanin butun metni.
Cikti bunu dogruluyor: yirmi iki satir basilmis ama gorunmuyor.

Bir de yerinden kopmus etiketler var. 03 · gary grills cooper'in on iki
asamalik dizisi 32. sayfada duruyor; onun sayilari, kaynak notu ve
telif satiri 35. sayfada kalmis ve oradaki iki kesitin altina gomulmus.
Etiketler dizinin oldugu sayfaya, gorsellerinin hizasina tasinir.

Gorsellere dokunulmaz.

    python3 fix-layers.py girdi.idml cikti.idml
"""
import os, sys, re, zipfile, shutil
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from place import transform

if len(sys.argv) < 3:
    sys.exit('kullanim: fix-layers.py girdi.idml cikti.idml')
SRC, DST = sys.argv[1], sys.argv[2]
PT = 72 / 25.4

# Gorselin altinda kalanlar: yaprakta en one alinir.
ONE = ['u1678', 'u554b', 'u178f', 'u1a9d', 'u1a87', 'u1d7b', 'u1d96', 'u1de5',
       # Bunlarin uzerini kaplayan gorselin o kosesi bos, yani ciktida
       # goruluyorlar; yine de gorselden sonraya alinir ki bir daha
       # kimse gorselin altinda kalmasin.
       'u155c', 'u53c9', 'u5534', 'u1dac']

# Ait oldugu sayfaya tasinanlar: (cerceve, hedef sayfa, yeni sol, yeni ust)
# Sayilar 32. sayfadaki serit gorsellerinin hizasinda durur.
TASI = [
    # Olculer sayfanin sol ust kosesine gore, punto.
    ('u1a5b', 32,  45.4, 634.0),   # Stage 1 — the source
    ('u1a71', 32,  45.4, 646.0),   # telif satiri, iki satir tutuyor
    ('u1b40', 32, 430.7, 684.0),   # Of 12 stages, 6 · in order
    ('u5245', 32,  45.4, 700.0),   # 1  · kaynak karesi
    ('u1ae8', 32, 141.7, 700.0),   # 2  · cizim
    ('u5262', 32, 238.0, 700.0),   # 3  · zemin
    ('u1afe', 32, 334.4, 700.0),   # 6
    ('u1b14', 32, 430.7, 700.0),   # 8
    ('u1b2a', 32, 527.1, 700.0),   # 12
]

# Ayni yaprakta yeri yanlis olanlar: (cerceve, yeni ust)
# 'The row of figures on the boat' ustteki kesiti anlatiyor ama alttaki
# kesitin altinda duruyordu.
# u1dc5'in sozu uzadi ve alttaki kesitin uzerine tasiyordu; yukari alinir.
YER = [('u1de5', 340.0), ('u1dc5', 526.0)]

Z = zipfile.ZipFile(SRC)


def links_of(zf):
    out = []
    for n in sorted(zf.namelist()):
        if not n.startswith('Spreads/'): continue
        for el in ET.fromstring(zf.read(n)).iter('Link'):
            out.append((n, el.get('LinkResourceURI'), el.get('LinkResourceFormat')))
    return out


def frame_re(sid):
    return re.compile(r'[ \t]*<TextFrame\b[^>]*Self="%s"[\s\S]*?</TextFrame>\n?'
                      % re.escape(sid))


def page_origin(sp_xml, want):
    sp = ET.fromstring(sp_xml).find('.//Spread')
    for p in sp.findall('Page'):
        if p.get('Name') != str(want): continue
        g = [float(v) for v in p.get('GeometricBounds').split()]
        it = [float(v) for v in (p.get('ItemTransform') or '1 0 0 1 0 0').split()]
        return g[1] + it[4], g[0] + it[5]
    return None


def box_of(xml, sid):
    sp = ET.fromstring(xml).find('.//Spread')
    for f in sp.iter('TextFrame'):
        if f.get('Self') == sid: return transform(f)
    return None


raw = {n: Z.read(n).decode('utf-8') if n.startswith('Spreads/') else Z.read(n)
       for n in Z.namelist()}
spreads = [n for n in raw if n.startswith('Spreads/')]
where = {}
for n in spreads:
    for m in re.finditer(r'<TextFrame\b[^>]*Self="(\w+)"', raw[n]):
        where[m.group(1)] = n

report = []

# ── 1 · one al ──────────────────────────────────────────────────────
for sid in ONE:
    n = where.get(sid)
    if not n: sys.exit('DURDU: %s bulunamadi' % sid)
    m = frame_re(sid).search(raw[n])
    if not m: sys.exit('DURDU: %s cercevesi okunamadi' % sid)
    blk = m.group(0)
    s = raw[n][:m.start()] + raw[n][m.end():]
    raw[n] = s.replace('</Spread>', blk.rstrip('\n') + '\n\t</Spread>', 1)
    report.append(('one alindi', sid, n.split('/')[-1], ''))

# ── 2 · baska sayfaya tasi ──────────────────────────────────────────
for sid, page, nx, ny in TASI:
    n = where.get(sid)
    if not n: sys.exit('DURDU: %s bulunamadi' % sid)
    hedef = next((k for k in spreads
                  if re.search(r'<Page\b[^>]*Name="%d"' % page, raw[k])), None)
    if not hedef: sys.exit('DURDU: s.%d yapragi bulunamadi' % page)
    b = box_of(raw[n], sid)
    m = frame_re(sid).search(raw[n])
    blk = m.group(0)
    raw[n] = raw[n][:m.start()] + raw[n][m.end():]
    ox, oy = page_origin(raw[hedef], page)
    # Cercevenin kendi yolu degismez; yalnizca oteleme yeniden kurulur.
    t = re.search(r'ItemTransform="([-\d.eE ]+)"', blk)
    v = [float(x) for x in t.group(1).split()]
    # Yolun kendi uzayindaki sol-ust kosesi
    xs, ys = [], []
    for q in re.finditer(r'Anchor="([-\d.eE]+) ([-\d.eE]+)"', blk):
        xs.append(float(q.group(1))); ys.append(float(q.group(2)))
    v[4] = (ox + nx) - min(xs)
    v[5] = (oy + ny) - min(ys)
    blk = blk.replace(t.group(0), 'ItemTransform="%s"'
                      % ' '.join('%.6g' % x for x in v))
    raw[hedef] = raw[hedef].replace('</Spread>', blk.rstrip('\n') + '\n\t</Spread>', 1)
    where[sid] = hedef
    report.append(('tasindi', sid, hedef.split('/')[-1],
                   's.%d  x%.1f y%.1f punto' % (page, nx, ny)))

# ── 3 · ayni yaprakta yerini duzelt ─────────────────────────────────
for sid, ny in YER:
    n = where[sid]
    m = frame_re(sid).search(raw[n])
    blk = m.group(0)
    b = box_of(raw[n], sid)
    sp = ET.fromstring(raw[n]).find('.//Spread')
    oy = None
    for p in sp.findall('Page'):
        g = [float(v) for v in p.get('GeometricBounds').split()]
        it = [float(v) for v in (p.get('ItemTransform') or '1 0 0 1 0 0').split()]
        lo, hi = g[1] + it[4], g[3] + it[4]
        if lo - 1 <= (b[0] + b[2]) / 2 <= hi + 1: oy = g[0] + it[5]
    t = re.search(r'ItemTransform="([-\d.eE ]+)"', blk)
    v = [float(x) for x in t.group(1).split()]
    v[5] += (oy + ny) - b[1]
    nb = blk.replace(t.group(0), 'ItemTransform="%s"'
                     % ' '.join('%.6g' % x for x in v))
    raw[n] = raw[n][:m.start()] + nb + raw[n][m.end():]
    report.append(('yeri duzeltildi', sid, n.split('/')[-1], 'y %.1f punto' % ny))

# ── 4 · rengi sifirla ───────────────────────────────────────────────
# Bu cercevelerin bir kismi daha once koyu bir gorselin altindayken
# olculmus ve kagit rengine cevrilmisti. Artik baska bir yerde ya da
# gorunur durumdalar; rengi stilin kendi rengine birakilir, gerekiyorsa
# fix-contrast yeniden karar verir.
sifir = 0
for sid in ONE + [t[0] for t in TASI] + [t[0] for t in YER]:
    m = re.search(r'<TextFrame\b[^>]*Self="%s"[^>]*>' % re.escape(sid),
                  raw[where[sid]])
    q = re.search(r'ParentStory="(\w+)"', m.group(0))
    if not q: continue
    sp_ = 'Stories/Story_%s.xml' % q.group(1)
    if sp_ not in raw: continue
    d = raw[sp_]
    if isinstance(d, bytes): d = d.decode('utf-8')
    n2 = re.sub(r'(<CharacterStyleRange\b[^>]*?)\s+FillColor="[^"]*"', r'\1', d)
    if n2 != d:
        raw[sp_] = n2; sifir += 1
if sifir: report.append(('rengi sifirlandi', '%d oyku' % sifir, '', ''))

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
tf = sum(len(list(ET.fromstring(z2.read(n)).iter('TextFrame')))
         for n in z2.namelist() if n.startswith('Spreads/'))
z2.close()
tf0 = sum(len(list(ET.fromstring(Z.read(n)).iter('TextFrame')))
          for n in Z.namelist() if n.startswith('Spreads/'))
if before != after: os.remove(tmp); sys.exit('DURDU: bag kaydi degisti')
if not ok: os.remove(tmp); sys.exit('DURDU: XML bozuldu')
if tf != tf0: os.remove(tmp); sys.exit('DURDU: cerceve sayisi %d -> %d' % (tf0, tf))
shutil.move(tmp, DST)

# Tasinan cerceveler ciktida hala eski yerlerinde duruyor. Sonraki
# betikler onlari yaziyla eslememeli; kimlikleri buraya yazilir.
import json
moved = set()
for sid, page, nx, ny in TASI + [(a, None, None, b) for a, b in YER]:
    m = re.search(r'<TextFrame\b[^>]*Self="%s"[^>]*ParentStory="(\w+)"'
                  % re.escape(sid), raw[where[sid]])
    if not m:
        m = re.search(r'<TextFrame\b[^>]*ParentStory="(\w+)"[^>]*Self="%s"'
                      % re.escape(sid), raw[where[sid]])
    if m: moved.add(m.group(1))
yj = os.path.join(os.path.dirname(os.path.abspath(DST)), 'yeni.json')
old = set(json.load(open(yj))) if os.path.exists(yj) else set()
json.dump(sorted(old | moved), open(yj, 'w'))

print('%s -> %s' % (os.path.basename(SRC), os.path.basename(DST)))
for what, sid, n, extra in report:
    print('  %-16s %-9s %-24s %s' % (what, sid, n, extra))
print('  yazi cercevesi %d · bag kaydi %d · hepsi birebir ayni' % (tf, len(before)))
