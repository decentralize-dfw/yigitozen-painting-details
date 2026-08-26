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
WHERE   = json.load(open(os.path.join(HERE, 'where.json'), encoding='utf-8'))
MOTIF   = json.load(open(os.path.join(HERE, 'motif.json'), encoding='utf-8'))
CREDITS = json.load(open(os.path.join(HERE, 'credits.json'), encoding='utf-8'))

# Kayitta detay diye gecen ama detay olmayanlar: bunlar isin baska bir hali
# ya da baska bir denemesi. Kitapta detay bolumune degil, etudlerin yanina.
NOT_DETAIL = {
    'ciaocapo_detail_6.jpg': 'Another version, on green and blue',
    'ciaocapo_detail_7.jpg': 'The pair in blue and grey',
    'ciaocapo_detail_8.jpg': 'The pair, before the colour',
    'cellularspleens_detail_4.jpg': 'The whole, in another version',
}
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

# Uc detay iki sayfaya tasar. Detaylar tam 1800 x 1200, yani 1.5; ikiye
# bolununce her yari 0.75 eder ve sayfanin orani da 240/320 = 0.75. Yani
# iki sayfayi bastan basa dolduruyor ve yine hicbir yeri kesilmiyor.
BLEED = {(1, 6), (6, 0), (15, 1)}

