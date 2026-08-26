#!/usr/bin/env python3
"""
ARTBOOKLET — Yigit Ozen

booklet.html'i works.json'dan uretir, gorselleri images/ altina hazirlar.

    python3 build.py ../../yigit/works.json
    node print-pdf.js

DUZEN
Sayfa bir izgaradir: 240 x 320 mm, kenarlar 16 mm, on iki sutun, dort mm
bosluk. Her sey milimetreyle o izgaraya konur.

Iki kural her sayfada gecerlidir:

  1. Hicbir gorsel kirpilmaz. Genisligi verilir, yuksekligi kendi oraniyla
     hesaplanir. Yatay bir detayi dikey bir sayfaya sigdirmak icin kesmek,
     detayin gosterilme sebebini yok eder.
  2. Sayfaya perde, gradyan, gölge konmaz. Beyaz kagit, siyah murekkep,
     ince cizgi. Renk yalnizca resimden gelir.

Bunlarin disinda her sayfa kendi malzemesine gore kurulur: bir tablonun
dik mi yatay mi oldugu, kac detayi oldugu, sureci var mi. Ayni iki sayfa
yoktur, ama hepsi ayni izgaradan cikar.
"""
import json, os, sys, html, math
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
IMG  = os.path.join(HERE, 'images')
SRC  = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', '..', 'yigit', 'works.json')
ROOT = os.path.dirname(os.path.abspath(SRC))

e = lambda t: html.escape(str(t), quote=True)

# ── izgara ───────────────────────────────────────────────────────────
PW, PH   = 240.0, 320.0
ML, MR   = 16.0, 16.0
MT, MB   = 15.0, 18.0
COLS, GAP = 12, 4.0
CW = (PW - ML - MR - (COLS - 1) * GAP) / COLS          # bir sutun
CONTENT_W = PW - ML - MR
CONTENT_H = PH - MT - MB

def X(i):  return ML + i * (CW + GAP)                  # i. sutunun sol kenari
def W(n):  return n * CW + (n - 1) * GAP               # n sutunluk genislik
def R(i):  return ML + CONTENT_W - W(i)                # sagdan i sutun

# ── gorsel hazirligi ─────────────────────────────────────────────────
made = {}
def prep(src, placed_mm, tag, box=None):
    """Bir dosyayi sayfada duracagi olcuye gore hazirlar. Genislik
       milimetre olarak verilir; dosya o genisligin 13 katinda kesilir,
       yani kabaca 330 nokta/inc, en fazla 1500 piksel. Kucuk duracak bir
       gorsel icin buyuk dosya tasimanin anlami yok.

       Tablolarin cogunda saklanan fotograf duvari da tasiyor; kayittaki
       `box` tuvalin fotograf icindeki yeridir, once oradan kesilir."""
    px = int(min(1200, max(340, placed_mm * 10)))
    key = (src, px, tuple(box) if box else None)
    if key in made: return made[key]
    im = Image.open(os.path.join(ROOT, src.lstrip('/'))).convert('RGB')
    if box:
        w, h = im.size
        x, y, bw, bh = box
        im = im.crop((round(x*w), round(y*h), round((x+bw)*w), round((y+bh)*h)))
    w, h = im.size
    s = min(1.0, px / float(max(w, h)))
    if s < 1.0: im = im.resize((max(1, round(w*s)), max(1, round(h*s))), Image.LANCZOS)
    out = '%s-%d.jpg' % (tag, px)
    im.save(os.path.join(IMG, out), quality=77, subsampling=2, optimize=True)
    made[key] = ('images/' + out, im.size[0] / float(im.size[1]))
    return made[key]

def ratio(src, box=None):
    im = Image.open(os.path.join(ROOT, src.lstrip('/')))
    w, h = im.size
    if box: return (box[2] * w) / (box[3] * h)
    return w / float(h)

