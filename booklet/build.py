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
ARGS  = [a for a in sys.argv[1:] if not a.startswith('--')]
SHORT = '--short' in sys.argv          # gonderim icin on alti sayfalik surum
SELECT = [1, 2, 3, 5, 12, 14, 24, 27]  # kisa surumde gosterilen isler
SRC  = ARGS[0] if ARGS else os.path.join(HERE, '..', '..', 'yigit', 'works.json')
ROOT = os.path.dirname(os.path.abspath(SRC))

e = lambda t: html.escape(str(t), quote=True)

# ── izgara ───────────────────────────────────────────────────────────
PW, PH   = 240.0, 320.0
CAP_Y    = 292.0        # tam sayfa gorsellerin kunye satiri
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

_ph = {}
def phash(src):
    """Kaba bir gorsel parmak izi: 8x8 griye indirir, ortalamanin ustunde
       olan pikselleri bit olarak tutar."""
    if src in _ph: return _ph[src]
    im = Image.open(os.path.join(ROOT, src.lstrip('/'))).convert('L').resize((8, 8))
    px = list(im.getdata()); avg = sum(px) / 64.0
    _ph[src] = [1 if v > avg else 0 for v in px]
    return _ph[src]


def far(a, b):
    return sum(1 for x, y in zip(phash(a), phash(b)) if x != y)


def spread_out(items, thr=8):
    """Sirayi bozmadan, arka arkaya gelen iki gorsel birbirine cok
       benziyorsa sonrakilerden farkli olan biriyle yer degistirir."""
    out = list(items)
    for i in range(1, len(out)):
        if far(out[i-1][0], out[i][0]) >= thr: continue
        for j in range(i + 1, len(out)):
            if far(out[i-1][0], out[j][0]) >= thr:
                out[i], out[j] = out[j], out[i]; break
    return out


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
WHERE   = json.load(open(os.path.join(HERE, 'where.json'), encoding='utf-8'))
MOTIFS  = json.load(open(os.path.join(HERE, 'motifs.json'), encoding='utf-8'))
CREDITS = json.load(open(os.path.join(HERE, 'credits.json'), encoding='utf-8'))

# Kayitta detay diye gecen ama detay olmayanlar: bunlar isin baska bir hali
# ya da baska bir denemesi. Kitapta detay bolumune degil, etudlerin yanina.
NOT_DETAIL = {
    'ciaocapo_detail_6.jpg': 'Another version, on green and blue',
    'ciaocapo_detail_7.jpg': 'The pair in blue and grey',
    'ciaocapo_detail_8.jpg': 'The pair, before the colour',
    'cellularspleens_detail_4.jpg': 'The whole, in another version',
}
# Bunlar kayitta "Detail" diye gecer ama detay degildir; kunyede boyle yazar.
NOT_DETAIL_KIND = dict.fromkeys(NOT_DETAIL, 'Version')
for w in WORKS:
    ims = w['images']
    w['plate']   = ims[0]
    base = lambda i: i['src'].split('/')[-1]
    w['details'] = [i for i in ims[1:]
                    if i.get('label') == 'Detail' and base(i) not in NOT_DETAIL]
    w['aside']   = [i for i in ims[1:] if i.get('label') in ('Study', 'Version')
                    or base(i) in NOT_DETAIL]
    w['process'] = [i for i in ims[1:] if i.get('label') == 'In progress']
    w['ar']      = ims[0].get('ar') or ratio(ims[0]['src'], ims[0].get('box'))

BY_N = {w['n']: w for w in WORKS}
first_page = {}
def where(d):
    b = d['src'].split('/')[-1]
    return NOT_DETAIL.get(b) or WHERE.get(b, d.get('label', 'Detail'))


def kind(d):
    b = d['src'].split('/')[-1]
    return NOT_DETAIL_KIND.get(b) or d.get('label', 'Study')

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
BLURB = ('Thirty-five works made since 2019 across Istanbul, Milan and Luxembourg: '
         'acrylic on canvas, on carton and on paper, and one drawing in charcoal on the '
         'reverse of a canvas. They are given here newest first, and a small figure with '
         'crossed eyes runs through them from one end of the seven years to the other.')
SHORT_BLURB = ('Eight of thirty-five works made since 2019 across Istanbul, Milan and '
               'Luxembourg: acrylic on canvas, on carton and on paper. The whole book, '
               'with every detail and the stages of the newest paintings, is at '
               'yigitozen.xyz/artbook. A small figure with crossed eyes runs through the '
               'thirty-five from one end of the seven years to the other; the last spread '
               'here is about it.')

BIO = ['Yiğit Özen was born in 1994 in Istanbul and trained as an architect.',
       'The painting dates from 2018 onward. The thirty-five works in this book were made '
       'between 2019 and 2026, across Istanbul, Milan and Luxembourg.',
       'From 2020 the studio work went largely to XR and spatial design, and the canvases '
       'thin out to one commission in 2023 before the painting resumes in 2026. The years '
       'are given as they fall rather than smoothed over.',
       'Alongside the paintings, Özen works as an XR and spatial web designer, and is the '
       'founder of decentralize design in Milan and Virtually Ever After in Luxembourg. '
       'That practice has been shown at Kunsthalle Zürich, the Royal Institution in '
       'London, Holy Art Gallery London and Art Basel Miami.']
