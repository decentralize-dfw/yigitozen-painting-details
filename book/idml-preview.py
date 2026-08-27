# -*- coding: utf-8 -*-
"""
IDML'i geri okuyup resme cevirir.

Denetim XML'in tutarli oldugunu soyler, sayfanin dogru gorundugunu soylemez.
Bu betik paketi InDesign'in okudugu gibi okur — yapragin kendi koordinat
sistemi, sayfa sinirlari, her nesnenin yolu, her gorselin kendi donusumu —
ve ciziyor. Cikan resim kitabin o sayfasina benziyorsa koordinat sistemi
dogrudur; benzemiyorsa hata cizimde gorunur.

    python3 idml-preview.py 21          # 21. sayfanin yapragi
    python3 idml-preview.py 21 --out x.png
"""
import os, sys, zipfile, io
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir, 'Yigit-Ozen-Paintings-InDesign'))
WANT = int(next((a for a in sys.argv[1:] if a.isdigit()), '21'))
OUT = None
for i, a in enumerate(sys.argv):
    if a == '--out' and i + 1 < len(sys.argv): OUT = sys.argv[i + 1]
OUT = OUT or os.path.join(HERE, '_idml-preview.png')

IDML = next(os.path.join(ROOT, f) for f in os.listdir(ROOT) if f.endswith('.idml'))
z = zipfile.ZipFile(IDML)
PT = 72 / 25.4
S = 2.4                                   # onizleme olcegi

def bounds(el):
    pts = [p.get('Anchor').split() for p in el.iter('PathPointType')]
    xs = [float(p[0]) for p in pts]; ys = [float(p[1]) for p in pts]
    return min(xs), min(ys), max(xs), max(ys)

target = None
for n in z.namelist():
    if not n.startswith('Spreads/'): continue
    t = ET.fromstring(z.read(n))
    sp = t.find('.//Spread')
    nums = [p.get('Name') for p in sp.findall('Page')]
    if str(WANT) in nums:
        target = (n, t, sp, nums); break
if not target: sys.exit('%d numarali sayfa bulunamadi' % WANT)
name, tree, spread, nums = target

pages = spread.findall('Page')
gx1 = min(float(p.get('GeometricBounds').split()[1]) for p in pages)
gx2 = max(float(p.get('GeometricBounds').split()[3]) for p in pages)
gy2 = max(float(p.get('GeometricBounds').split()[2]) for p in pages)
W, H = int((gx2 - gx1) * S), int(gy2 * S)
im = Image.new('RGB', (W, H), 'white')
dr = ImageDraw.Draw(im, 'RGBA')
tx = lambda X: int((X - gx1) * S)
ty = lambda Y: int(Y * S)

drawn = {'img': 0, 'txt': 0, 'rect': 0}
for el in list(spread):
    if el.tag == 'Rectangle':
        x1, y1, x2, y2 = bounds(el)
        img = el.find('Image')
        if img is not None:
            uri = img.find('Link').get('LinkResourceURI')[5:]
            p = os.path.join(ROOT, uri)
            it = [float(v) for v in img.get('ItemTransform').split()]
            gb = img.find('.//GraphicBounds')
            nw = float(gb.get('Right')); nh = float(gb.get('Bottom'))
            if os.path.isfile(p) and not p.lower().endswith('.svg'):
                src = Image.open(p).convert('RGB')
                # Gorselin kendi donusumu: olcek ve kaydirma
                dw, dh = max(1, int(nw * it[0] * S)), max(1, int(nh * it[3] * S))
                src = src.resize((dw, dh), Image.LANCZOS)
                # Cerceveye kirp
                box = Image.new('RGB', (max(1, tx(x2) - tx(x1)),
                                        max(1, ty(y2) - ty(y1))), 'white')
                box.paste(src, (int((it[4] - x1) * S), int((it[5] - y1) * S)))
                im.paste(box, (tx(x1), ty(y1)))
                drawn['img'] += 1
            else:
                dr.rectangle([tx(x1), ty(y1), tx(x2), ty(y2)],
                             outline=(0, 128, 255), width=2)
        else:
            f = el.get('FillColor') or ''
            col = {'Color/ink': (17, 17, 17), 'Color/hair': (216, 216, 216),
                   'Color/dark': (12, 12, 12)}.get(f)
            if f.startswith('Gradient'):
                for k in range(ty(y1), ty(y2)):
                    a = int(112 * (1 - (k - ty(y1)) / max(1.0, ty(y2) - ty(y1))))
                    dr.line([(tx(x1), k), (tx(x2), k)], fill=(0, 0, 0, a))
            elif col:
                dr.rectangle([tx(x1), ty(y1), max(tx(x1) + 1, tx(x2)),
                              max(ty(y1) + 1, ty(y2))], fill=col)
            else:
                dr.rectangle([tx(x1), ty(y1), tx(x2), ty(y2)],
                             outline=(200, 60, 60), width=1)
            drawn['rect'] += 1
    elif el.tag == 'TextFrame':
        x1, y1, x2, y2 = bounds(el)
        sid = el.get('ParentStory')
        txt = ''
        sp2 = 'Stories/Story_%s.xml' % sid
        if sp2 in z.namelist():
            st = ET.fromstring(z.read(sp2))
            txt = ' '.join((c.text or '') for c in st.iter('Content'))
        dr.rectangle([tx(x1), ty(y1), tx(x2), ty(y2)],
                     outline=(0, 170, 90, 200), width=1)
        if txt.strip():
            dr.text((tx(x1) + 2, ty(y1) + 1), txt.strip()[:70],
                    fill=(0, 110, 60))
        drawn['txt'] += 1

# Sayfa sinirlari
for p in pages:
    g = [float(v) for v in p.get('GeometricBounds').split()]
    dr.rectangle([tx(g[1]), ty(g[0]), tx(g[3]) - 1, ty(g[2]) - 1],
                 outline=(255, 0, 200), width=2)
im.save(OUT)
print('%s  sayfa %s  %dx%d px' % (os.path.basename(OUT), '+'.join(nums), W, H))
print('  cizilen: gorsel %d · yazi cercevesi %d · dikdortgen %d'
      % (drawn['img'], drawn['txt'], drawn['rect']))