# ── sayfa ────────────────────────────────────────────────────────────
class Page:
    def __init__(self, run='', klass=''):
        self.run, self.klass, self.bits = run, klass, []
    def raw(self, s): self.bits.append(s); return self
    def box(self, x, y, w, inner, klass=''):
        self.bits.append('<div class="b %s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm">%s</div>'
                         % (klass, x, y, w, inner))
        return self
    def rule(self, x, y, w, thick=False):
        self.bits.append('<div class="r%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm"></div>'
                         % (' t' if thick else '', x, y, w))
        return self
    def pic(self, src, x, y, w, cap=None, box=None, tag=None, above=False):
        """Genisligi verilen, yuksekligi kendi oranindan cikan bir gorsel.
           Alt yazi altina, ya da istenirse ustune konur."""
        path, ar = prep(src, w, tag or os.path.splitext(os.path.basename(src))[0], box)
        h = w / ar
        if cap and above:
            self.box(x, y, w, e(cap), 'cap')
            y += 3.4
        self.bits.append('<img src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm">'
                         % (path, x, y, w, h))
        if cap and not above:
            self.box(x, y + h + 1.8, w, e(cap), 'cap')
        return y + h + (5.4 if cap and not above else 0)

PAGES = []
def page(run='', klass=''):
    p = Page(run, klass); PAGES.append(p); return p

# ── veri ─────────────────────────────────────────────────────────────
WORKS = json.load(open(SRC, encoding='utf-8'))
WHERE = json.load(open(os.path.join(HERE, 'where.json'), encoding='utf-8'))
for w in WORKS:
    ims = w['images']
    w['plate']   = ims[0]
    w['details'] = [i for i in ims[1:] if i.get('label') == 'Detail']
    w['aside']   = [i for i in ims[1:] if i.get('label') in ('Study', 'Version')]
    w['process'] = [i for i in ims[1:] if i.get('label') == 'In progress']
    w['ar']      = ims[0].get('ar') or ratio(ims[0]['src'], ims[0].get('box'))

BY_N = {w['n']: w for w in WORKS}
first_page = {}
def where(d):
    return WHERE.get(d['src'].split('/')[-1], d.get('label', 'Detail'))

# ── metin ────────────────────────────────────────────────────────────
P1 = ('The figures in these paintings are assembled rather than drawn whole. A body '
      'accumulates out of clusters of rounded cells and bubbles that lean against one '
      'another, and it may close or stay open: which way it goes belongs to where that '
      'figure stands in the scene and to what it is thinking there. Bodies and faces are '
      'the medium the work is made in, and the question they carry is an existential one. '
      'What lies behind them is not a backdrop but a place, and those places work as '
      'dimensions.')
P2 = ('The decisions are taken in wet paint, on the spot. Layer goes over layer like a '
      'palimpsest, and they are not layers of light and shadow: they are colour clusters '
      'of movement, energy, aura and feeling. Large areas of ground are left bare, and '
      'they carry as much weight as the painted part.')
P3 = ('Familiar compositional formats are kept while the agreement that made them legible '
      'is withdrawn: an object is held out, a sign is displayed, and what either stands '
      'for is never supplied. Titles act as a second body in the scene, bending the image '
      'instead of describing it. Power appears as a distribution of weight, one figure '
      'left underneath the stack. At the edges a small onlooker sits with its eyes closed '
      'and its mouth sewn shut, so the witness is cancelled before anything can be '
      'reported. Scale works as a verdict, one face given as a person and the rest reduced '
      'to signs, sometimes a face replaced by a number.')
BLURB = ('Thirty-five paintings made since 2019 across Istanbul, Milan and Luxembourg. '
         'Acrylic on canvas, carton and paper, with one charcoal drawing. The decisions '
         'are taken in wet paint, on the spot, and layer goes over layer like a '
         'palimpsest: colour clusters of movement, energy, aura and feeling rather than '
         'of light and shadow.')
BIO = ['Yiğit Özen was born in 1994 in Istanbul and trained as an architect.',
       'The paintings date from 2018 onward and were made across Istanbul, Milan and '
       'Luxembourg.',
       'Alongside the paintings, Özen works as an XR and spatial web designer, and is the '
       'founder of decentralize design in Milan and Virtually Ever After in Luxembourg. '
       'That practice has been shown at Kunsthalle Zürich, the Royal Institution in '
       'London, Holy Art Gallery London and Art Basel Miami.']
