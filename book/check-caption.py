# -*- coding: utf-8 -*-
"""Aciklamasi olmayan gorsel, gorseli olmayan aciklama.

Her gorselin bir kunyesi olmali ve her kunye bir gorseli anlatmali. Kunye
gorselin altinda, ustunde ya da uzerinde durabilir; olcu yakinliktir.

    python3 check-caption.py belge.idml
"""
import os, sys, re, zipfile, urllib.parse
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from place import transform, PT

if len(sys.argv) < 2: sys.exit('kullanim: check-caption.py belge.idml')
Z = zipfile.ZipFile(sys.argv[1])
NEAR = 42.0 * PT          # kunye gorselden en fazla bu kadar uzakta olabilir
LABEL = ('m g', 'm rt g', 'm g rt', 'm', 'm rt', 'm wh', 'm rt wh', 'm ct')


def story(sid):
    p = 'Stories/Story_%s.xml' % sid
    if p not in Z.namelist(): return '', ''
    st = ET.fromstring(Z.read(p))
    t = re.sub(r'\s+', ' ', ''.join((c.text or '') for c in st.iter('Content'))).strip()
    sty = next((q.get('AppliedParagraphStyle', '').split('/')[-1]
                for q in st.iter('ParagraphStyleRange')), '')
    return t, sty


noimg, nocap = [], []
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

    def page_of(b):
        return next((v for v, (a1, a2) in pg.items()
                     if a1 - 1 <= (b[0] + b[2]) / 2 <= a2 + 1), None)

    imgs, caps = [], []
    for r in sp.iter('Rectangle'):
        im = r.find('Image')
        if im is None: continue
        b = transform(r)
        if not b: continue
        f = urllib.parse.unquote(
            im.find('Link').get('LinkResourceURI') or '').split('/')[-1]
        imgs.append((b, r.get('Self'), f, page_of(b)))
    for f in sp.iter('TextFrame'):
        sid = f.get('ParentStory')
        t, sty = story(sid)
        if not t or sty not in LABEL: continue
        if re.match(r'^(cn|cw|cs|cr)', sid or ''): sty = 'yeni'
        b = transform(f)
        caps.append((b, f.get('Self'), t, page_of(b), sty))

    def near(a, b):
        ox = min(a[2], b[2]) - max(a[0], b[0])
        dy = max(a[1] - b[3], b[1] - a[3], 0.0)
        return ox > 0 and dy < NEAR

    # Tam sayfa kaplayan levhanin kunyesi karsi sayfadadir: kitap bunu
    # "Opposite ·" satiriyla ya da karsi sayfadaki baslik blokuyla yapar.
    # Iki sayfa ayni yaprakta oldugu icin burada gorunur.
    opp = [c for c in caps if ' · Opposite · ' in c[2]]
    titled = set()
    for f2 in sp.iter('TextFrame'):
        t2, s2 = story(f2.get('ParentStory'))
        if s2.startswith('d') and t2:
            b2 = transform(f2)
            if b2: titled.add(page_of(b2))
    for b, sid, f, q in imgs:
        if any(near(b, c[0]) for c in caps): continue
        # Eserin levhasi kendi basligiyla adlanir; ayrica kunye istemez.
        # Ama bir sayfada birden cok kesit varsa her biri kendi kunyesini
        # ister — hangisinin ne oldugu baslikten cikmaz.
        alone = sum(1 for i in imgs if i[3] == q) == 1
        full = (b[2] - b[0]) > 150 * PT and (b[3] - b[1]) > 150 * PT
        if full and (opp or (titled - {q})): continue
        if alone and titled: continue
        nocap.append((q, sid, f, round((b[2] - b[0]) / PT), round((b[3] - b[1]) / PT)))
    for b, sid, t, q, sty in caps:
        if not any(near(i[0], b) for i in imgs):
            noimg.append((q, sid, sty, t[:60]))

print('ACIKLAMASI OLMAYAN GORSEL: %d' % len(nocap))
for q, sid, f, w, h in sorted(nocap, key=lambda r: (r[0] is None, r[0])):
    print('  s.%-5s %-9s %-38s %dx%d mm' % (q, sid, f[:38], w, h))
print('GORSELI OLMAYAN KUNYE: %d' % len(noimg))
for q, sid, sty, t in sorted(noimg, key=lambda r: (r[0] is None, r[0])):
    print('  s.%-5s %-9s %-6s %r' % (q, sid, sty, t))
sys.exit(1 if (nocap or noimg) else 0)
