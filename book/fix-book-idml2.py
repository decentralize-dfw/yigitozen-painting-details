# -*- coding: utf-8 -*-
"""
Duzenlenmis kitapta iki seyi onarir, yine baglarina dokunmadan.

1 · Kapak. Uc yazi cercevesinin fontu yerel olarak Helvetica'ya cevrilmis.
    Paragraf stilleri dogru duruyor — 'd l' ve 'm wh' — yalniz font ve renk
    ezilmis. Yerel eziklikler kaldirilir, stiller yeniden gecerli olur.

2 · Koyu zemin ustunde koyu yazi. Gorseller yer degistirince folyolar ve
    kunyeler resmin uzerine dustu. Zemini gercekten koyu olan yerlerde yazi
    kagit rengine alinir. Hangi yerlerin koyu oldugu tahminle degil, ciktinin
    o noktasindaki parlaklik olculerek belirlenir.

    python3 fix-book-idml2.py girdi.idml render.pdf cikti.idml

Spreads/ hic acilmaz; her Link kaydi once ve sonra karsilastirilir, biri
bile oynamissa dosya yazilmaz.
"""
import os, sys, re, zipfile, shutil
import xml.etree.ElementTree as ET
import pymupdf

if len(sys.argv) < 4:
    sys.exit('kullanim: fix-book-idml2.py girdi.idml render.pdf cikti.idml')
SRC, PDF, DST = sys.argv[1], sys.argv[2], sys.argv[3]

Z = zipfile.ZipFile(SRC)
D = pymupdf.open(PDF)


def links_of(zf):
    out = []
    for n in sorted(zf.namelist()):
        if not n.startswith('Spreads/'): continue
        for el in ET.fromstring(zf.read(n)).iter('Link'):
            out.append((n, el.get('LinkResourceURI'), el.get('LinkResourceFormat')))
    return out


def story_text(sid):
    p = 'Stories/Story_%s.xml' % sid
    if p not in Z.namelist(): return ''
    return ''.join((c.text or '')
                   for c in ET.fromstring(Z.read(p)).iter('Content'))


# ── 1 · kapaktaki yerel ezikliklerin yeri ───────────────────────────
cover = set()
for n in sorted(Z.namelist()):
    if not n.startswith('Spreads/'): continue
    t = ET.fromstring(Z.read(n))
    if not any(p.get('Name') == '1' for p in t.find('.//Spread').findall('Page')):
        continue
    for f in t.findall('.//TextFrame'):
        cover.add(f.get('ParentStory'))
    break

# ── 2 · koyu zemin ustunde kalan yazilar ────────────────────────────
# Once ciktida olculur: yazinin altindaki zeminin parlakligi 128'in
# altindaysa o yazi kagit rengine alinacaktir.
DARKINK = ('Color/ink', 'Color/grey', 'Color/$ID/[Black]')
wanted = set()
for i, pg in enumerate(D):
    rects = [r for im in pg.get_images(full=True) for r in pg.get_image_rects(im[0])]
    if not rects: continue
    for b in pg.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            for s in l.get('spans', []):
                t = s['text'].strip()
                if not t: continue
                if s.get('color', 0) not in (0x111111, 0x000000, 0x6e6e6e, 0x1a1a1a):
                    continue
                bb = pymupdf.Rect(s['bbox'])
                if not any((bb & r).is_valid and (bb & r).get_area() > bb.get_area() * .6
                           for r in rects):
                    continue
                pm = pg.get_pixmap(clip=bb, matrix=pymupdf.Matrix(1, 1))
                if pm.width * pm.height == 0: continue
                px, step = pm.samples, pm.n
                lum = sum(px[k] for k in range(0, len(px), step)) / max(1, len(px) // step)
                if lum < 128:
                    wanted.add((i + 1, re.sub(r'\s+', ' ', t)[:40]))

# Hangi hikaye hangi sayfada
page_of = {}
for n in Z.namelist():
    if not n.startswith('Spreads/'): continue
    t = ET.fromstring(Z.read(n)); sp = t.find('.//Spread')
    rng = []
    for p in sp.findall('Page'):
        g = [float(v) for v in p.get('GeometricBounds').split()]
        rng.append((g[1], g[3], p.get('Name')))
    for f in t.findall('.//TextFrame'):
        pts = [q.get('Anchor').split() for q in f.iter('PathPointType')]
        x1 = min(float(q[0]) for q in pts)
        for lo, hi, name in rng:
            if lo - 1 <= x1 <= hi + 1 and name.isdigit():
                page_of[f.get('ParentStory')] = int(name); break

lighten = set()
for sid, pn in page_of.items():
    txt = re.sub(r'\s+', ' ', story_text(sid)).strip()
    if not txt: continue
    for wp, wt in wanted:
        if wp != pn: continue
        if wt.lower()[:26] in txt.lower() or txt.lower()[:26] in wt.lower():
            lighten.add(sid); break

# ── yaz ─────────────────────────────────────────────────────────────
before = links_of(Z)
n_cover = n_light = 0
parts = []
for info in Z.infolist():
    data = Z.read(info.filename)
    m = re.match(r'Stories/Story_(\w+)\.xml$', info.filename)
    if m:
        sid = m.group(1)
        s = data.decode('utf-8')
        new = s
        if sid in cover:
            # Yerel font ve renk ezikligini kaldir: stil yeniden gecerli olsun.
            new = re.sub(r'\s*<AppliedFont type="string">Helvetica[^<]*</AppliedFont>',
                         '', new)
            new = re.sub(r'\s+FontStyle="(?:Light|Bold|Regular|Oblique)"(?=[^>]*>)',
                         '', new)
            new = re.sub(r'\s+FillColor="Color/(?!ink|grey|paper)[^"]*"', '', new)
            if new != s: n_cover += 1
        if sid in lighten:
            # Koyu zemin: yazi kagit rengine alinir.
            s2 = new
            new = re.sub(r'FillColor="Color/(?:ink|grey)"',
                         'FillColor="Color/paper"', new)
            if 'FillColor=' not in s2:
                new = new.replace('<CharacterStyleRange ',
                                  '<CharacterStyleRange FillColor="Color/paper" ')
            if new != s2: n_light += 1
        if new != s: data = new.encode('utf-8')
    parts.append((info, data))

tmp = DST + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for info, data in parts:
        if info.filename == 'mimetype':
            zi = zipfile.ZipInfo('mimetype'); zi.compress_type = zipfile.ZIP_STORED
            zo.writestr(zi, data)
        else:
            zo.writestr(info.filename, data)

z2 = zipfile.ZipFile(tmp)
after = links_of(z2)
same = Z.namelist() == z2.namelist()
ok = True
for n in z2.namelist():
    if n.endswith('.xml'):
        try: ET.fromstring(z2.read(n))
        except Exception as e: ok = False; print('AYRISMADI', n, e)
z2.close()
if before != after: os.remove(tmp); sys.exit('DURDU: bag kaydi degismis')
if not same: os.remove(tmp); sys.exit('DURDU: paket girisleri degismis')
if not ok: os.remove(tmp); sys.exit('DURDU: XML bozuldu')
shutil.move(tmp, DST)

print('%s -> %s' % (os.path.basename(SRC), os.path.basename(DST)))
print('  kapak: yerel Helvetica ezikligi kaldirilan hikaye %d' % n_cover)
print('  koyu zemin ustunde kagit rengine alinan hikaye %d (%d yazi parcasi olculdu)'
      % (n_light, len(wanted)))
print('  bag kaydi %d · hepsi birebir ayni · her XML ayrisiyor' % len(before))