CV = [('Awards and mentions', [
        ('Creatorverse Buildathon by Parcel x PangeaDAO, Music Venue, Winner', '2022'),
        ('Creatorverse Buildathon by Parcel x PangeaDAO, Meeting Space, Runner-up', '2022'),
        ('Grant Program by EnterDAO’s Landworks, Fashion Venue, Winner', '2022'),
        ('Grant Program by EnterDAO’s Landworks, Headquarters, Winner', '2022'),
        ('Top 50 Creators of Metaverse by Metamundo', '2023'),
        ('CryptoCubes by Han, Runner-up', '2023'),
        ('VCA x Draup Virtual Fashion Residency, 1st Prize, selected by RedDAO', '2023'),
        ('MONA 3D Objects Buildathon, Center Pieces, Honorable Mention', '2024')]),
      ('Talks', [
        ('Virtual Show &amp; Tell at Hyperfy, hosted by untitled, xyz', '2023'),
        ('VCA Mentorship, 6th Cohort, Architecture in the Metaverse', '2023'),
        ('Opening Keynote, Digital Fashion Summit, Creative Denmark', '2024')]),
      ('Exhibitions', [
        ('Power of the Nature, Fabbrica del Vapore, Milan', '2019'),
        ('The Arts Special Projects, Fabbrica del Vapore, Milan', '2019'),
        ('Communitas III by Kollektiv Kollektiv, Kunsthaus Steffisburg', '2021'),
        ('New Freedom Think, Mads Gallery, Milan', '2022'),
        ('Art Design, Holy Art Gallery, London', '2022'),
        ('Klein Metaverse Event, BabylonsNFT, Yachtingverse', '2022'),
        ('DYOR, Kunsthalle Zürich, Zurich', '2022'),
        ('Creators of the Metaverse by Metamundo, Art Basel Miami', '2022'),
        ('First Look Metaverse Watch Party, MONA', '2023'),
        ('KODA by Polkadot, Factory Berlin, Berlin', '2023'),
        ('New Codes by VCA, Draup and Mad Global, Royal Institution, London', '2023')])]

# ══ on sayfalar ══════════════════════════════════════════════════════
# Kapak. Kirpma burada da yok: resim sayfanin genisligince, kendi
# yuksekligiyle duruyor, alti siyah kagit ve ad.
cover, car = prep('/img/full/detail/7famboardgame_detail_3.jpg', 240, 'cover')
p = page('', 'cover dark')
p.raw('<img src="%s" style="left:0;top:36mm;width:240mm;height:%.2fmm">' % (cover, 240 / car))
p.box(ML, 13, CONTENT_W, 'Artbooklet<span class="rt">Thirty-five works</span>', 'lab')
p.box(ML, 232, CONTENT_W, 'YIĞIT<br>ÖZEN', 'cvr-ti')
p.rule(ML, 288, CONTENT_W)
p.box(ML, 291, CONTENT_W,
      'Paintings since 2019<span class="rt">Istanbul &middot; Milan &middot; Luxembourg &middot; yigitozen.xyz</span>',
      'lab')

p = page('Imprint')
p.rule(ML, 15, CONTENT_W, True)
p.box(ML, 18, W(6), 'Artbooklet', 'lab')
p.box(ML, 232, W(5), 'Paintings<br>since 2019', 'ti big-ti')
p.box(ML, 258, W(5), 'Yiğit Özen', 'lab')
p.box(X(6), 232, W(6), e(BLURB), 'note')
p.box(ML, 292, CONTENT_W, '35 works<span class="rt">yigitozen.xyz</span>', 'cap')

p = page('On the work')
p.box(ML, 150, CONTENT_W, 'The decisions<br>are taken in wet paint,<br><em>on the spot.</em>', 'shout')
p.rule(ML, 292, CONTENT_W)
p.box(ML, 294, CONTENT_W, 'On the work', 'cap')

p = page('On the work')
p.rule(ML, 15, CONTENT_W, True)
p.box(ML, 18, W(4), 'On the work', 'lab')
p.box(X(4), 18, W(8), 'A body accumulates out of clusters of rounded cells and bubbles '
                      'that lean against one another, and it may close or stay open.', 'lead')
p.box(ML, 200, W(4), e(P1), 'note')
p.box(X(4), 200, W(4), e(P2), 'note')
p.box(X(8), 200, W(4), e(P3), 'note')

por, _ = prep('/img/portrait.jpg', 84, 'portrait')
p = page('Biography')
p.rule(ML, 15, CONTENT_W, True)
p.box(ML, 18, W(4), 'Biography', 'lab')
p.raw('<img src="%s" style="left:%.2fmm;top:36mm;width:%.2fmm">' % (por, X(6), W(6)))
p.box(ML, 232, W(5), 'Yiğit<br>Özen', 'ti big-ti')
p.box(X(6), 232, W(6), ''.join('<p>%s</p>' % e(x) for x in BIO), 'note')

