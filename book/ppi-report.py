# -*- coding: utf-8 -*-
"""
Baski ustasindaki her gorselin kagitta kac ppi ettigini soyler, ve
yetmeyenler icin kaynagin kac piksel olmasi gerektigini yazar.

    python3 book.py <works.json> --print
    python3 ppi-report.py

Buyutme yapilmaz: bir fotograf kac pikselse o kadardir. Bu liste, hangi
tablonun yeniden cekilmesi gerektigini soyleyen listedir.
"""
import os, re, json
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', 'yigit'))
html = open(os.path.join(HERE, 'book-print.html'), encoding='utf-8').read()
works = {w['n']: w for w in json.load(open(os.path.join(ROOT, 'works.json'),
                                           encoding='utf-8'))}
IMG = re.compile(r'<img[^>]*src="images-print/([^"]+)"[^>]*'
                 r'width:([\d.]+)mm;height:([\d.]+)mm')
rows, seen = [], set()
for f, wmm, hmm in IMG.findall(html):
    fp = os.path.join(HERE, 'images-print', f)
    if f in seen or not os.path.isfile(fp): continue
    seen.add(f)
    px, pyh = Image.open(fp).size
    wmm, hmm = float(wmm), float(hmm)
    # object-fit: cover kutuyu doldurur, gorsel kutudan buyuk cizilebilir;
    # kagitta gorunen yogunluk hangi kenar tasiyorsa ondan cikar.
    scale = max(wmm / px, hmm / pyh)
    rows.append({'f': f, 'px': px, 'mm': round(wmm),
                 'ppi': round(25.4 / scale)})

def who(f):
    m = re.match(r'[wp](\d\d)', f)
    if m and int(m.group(1)) in works:
        n = int(m.group(1))
        return '%02d %s' % (n, works[n]['title'][:32])
    if f.startswith('m'):  return 'tekrar edenler bolumu'
    if f.startswith('ix'): return 'dizin'
    if f.startswith('recur'): return 'tekrar edenler acilisi'
    return f[:32]

rows.sort(key=lambda r: r['ppi'])
band = lambda lo, hi: sum(1 for r in rows if lo <= r['ppi'] < hi)
print('%d ayri gorsel basiliyor.' % len(rows))
print('  300 ppi ve ustu : %d' % sum(1 for r in rows if r['ppi'] >= 300))
print('  240 - 299       : %d' % band(240, 300))
print('  180 - 239       : %d' % band(180, 240))
print('  180 altinda     : %d' % band(0, 180))
low = [r for r in rows if r['ppi'] < 240]
print('\nYETMEYENLER — kaynak dosya kac piksel olmali:\n')
print('%-34s %7s %5s %5s  %s' % ('IS', 'piksel', 'mm', 'ppi', '300 ppi icin'))
print('-' * 84)
for r in low[:24]:
    need = int(r['mm'] / 25.4 * 300)
    print('%-34s %7d %5d %5d  %5d px  (x%.1f)'
          % (who(r['f'])[:34], r['px'], r['mm'], r['ppi'], need, need / r['px']))
