# -*- coding: utf-8 -*-
"""
editor/ -> yigit/booklet-editor/

Depodaki duzenleyici, arsivin tam boy dosyalarini depo icinden okur.
Siteye konan kopya bunu yapamaz: o dosyalar orada yok ve bir kismi
on megabaytin ustunde. Bu betik siteye konacak seti kurar: sayfa
kesitleri, baski seti, arsivin 2600 piksellik turevleri, on izlemeler,
yazi tipleri ve tek bir data.js.

Yollar siteye gore yazilir: /booklet-editor/ icinden 'img/...' okunur,
'editor/img/...' degil.
"""
import os, sys, json, shutil
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, os.pardir))
SRC  = os.path.join(REPO, 'editor')
DST  = os.path.abspath(sys.argv[1] if len(sys.argv) > 1
                       else os.path.join(REPO, os.pardir, 'yigit', 'booklet-editor'))
FULL_PX = 2600

def rel(p):
    """model.json depo koku icin yazilmistir; site kopyasi kendi icinden okur."""
    return p[len('editor/'):] if p.startswith('editor/') else p

# ── sayfa kesitleri ve baski seti: eskiyi birak, yeniyi koy ─────────
for d in ('img', 'img-print', 'thumb', 'fonts'):
    s, t = os.path.join(SRC, d), os.path.join(DST, d)
    if not os.path.isdir(s): continue
    if os.path.isdir(t): shutil.rmtree(t)
    shutil.copytree(s, t)
    print('%-10s %4d files  %s' % (d, len(os.listdir(t)),
          '%.0f MB' % (sum(os.path.getsize(os.path.join(t, f))
                           for f in os.listdir(t)) / 1048576)))
shutil.copyfile(os.path.join(SRC, 'book.css'), os.path.join(DST, 'book.css'))

# ── model: yollar site koku yerine klasorun kendisine gore ──────────
model = json.load(open(os.path.join(SRC, 'model.json'), encoding='utf-8'))
n_img = 0
for p in model['pages']:
    for e in p['els']:
        if e.get('t') == 'img':
            e['src'] = rel(e['src']); n_img += 1

# ── arsiv: tam boy dosya siteye 2600 pikselde jpeg olarak kopyalanir ─
FULLD = os.path.join(DST, 'full')
if not os.path.isdir(FULLD): os.makedirs(FULLD)
arch = json.load(open(os.path.join(SRC, 'archive.json'), encoding='utf-8'))
made, kept, gone = 0, 0, []
for g in arch['groups']:
    for it in g['items']:
        if it.get('thumb'): it['thumb'] = rel(it['thumb'])
        best = it.get('full')
        if not best: continue
        stem = os.path.splitext(os.path.basename(it['thumb'] or best))[0]
        out  = os.path.join(FULLD, stem + '.jpg')
        srcp = (os.path.join(SRC, best[len('editor/'):]) if best.startswith('editor/')
                else os.path.join(REPO, best))
        if not os.path.isfile(out):
            if not os.path.isfile(srcp): gone.append(best); it['full'] = None; continue
            try:
                im = Image.open(srcp)
                if im.mode not in ('RGB', 'L'): im = im.convert('RGB')
                if im.size[0] > FULL_PX: im.thumbnail((FULL_PX, FULL_PX), Image.LANCZOS)
                im.convert('RGB').save(out, 'JPEG', quality=82, optimize=True)
                made += 1
            except Exception as e:
                gone.append('%s (%s)' % (best, e)); it['full'] = None; continue
        else:
            kept += 1
        it['full'] = 'full/' + stem + '.jpg'
        it['px']   = Image.open(out).size[0]

printpx = json.load(open(os.path.join(SRC, 'printpx.json'), encoding='utf-8'))
with open(os.path.join(DST, 'data.js'), 'w', encoding='utf-8') as f:
    f.write('window.BOOKLET={model:')
    json.dump(model, f, ensure_ascii=False, separators=(',', ':'))
    f.write(',archive:')
    json.dump(arch, f, ensure_ascii=False, separators=(',', ':'))
    f.write(',printPx:')
    json.dump(printpx, f, separators=(',', ':'))
    f.write('};\n')

print('pages %d  page images %d' % (len(model['pages']), n_img))
print('archive full: %d made, %d already there, %d unavailable' % (made, kept, len(gone)))
for x in gone[:5]: print('   missing:', x)
print('deployed to', DST)