p = page('Biography')
y = 15.0
for h4, rows in CV:
    p.rule(ML, y, CONTENT_W, True)
    p.box(ML, y + 2.4, W(3), h4, 'lab')
    yy = y + 2.4
    for a, b in rows:
        p.box(X(3), yy, W(8), a, 'cv')
        p.box(R(1), yy, W(1), b, 'cv rt')
        yy += 5.6
    y = yy + 7

toc_pages = [page('Contents'), page('Contents')]

# ══ eserler ══════════════════════════════════════════════════════════
def label_row(p, w, y):
    """Sayfanin tepesindeki ince serit: teknik, olcu, yer, yil."""
    p.rule(ML, y, CONTENT_W, True)
    p.box(ML,    y + 2.4, W(4), e(w['medium']), 'lab')
    p.box(X(4),  y + 2.4, W(3), e(w['dim']), 'lab')
    p.box(X(7),  y + 2.4, W(3), e(w.get('place', '')), 'lab dim')
    p.box(R(1),  y + 2.4, W(1), e(w['year']), 'lab rt')

def facet_row(p, w, y):
    p.rule(ML, y, CONTENT_W)
    for i, (h, t) in enumerate(zip(('Colour', 'Composition', 'Hand'), w['facets'])):
        p.box(X(i * 4), y + 2.2, W(4) - 4, '<b>%s</b>%s' % (h, e(t)), 'cap')

def work_open(w):
    """Eserin acilis sayfasi. Tablo kendi oraniyla, sayfanin bir yaninda;
       yazi obur yanda. Dik tablo bir yer ister, yatay tablo baska: duzen
       resmin sekline gore kurulur, resim duzene gore kesilmez."""
    p = page(w['run'])
    label_row(p, w, 15)
    tag = 'w%02d' % w['n']
    left = (w['n'] % 2 == 1)
    if w['ar'] < 0.95:                                  # dik tablo
        cw = W(7)
        px = ML if left else R(7)
        tx = R(4) if left else ML
        py = 34
        p.pic(w['plate']['src'], px, py, cw, box=w['plate'].get('box'), tag=tag)
        p.box(tx, 34, W(4), '%02d' % w['n'], 'num')
        p.box(tx, 52, W(4), '<em>%s</em>' % e(w['title']), 'ti')
        p.box(tx, 52 + 4.6 * math.ceil(len(w['title']) / 22.0) + 6, W(4), e(w['note']), 'note')
    elif w['ar'] > 1.15:                                # yatay tablo
        cw = W(10)
        px = ML if left else R(10)
        p.box(R(1) if left else ML, 34, W(1), '%02d' % w['n'], 'num')
        p.pic(w['plate']['src'], px, 34, cw, box=w['plate'].get('box'), tag=tag)
        ty = 34 + cw / w['ar'] + 12
        p.box(ML, ty, W(5), '<em>%s</em>' % e(w['title']), 'ti')
        p.box(X(6), ty, W(6), e(w['note']), 'note')
    else:                                               # kare tablo
        cw = W(8)
        px = X(2) if left else X(2)
        p.pic(w['plate']['src'], px, 40, cw, box=w['plate'].get('box'), tag=tag)
        p.box(ML, 15 + 12, W(2), '%02d' % w['n'], 'num')
        ty = 40 + cw / w['ar'] + 12
        p.box(ML, ty, W(5), '<em>%s</em>' % e(w['title']), 'ti')
        p.box(X(6), ty, W(6), e(w['note']), 'note')
    facet_row(p, w, 272)
    first_page[w['n']] = len(PAGES)
    return p

FOOT = 272.0            # sayfanin dip cizgisi: her sayfada ayni yerde

# Bir satirda kac gorsel ve her birinin kac sutun genisliginde olacagi.
# Iki gorsel ya yan yana altisar sutun, ya alt alta sekizer: hangisi sayfayi
# daha iyi doldurursa. Secim malzemeye gore yapilir, kaliba gore degil.
SHAPES = [(1, 12), (1, 9), (1, 7), (2, 6), (2, 5), (3, 4), (3, 3), (4, 3)]

def rows_h(items, cols, span, capsp):
    cw = W(span)
    return [max(cw / ratio(src, box) for src, _, box in items[i:i + cols]) + capsp
            for i in range(0, len(items), cols)]

