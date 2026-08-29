# -*- coding: utf-8 -*-
"""Oturmus sayfayi ciziyor.

InDesign burada yok. Ama elimde ciktinin kendisi, oturmus yerler ve
kitabin yazi tipleri var: sayfanin gorselleri ciktidan oldugu gibi
alinir, yazilar silinir, sonra her satir yeni yerine kendi yazi tipiyle
yeniden dizilir. Yeni kunyeler de belgeden okunup cizilir.

Cikan resim InDesign'in cizecegi sayfa degildir — satir sonlari yeniden
hesaplanmaz — ama her satirin nereye dustugu gercektir, ve gorulmesi
gereken de odur.

    python3 proof.py duzen.idml kunyeli.idml cikti.pdf sayfa [sayfa ...]
"""
import os, sys, re, zipfile
import xml.etree.ElementTree as ET
import pymupdf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stackmodel import read
from fix_stack_lib import settle, lineboxes, grow_changed
from place import transform, caption_height

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = {
    'Inter-Regular':  'Inter-400.ttf',   'Inter-Medium':   'Inter-500.ttf',
    'Inter-SemiBold': 'Inter-600.ttf',   'Inter-Bold':     'Inter-700.ttf',
    'Newsreader-Regular': 'Newsreader-400.ttf',
    'Newsreader-Italic':  'Newsreader-Italic-400.ttf',
    'Helvetica': 'Inter-400.ttf', 'Helvetica-Bold': 'Inter-700.ttf',
    'Helvetica-Light': 'Inter-400.ttf',
}
import json
LAY, CAP, PDF = sys.argv[1], sys.argv[2], sys.argv[3]
WANT = [int(a) for a in sys.argv[4:] if a.isdigit()]
BOOK = None
for i, a in enumerate(sys.argv):
    if a == '--pdf' and i + 1 < len(sys.argv): BOOK = sys.argv[i + 1]
OUT = os.path.dirname(os.path.abspath(CAP))
dj = os.path.join(os.path.dirname(os.path.abspath(LAY)), 'degisen.json')
CH = json.load(open(dj)) if os.path.exists(dj) else {}

pages, lines, miss = read(LAY, PDF, {k: v[0] for k, v in CH.items()})
grow_changed(pages, CH)
OUTDOC = pymupdf.open() if BOOK else None
D = pymupdf.open(PDF)

# ── son belgedeki renkler ───────────────────────────────────────────
# Kanit ciktidan cizilir, ama renk artik ciktinin rengi degil: kagit
# uzerinde okunmayan yazilar bu asamada yeniden renklendirildi. Her
# oykunun gecerli rengi belgeden okunur.
Z = zipfile.ZipFile(CAP)
SW = {}
for el in ET.fromstring(Z.read('Resources/Graphic.xml')).iter('Color'):
    v = (el.get('ColorValue') or '').split()
    sp_ = el.get('Space')
    if sp_ == 'RGB' and len(v) == 3:
        SW[el.get('Self')] = tuple(float(x) / 255 for x in v)
    elif sp_ == 'CMYK' and len(v) == 4:
        c, m, y_, k = [float(x) / 100 for x in v]
        SW[el.get('Self')] = ((1 - c) * (1 - k), (1 - m) * (1 - k), (1 - y_) * (1 - k))
STYCOL = {}
for el in ET.fromstring(Z.read('Resources/Styles.xml')).iter('ParagraphStyle'):
    if el.get('Name'): STYCOL[el.get('Name')] = el.get('FillColor')
COL = {}
for n in Z.namelist():
    m = re.match(r'Stories/Story_(\w+)\.xml$', n)
    if not m: continue
    raw = Z.read(n).decode('utf-8')
    st = ET.fromstring(raw)
    ov = re.search(r'<CharacterStyleRange[^>]*FillColor="([^"]+)"', raw)
    sty = next((q.get('AppliedParagraphStyle', '').split('/')[-1]
                for q in st.iter('ParagraphStyleRange')), '')
    ref = ov.group(1) if ov else STYCOL.get(sty)
    if ref in SW: COL[m.group(1)] = SW[ref]
