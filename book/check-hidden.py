# -*- coding: utf-8 -*-
"""Ciktida yazilmis ama gorunmeyen yazi.

IDML'de yaprakta sonra gelen nesne ustte durur. Bazi sayfalarda gorseller
yazi cercevelerinden sonra yazilmis; orada yazi gorselin altinda kalir.
Dosyada durur, PDF'in yazi katmaninda da durur, ama kimse goremez.

Olcum dogrudan yapilir: sayfanin normal hali ile yazisi cikarilmis hali
karsilastirilir. Bir satirin kutusunda iki resim ayni ciktiysa o satir
zaten gorunmuyordu.

    python3 check-hidden.py belge.idml cikti.pdf
"""
import os, sys, collections
import pymupdf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stackmodel import read

if len(sys.argv) < 3: sys.exit('kullanim: check-hidden.py belge.idml cikti.pdf')
IDML, PDF = sys.argv[1], sys.argv[2]
pages, lines, miss = read(IDML, PDF)
D = pymupdf.open(PDF)
Z = 2.0

hid = collections.defaultdict(list)
for q in sorted(pages):
    L = lines.get(q, [])
    if not L: continue
    a = pymupdf.open(); a.insert_pdf(D, from_page=q - 1, to_page=q - 1)
    b = pymupdf.open(); b.insert_pdf(D, from_page=q - 1, to_page=q - 1)
    for l in L:
        b[0].add_redact_annot(pymupdf.Rect(l['x1'] - 1.5, l['y1'] - 3,
                                           l['x2'] + 1.5, l['y2'] + 3))
    b[0].apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE,
                          graphics=pymupdf.PDF_REDACT_LINE_ART_NONE)
    pa = a[0].get_pixmap(matrix=pymupdf.Matrix(Z, Z), colorspace=pymupdf.csGRAY)
    pb = b[0].get_pixmap(matrix=pymupdf.Matrix(Z, Z), colorspace=pymupdf.csGRAY)
    for l in L:
        r = pymupdf.Rect(l['x1'], l['y1'], l['x2'], l['y2']) * Z
        xs = range(max(0, int(r.x0)), max(1, min(pa.width, int(r.x1))))
        ys = range(max(0, int(r.y0)), max(1, min(pa.height, int(r.y1))))
        d = max((abs(pa.pixel(i, j)[0] - pb.pixel(i, j)[0])
                 for j in ys for i in xs), default=0)
        if d < 12: hid[q].append((l['t'], d))

n = sum(len(v) for v in hid.values())
print('sayfa %d · satir %d' % (len(pages), sum(len(v) for v in lines.values())))
print('GORUNMEYEN SATIR: %d (%d sayfada)' % (n, len(hid)))
for q in sorted(hid):
    for t, d in hid[q]:
        print('  s.%-4d %r' % (q, t[:70]))
sys.exit(1 if n else 0)