def grid_page(run, items, head=None, tag='d', cap=True, y0=30.0):
    """Bir sayfaya n gorsel. Satir duzeni sayfayi en iyi dolduracak sekilde
       secilir, artan bosluk satir aralarina dagitilir, her gorsel kendi
       orani ile durur. Kirpma yok."""
    avail = FOOT - y0
    capsp = 5.4 if cap else 0
    best = None
    for cols, span in SHAPES:
        if cols > len(items) or cols * span > COLS: continue
        hs = rows_h(items, cols, span, capsp)
        h = sum(hs)
        if h > avail: continue
        score = abs(h / avail - .84)
        if best is None or score < best[0]: best = (score, cols, span, hs)
    if best is None:
        cols, span = 4, 3
        hs = rows_h(items, cols, span, capsp)
    else:
        _, cols, span, hs = best

    rows = len(hs)
    slack = max(0.0, avail - sum(hs))
    gapv = min(26.0, slack / max(1, rows - 1)) if rows > 1 else 0.0
    y = y0 + (slack * .5 if rows == 1 else (slack - gapv * (rows - 1)) * .2)

    p = page(run)
    if head:
        p.rule(ML, 15, CONTENT_W, True)
        p.box(ML, 17.4, W(7), head[0], 'lab')
        if len(head) > 1: p.box(R(3), 17.4, W(3), head[1], 'lab rt')
    cw = W(span)
    step = 0 if cols == 1 else (CONTENT_W - cw) / (cols - 1)
    for k, i in enumerate(range(0, len(items), cols)):
        for j, (src, cap_t, box) in enumerate(items[i:i + cols]):
            p.pic(src, ML + j * step, y, cw, cap=(cap_t if cap else None), box=box,
                  tag='%s%03d' % (tag, i + j))
        y += hs[k] + gapv
    return p

def detail_pages(w):
    """Detaylar. Ilki tek basina ve buyuk, alt kenari sayfanin dip cizgisine
       oturur; kitabin her yerinde ayni ufuk. Kalanlar izgarada, hepsi butun
       halde: yatay bir detay yatay durur."""
    ds = list(w['details'])
    if not ds: return
    d0 = ds.pop(0)
    p = page(w['run'])
    p.rule(ML, 15, CONTENT_W, True)
    p.box(ML, 17.4, W(7), '%02d &nbsp; %s' % (w['n'], e(w['title'])), 'lab')
    p.box(R(3), 17.4, W(3), 'Detail', 'lab rt')
    a0 = ratio(d0['src'])
    cw = W(11) if a0 > 1.15 else (W(6) if a0 < .85 else W(8))
    x  = ML if a0 > 1.15 else (X(3) if w['n'] % 2 else X(2))
    y  = FOOT - 5.4 - cw / a0
    if y < 30: y = 30
    p.pic(d0['src'], x, y, cw, cap=where(d0), tag='w%02dd00' % w['n'])
    n = 0
    while ds:
        take = 6 if len(ds) >= 5 else len(ds)
        chunk, ds = ds[:take], ds[take:]
        grid_page(w['run'], [(d['src'], where(d), None) for d in chunk],
                  head=('%02d &nbsp; %s' % (w['n'], e(w['title'])), 'Details'),
                  tag='w%02dg%d' % (w['n'], n))
        n += 1

def process_page(w):
    """Surec. Hepsi tek sayfada, kucuk, altlarinda yazi yok: bunlar bir
       eserin nasil kurulduguna dair sira, tek tek gosterilecek levha degil."""
    ps = w['process']
    if not ps: return
    cols = 4 if len(ps) > 6 else 3
    span = COLS // cols
    cw = W(span)
    p = page(w['run'])
    p.rule(ML, 15, CONTENT_W, True)
    p.box(ML, 17.4, W(6), '%02d &nbsp; %s' % (w['n'], e(w['title'])), 'lab')
    p.box(R(3), 17.4, W(3), 'Process', 'lab rt')
    rows = math.ceil(len(ps) / float(cols))
    hs = [max(cw / ratio(d['src']) for d in ps[i:i + cols])
          for i in range(0, len(ps), cols)]
    slack = max(0.0, (FOOT - 30.0) - sum(hs))
    gapv = min(14.0, slack / max(1, rows - 1)) if rows > 1 else 0.0
    y = 30.0
    for k, i in enumerate(range(0, len(ps), cols)):
        for j, d in enumerate(ps[i:i + cols]):
            p.pic(d['src'], X(j * span), y, cw, tag='w%02dp%02d' % (w['n'], i + j))
        y += hs[k] + gapv
    p.box(ML, 292, CONTENT_W, '%d stages' % len(ps), 'cap')

