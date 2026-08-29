# -*- coding: utf-8 -*-
"""Bitmis belgenin son denetimi.

Oturmus duzenin gercek yerleri oturmus.json'da; yeni kunyelerin yeri
belgenin kendisinde. Ikisi birlestirilir ve sayfa sayfa bakilir: hicbir
sey hicbir seyin ustune binmemeli.

    python3 check-final.py belge.idml oturmus.json
"""
import os, sys, json, re, zipfile, collections
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from place import transform, caption_height, PT, HEAD, FOOT, OUTER

if len(sys.argv) < 3:
    sys.exit('kullanim: check-final.py belge.idml oturmus.json')
Z = zipfile.ZipFile(sys.argv[1])
TAKEN = {int(k): v for k, v in json.load(open(sys.argv[2])).items()}
NEW = re.compile(r'^(cn|cw|cs|cr)')


def stx(sid):
    p = 'Stories/Story_%s.xml' % sid
    if p not in Z.namelist(): return ''
    return re.sub(r'\s+', ' ', ''.join(
        (c.text or '') for c in ET.fromstring(Z.read(p)).iter('Content'))).strip()


fresh = collections.defaultdict(list)
outside = []
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
    for f in sp.iter('TextFrame'):
        sid = f.get('ParentStory')
        if not NEW.match(sid or ''): continue
        b = transform(f)
        pn = next((q for q, (a1, b1, a2, b2) in pages.items()
                   if a1 - 1 <= (b[0] + b[2]) / 2 <= a2 + 1), None)
        if pn is None: continue
        ox, oy = pages[pn][0], pages[pn][1]
        t = stx(sid)
        h = caption_height(t, b[2] - b[0])
        box = (b[0] - ox, b[1] - oy, b[2] - ox, b[1] - oy + h)
        fresh[pn].append((box, sid, t))
        pw = pages[pn][2] - pages[pn][0]
        ph = pages[pn][3] - pages[pn][1]
        if (box[0] < -0.5 or box[2] > pw + 0.5 or box[1] < HEAD - 0.5
                or box[3] > ph - FOOT + 0.5):
            outside.append((pn, sid, [round(v, 1) for v in box]))

clash = []
for pn in sorted(set(list(TAKEN) + list(fresh))):
    boxes = [(b, 'oturmus', '') for b in TAKEN.get(pn, [])]
    boxes += [(b, sid, t) for b, sid, t in fresh[pn]]
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            (a, ai, at), (b, bi, bt) = boxes[i], boxes[j]
            if ai == 'oturmus' and bi == 'oturmus': continue
            ox = min(a[2], b[2]) - max(a[0], b[0])
            oy = min(a[3], b[3]) - max(a[1], b[1])
            tx = min(0.4, 0.6 * min(a[2] - a[0], b[2] - b[0]))
            ty = min(0.4, 0.6 * min(a[3] - a[1], b[3] - b[1]))
            if ox > tx and oy > ty:
                clash.append((pn, round(ox / PT, 1), round(oy / PT, 1),
                              ai, at[:40], bi, bt[:40]))

n = sum(len(v) for v in fresh.values())
print('sayfa %d · oturmus satir %d · yeni kunye %d'
      % (len(TAKEN), sum(len(v) for v in TAKEN.values()), n))
print('UST USTE BINEN: %d' % len(clash))
for c in clash[:20]:
    print('  s.%-4d %.1f x %.1f mm\n        %s %r\n        %s %r'
          % (c[0], c[1], c[2], c[3], c[4], c[5], c[6]))
print('YAZI ALANININ DISINDA: %d' % len(outside))
for o in outside[:12]: print('  s.%-4d %-9s %s' % o)
sys.exit(1 if (clash or outside) else 0)
