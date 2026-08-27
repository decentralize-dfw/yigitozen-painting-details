# -*- coding: utf-8 -*-
"""
book.html -> editor/model.json + editor/archive.json

Kitabin cizilmis halini duzenlenebilir bir belgeye cevirir. Her sayfa,
milimetre cinsinden yerleri belli ogelerden olusur; booklet-editor.html
bunu okur, tasinan her ogeyi ayni birimde geri yazar ve ayni CSS ile
basar. Boylece ekranda gordugun sey basilacak sey olur.

    python3 make-editor-model.py
"""
import os, re, json, shutil
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, os.pardir))
ROOT = os.path.abspath(os.path.join(REPO, os.pardir, 'yigit'))
OUT  = os.path.join(REPO, 'editor')
IMG  = os.path.join(OUT, 'img')
for d in (OUT, IMG):
    if not os.path.isdir(d): os.makedirs(d)

html = open(os.path.join(HERE, 'book.html'), encoding='utf-8').read()

SEC = re.compile(r'<section class="pg ([^"]*)" data-fam="([^"]*)"><div class="tp">(.*?)</div></section>', re.S)
STYLE = re.compile(r'(left|top|width|height):([-\d.]+)mm')

def sty(s2):
    """Stil dizesinden milimetre degerlerini alir."""
    return dict((k, float(v)) for k, v in STYLE.findall(s2))

def attrs(tag):
    return dict(re.findall(r'(\w[\w-]*)="([^"]*)"', tag))

def scan(body):
    """Sayfanin govdesini sirayla gezer. Ic ice gecen div'ler sayilarak
       kapanis bulunur, boylece hicbir kutu atlanmaz."""
    out, i = [], 0
    while True:
        j = body.find('<', i)
        if j < 0: break
        k = body.find('>', j)
        if k < 0: break
        tag = body[j:k + 1]
        if tag.startswith('<img'):
            out.append((attrs(tag), None)); i = k + 1; continue
        if tag.startswith('<div'):
            depth, m2 = 1, k + 1
            while depth:
                nd = body.find('<div', m2); cd = body.find('</div>', m2)
                if cd < 0: break
                if 0 <= nd < cd: depth += 1; m2 = nd + 4
                else: depth -= 1; m2 = cd + 6
            out.append((attrs(tag), body[k + 1:m2 - 6]))
            i = m2; continue
        i = k + 1
    return out

pages = []
for cls, fam, body in SEC.findall(html):
    els = []
    for a, inner in scan(body):
        c = a.get('class', '')
        st = sty(a.get('style', ''))
        if inner is None:
            pos = ''
            mp = re.search(r'object-position:([^";]*)', a.get('style', ''))
            if mp: pos = mp.group(1)
            els.append({'t': 'img', 'cls': c, 'src': a.get('src', ''),
                        'x': st.get('left', 0.0), 'y': st.get('top', 0.0),
                        'w': st.get('width', 0.0), 'h': st.get('height', 0.0),
                        'pos': pos})
        elif c.startswith('b '):
            extra = re.sub(r'(left|top|width):[-\d.]+mm;?', '', a.get('style', '')).strip(' ;')
            els.append({'t': 'txt', 'cls': c[2:], 'x': st.get('left', 0.0),
                        'y': st.get('top', 0.0), 'w': st.get('width', 0.0),
                        'style': extra, 'html': inner.strip()})
        elif c == 'fr':
            els.append({'t': 'frame', 'x': st.get('left', 0.0), 'y': st.get('top', 0.0),
                        'w': st.get('width', 0.0), 'h': st.get('height', 0.0)})
        elif c == 'shade':
            els.append({'t': 'shade'})
        elif c.startswith('r'):
            els.append({'t': 'rule', 'cls': c, 'x': st.get('left', 0.0),
                        'y': st.get('top', 0.0), 'w': st.get('width', 0.0),
                        'h': st.get('height', 0.0)})
    for e in els:
        if e['t'] == 'img':
            e['src'] = 'editor/img/' + os.path.basename(e['src'])
    els.sort(key=lambda e: (e.get('y', 0), e.get('x', 0)))
    pages.append({'cls': cls.strip(), 'fam': fam, 'els': els})