def aside_page(w):
    """Kokte duran calismalar: bir eserin etudu ya da baska bir hali."""
    if not w['aside']: return
    grid_page(w['run'], [(a['src'], a.get('label'), None) for a in w['aside']],
              head=('%02d &nbsp; %s' % (w['n'], e(w['title'])),
                    'Study' if len(w['aside']) == 1 and w['aside'][0].get('label') == 'Study'
                    else 'Studies and versions'),
              tag='w%02da' % w['n'], y0=40)

YEARS = []
for w in WORKS:
    if w['year'] not in YEARS: YEARS.append(w['year'])

for yr in YEARS:
    group = [w for w in WORKS if w['year'] == yr]
    places = {}
    for w in group: places[w.get('place', '')] = places.get(w.get('place', ''), 0) + 1
    place = max(places, key=places.get)
    run = '%s &middot; %s' % (yr, place)
    for w in group: w['run'] = run

    p = page(run, 'dark')
    p.box(ML, 196, CONTENT_W, e(yr), 'yr')
    p.box(ML, 262, W(5), e(place), 'ti')
    p.rule(ML, 276, CONTENT_W)
    p.box(ML, 279, W(8), ' &nbsp;&middot;&nbsp; '.join('%02d' % x['n'] for x in group), 'cap')
    p.box(R(2), 279, W(2), '%d works' % len(group), 'cap rt')

    for w in group:
        work_open(w)
        aside_page(w)
        detail_pages(w)
        process_page(w)

# ══ arka ═════════════════════════════════════════════════════════════
p = page('Colophon')
p.rule(ML, 15, CONTENT_W, True)
p.box(ML, 17.4, W(4), 'Colophon', 'lab')
p.box(ML, 232, W(5),
      'All works by Yiğit Özen, born 1994 in Istanbul and trained as an architect.', 'note')
p.box(X(6), 232, W(6),
      'Dimensions are given as width by height. Plates reproduce documentation of the '
      'paintings; colour and surface differ from the works themselves. A technical '
      'catalogue of the same works, with the full index, is published separately.'
      '<p>All works &copy; Yiğit Özen. All rights reserved.</p>', 'note')
p.box(ML, 292, CONTENT_W,
      'yigitozen.xyz &middot; de-centralize.com<span class="rt">'
      'Instagram @yjgjf &middot; x@yigitozen.xyz</span>', 'cap')

logo = page('', 'last')
logo.raw('<img class="mk" src="images/logo.svg">')

# ══ icindekiler ══════════════════════════════════════════════════════
def toc(p, items, head=None):
    y = 15.0
    p.rule(ML, y, CONTENT_W, True)
    p.box(ML, y + 2.4, W(4), head or 'Contents (continued)', 'lab')
    y += 14
    for w in items:
        p.box(ML,   y, W(1), '%02d' % w['n'], 'toc n')
        p.box(X(1), y, W(7), e(w['title']), 'toc t')
        p.box(X(9), y, W(2), e(w['year']), 'toc y')
        p.box(R(1), y, W(1), str(first_page[w['n']]), 'toc p rt')
        p.rule(ML, y + 6.4, CONTENT_W)
        y += 8.6

toc(toc_pages[0], WORKS[:18], 'Contents')
toc(toc_pages[1], WORKS[18:])

# ══ yaz ══════════════════════════════════════════════════════════════
out = ['<!doctype html>', '<html lang="en">', '<head>', '<meta charset="utf-8">',
       '<title>Yiğit Özen &mdash; Artbooklet</title>',
       '<link rel="stylesheet" href="booklet.css">', '</head>', '<body>', '']
for i, p in enumerate(PAGES, start=1):
    side = 'L' if i % 2 == 0 else 'R'
    folio = ('' if p.klass in ('cover dark', 'last') else
             '<div class="folio"><span class="n">%d</span><span class="run">%s</span></div>'
             % (i, p.run))
    out.append('<section class="pg %s%s">%s%s</section>'
               % (side, (' ' + p.klass if p.klass else ''), ''.join(p.bits), folio))
    out.append('')
out += ['</body>', '</html>', '']
open(os.path.join(HERE, 'booklet.html'), 'w', encoding='utf-8').write('\n'.join(out))
print('pages: %d' % len(PAGES))
print('images: %d' % len(made))
