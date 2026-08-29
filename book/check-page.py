# -*- coding: utf-8 -*-
"""Sayfada birbirinin uzerine binen her sey — satir satir.

Cerceveyi tek kutu saymak yanlis sonuc verir: uc satirlik bir baslik
kunyenin satirini arasina alir, cercevelerin kutulari ust uste biner ama
harfler binmeyebilir. Olcu satirin kendisiyle, satirin da fontun kutusuyla
degil gorunen murekkebiyle alinir (bkz. ink.py).

    python3 check-page.py belge.idml cikti.pdf
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stackmodel import read

if len(sys.argv) < 3:
    sys.exit('kullanim: check-page.py belge.idml cikti.pdf')
pages, lines, miss = read(sys.argv[1], sys.argv[2])
PAD = 0.4

bad = []
for q, P in sorted(pages.items()):
    boxes = []
    for it in P['items']:
        if it.get('approx') and not it.get('fresh'): continue
        if it['kind'] == 'rule' or not it['lines']:
            boxes.append((it['ren'], it, it['txt'] or '(cizgi)'))
        else:
            for l in it['lines']:
                boxes.append(((l['x1'], l['y1'], l['x2'], l['y2']), it, l['t']))
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            (a, ai, at), (b, bi, bt) = boxes[i], boxes[j]
            if ai is bi: continue
            ox = min(a[2], b[2]) - max(a[0], b[0])
            oy = min(a[3], b[3]) - max(a[1], b[1])
            # Ince bir cizgi basligin tam ortasinda dursa bile ortusme
            # cizginin boyu kadardir, yarim punto. Esik bu yuzden kucuk
            # olanin boyuna gore alinir.
            ty = min(PAD, 0.6 * min(a[3] - a[1], b[3] - b[1]))
            tx = min(PAD, 0.6 * min(a[2] - a[0], b[2] - b[0]))
            if ox > tx and oy > ty:
                bad.append((q, round(oy, 1), ai, at, bi, bt))

print('sayfa %d · nesne %d · ciktida eslesmeyen cerceve %d'
      % (len(pages), sum(len(p['items']) for p in pages.values()), len(miss)))
print('UST USTE BINEN: %d' % len(bad))
for q, oy, ai, at, bi, bt in bad:
    print('  s.%-4d %5.1f pt · %-6s %-9s %s\n                 %-6s %-9s %s'
          % (q, oy, ai['role'], ai['self'], at[:44],
             bi['role'], bi['self'], bt[:44]))
sys.exit(1 if bad else 0)