# Sergi listesi ikiye ayrilir. Bir resim kitabinda ikisi ayrimsiz durursa
# okuyucu tasarim isinin sergilerini resimlerin sergisi sanir.
CV = [('Painting, selected exhibitions', [
        ('Power of the Nature, Fabbrica del Vapore, Milan', '2019'),
        ('The Arts Special Projects, Fabbrica del Vapore, Milan', '2019')]),
      ('XR and spatial design, selected', [
        ('Communitas III by Kollektiv Kollektiv, Kunsthaus Steffisburg', '2021'),
        ('New Freedom Think, Mads Gallery, Milan', '2022'),
        ('Art Design, Holy Art Gallery, London', '2022'),
        ('DYOR, Kunsthalle Zürich, Zurich', '2022'),
        ('Creators of the Metaverse by Metamundo, Art Basel Miami', '2022'),
        ('New Codes by VCA, Draup and Mad Global, Royal Institution, London', '2023')]),
      ('Talks', [
        ('VCA Mentorship, 6th Cohort, Architecture in the Metaverse', '2023'),
        ('Opening Keynote, Digital Fashion Summit, Creative Denmark', '2024')])]

# ══ on sayfalar ══════════════════════════════════════════════════════
# Kapak. Kirpma burada da yok: resim sayfanin genisligince, kendi
# yuksekligiyle duruyor, alti siyah kagit ve ad.
cover, car = prep('/img/full/detail/7famboardgame_detail_3.jpg', 240, 'cover')
p = page('', 'cover dark')
p.raw('<img src="%s" style="left:0;top:36mm;width:240mm;height:%.2fmm">' % (cover, 240 / car))
p.box(ML, 13, CONTENT_W, 'Artbooklet<span class="rt">Thirty-five works</span>', 'lab')
p.box(ML, 232, CONTENT_W, 'Yİ\u011eİT<br>ÖZEN', 'cvr-ti')
p.rule(ML, 288, CONTENT_W)
p.box(ML, 291, CONTENT_W,
      'Paintings since 2019<span class="rt">Istanbul &middot; Milan &middot; Luxembourg &middot; yigitozen.xyz</span>',
      'lab')

# Ic kapak. On sayfalarin tek sayida bitmesini de saglar, boylece ilk
# eserin acilisi bos bir sayfa acmadan sag sayfaya duser.
if not SHORT:
    p = page('')
    p.box(ML, 150, W(7), 'Paintings<br>since 2019', 'ti big-ti')
    p.rule(ML, 176, W(7))
    p.box(ML, 179, W(7), 'Yiğit Özen<span class="rt">Thirty-five works</span>', 'lab')

p = page('Imprint')
p.rule(ML, 15, CONTENT_W, True)
p.box(ML, 18, W(6), 'Artbooklet', 'lab')
p.box(ML, 232, W(5), 'Paintings<br>since 2019', 'ti big-ti')
p.box(ML, 258, W(5), 'Yiğit Özen', 'lab')
p.box(X(6), 232, W(6), e(SHORT_BLURB if SHORT else BLURB), 'note')
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
if SHORT:
    p = page('Biography')
    p.rule(ML, 15, CONTENT_W, True)
    p.box(ML, 18, W(4), 'Biography', 'lab')
    p.raw('<img src="%s" style="left:%.2fmm;top:36mm;width:%.2fmm">' % (por, X(7), W(5)))
    p.box(ML, 232, W(5), 'Yiğit<br>Özen', 'ti big-ti')
    p.box(X(6), 232, W(6), ''.join('<p>%s</p>' % e(x) for x in BIO[:2]) +
          '<p>Painting, selected: Power of the Nature and The Arts Special Projects, '
          'Fabbrica del Vapore, Milan, 2019. The XR and spatial design practice is listed '
          'separately at de-centralize.com.</p>', 'note')
toc_pages = []
if not SHORT:
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
# Bir eserin yazisi baskasinin cumlesiyle basliyorsa kaynagi yaninda durur.
SOURCE = {3: 'Tony Soprano, <em>The Sopranos</em>, HBO, season one'}


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
        ny = 52 + 4.6 * math.ceil(len(w['title']) / 22.0) + 6
        p.box(tx, ny, W(4), e(w['note']), 'note')
        ny += 4.05 * math.ceil(len(w['note']) / 46.0) + 4
        if w['n'] in SOURCE:
            p.box(tx, ny, W(4), SOURCE[w['n']], 'cap')
            ny += 3.3 * math.ceil(len(SOURCE[w['n']]) / 58.0) + 5
        if w.get('read'):
            p.box(tx, ny, W(4), e(w['read']), 'note')
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

def scatter_page(run, items, head=None, tag='d', flip=False):
    """Detay sayfasi. Izgara degil: biri genis biri dar iki sutun, birbirine
       gore kaydirilmis, ve her sutun sayfanin dibine kadar dagitilmis.
       Sayfadan sayfaya genis sutun yer degistirir."""
    p = page(run)
    if head:
        p.rule(ML, 15, CONTENT_W, True)
        p.box(ML, 17.4, W(7), head[0], 'lab')
        if len(head) > 1: p.box(R(3), 17.4, W(3), head[1], 'lab rt')
    a_w, b_w = (W(4), W(7)) if flip else (W(7), W(4))
    a_x, b_x = (X(8), ML) if flip else (ML, X(8))
    lanes = [{'x': a_x, 'w': a_w, 'y0': 30.0, 'it': []},
             {'x': b_x, 'w': b_w, 'y0': 72.0, 'it': []}]
    for i, it in enumerate(items):
        lanes[i % 2]['it'].append((i, it))
    for ln in lanes:
        if not ln['it']: continue
        # Sigmiyorsa sutun daralir; hicbir gorsel kesilmez, hicbiri sayfadan
        # tasmaz, yalnizca kucultulur.
        for _ in range(30):
            hs = [ln['w'] / ratio(src, box) + 5.4 for _, (src, _c, box) in ln['it']]
            if sum(hs) <= FOOT - ln['y0']: break
            ln['w'] *= .94
        n = len(hs)
        slack = max(0.0, (FOOT - ln['y0']) - sum(hs))
        gap = min(30.0, slack / n) if n else 0.0
        y = ln['y0'] + (slack - gap * (n - 1)) * (.35 if n > 1 else .5)
        for k, (i, (src, cap_t, box)) in enumerate(ln['it']):
            p.pic(src, ln['x'], y, ln['w'], cap=cap_t, box=box,
                  tag='%s%03d' % (tag, i))
            y += hs[k] + gap
    return p