def bleed_spread(w, k, d):
    """Bir detayi iki sayfaya, ortadan bolerek, kirpmadan."""
    src = os.path.join(ROOT, d['src'].lstrip('/'))
    im = Image.open(src).convert('RGB')
    iw, ih = im.size
    for half in (0, 1):
        c = im.crop((half * iw // 2, 0, (half + 1) * iw // 2, ih))
        t = 'w%02db%d%d' % (w['n'], k, half)
        c2 = c.copy(); c2.thumbnail((1100, 1100), Image.LANCZOS)
        c2.save(os.path.join(IMG, t + '.jpg'), quality=80, subsampling=2, optimize=True)
        p = page(w['run'], 'dark')
        p.raw('<img src="images/%s.jpg" style="left:0;top:0;width:240mm;height:320mm">' % t)
        if half:
            p.box(R(5), 292, W(5), '%02d &nbsp; %s' % (w['n'], e(where(d))), 'cap rt onimg')


def bleed_page_one(w, k, d):
    """Orani tam sayfayla ayni olan bir detay: bastan basa, kesilmeden."""
    path, _ = prep(d['src'], 240, 'w%02dB%d' % (w['n'], k))
    p = page(w['run'], 'dark')
    p.raw('<img src="%s" style="left:0;top:0;width:240mm;height:320mm">' % path)
    p.box(R(5), 292, W(5), '%02d \u00b7 %s' % (w['n'], e(where(d))), 'cap rt onimg')


def detail_pages(w):
    """Detaylar. Ilki tek basina ve buyuk, alt kenari sayfanin dip cizgisine
       oturur; kitabin her yerinde ayni ufuk. Kalanlar izgarada, hepsi butun
       halde: yatay bir detay yatay durur."""
    ds = list(w['details'])
    if not ds: return
    # Yalniz orani tam 1.5 olan bir detay iki sayfaya bolunebilir; baska bir
    # oranda yarim sayfaya sigdirmak icin germek gerekir ve o gerilmez.
    # Bir detay ancak orani tutuyorsa sayfayi doldurur: 1.5 ise ikiye
    # bolunup cift sayfaya, 0.75 ise tek sayfaya, tam olarak. Baska bir
    # oranda germek gerekir, o yuzden yerinde birakilir.
    for k in sorted([k for (n, k) in BLEED if n == w['n']], reverse=True):
        if k >= len(ds): continue
        a = ratio(ds[k]['src'])
        if abs(a - 1.5) < .02:   bleed_spread(w, k, ds.pop(k))
        elif abs(a - .75) < .02: bleed_page_one(w, k, ds.pop(k))
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
    note = None
    for k, i in enumerate(range(0, len(ps), cols)):
        for j, d in enumerate(ps[i:i + cols]):
            p.pic(d['src'], X(j * span), y, cw, tag='w%02dp%02d' % (w['n'], i + j))
            c = CREDITS.get(d['src'].split('/')[-1])
            if c: note = c
        y += hs[k] + gapv
    if note:
        p.rule(ML, 286, W(9))
        p.box(ML, 288, W(9), e(note), 'cap')
    p.box(R(2), 292, W(2), '%d stages' % len(ps), 'cap rt')

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
    if SHORT: group = [w for w in group if w['n'] in SELECT]
    if not group: continue
    places = {}
    for w in group: places[w.get('place', '')] = places.get(w.get('place', ''), 0) + 1
    place = max(places, key=places.get)
    run = '%s &middot; %s' % (yr, place)
    for w in group: w['run'] = run

    if not SHORT:
      p = page(run, 'dark')
      p.box(ML, 196, CONTENT_W, e(yr), 'yr')
      p.box(ML, 262, W(5), e(place), 'ti')
      p.rule(ML, 276, CONTENT_W)
      p.box(ML, 279, W(8), ' &nbsp;&middot;&nbsp; '.join('%02d' % x['n'] for x in group), 'cap')
      p.box(R(2), 279, W(2), ('%d work%s' % (len(group), '' if len(group) == 1 else 's')), 'cap rt')

    for w in group:
        work_open(w)
        if SHORT: continue
        aside_page(w)
        detail_pages(w)
        process_page(w)

# ══ motif ═══════════════════════════════════════════════════════════
def motif_pages():
    """Kitabin en cok is goren iki sayfasi: 2019'dan 2026'ya tekrar eden
       figur, adiyla ve gectigi butun islerden kesitlerle yan yana."""
    ws = [BY_N[c['n']] for c in MOTIF['crops']]
    yrs = sorted(set(x['year'] for x in ws))
    p = page('The onlooker')
    p.rule(ML, 15, CONTENT_W, True)
    p.box(ML, 17.4, W(6), 'A recurring figure', 'lab')
    p.box(R(3), 17.4, W(3), '%s&ndash;%s' % (yrs[0], yrs[-1]), 'lab rt')
    p.box(ML, 120, W(8), 'The onlooker', 'shout')
    p.box(ML, 176, W(5),
          'A small figure turns up in eight of these paintings, built from stacked '
          'circles, an X drawn over each eye and in one of them a mouth stitched shut. '
          'It is never the subject. It stands at the foot of the heap, in a row along a '
          'boat, hung upside down in a corner, ranged across a board: present at the '
          'scene and unable to report it.', 'note')
    p.box(X(6), 176, W(6),
          'It is also the answer to the gap in the dates. The canvases stop in 2020 and '
          'start again in 2026, but the figure that opens the book on a chequered board '
          'is the same one drawn in red on paper seven years earlier. What paused was the '
          'painting, not the language.'
          '<p>Where it appears: %s.</p>' % ', '.join('%02d' % c['n'] for c in MOTIF['crops']),
          'note')
    p.rule(ML, 272, CONTENT_W)
    p.box(ML, 274, CONTENT_W, 'Eight works, seven years', 'cap')

    items = []
    for c in MOTIF['crops']:
        w = BY_N[c['n']]
        items.append((w['plate']['src'],
                      '%02d \u00b7 %s \u00b7 %s' % (w['n'], w['year'], c['line']),
                      crop_of(w, c['box'])))
    grid_page('The onlooker', items,
              head=('The onlooker, in each painting it appears in', 'Details'),
              tag='motif', y0=28.0)


def crop_of(w, b):
    """Motif kutusu tablonun kirpilmis hali icinde verilmistir; saklanan
       fotografin icindeki yerine cevirir."""
    pb = w['plate'].get('box') or [0, 0, 1, 1]
    return [pb[0] + b[0] * pb[2], pb[1] + b[1] * pb[3], b[2] * pb[2], b[3] * pb[3]]


motif_pages()

# ══ arka ═════════════════════════════════════════════════════════════
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

# Butun kitap tek sayfada, kucuk: 35 tablo, numaralariyla.
p = page('Index')
p.rule(ML, 15, CONTENT_W, True)
p.box(ML, 17.4, W(6), 'The thirty-five', 'lab')
p.box(R(3), 17.4, W(3), 'Index', 'lab rt')
def index_fits(ncols, span):
    cw = W(span)
    h = 0.0
    for i in range(0, len(WORKS), ncols):
        h += max(cw / x['ar'] for x in WORKS[i:i + ncols]) + 8.5
    return h

ncols, span = 6, 2
for c, sp in ((6, 2), (7, 1), (8, 1)):
    if c * sp <= COLS and index_fits(c, sp) <= FOOT - 30: ncols, span = c, sp; break
cw = W(span)
step = (CONTENT_W - cw) / (ncols - 1)
y = 30.0
for i in range(0, len(WORKS), ncols):
    row = WORKS[i:i + ncols]
    hmax = 0
    for j, w in enumerate(row):
        p.pic(w['plate']['src'], ML + j * step, y, cw, box=w['plate'].get('box'),
              tag='ix%02d' % w['n'])
        h = cw / w['ar']
        p.box(ML + j * step, y + h + 1.6, cw, '%02d' % w['n'], 'cap')
        hmax = max(hmax, h)
    y += hmax + 8.5

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
for name, i in (('The onlooker', None), ('Colophon', None), ('Index', None)):
    pass
json.dump({'marks': marks, 'pages': len(PAGES), 'short': SHORT},
          open(os.path.join(HERE, 'outline-short.json' if SHORT else 'outline.json'),
               'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

print('pages: %d' % len(PAGES))
print('images: %d' % len(made))
