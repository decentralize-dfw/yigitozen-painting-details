# -*- coding: utf-8 -*-
"""Cizgi yazinin uzerinden geciyor mu.

Kitapta 115 ince dolu dikdortgen var: sayfa cizgileri. Kullanicinin
gonderdigi ekran goruntusunde bunlardan biri basligin icinden geciyor.
Cerceve kenari degil, cizilmis cizgi.

Cizgilerin yeri IDML'den, basilan yazinin yeri ciktidan okunur; ciktidaki
satir kutusu yalan soylemez. Kesisen her cift bir sayfa hatasidir.

    python3 check-rules.py belge.idml cikti.pdf
"""
import os, sys, zipfile, collections
import xml.etree.ElementTree as ET
import pymupdf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from place import transform, PT

if len(sys.argv) < 3:
    sys.exit('kullanim: check-rules.py belge.idml cikti.pdf')
Z = zipfile.ZipFile(sys.argv[1])
D = pymupdf.open(sys.argv[2])

lines = collections.defaultdict(list)
for i, pg in enumerate(D):
    for b in pg.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            xs = [s['bbox'] for s in l['spans']]
            t = ''.join(s['text'] for s in l['spans']).strip()
            if not t: continue
            # Gercek harf kutusu: pymupdf'in span kutusu fontun inis-cikis
            # payini da tasir; asagida bir puntoluk pay birakilir.
            lines[i + 1].append((min(b[0] for b in xs), min(b[1] for b in xs),
                                 max(b[2] for b in xs), max(b[3] for b in xs), t))

rules = []
for n in Z.namelist():
    if not n.startswith('Spreads/'): continue
    sp = ET.fromstring(Z.read(n)).find('.//Spread')
    pages = {}
    for p in sp.findall('Page'):
        g = [float(v) for v in p.get('GeometricBounds').split()]
        it = [float(v) for v in (p.get('ItemTransform') or '1 0 0 1 0 0').split()]
        if p.get('Name', '').isdigit():
            pages[int(p.get('Name'))] = (g[1] + it[4], g[0] + it[5],
                                         g[3] + it[4], g[2] + it[5])
    for r in sp.iter('Rectangle'):
        if r.find('Image') is not None: continue
        b = transform(r)
        if not b: continue
        if (b[3] - b[1]) > 3.0: continue          # cizgi degil
        pn = next((q for q, (a1, b1, a2, b2) in pages.items()
                   if a1 - 1 <= (b[0] + b[2]) / 2 <= a2 + 1), None)
        if pn is None: continue
        ox, oy = pages[pn][0], pages[pn][1]
        rules.append((pn, r.get('Self'), n,
                      b[0] - ox, b[1] - oy, b[2] - ox, b[3] - oy))

hit = []
for pn, sid, part, x1, y1, x2, y2 in rules:
    for lx1, ly1, lx2, ly2, t in lines.get(pn, []):
        ox = min(x2, lx2) - max(x1, lx1)
        oy = min(y2, ly2 - 1.0) - max(y1, ly1 + 1.0)
        if ox > 1.0 and oy > 0.0:
            hit.append((pn, sid, part, round(oy, 2), t[:60],
                        round(y1, 1), round(ly1, 1), round(ly2, 1)))

print('cizgi %d · basili satir %d' % (len(rules), sum(len(v) for v in lines.values())))
print('CIZGI YAZININ USTUNDEN GECIYOR: %d' % len(hit))
for h in sorted(hit):
    print('  s.%-4d %-8s cizgi y=%6.1f · satir y=%.1f..%.1f (%.2f pt icinde)\n        %r'
          % (h[0], h[1], h[5], h[6], h[7], h[3], h[4]))
sys.exit(1 if hit else 0)