model = {
    'trim': [240.0, 320.0], 'bleed': 5.0,
    'grid': {'cols': 12, 'gut': 4.0, 'measure': 204.0, 'outer': 16.0, 'inner': 20.0,
             'head': 18.0, 'foot': 22.0, 'regs': [18.0, 83.0, 148.0, 213.0], 'baseline': 5.0},
    'pages': pages,
}
json.dump(model, open(os.path.join(OUT, 'model.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, separators=(',', ':'))

# Sayfalarin kullandigi butun kesitler editorun kendi klasorune kopyalanir.
used = set()
for p in pages:
    for e in p['els']:
        if e['t'] == 'img': used.add(e['src'])
n = 0
for src in sorted(used):
    s = os.path.join(HERE, os.path.basename(os.path.dirname(src)), os.path.basename(src))
    if not os.path.isfile(s):
        s = os.path.join(HERE, 'images', os.path.basename(src))
    if os.path.isfile(s):
        shutil.copyfile(s, os.path.join(IMG, os.path.basename(src))); n += 1

# Editorun kendi kopyasi: ayni yazi, ayni olcu, ayni kagit.
shutil.copyfile(os.path.join(HERE, 'book.css'), os.path.join(OUT, 'book.css'))
FONTS = os.path.join(OUT, 'fonts')
if not os.path.isdir(FONTS): os.makedirs(FONTS)
for f in os.listdir(os.path.join(HERE, 'fonts')):
    if f.endswith(('.ttf', '.txt')):
        shutil.copyfile(os.path.join(HERE, 'fonts', f), os.path.join(FONTS, f))
for f in ('logo.svg',):
    sp = os.path.join(HERE, 'images', f)
    if os.path.isfile(sp): shutil.copyfile(sp, os.path.join(IMG, f))

# ── arsiv: ise gore gruplanmis, tam cozunurluklu kaynaklar ───────────
works = json.load(open(os.path.join(ROOT, 'works.json'), encoding='utf-8'))

def stem(p):
    return re.sub(r'[^a-z0-9]', '', os.path.basename(p).rsplit('.', 1)[0].lower())

ARCH = {}
for dirpath, _, files in os.walk(REPO):
    if os.sep + 'book' in dirpath or os.sep + 'editor' in dirpath or '.git' in dirpath:
        continue
    for f in files:
        if f.rsplit('.', 1)[-1].lower() not in ('jpg', 'jpeg', 'png'): continue
        fp = os.path.join(dirpath, f)
        try: wpx = Image.open(fp).size[0]
        except Exception: continue
        st = stem(f)
        if st not in ARCH or wpx > ARCH[st][1]:
            ARCH[st] = (os.path.relpath(fp, REPO).replace(os.sep, '/'), wpx)

THUMBS = os.path.join(OUT, 'thumb')
if not os.path.isdir(THUMBS): os.makedirs(THUMBS)

LABEL = {'Detail': 'Detail', 'In progress': 'Stage', 'Study': 'Study',
         'Version': 'Version', 'Film': 'Film'}
groups, made = [], 0
for w in works:
    items = []
    for i, im in enumerate(w['images']):
        src = im['src']
        if src.startswith('http'): continue
        base = os.path.basename(src)
        full = ARCH.get(stem(src))
        site = os.path.join(ROOT, src.lstrip('/'))
        best = full[0] if full else None
        px = full[1] if full else 0
        if not best and os.path.isfile(site):
            px = Image.open(site).size[0]
        # kucuk on izleme: her kaynaktan bir kez uretilir
        th = 'thumb/' + stem(src) + '.jpg'
        tp = os.path.join(OUT, th)
        if not os.path.isfile(tp):
            srcp = os.path.join(REPO, best) if best else site
            if os.path.isfile(srcp):
                try:
                    thumb = Image.open(srcp)
                    if thumb.mode not in ('RGB', 'L'): thumb = thumb.convert('RGB')
                    thumb.thumbnail((300, 300), Image.LANCZOS)
                    thumb.convert('RGB').save(tp, 'JPEG', quality=72, optimize=True)
                    made += 1
                except Exception:
                    th = None
        if not os.path.isfile(tp): th = None
        # Arsivde tam boy dosya yoksa, editor icin 1800 pikselde bir
        # kopya uretilir; surukleyince gelen sey her zaman en iyisidir.
        if not best and os.path.isfile(site):
            FULL = os.path.join(OUT, 'full')
            if not os.path.isdir(FULL): os.makedirs(FULL)
            fn = 'full/' + stem(src) + '.jpg'
            fp = os.path.join(OUT, fn)
            if not os.path.isfile(fp):
                try:
                    big = Image.open(site)
                    if big.mode not in ('RGB', 'L'): big = big.convert('RGB')
                    if big.size[0] > 1800:
                        big.thumbnail((1800, 1800), Image.LANCZOS)
                    big.convert('RGB').save(fp, 'JPEG', quality=82, optimize=True)
                except Exception:
                    fn = None
            if fn and os.path.isfile(fp):
                best = 'editor/' + fn
                px = Image.open(fp).size[0]
        elif best:
            best = best
        items.append({'name': LABEL.get(im.get('label'), 'Plate' if i == 0 else 'Image'),
                      'file': base, 'thumb': ('editor/' + th) if th else None,
                      'full': best, 'px': px,
                      'site': src})
    groups.append({'n': w['n'], 'title': w['title'], 'year': w['year'], 'items': items})

json.dump({'groups': groups}, open(os.path.join(OUT, 'archive.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, separators=(',', ':'))

# Duzenleyici cift tiklayinca da acilsin diye veri bir betik olarak yazilir:
# file:// altinda fetch engellenir, <script src> engellenmez.
with open(os.path.join(OUT, 'data.js'), 'w', encoding='utf-8') as f:
    f.write('window.BOOKLET={model:')
    json.dump(model, f, ensure_ascii=False, separators=(',', ':'))
    f.write(',archive:')
    json.dump({'groups': groups}, f, ensure_ascii=False, separators=(',', ':'))
    f.write('};\n')
print('pages: %d  elements: %d' % (len(pages), sum(len(p['els']) for p in pages)))
print('editor images copied: %d   thumbnails made: %d' % (n, made))
print('archive groups: %d  items: %d' % (len(groups), sum(len(g['items']) for g in groups)))