NEW = re.compile(r'^(cn|cw|cs|cr)')
caps = {}
for n in Z.namelist():
    if not n.startswith('Spreads/'): continue
    sp = ET.fromstring(Z.read(n)).find('.//Spread')
    pg = {}
    for p in sp.findall('Page'):
        g = [float(v) for v in p.get('GeometricBounds').split()]
        it = [float(v) for v in (p.get('ItemTransform') or '1 0 0 1 0 0').split()]
        if p.get('Name', '').isdigit():
            pg[int(p.get('Name'))] = (g[1] + it[4], g[0] + it[5],
                                      g[3] + it[4], g[2] + it[5])
    for f in sp.iter('TextFrame'):
        sid = f.get('ParentStory')
        if not NEW.match(sid or ''): continue
        b = transform(f)
        q = next((k for k, (a1, b1, a2, b2) in pg.items()
                  if a1 - 1 <= (b[0] + b[2]) / 2 <= a2 + 1), None)
        if q is None: continue
        st = ET.fromstring(Z.read('Stories/Story_%s.xml' % sid))
        t = re.sub(r'\s+', ' ', ''.join((c.text or '') for c in st.iter('Content'))).strip()
        white = 'Color/paper' in Z.read('Stories/Story_%s.xml' % sid).decode('utf-8')
        ox, oy = pg[q][0], pg[q][1]
        caps.setdefault(q, []).append(
            (b[0] - ox, b[1] - oy, b[2] - ox, t.upper(), white))

for q in WANT:
    P = pages[q]
    new, moved = settle(P)
    d2 = pymupdf.open(); d2.insert_pdf(D, from_page=q - 1, to_page=q - 1)
    p2 = d2[0]
    rules = []
    for k, i in enumerate(P['items']):
        if i['role'] == 'rule':
            r = i['ren']
            rules.append((r, new[k] - r[1]))
            p2.draw_rect(pymupdf.Rect(r[0], r[1] - .6, r[2], r[3] + .6),
                         color=None, fill=(1, 1, 1))
        for bx in lineboxes(i):
            p2.add_redact_annot(pymupdf.Rect(bx[0] - 1, bx[1] - 2.5,
                                             bx[2] + 1, bx[3] + 2.5))
    p2.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE,
                        graphics=pymupdf.PDF_REDACT_LINE_ART_NONE)
    for r, d in rules:
        p2.draw_rect(pymupdf.Rect(r[0], r[1] + d, r[2], r[3] + d),
                     color=None, fill=(.72, .72, .72))
    for k, i in enumerate(P['items']):
        if i['role'] == 'rule' or not i['lines']: continue
        d = new[k] - i['ren'][1]
        if i.get('story') in CH:
            # Yazisi degisti: ciktidaki eski satirlar degil, belgedeki
            # yeni yazi cizilir, cercevenin kendi genisligine sarilarak.
            s0 = i['lines'][0]['span']
            fp0 = os.path.join(HERE, 'fonts', FONT.get(s0['font'], 'Inter-400.ttf'))
            c0 = s0['color']
            p2.insert_textbox(
                pymupdf.Rect(i['ren'][0], i['ren'][1] + d - 2,
                             max(i['ren'][2], i['ren'][0] + 120),
                             i['ren'][3] + d + 60),
                CH[i['story']][1].upper() if s0['size'] < 9 else CH[i['story']][1],
                fontfile=fp0, fontname='ch%d' % k, fontsize=s0['size'],
                lineheight=1.46,
                color=COL.get(i.get('story'),
                              (((c0 >> 16) & 255) / 255, ((c0 >> 8) & 255) / 255,
                               (c0 & 255) / 255)))
            continue
        for l in i['lines']:
            s = l['span']
            fp = os.path.join(HERE, 'fonts', FONT.get(s['font'], 'Inter-400.ttf'))
            c = s['color']
            p2.insert_text((l['x1'], s['origin'][1] + d), l['t'],
                           fontfile=fp, fontname='f' + str(abs(hash(fp)) % 9999),
                           fontsize=s['size'],
                           color=COL.get(i.get('story'),
                                         (((c >> 16) & 255) / 255,
                                          ((c >> 8) & 255) / 255, (c & 255) / 255)))
    fp = os.path.join(HERE, 'fonts', 'Inter-500.ttf')
    for x1, y1, x2, t, white in caps.get(q, []):
        p2.insert_textbox(pymupdf.Rect(x1, y1, x2, y1 + caption_height(t, x2 - x1) + 40),
                          t, fontfile=fp, fontname='cap', fontsize=7.6,
                          lineheight=1.46,
                          color=(1, 1, 1) if white else (.42, .42, .42))
    if OUTDOC is not None:
        OUTDOC.insert_pdf(d2)
    else:
        pm = p2.get_pixmap(matrix=pymupdf.Matrix(2.0, 2.0))
        pm.save(os.path.join(OUT, 'oturmus-s%03d.png' % q))
    print('s.%-4d inen blok %d · kunye %d' % (q, len(moved), len(caps.get(q, []))))

if OUTDOC is not None:
    OUTDOC.save(BOOK, garbage=3, deflate=True)
    print('kanit: %s · %d sayfa' % (os.path.basename(BOOK), len(OUTDOC)))
