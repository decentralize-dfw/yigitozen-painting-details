# -*- coding: utf-8 -*-
"""Her yazinin altindaki zemine karsi okunurlugu.

Ayni gri beyaz kagit uzerinde okunur, koyu bir tablonun uzerinde
kaybolur. Olcum icin sayfanin yazisiz hali kurulur — yazilar cikarilir,
gorseller oldugu gibi kalir — ve her satirin tam altindaki zemin
orneklenir.

Okunurluk WCAG'in isik orani ile olculur; 3'un altina dusen her satir
bildirilir.

    python3 check-contrast.py belge.idml cikti.pdf
"""
import os, sys, collections
import xml.etree.ElementTree as ET
import pymupdf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stackmodel import read

if len(sys.argv) < 3:
    sys.exit('kullanim: check-contrast.py belge.idml cikti.pdf')
IDML, PDF = sys.argv[1], sys.argv[2]
pages, lines, miss = read(IDML, PDF)
D = pymupdf.open(PDF)


def lum(c):
    def f(v):
        v /= 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])


def ratio(a, b):
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


bad = []
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
        xs = range(max(0, int(r.x0)), min(pm.width, int(r.x1)) or 1)
        ys = range(max(0, int(r.y0)), min(pm.height, int(r.y1)) or 1)
        px = [pm.pixel(i, j) for j in ys for i in xs]
        if not px: continue
        c = l['span']['color']
        fg = ((c >> 16) & 255, (c >> 8) & 255, c & 255)
        # Tek bir kotu benek olcu degildir: bir tablonun uzerinde her
        # renkten bir parca bulunur. Olculen sey, zeminin ne kadarinin
        # yaziyi yutacagi — alanin dortte birinden fazlasi ise yazi
        # okunmaz sayilir.
        rs = [ratio(fg, p) for p in px]
        share = sum(1 for r in rs if r < 3.0) / len(rs)
        rs.sort()
        med = sorted(px, key=lum)[len(px) // 2]
        if share > 0.25:
            bad.append((q, round(share, 2), round(rs[len(rs) // 2], 2), fg, med,
                        round(l['span']['size'], 1), l['t'][:52]))

print('sayfa %d · satir %d' % (len(pages), sum(len(v) for v in lines.values())))
print('OKUNMASI ZOR: %d' % len(bad))
seen = set()
for q, share, rr, fg, med, sz, t in bad:
    k = (q, t)
    if k in seen: continue
    seen.add(k)
    print('  s.%-4d yutulan alan %%%2d · orta oran %4.2f · %4.1fpt yazi rgb%s zemin rgb%s\n        %r'
          % (q, int(share * 100), rr, sz, fg, med, t))
sys.exit(1 if bad else 0)