def mosaic_page(run, items, head=None, tag='m'):
    """Bir figurun gectigi butun tablolardan kesitler. Iki sutun, satirlar
       ayni yukseklikte; her kesit satirin dip cizgisine oturur, boylece
       kunyeler tek hizada dizilir ve sayfa dagilmaz."""
    p = page(run)
    Y0, CAPH, RGAP, FT = 32.0, 9.0, 11.0, 10.0
    if head:
        p.rule(ML, 15, CONTENT_W, True)
        p.box(ML, 17.4, W(8), head[0], 'lab')
        if len(head) > 1: p.box(R(3), 17.4, W(3), head[1], 'lab rt')
    n = len(items)
    cols = 2
    rows = int(math.ceil(n / float(cols)))
    cellw = (CONTENT_W - GAP * 2) / cols
    step = cellw + GAP * 2
    bh = ((FOOT - FT - Y0) - rows * CAPH - (rows - 1) * RGAP) / rows
    y = Y0
    for r in range(rows):
        row = items[r * cols:(r + 1) * cols]
        for j, (src, cap_t, box) in enumerate(row):
            ar = ratio(src, box)
            iw = min(cellw, bh * ar)
            ih = iw / ar
            x = ML + j * step
            path, _ = prep(src, iw, '%s%02d' % (tag, r * cols + j), box)
            p.raw('<img src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm">'
                  % (path, x, y + bh - ih, iw, ih))
            p.box(x, y + bh + 1.8, cellw, e(cap_t), 'cap')
        if r < rows - 1:
            p.rule(ML, y + bh + CAPH + RGAP / 2 - 1.0, CONTENT_W)
        y += bh + CAPH + RGAP
    return p


# ── kucuk gorselli dizin, bir sayfa ─────────────────────────────────
def index_page(run):
    """Otuz bes tablo tek sayfada. Her hucre ayni yukseklikte bir bant;
       gorsel bandin altina oturur, bu yuzden butun satirlar ayni cizgide
       biter ve numaralar tek bir hizada durur."""
    p = page(run)
    p.rule(ML, 15, CONTENT_W, True)
    p.box(ML, 17.4, W(6), 'The thirty-five', 'lab')
    p.box(R(3), 17.4, W(3), 'Index', 'lab rt')
    NC, Y0, CAP, RGAP = 7, 32.0, 5.6, 9.0
    FT = 8.0
    rows = [WORKS[i:i + NC] for i in range(0, len(WORKS), NC)]
    nr = len(rows)
    step = CONTENT_W / NC
    cw = step - GAP
    bh = ((FOOT - FT - Y0) - nr * CAP - (nr - 1) * RGAP) / nr
    y = Y0
    for row in rows:
        for j, w in enumerate(row):
            iw = min(cw, bh * w['ar'])
            ih = iw / w['ar']
            x = ML + j * step
            path, _ = prep(w['plate']['src'], iw, 'ix%02d' % w['n'], w['plate'].get('box'))
            p.raw('<img src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm">'
                  % (path, x, y + bh - ih, iw, ih))
            p.box(x, y + bh + 1.6, cw, '%02d' % w['n'], 'cap')
        p.rule(ML, y + bh + CAP + RGAP / 2 - 1.0, CONTENT_W)
        y += bh + CAP + RGAP
    p.rule(ML, 272, CONTENT_W)
    p.box(ML, 274.2, W(8), 'Plates are reproduced at a common height; the numbers are '
          'the sequence of the book, newest first', 'cap')
    p.box(R(2), 274.2, W(2), '35 works', 'cap rt')
    return p


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

# Bir eserin acilis sayfasi hep sag sayfada durur ve karsisindaki sol sayfa
# da o eserin kendi detayidir, bir oncekinin degil. Hangi detayin one
# gectigi rastgele degil: her eser icin sirasi verilmis, oran tutmazsa
# siradaki denenir.
LEAD = {1:[0,4,1], 2:[2,0,6], 3:[2,1,8], 4:[3,0,1], 5:[4,0,6], 6:[0,6,2],
        8:[0,1,4], 9:[0,1,2], 12:[1,0,3], 14:[0,1,2], 15:[0,1,4], 27:[0]}


def order(w):
    """Eserin detaylari, one cikarilmis olanlar basta."""
    pref = LEAD.get(w['n'], [])
    ks = [k for k in pref if k < len(w['details'])]
    return ks + [k for k in range(len(w['details'])) if k not in ks]


