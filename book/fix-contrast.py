# -*- coding: utf-8 -*-
"""Okunmayan yaziyi zeminine gore yeniden renklendirir.

Kitabin ayni gri kunyesi beyaz kagit uzerinde okunur, koyu bir tablonun
uzerinde kaybolur; koyu folyo siyah bir tam sayfa gorselin uzerinde hic
gorunmez. Burada her cercevenin altindaki zemin ciktidan orneklenir —
sayfanin yazisiz hali kurulur, gorseller yerinde kalir — ve cerceve
kagit rengine ya da murekkebe cevrilir; hangisi o zeminde daha cok
okunuyorsa.

Kapaktaki buyuk yazilara dokunulmaz: orada beyazin mavi uzerinde durmasi
bir tercihtir, hata degil. Yirmi puntodan buyuk her yazi boyle sayilir ve
yalnizca bildirilir.

    python3 fix-contrast.py girdi.idml cikti.pdf cikti.idml [--rapor]
"""
import os, sys, re, zipfile, shutil
import xml.etree.ElementTree as ET
import pymupdf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stackmodel import read

if len(sys.argv) < 4:
    sys.exit('kullanim: fix-contrast.py girdi.idml cikti.pdf cikti.idml [--rapor]')
SRC, PDF, DST = sys.argv[1], sys.argv[2], sys.argv[3]
import json
_d = os.path.dirname(os.path.abspath(SRC))
_ch = json.load(open(os.path.join(_d, 'degisen.json'))) \
    if os.path.exists(os.path.join(_d, 'degisen.json')) else {}
_ye = json.load(open(os.path.join(_d, 'yeni.json'))) \
    if os.path.exists(os.path.join(_d, 'yeni.json')) else []
pages, lines, miss = read(SRC, PDF, {k: v[0] for k, v in _ch.items()}, _ye)
D = pymupdf.open(PDF)

CAND = {'Color/paper': (255, 255, 255), 'Color/ink': (17, 17, 17)}
BIG = 20.0
SHARE = 0.25


def lum(c):
    def f(v):
        v /= 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])


def ratio(a, b):
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def swallowed(fg, px):
    return sum(1 for p in px if ratio(fg, p) < 3.0) / len(px)


ground = {}
for q in sorted(pages):
    L = lines.get(q, [])
    if not L: continue
    d2 = pymupdf.open(); d2.insert_pdf(D, from_page=q - 1, to_page=q - 1)
    p2 = d2[0]
    for l in L:
        p2.add_redact_annot(pymupdf.Rect(l['x1'] - 1.5, l['y1'] - 3,
                                         l['x2'] + 1.5, l['y2'] + 3))
    p2.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE,
                        graphics=pymupdf.PDF_REDACT_LINE_ART_NONE)
    pm = p2.get_pixmap(matrix=pymupdf.Matrix(1.4, 1.4))
    for l in L:
        r = pymupdf.Rect(l['x1'], l['y1'], l['x2'], l['y2']) * 1.4
        xs = range(max(0, int(r.x0)), max(1, min(pm.width, int(r.x1))))
        ys = range(max(0, int(r.y0)), max(1, min(pm.height, int(r.y1))))
        px = [pm.pixel(i, j) for j in ys for i in xs]
        if px: ground[id(l)] = px

change, keep, big = {}, 0, []
for q in sorted(pages):
    for it in pages[q]['items']:
        if it['kind'] != 'text' or not it['lines']: continue
        px = [p for l in it['lines'] for p in ground.get(id(l), [])]
        if not px: continue
        sz = max(l['span']['size'] for l in it['lines'])
        c = it['lines'][0]['span']['color']
        fg = ((c >> 16) & 255, (c >> 8) & 255, c & 255)
        now = swallowed(fg, px)
        if now <= SHARE: keep += 1; continue
        if sz >= BIG: big.append((q, it['self'], round(now, 2), it['txt'][:44])); continue
        best = min(CAND, key=lambda k: swallowed(CAND[k], px))
        if swallowed(CAND[best], px) >= now: continue
        change[it['story']] = (best, q, it['self'], round(now, 2),
                               round(swallowed(CAND[best], px), 2), it['txt'][:44])

print('%s' % os.path.basename(SRC))
print('  okunan cerceve %d · rengi degisen %d · dokunulmayan buyuk yazi %d'
      % (keep, len(change), len(big)))
for sid, (col, q, self_, was, now, t) in sorted(change.items(), key=lambda x: x[1][1]):
    print('     s.%-4d %-9s %%%2d -> %%%2d  %-12s %r'
          % (q, self_, int(was * 100), int(now * 100), col.split('/')[1], t))
for q, self_, was, t in big:
    print('     s.%-4d %-9s buyuk yazi, elde birakildi (%%%d)  %r'
          % (q, self_, int(was * 100), t))
if '--rapor' in sys.argv: sys.exit(0)

Z = zipfile.ZipFile(SRC)


def links_of(zf):
    out = []
    for n in sorted(zf.namelist()):
        if not n.startswith('Spreads/'): continue
        for el in ET.fromstring(zf.read(n)).iter('Link'):
            out.append((n, el.get('LinkResourceURI'), el.get('LinkResourceFormat')))
    return out


before = links_of(Z)
parts = []
for info in Z.infolist():
    d = Z.read(info.filename)
    m = re.match(r'Stories/Story_(\w+)\.xml$', info.filename)
    if m and m.group(1) in change:
        col = change[m.group(1)][0]
        s = d.decode('utf-8')
        s = re.sub(r'(<CharacterStyleRange\b[^>]*?)\s*FillColor="[^"]*"', r'\1', s)
        s = s.replace('<CharacterStyleRange ',
                      '<CharacterStyleRange FillColor="%s" ' % col)
        d = s.encode('utf-8')
    parts.append((info.filename, d))

tmp = DST + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for name, d in parts:
        if name == 'mimetype':
            zi = zipfile.ZipInfo('mimetype'); zi.compress_type = zipfile.ZIP_STORED
            zo.writestr(zi, d)
        else:
            zo.writestr(name, d)

z2 = zipfile.ZipFile(tmp)
ok = True
for nm in z2.namelist():
    if nm.endswith('.xml'):
        try: ET.fromstring(z2.read(nm))
        except Exception as e: ok = False; print('AYRISMADI', nm, e)
after = links_of(z2); z2.close()
if before != after: os.remove(tmp); sys.exit('DURDU: bag kaydi degisti')
if not ok: os.remove(tmp); sys.exit('DURDU: XML bozuldu')
shutil.move(tmp, DST)
print('  -> %s · bag kaydi %d, hepsi birebir ayni'
      % (os.path.basename(DST), len(before)))
