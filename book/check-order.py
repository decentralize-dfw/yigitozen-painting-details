# -*- coding: utf-8 -*-
"""Gorselin altinda kalan yazi.

IDML'de yaprakta sonra gelen nesne ustte durur. Kullanicinin dosyasinda
bazi yapraklarda gorseller yazi cercevelerinden sonra yaziliydi; o
sayfalarda yazi gorselin altinda kaliyor ve hic gorunmuyor. Cikti bunu
dogruluyor: s.42'de iki yazi da basilmis ama gorunmuyor.

Burada her yazi cercevesi, kendisinden SONRA gelen gorsellerle
karsilastirilir ve ustunu kapatan varsa bildirilir.

    python3 check-order.py belge.idml
"""
import os, sys, re, zipfile
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from place import transform

if len(sys.argv) < 2: sys.exit('kullanim: check-order.py belge.idml')
Z = zipfile.ZipFile(sys.argv[1])


def stx(sid):
    p = 'Stories/Story_%s.xml' % sid
    if p not in Z.namelist(): return ''
    return re.sub(r'\s+', ' ', ''.join(
        (c.text or '') for c in ET.fromstring(Z.read(p)).iter('Content'))).strip()


hidden = []
for n in sorted(Z.namelist()):
    if not n.startswith('Spreads/'): continue
    sp = ET.fromstring(Z.read(n)).find('.//Spread')
    if sp is None: continue
    pg = {}
    for p in sp.findall('Page'):
        g = [float(v) for v in p.get('GeometricBounds').split()]
        it = [float(v) for v in (p.get('ItemTransform') or '1 0 0 1 0 0').split()]
        if p.get('Name', '').isdigit():
            pg[int(p.get('Name'))] = (g[1] + it[4], g[3] + it[4])
    items = [(k, el) for k, el in enumerate(list(sp))
             if el.tag in ('Rectangle', 'TextFrame', 'Polygon', 'Oval')]
    for k, el in items:
        if el.tag != 'TextFrame': continue
        b = transform(el)
        if not b: continue
        q = next((v for v, (a1, a2) in pg.items() if a1 - 1 <= (b[0] + b[2]) / 2 <= a2 + 1), None)
        cover = 0.0
        who = []
        for k2, el2 in items:
            if k2 <= k or el2.find('Image') is None: continue
            c = transform(el2)
            if not c: continue
            ox = min(b[2], c[2]) - max(b[0], c[0])
            oy = min(b[3], c[3]) - max(b[1], c[1])
            if ox > 0 and oy > 0:
                cover = max(cover, ox * oy / max(1.0, (b[2] - b[0]) * (b[3] - b[1])))
                who.append(el2.get('Self'))
        if cover > 0.15:
            hidden.append((q, n, el.get('Self'), round(cover, 2),
                           who, stx(el.get('ParentStory'))[:56]))

print('gorselin altinda kalan yazi: %d' % len(hidden))
for q, n, sid, c, who, t in sorted(hidden, key=lambda r: (r[0] is None, r[0])):
    print('  s.%-5s %-9s %%%3d ortulu · ustundeki gorsel %-24s %r'
          % (q, sid, int(c * 100), ','.join(who)[:24], t))
sys.exit(1 if hidden else 0)