def take(w, used, want):
    """Orani tutan ilk detay: 'wide' 1.5, 'tall' 0.75, 'any' hepsi."""
    for k in order(w):
        if k in used: continue
        a = ratio(w['details'][k]['src'])
        if want == 'wide' and abs(a - 1.5) > .02: continue
        if want == 'tall' and abs(a - .75) > .02: continue
        return k
    return None


def bleed_spread(w, k, d):
    """Orani 1.5 olan bir detay iki sayfaya, ortadan bolerek, kirpmadan.
       Iki yari da 0.75 eder, sayfanin orani da 0.75."""
    im = Image.open(os.path.join(ROOT, d['src'].lstrip('/'))).convert('RGB')
    iw, ih = im.size
    for half in (0, 1):
        c = im.crop((half * iw // 2, 0, (half + 1) * iw // 2, ih))
        t = 'w%02db%d%d' % (w['n'], k, half)
        c2 = c.copy(); c2.thumbnail((1100, 1100), Image.LANCZOS)
        c2.save(os.path.join(IMG, t + '.jpg'), quality=78, subsampling=2, optimize=True)
        p = page(w['run'], 'dark')
        p.raw('<img src="images/%s.jpg" style="left:0;top:0;width:240mm;height:320mm">' % t)
        if half:
            p.box(R(5), 292, W(5), '%02d \u00b7 %s' % (w['n'], e(where(d))), 'cap rt onimg')


def blank(run):
    page(run, 'blank')


def align(run, parity):
    """Sonraki sayfanin tek ya da cift olmasini saglar. Bir eserin acilisi
       hep tek sayida bir sayfaya, yani sagina dusmek zorunda. Kitapta bunun
       icin bos sayfa acilmaz; sayfa sayilari malzemeyle ayarlanir."""
    while (len(PAGES) + 1) % 2 != parity % 2:
        blank(run)


def plate_cap(w, d):
    """Tam sayfa duran bir gorselin kunyesi. Tek bicim: numarasi, orta nokta,
       tabloda neresi oldugu. Kitabin her yerinde ayni yerde, ayni aralikta."""
    return '%02d \u00b7 %s' % (w['n'], e(where(d)))


def full_page(w, d, tag):
    """Tam sayfa bir gorsel. Sayfa orani 0.75; gorselin orani buna cok
       yakinsa sayfayi bastan basa doldurur, fark kenardan alinir. Degilse
       kirpilmaz: yatikca kenardan kenara, dikce tepeden asagi tasar ve
       kunye her yerde ayni yerde, ayni bicimde, beyaz uzerinde durur."""
    a = ratio(d['src'])
    path, _ = prep(d['src'], 240, tag)
    if abs(a - .75) <= .023:                      # sayfayi doldurur
        p = page(w['run'], 'dark full')
        p.raw('<img class="cover" src="%s">' % path)
        p.box(ML, 292, CONTENT_W, plate_cap(w, d), 'cap onimg')
        return p
    p = page(w['run'], 'plate')
    h = PW / a
    if h <= CAP_Y - 4.0:                          # yatik: kenardan kenara
        top = min((PH - h) / 2, (CAP_Y - 4.0) - h)
        p.raw('<img src="%s" style="left:0;top:%.2fmm;width:240mm;height:%.2fmm">'
              % (path, top, h))
    else:                                         # dik: tepeden asagi
        h = CAP_Y - 4.0
        wd = h * a
        p.raw('<img src="%s" style="left:%.2fmm;top:0;width:%.2fmm;height:%.2fmm">'
              % (path, (PW - wd) / 2, wd, h))
    p.box(ML, 292, CONTENT_W, plate_cap(w, d), 'cap')
    return p


def lead_page(w, k, d):
    """Eserin acilis sayfasi: tam sayfa, dik de olsa yatik da olsa."""
    full_page(w, d, 'w%02dL%d' % (w['n'], k))


def lead_in(w):
    """Acilisin karsisindaki sol sayfa: eserin kendi detayi, tam sayfa.
       Hangisi oldugu LEAD'de verilmis, rastgele degil."""
    ks = [k for k in order(w)]
    k = ks[0]
    lead_page(w, k, w['details'][k])
    w['used_lead'] = [k]


def wide_spread(w):
    """Acilistan hemen sonra, orani 1.5 olan bir detay iki sayfaya. Acilis
       tek sayida oldugu icin bu her zaman tam bir acilima oturur."""
    used = w.get('used_lead', [])
    k = take(w, used, 'wide')
    if k is None: return
    used.append(k); w['used_lead'] = used
    bleed_spread(w, k, w['details'][k])


# Detay sayfasinin duzeni. Dort yuva alt alta, aralari esit, sutun sayfanin
# ortasinda. Yuvalardan biri kimi zaman bos birakilip yazi alir, kimi zaman
# ikiye bolunup iki kucuk gorsel alir. Dagitilmis degil, kurulmus.
SLOTS, SGAP, STOP, SBOT = 4, 10.0, 26.0, 20.0
IMAX_W = W(11)                                  # yanlarda esit, genis kenar


def column_page(w, items, tag):
    """Bir sayfa: ustten asagi esit yuvalar, en fazla dort. Yuva sayisi
       sayfadaki oge sayisi kadardir, boylece uc ya da iki oge kalinca
       gorseller kucuk kalmaz, buyur. Hicbiri kosaya degmez; iki yanda
       esit kenar birakilir."""
    n = max(1, min(SLOTS, len(items)))
    slot_h = (PH - STOP - SBOT - (n - 1) * SGAP) / n
    p = page(w['run'])
    p.box(ML, 9.5, W(8), '%02d &nbsp; %s' % (w['n'], e(w['title'])), 'lab')
    p.box(R(3), 9.5, W(3), 'Detail', 'lab rt')
    y = STOP
    for it in items[:n]:
        if isinstance(it, tuple) and it[0] == 'text':
            p.box(X(2), y + slot_h * .30, W(8), it[1], 'lead')
            y += slot_h + SGAP; continue
        if isinstance(it, list):                   # yuva ikiye bolunur
            pair = it[:2]
            gw = (IMAX_W - GAP * 2) / 2
            hs = [min(slot_h - 6.0, gw / ratio(d['src'])) for d in pair]
            hh = min(hs)
            ws = [hh * ratio(d['src']) for d in pair]
            x = (PW - (sum(ws) + GAP * 2)) / 2
            for d, cwid in zip(pair, ws):
                p.pic(d['src'], x, y + (slot_h - hh) / 2 - 2.0, cwid,
                      cap=where(d), tag='%s%s' % (tag, d['src'][-9:-4]))
                x += cwid + GAP * 2
            y += slot_h + SGAP; continue
        d = it
        a = ratio(d['src'])
        cw = min(IMAX_W, (slot_h - 6.0) * a)
        hh = cw / a
        p.pic(d['src'], (PW - cw) / 2, y + (slot_h - hh) / 2 - 2.0, cw,
              cap=where(d), tag='%s%s' % (tag, d['src'][-9:-4]))
        y += slot_h + SGAP
    return p


def upright_page(w, d, tag):
    """Dik bir detay tek basina, tam sayfa."""
    return full_page(w, d, tag)


def detail_plan(w):
    """Kac sayfa tutacagi: dikler birer sayfa, yataylar dorderli sutun."""
    used = list(w.get('used_lead', []))
    rest = [w['details'][k] for k in order(w) if k not in used]
    up = [d for d in rest if ratio(d['src']) < 1.0]
    wide = [d for d in rest if ratio(d['src']) >= 1.0]
    return up, wide


def detail_pages(w, extra=0):
    """Once dik detaylar, her biri tam sayfa. Sonra yataylar: sayfa basina
       en cok dort, yuvalar oge sayisina gore buyur. `extra` bir sayfa daha
       acar; o sayfadaki bos yuvaya isin kendi cumlesi gelir."""
    up, wide = detail_plan(w)
    for d in up:
        upright_page(w, d, 'w%02du%s' % (w['n'], d['src'][-9:-4]))
    if not wide: return
    wide = [x for x in spread_out([(d['src'], None, None) for d in wide])]
    wide = [next(d for d in w['details'] if d['src'] == src) for src, _c, _b in wide]
    n = len(wide)
    pages = int(math.ceil(n / 4.0)) + (1 if extra else 0)
    per = int(math.ceil(n / float(pages)))
    chunks, at = [], 0
    for _ in range(pages):
        chunks.append(wide[at:at + per]); at += per
    chunks = [c for c in chunks if c]
    for pi, chunk in enumerate(chunks):
        items = list(chunk)
        if len(items) == 5:                       # besinci, ikili yuvaya
            items = items[:3] + [items[3:5]]
        if extra and pi == len(chunks) - 1 and len(items) < SLOTS:
            items.insert(max(1, len(items) // 2), ('text', e(w['facets'][pi % 3])))
        column_page(w, items[:SLOTS], 'w%02dc%d' % (w['n'], pi))


def process_page(w, pages=1):
    """Surec. Kucuk, sik, izgarada: kitapta izgaranin yeri yalniz burasi,
       cunku bunlar levha degil, bir sira."""
    ps = w['process']
    if not ps or pages <= 0: return
    per = int(math.ceil(len(ps) / float(pages)))
    for pi in range(pages):
        part = ps[pi * per:(pi + 1) * per]
        if not part: continue
        cols = 4 if len(part) > 6 else 3
        span = COLS // cols
        cw = W(span)
        p = page(w['run'])
        p.rule(ML, 15, CONTENT_W, True)
        p.box(ML, 17.4, W(7), '%02d &nbsp; %s' % (w['n'], e(w['title'])), 'lab')
        p.box(R(3), 17.4, W(3), 'Process', 'lab rt')
        rows = int(math.ceil(len(part) / float(cols)))
        base, rem = divmod(len(part), rows)        # satirlar denk bolunur
        sizes = [base + 1] * rem + [base] * (rows - rem)
        bands, at = [], 0
        for sz in sizes:
            bands.append(part[at:at + sz]); at += sz
        hs = [max(cw / ratio(d['src']) for d in band) for band in bands]
        slack = max(0.0, (FOOT - 30.0) - sum(hs))
        gapv = min(24.0, slack / max(1, rows - 1)) if rows > 1 else 0.0
        gaph = (CONTENT_W - cols * cw) / max(1, cols - 1)
        y = 30.0 + max(0.0, slack - gapv * max(0, rows - 1)) * .40
        note = None
        idx = 0
        for k, band in enumerate(bands):
            roww = len(band) * cw + (len(band) - 1) * gaph
            x = ML + (CONTENT_W - roww) / 2
            for d in band:
                p.pic(d['src'], x, y, cw,
                      tag='w%02dp%02d' % (w['n'], pi * per + idx))
                x += cw + gaph; idx += 1
                c = CREDITS.get(d['src'].split('/')[-1])
                if c: note = c
            y += hs[k] + gapv
        if note:
            p.rule(ML, 286, W(9)); p.box(ML, 288, W(9), e(note), 'cap')
        p.box(R(2), 292, W(2),
              ('%d of %d stages' % (len(part), len(ps))) if pages > 1
              else ('%d stages' % len(ps)), 'cap rt')


def aside_page(w):
    """Kokte duran calismalar: bir eserin etudu ya da baska bir hali. Bunlar
       detay degil, ayri resimlerdir; kunyeleri de oyle yazar. Duzen dagilmaz:
       sol kenara hizali bir yigin, karsisinda yazi sutunu."""
    if not w['aside']: return
    items = w['aside']
    n = len(items)
    p = page(w['run'])
    p.rule(ML, 15, CONTENT_W, True)
    p.box(ML, 17.4, W(7), '%02d &nbsp; %s' % (w['n'], e(w['title'])), 'lab')
    p.box(R(3), 17.4, W(3), 'Studies and versions', 'lab rt')
    Y0, AGAP, FT = 32.0, 12.0, 14.0
    avail = (FOOT - FT) - Y0
    if n == 1:
        a0 = items[0]
        ar = ratio(a0['src'], a0.get('box'))
        iw = min(CONTENT_W, (avail - 12.0) * ar)
        ih = iw / ar
        y = Y0 + (avail - ih - 12.0) / 2.0
        path, _ = prep(a0['src'], iw, 'w%02da0' % w['n'], a0.get('box'))
        p.raw('<img src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm">'
              % (path, ML, y, iw, ih))
        p.box(ML, y + ih + 2.4, W(7), e(where(a0)), 'cap')
        p.box(R(2), y + ih + 2.4, W(2), e(kind(a0)), 'cap rt')
    else:
        IMAX = W(6)
        ars = [ratio(a0['src'], a0.get('box')) for a0 in items]
        hs = [IMAX / a for a in ars]
        room = avail - (n - 1) * AGAP
        k0 = min(1.0, room / sum(hs))
        hs = [h * k0 for h in hs]
        pad = max(0.0, (room - sum(hs)) / n) / 2.0
        y = Y0
        for k, a0 in enumerate(items):
            ar = ars[k]
            ih = hs[k]
            iw = ih * ar
            bh = ih + 2 * pad
            y += pad
            path, _ = prep(a0['src'], iw, 'w%02da%d' % (w['n'], k), a0.get('box'))
            p.raw('<img src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm">'
                  % (path, ML, y, iw, ih))
            p.box(X(7), y - 1.0, W(4), e(where(a0)), 'note')
            p.box(R(1), y - 1.0, W(1), e(kind(a0)), 'cap rt')
            if k < n - 1:
                p.rule(ML, y + ih + pad + AGAP / 2 - 1.0, CONTENT_W)
            y += ih + pad + AGAP
    p.rule(ML, 272, CONTENT_W)
    p.box(ML, 274.2, W(8),
          'Sheets and earlier states kept in the studio, shown here beside the work '
          'they belong to', 'cap')
    p.box(R(2), 274.2, W(2), '%d shown' % n, 'cap rt')


# ══ eserler ════════════════════════════════════════════════════════
# Yil ayraci yok. Bir yilda tek is kaldiginda o ise koca bir ayrac sayfasi
# acmak isi kucultuyordu; yil zaten her sayfanin dibinde yaziyor. Isler
# kesintisiz, yeniden eskiye.
for w in WORKS:
    w['run'] = '%s &middot; %s' % (w['year'], w.get('place', ''))


def quote_page(w):
    """Tek kalan detayi olmayan bir isin karsi sayfasi. Ayni tabloyu ikinci
       kez, ayni boyda basmanin anlami yok; onun yerine kendi yazisindan
       bir cumle, buyuk."""
    line = w['note'].split('. ')[0].strip()
    if not line.endswith('.'): line += '.'
    p = page(w['run'])
    p.box(ML, 9.5, W(6), '%02d &nbsp; %s' % (w['n'], e(w['title'])), 'lab')
    p.box(ML, 150, W(9), e(line), 'shout')
    p.rule(ML, 272, CONTENT_W)
    p.box(ML, 274, W(6), e(w['year']) + ' \u00b7 ' + e(w.get('place', '')), 'cap')


def plan(w):
    """Acilistan sonraki sayfa sayisi cift olmak zorunda, yoksa sonraki is
       bir baskasinin sayfasiyla ayni acilima duser. Bos sayfa acilmaz:
       gereken tek sayfa, dortlu sutunlardan birinin yazi ya da ikili yuva
       almasiyla kazanilir."""
    up, wide = detail_plan(w)
    base = len(up) + int(math.ceil(len(wide) / 4.0)) if wide else len(up)
    ap = 1 if w['aside'] else 0
    pps = ([1, 2] if len(w['process']) >= 8 else [1]) if w['process'] else [0]
    for extra in (0, 1):
        for pp in pps:
            if (base + extra + ap + pp) % 2 == 0:
                return extra, pp
    return 0, (pps[0] if pps else 0)


plain = []                      # detayi olmayan isler, ikiser ikiser


def flush_plain():
    """Detayi olmayan isler bir acilimi paylasir, sayfa basina bir is. Tek
       kalirlarsa ilkine tablosunun tam sayfasi acilis olur; boylece bos
       sayfa acmak gerekmez."""
    if not plain: return
    align(plain[0]['run'], 0)
    if len(plain) % 2:
        w0 = plain.pop(0)
        quote_page(w0); work_open(w0)
    while plain:
        work_open(plain.pop(0))


for w in (WORKS if not SHORT else [x for x in WORKS if x['n'] in SELECT]):
    if SHORT:
        work_open(w); continue
    if not w['details'] and not w['aside']:
        plain.append(w); continue
    flush_plain()
    align(w['run'], 0)                    # acilis her zaman sag sayfada
    if not w['details']:
        # Detayi yok ama etudu ya da baska bir hali var: acilisin karsisina
        # o gecer. Tabloyu ikinci kez basmaya gerek kalmaz.
        aside_page(w)
        work_open(w)
        if len(PAGES) % 2 == 0: quote_page(w)     # ender: cift kalirsa
        continue
    extra, pp = plan(w)
    lead_in(w)
    work_open(w)
    detail_pages(w, extra)
    aside_page(w)
    process_page(w, pp)
    # Sayim yine de tutmazsa bos sayfa acilmaz: isin kendi cumlesi gecer.
    if len(PAGES) % 2 == 0: quote_page(w)
flush_plain()

# ══ motif ═══════════════════════════════════════════════════════════
# Kitabin en cok is goren bolumu: yedi yil boyunca tekrar eden alti sey,
# her biri bir yazi sayfasi ve gectigi butun islerden kesitler.
def crop_of(w, b):
    """Motif kutusu kirpilmis tablonun icinde verilmistir; saklanan
       fotografin icindeki yerine cevirir."""
    pb = w['plate'].get('box') or [0, 0, 1, 1]
    return [pb[0] + b[0] * pb[2], pb[1] + b[1] * pb[3], b[2] * pb[2], b[3] * pb[3]]


def motif_section(sec):
    """Sol sayfa yazi, sag sayfa resimler. Ikisi arka arkaya degil, karsi
       karsiya durur."""
    ws = [BY_N[c['n']] for c in sec['crops']]
    align(sec['name'], 0)
    p = page(sec['name'])
    p.rule(ML, 15, CONTENT_W, True)
    p.box(ML, 17.4, W(6), 'A recurring figure', 'lab')
    p.box(R(3), 17.4, W(3), e(sec['range']), 'lab rt')
    p.box(ML, 118, W(8), e(sec['name']), 'shout')
    p.box(ML, 158, W(7), e(sec['lead']), 'lead')
    p.box(ML, 190, W(5), e(sec['a']), 'note')
    p.box(X(6), 190, W(6), e(sec['b']), 'note')
    p.rule(ML, 272, CONTENT_W)
    p.box(ML, 274, W(8), '%d works' % len(ws), 'cap')
    p.box(R(4), 274, W(4), ' \u00b7 '.join('%02d' % c['n'] for c in sec['crops']), 'cap rt')

    items = [(BY_N[c['n']]['plate']['src'],
              '%02d \u00b7 %s \u00b7 %s' % (c['n'], BY_N[c['n']]['year'], c['line']),
              crop_of(BY_N[c['n']], c['box']))
             for c in sec['crops']]
    mosaic_page(sec['name'], items,
                head=(e(sec['name']) + ', in each painting it appears in', 'Details'),
                tag='m-' + sec['key'])


# Once dizin: otuz besin hepsi bir arada, kendi bolumu olarak. Sonra
# tekrar edenler: "bunlarin icinden su alti sey cikiyor".
if not SHORT:
    align('Index', 0)
    p = page('Index')
    p.rule(ML, 15, CONTENT_W, True)
    p.box(ML, 17.4, W(6), 'Thirty-five works', 'lab')
    p.box(R(3), 17.4, W(3), 'Index', 'lab rt')
    p.box(ML, 150, W(9), 'The<br>thirty-five', 'shout')
    p.rule(ML, 272, CONTENT_W)
    p.box(ML, 274, W(9), 'Made since 2019 across Istanbul, Milan and Luxembourg', 'cap')
    index_page('Index')

# Kisa surumde alti bolumun yalniz ilki: gonderim icin bir ornek yeter.
if not SHORT:
    align('The recurring', 0)
    p = page('The recurring')
    p.rule(ML, 15, CONTENT_W, True)
    p.box(ML, 17.4, W(6), 'Six things that come back', 'lab')
    p.box(R(3), 17.4, W(3), '2019&ndash;2026', 'lab rt')
    p.box(ML, 150, W(9), 'The<br>recurring', 'shout')
    p.rule(ML, 272, CONTENT_W)
    p.box(ML, 274, W(9), ' \u00b7 '.join(x['name'] for x in MOTIFS['sections']), 'cap')
    p.box(R(2), 274, W(2), '%d figures' % len(MOTIFS['sections']), 'cap rt')

    # Karsi sayfa: alti seyin her birinden bir kesit, bolumun icindekileri.
    # Butun satirlar ayni yukseklikte bir bant; kesit bandin icine oturur.
    q = page('The recurring')
    q.rule(ML, 15, CONTENT_W, True)
    q.box(ML, 17.4, W(6), 'What comes back', 'lab')
    q.box(R(3), 17.4, W(3), 'Contents', 'lab rt')
    RY0, RGAP = 34.0, 12.0
    nsec = len(MOTIFS['sections'])
    ih = ((FOOT - 8.0 - RY0) - (nsec - 1) * RGAP) / nsec
    y = RY0
    for sec in MOTIFS['sections']:
        c = sec['crops'][0]
        wk = BY_N[c['n']]
        bx = crop_of(wk, c['box'])
        iw = min(W(5), ih * ratio(wk['plate']['src'], bx))
        path, _ = prep(wk['plate']['src'], iw, 'rc-' + sec['key'], bx)
        q.raw('<img src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm">'
              % (path, ML, y, iw, ih))
        q.box(X(6), y - 1.0, W(4), e(sec['name']), 'ti')
        q.box(X(6), y + 7.6, W(5), e(sec['lead']), 'cap')
        q.box(R(1), y - 1.0, W(1), '%02d' % len(sec['crops']), 'cap rt')
        if sec is not MOTIFS['sections'][-1]:
            q.rule(ML, y + ih + RGAP / 2 - 1.0, CONTENT_W)
        y += ih + RGAP
    q.rule(ML, 272, CONTENT_W)
    q.box(ML, 274.2, W(8), 'Each figure is shown in every painting it appears in, '
          'on the pages that follow', 'cap')
    q.box(R(3), 274.2, W(3), 'Pages 114&ndash;125', 'cap rt')

for sec in (MOTIFS['sections'][:1] if SHORT else MOTIFS['sections']):
    motif_section(sec)

# ══ arka ══# ══ arka ═════════════════════════════════════════════════════════════
p = page('Colophon')
p.rule(ML, 15, CONTENT_W, True)
p.box(ML, 17.4, W(4), 'Colophon', 'lab')
p.box(ML, 168, W(5),
      '<p>All works by Yiğit Özen, born 1994 in Istanbul and trained as an architect. '
      'Works are given newest first, so a paragraph that says a thing happens for the '
      'first time means the first time reading backwards through the book.</p>'
      '<p>Dimensions are width by height, in centimetres.</p>'
      '<p>Photography by the artist. Plates and details reproduce documentation of the '
      'paintings; colour and surface differ from the works themselves.</p>', 'note')
p.box(X(6), 168, W(6),
      '<p>Where a paragraph gives a proportion or a percentage, it was measured on the '
      'documentation file rather than on the painting, and it describes that file. No '
      'colour target was used in the photography, so the figures are a reading of the '
      'photograph and not a colorimetric claim about the paint.</p>'
      '<p>The epigraph on 03 is Tony Soprano, <em>The Sopranos</em>, HBO. The first frame '
      'of the process pages on 02 and 03 is a reference the painting was begun from and '
      'is credited on the page it appears.</p>'
      '<p>A technical catalogue of the same works, with the full index, is published '
      'separately.</p>'
      '<p>All works &copy; Yiğit Özen. All rights reserved.</p>', 'note')
p.rule(ML, 276, CONTENT_W, True)
p.box(ML, 279, W(5), 'For enquiries, availability and prices', 'lab')
p.box(X(5), 279, W(4), 'x@yigitozen.xyz<br>Instagram @yjgjf', 'cap plain')
p.box(R(3), 279, W(3), 'Studio, Luxembourg<br>yigitozen.xyz &middot; de-centralize.com',
      'cap plain rt')

if SHORT:
    index_page('Index')
if not SHORT:
    logo = page('', 'last')
    logo.raw('<img class="mk" src="images/logo.svg">')

# ══ icindekiler ══════════════════════════════════════════════════════
def toc(p, items, head=None):
    y = 15.0
    p.rule(ML, y, CONTENT_W, True)
    p.box(ML, y + 2.4, W(4), head or 'Contents (continued)', 'lab')
    y += 14
    for w in items:
        lines = 2 if len(w['title']) > 58 else 1
        p.box(ML,   y, W(1), '%02d' % w['n'], 'toc n')
        p.box(X(1), y, W(7), e(w['title']), 'toc t')
        p.box(X(9), y, W(2), e(w['year']), 'toc y')
        p.box(R(1), y, W(1), str(first_page[w['n']]), 'toc p rt')
        p.rule(ML, y + 6.4 + (lines - 1) * 4.2, CONTENT_W)
        y += 8.6 + (lines - 1) * 4.2

if toc_pages:
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
open(os.path.join(HERE, 'booklet-short.html' if SHORT else 'booklet.html'),
     'w', encoding='utf-8').write('\n'.join(out))
# PDF'in yer imleri icin: hangi baslik hangi sayfada
marks = []
for i, p in enumerate(PAGES, start=1):
    if p.klass == 'cover dark': marks.append(('Cover', i))
for name, i in ((('Imprint', 2), ('On the work', 4), ('Biography', 5))
                if SHORT else
                (('Imprint', 2), ('On the work', 4), ('Biography', 6), ('Contents', 8))):
    if i <= len(PAGES): marks.append((name, i))
seen = set()
for i, p in enumerate(PAGES, start=1):
    if p.klass == 'dark' and p.run and p.run not in seen:
        seen.add(p.run); marks.append((p.run.replace('&middot;', '·'), i))
for w in WORKS:
    if w['n'] in first_page:
        marks.append(('%02d  %s' % (w['n'], w['title']), first_page[w['n']]))
back = ['Index', 'The recurring'] + [x['name'] for x in MOTIFS['sections']] \
       + ['Colophon']
first_run = {}
for i, p in enumerate(PAGES, start=1):
    if p.run and p.run not in first_run: first_run[p.run] = i
for name in back:
    if name in first_run: marks.append((name, first_run[name]))
json.dump({'marks': marks, 'pages': len(PAGES), 'short': SHORT},
          open(os.path.join(HERE, 'outline-short.json' if SHORT else 'outline.json'),
               'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

print('pages: %d' % len(PAGES))
print('images: %d' % len(made))
