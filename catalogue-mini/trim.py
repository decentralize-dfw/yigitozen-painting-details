# -*- coding: utf-8 -*-
"""Levhalarin cevresindeki bos zemini keser.

Kayittaki fotograflar isin kendisinden genis: kagit ya da tuval beyaz bir
zeminin ustunde durdugu icin her kenarda bos alan var, ve sayfada is
oldugundan kucuk gorunuyor. Kesim olculur, uydurulmaz: koyulastigi yer
bulunur, biraz pay birakilir, ve is fotografin yarisindan azina duserse
kesim yapilmaz — o zaman zemin degil, isin kendisi acik demektir.

    python3 trim.py            # images/ icini yerinde keser
"""
import os, sys
from PIL import Image, ImageChops, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, 'images')
PAD = 0.006          # kalan kenar payi, kenar uzunlugunun orani
LIMIT = 0.45         # bundan fazlasini kesmeye kalkarsa dokunma

kesildi = birakildi = 0
rapor = []
for n in sorted(os.listdir(IMG)):
    if not n.lower().endswith('.jpg'): continue
    p = os.path.join(IMG, n)
    im = Image.open(p); im.load()
    g = im.convert('L').filter(ImageFilter.MedianFilter(3))
    W, H = g.size
    # Kenarlardaki zemin rengi: dort kosenin ortalamasi
    k = max(4, min(W, H) // 60)
    corners = [g.crop(b) for b in ((0, 0, k, k), (W - k, 0, W, k),
                                   (0, H - k, k, H), (W - k, H - k, W, H))]
    bg = sum(sum(c.getdata()) / (k * k) for c in corners) / 4.0
    if bg < 150:                       # koyu zemin: kesme
        birakildi += 1; continue
    bgim = Image.new('L', g.size, int(round(bg)))
    diff = ImageChops.difference(g, bgim).point(lambda v: 255 if v > 16 else 0)
    box = diff.getbbox()
    if not box: birakildi += 1; continue
    x1, y1, x2, y2 = box
    if (x2 - x1) < W * LIMIT or (y2 - y1) < H * LIMIT:
        birakildi += 1; continue
    px, py = int(W * PAD), int(H * PAD)
    box = (max(0, x1 - px), max(0, y1 - py), min(W, x2 + px), min(H, y2 + py))
    if box == (0, 0, W, H): birakildi += 1; continue
    im.crop(box).save(p, 'JPEG', quality=82, optimize=True, progressive=True)
    kesildi += 1
    rapor.append((n, W, H, box[2] - box[0], box[3] - box[1]))

print('kesilen %d · dokunulmayan %d' % (kesildi, birakildi))
for n, W, H, w, h in rapor[:10]:
    print('   %s %dx%d -> %dx%d (%%%d x %%%d)' % (n, W, H, w, h, 100 * w // W, 100 * h // H))
