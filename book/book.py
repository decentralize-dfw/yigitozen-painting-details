# -*- coding: utf-8 -*-
"""
YIĞIT ÖZEN — PAINTINGS SINCE 2019
Kitabi sifirdan kuran motor.

Kitabin tek bir fikri var: her tablo bir acilimdir. Sol sayfa yazidir ve
neredeyse bostur; sag sayfa tablonun kendisidir ve sayfayi doldurur. Otuz
bes acilim boyunca butun tablolar ayni bant icinde, ayni yukseklikte durur,
boylece okur onlari birbiriyle durustce karsilastirir.

Kirpma yoktur. Bir gorsel sayfa kenarina dayanabilir; kenardan tasip
icerigini kaybedemez. Tek istisna kapaktir.

    python3 book.py ../../yigit/works.json
    node print.js && python3 post.py
"""
import os, sys, json, math, hashlib
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', 'yigit'))
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
SHORT = '--short' in sys.argv
SRC = os.path.abspath(ARGS[0]) if ARGS else os.path.join(ROOT, 'works.json')
OUT = os.path.join(HERE, 'images')
if not os.path.isdir(OUT): os.makedirs(OUT)

# ── izgara ───────────────────────────────────────────────────────────
PW, PH = 240.0, 320.0
ML = MR = 20.0
MEASURE = PW - ML - MR                    # 200
COLS, GUT = 12, 5.0
COL = (MEASURE - (COLS - 1) * GUT) / COLS  # 12.0833

def X(i): return ML + i * (COL + GUT)
def W(n): return n * COL + (n - 1) * GUT
def R(n): return ML + MEASURE - W(n)

HEAD   = 13.4      # ust micro satiri
HRULE  = 18.4      # ust kural
BAND_T = 20.0      # levha bandi
BAND_H = 272.0     # butun tablolar bu bandin icinde
BAND_B = BAND_T + BAND_H
FRULE  = 272.0     # alt kural
FMICRO = 275.6
FOLIO  = 294.0

# ── gorsel hazirligi ─────────────────────────────────────────────────
# Basilacak genisligi bilerek kesilir: milimetre basina 5.4 piksel, yani
# 137 dpi. Kagitta bunun altina inmek gorunur, ustune cikmak dosyayi
# buyutur ve sayfada bir karsiligi olmaz.
CACHE, MADE = {}, set()

def prep(src, mm, tag, box=None):
    px = int(max(360, min(1360, round(mm * 5.4))))
    key = (src, px, tuple(box) if box else None)
    if key in CACHE: return CACHE[key]
    path = os.path.join(ROOT, src.lstrip('/'))
    im = Image.open(path)
    if im.mode not in ('RGB', 'L'): im = im.convert('RGB')
    if box:
        w, h = im.size
        im = im.crop((int(box[0] * w), int(box[1] * h),
                      int((box[0] + box[2]) * w), int((box[1] + box[3]) * h)))
    ar = im.size[0] / float(im.size[1])
    if im.size[0] > px:
        im = im.resize((px, max(1, int(round(px / ar)))), Image.LANCZOS)
    name = '%s-%d.jpg' % (tag, px)
    im.convert('RGB').save(os.path.join(OUT, name), 'JPEG',
                           quality=76, optimize=True, subsampling=2)
    MADE.add(name)
    CACHE[key] = ('images/' + name, ar)
    return CACHE[key]

def ratio(src, box=None):
    im = Image.open(os.path.join(ROOT, src.lstrip('/')))
    w, h = im.size
    return (box[2] * w) / (box[3] * h) if box else w / float(h)

def phash(src, box=None):
    im = Image.open(os.path.join(ROOT, src.lstrip('/'))).convert('L')
    if box:
        w, h = im.size
        im = im.crop((int(box[0] * w), int(box[1] * h),
                      int((box[0] + box[2]) * w), int((box[1] + box[3]) * h)))
    im = im.resize((8, 8), Image.LANCZOS)
    px = list(im.getdata()); avg = sum(px) / 64.0
    return sum(1 << i for i, v in enumerate(px) if v > avg)

def far(a, b):
    return bin(a ^ b).count('1')

def spread_out(items, thr=9):
    """Birbirine cok benzeyen iki kesit yan yana gelmesin."""
    if len(items) < 3: return items
    hs = [phash(d['src'], d.get('box')) for d in items]
    out, left = [items[0]], list(range(1, len(items)))
    used = [0]
    while left:
        last = hs[used[-1]]
        best = max(left, key=lambda i: far(hs[i], last))
        if far(hs[best], last) < thr:
            best = left[0]
        out.append(items[best]); used.append(best); left.remove(best)
    return out

def e(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('&amp;middot;', '&middot;').replace('&amp;ndash;', '&ndash;')
            .replace('&amp;nbsp;', '&nbsp;').replace('&amp;amp;', '&amp;')
            .replace('&amp;copy;', '&copy;').replace('&amp;lt;em&amp;gt;', '<em>')
            .replace('&lt;em&gt;', '<em>').replace('&lt;/em&gt;', '</em>')
            .replace('&lt;br&gt;', '<br>'))

# ── sayfa ────────────────────────────────────────────────────────────
PAGES = []

class Page(object):
    def __init__(self, run='', klass=''):
        self.run, self.klass, self.bits = run, klass, []
        self.folio = True
    def raw(self, s):
        self.bits.append(s); return self
    def box(self, x, y, w, inner, cls, extra=''):
        self.bits.append('<div class="b %s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;%s">%s</div>'
                         % (cls, x, y, w, extra, inner))
        return self
    def m(self, x, y, w, s, cls=''):   return self.box(x, y, w, s, ('m ' + cls).strip())
    def t(self, x, y, w, s, cls=''):   return self.box(x, y, w, s, ('t ' + cls).strip())
    def d(self, x, y, w, s, cls=''):   return self.box(x, y, w, s, ('d ' + cls).strip())
    def rule(self, x, y, w, thick=False):
        self.bits.append('<div class="r%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm"></div>'
                         % (' t' if thick else '', x, y, w))
        return self
    def pic(self, src, x, y, w, box=None, tag=None, cap=None, capw=None):
        """Genisligi verilen bir gorsel. Yukseklik kendi oranindan cikar."""
        t = tag or hashlib.md5(src.encode()).hexdigest()[:8]
        path, ar = prep(src, w, t, box)
        h = w / ar
        self.raw('<img src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm">'
                 % (path, x, y, w, h))
        if cap:
            cx = max(x, ML) if x < ML else x
            self.m(cx, y + h + 2.4, capw or max(w, W(4)), e(cap), 'g')
        return y + h
    def pich(self, src, x, y, h, box=None, tag=None, cap=None):
        """Yuksekligi verilen bir gorsel; x verilmezse ortalanir."""
        ar = ratio(src, box)
        w = h * ar
        if x is None: x = (PW - w) / 2
        t = tag or hashlib.md5(src.encode()).hexdigest()[:8]
        path, _ = prep(src, w, t, box)
        self.raw('<img src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm">'
                 % (path, x, y, w, h))
        if cap: self.m(max(x, ML), y + h + 2.4, W(6), e(cap), 'g')
        return x, w

def page(run='', klass=''):
    p = Page(run, klass); PAGES.append(p); return p

def head(p, left, right=None, thick=True):
    p.rule(ML, HRULE, MEASURE, thick)
    p.m(ML, HEAD, W(8), left)
    if right: p.m(R(4), HEAD, W(4), right, 'rt g')

# ── veri ─────────────────────────────────────────────────────────────
WORKS = json.load(open(SRC, encoding='utf-8'))
WHERE   = json.load(open(os.path.join(HERE, 'where.json'), encoding='utf-8'))
MOTIFS  = json.load(open(os.path.join(HERE, 'motifs.json'), encoding='utf-8'))
CREDITS = json.load(open(os.path.join(HERE, 'credits.json'), encoding='utf-8'))

NOT_DETAIL = {
    'ciaocapo_detail_6.jpg': 'Another version, on green and blue',
    'ciaocapo_detail_7.jpg': 'The pair in blue and grey',
    'ciaocapo_detail_8.jpg': 'The pair, before the colour',
    'cellularspleens_detail_4.jpg': 'The whole, in another version',
}
NOT_DETAIL_KIND = dict.fromkeys(NOT_DETAIL, 'Version')

for w in WORKS:
    ims = w['images']
    base = lambda i: i['src'].split('/')[-1]
    w['plate']   = ims[0]
    w['details'] = [i for i in ims[1:]
                    if i.get('label') == 'Detail' and base(i) not in NOT_DETAIL]
    w['aside']   = [i for i in ims[1:] if i.get('label') in ('Study', 'Version')
                    or base(i) in NOT_DETAIL]
    w['process'] = [i for i in ims[1:] if i.get('label') == 'In progress']
    w['ar']      = ims[0].get('ar') or ratio(ims[0]['src'], ims[0].get('box'))
    w['run']     = '%s &middot; %s' % (w['year'], w.get('place', ''))

BY_N = {w['n']: w for w in WORKS}
FIRST = {}

def where(d):
    b = d['src'].split('/')[-1]
    return NOT_DETAIL.get(b) or WHERE.get(b, d.get('label', 'Detail'))

def kind(d):
    b = d['src'].split('/')[-1]
    return NOT_DETAIL_KIND.get(b) or d.get('label', 'Study')

def sentence(w, i=0):
    parts = [x.strip() for x in w['note'].replace('; ', '. ').split('. ') if x.strip()]
    s = parts[min(i, len(parts) - 1)]
    return s if s.endswith('.') else s + '.'

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
               'Luxembourg. The whole book, with every detail and the stages of the '
               'newest paintings, is at yigitozen.xyz/artbook.')
BIO = ['Yiğit Özen was born in 1994 in Istanbul and trained as an architect.',
       'The painting dates from 2018 onward. The thirty-five works in this book were made '
       'between 2019 and 2026, across Istanbul, Milan and Luxembourg.',
       'From 2020 the studio work went largely to XR and spatial design, and the canvases '
       'thin out to one commission in 2023 before the painting resumes in 2026. The years '
       'are given as they fall rather than smoothed over.',
       'Alongside the paintings, Özen works as an XR and spatial web designer, and is the '
       'founder of decentralize design in Milan and Virtually Ever After in Luxembourg.']
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

FACETS = ('Colour', 'Composition', 'Hand')

# ══ eserin acilimi ═══════════════════════════════════════════════════
# Sol sayfa yazidir: ustte kunye satiri, ortada baslik, altta paragraf ve
# uc not. Sag sayfa tablodur ve bandi doldurur. Otuz bes acilim bunun
# disina cikmaz; degisen tek sey tablonun kendisidir.

def title_size(t):
    n = len(t)
    return 32 if n <= 26 else 26 if n <= 40 else 20 if n <= 62 else 15

def type_page(w):
    """Isin yazi sayfasi. Ustte kunye ve baslik, ortada beyaz, altta
       paragraf ve uc not: kitabin butun yazi sayfalari bu ritmi tutar."""
    p = page(w['run'])
    head(p, '%02d <i>&middot;</i> %s' % (w['n'], e(w['medium'])), e(w['run']))

    fs = title_size(w['title'])
    p.box(ML, 29.0, W(9), '<em>%s</em>' % e(w['title']), 'd',
          'font-size:%dpt' % fs)
    lines = 1 + int(len(w['title']) * fs * 0.52 / W(9))
    ty = 29.0 + lines * fs * 0.372 + 7.0
    ty = max(ty, 50.0)
    p.rule(ML, ty, W(9))
    p.m(ML, ty + 3.4, W(7),
        e(w['dim']) + ' <i>&middot;</i> ' + e(w.get('dim_in', '')))

    body = '<p>%s</p>' % e(w['note'])
    if w.get('read'):
        body += '<p class="g"><em>%s</em></p>' % e(w['read'])
    p.t(ML, 190.0, W(6), body)

    p.rule(ML, 258.0, MEASURE)
    for i, f in enumerate(FACETS):
        p.m(X(i * 4), 261.6, W(4) - 3, '<b>%s</b><br><i>%s</i>' % (f, e(w['facets'][i])))
    return p


def plate_page(w):
    """Tablonun kendisi. Butun tablolar ayni bandin icinde durur; dik
       olanlar bandin yuksekligini alir, yatik olanlar sayfanin
       genisligini. Hicbiri kirpilmaz."""
    p = page(w['run'], 'plate')
    h = BAND_H
    wd = h * w['ar']
    if wd > PW:
        wd = PW; h = wd / w['ar']
    x = (PW - wd) / 2
    y = BAND_T + (BAND_H - h) / 2
    path, _ = prep(w['plate']['src'], wd, 'p%02d' % w['n'], w['plate'].get('box'))
    p.raw('<img src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm">'
          % (path, x, y, wd, h))
    return p

# ══ detay sayfalari ══════════════════════════════════════════════════
# Dort kompozisyon var, elle kurulmus. Hicbiri kirpmaz, hicbiri ortalamaz,
# hepsi bir kenara ya da bir cizgiye dayanir. Ust uste iki sayfada ayni
# kompozisyon kullanilmaz.

DTOP, DBOT = 26.0, 288.0

def fit(wd, ar, maxh):
    h = wd / ar
    if h > maxh:
        h = maxh; wd = h * ar
    return wd, h

def sheet_head(p, w, label='Detail'):
    head(p, '%02d <i>&middot;</i> %s' % (w['n'], e(w['title'])), label, False)

def c_solo(p, w, ds, tag):
    d = ds[0]; ar = ratio(d['src'], d.get('box'))
    if ar >= 1.0:
        wd, h = fit(PW, ar, 250.0)
        x = (PW - wd) / 2
        y = 40.0
    else:
        h = 250.0; wd = h * ar
        x = (PW - wd) / 2; y = 34.0
    p.pic(d['src'], x, y, wd, d.get('box'), tag + '0')
    p.m(ML, y + h + 3.2, W(8), e(where(d)), 'g')

def c_stack(p, w, ds, tag):
    a, b = ds[0], ds[1]
    wa, ha = fit(W(9), ratio(a['src'], a.get('box')), 124.0)
    wb, hb = fit(W(6), ratio(b['src'], b.get('box')),
                 min(118.0, DBOT - 10.0 - (DTOP + ha + 26.0)))
    p.pic(a['src'], ML, DTOP, wa, a.get('box'), tag + '0')
    p.m(ML, DTOP + ha + 2.8, W(6), e(where(a)), 'g')
    yb = min(DBOT - hb, DTOP + ha + 48.0)
    p.pic(b['src'], ML + MEASURE - wb, yb, wb, b.get('box'), tag + '1')
    p.m(ML + MEASURE - max(wb, W(6)), yb + hb + 2.8, max(wb, W(6)),
        e(where(b)), 'g rt')

def c_drop(p, w, ds, tag):
    a, b = ds[0], ds[1]
    wa, ha = fit(PW, ratio(a['src'], a.get('box')), 162.0)
    xa = (PW - wa) / 2
    p.pic(a['src'], xa, 0.0, wa, a.get('box'), tag + '0')
    p.m(ML, ha + 4.0, W(8), '%02d <i>&middot;</i> %s' % (w['n'], e(where(a))))
    p.m(R(2), ha + 4.0, W(2), 'Detail', 'rt g')
    p.rule(ML, ha + 14.0, MEASURE)
    wb, hb = fit(W(7), ratio(b['src'], b.get('box')), DBOT - 10.0 - (ha + 38.0))
    yb = ha + 38.0
    p.pic(b['src'], ML + MEASURE - wb, yb, wb, b.get('box'), tag + '1')
    p.m(ML + MEASURE - max(wb, W(6)), yb + hb + 2.8, max(wb, W(6)),
        e(where(b)), 'g rt')

def c_pair(p, w, ds, tag):
    """Iki gorsel yan yana, ayni yukseklikte, alt kenarlari bir cizgide.
       Sayfanin ustu bos kalir; asagida duran bir cift gibi okunur."""
    a, b = ds[0], ds[1]
    ara = ratio(a['src'], a.get('box'))
    arb = ratio(b['src'], b.get('box'))
    h = min(158.0, (MEASURE - GUT * 2) / (ara + arb))
    wa, wb = h * ara, h * arb
    ybot = 262.0
    p.pic(a['src'], ML, ybot - h, wa, a.get('box'), tag + '0')
    p.m(ML, ybot + 2.8, max(wa, W(5)), e(where(a)), 'g')
    p.pic(b['src'], ML + MEASURE - wb, ybot - h, wb, b.get('box'), tag + '1')
    p.m(ML + MEASURE - max(wb, W(5)), ybot + 2.8, max(wb, W(5)), e(where(b)), 'g rt')


def c_hero(p, w, ds, tag):
    """Biri buyuk ve dis kenardan tasar, oteki kucuk ve karsi kosede
       durur. Sayfanin agirligi bir yana yatar."""
    a, b = ds[0], ds[1]
    left = (len(PAGES) % 2 == 0)
    ara = ratio(a['src'], a.get('box'))
    wa = 156.0
    ha = wa / ara
    if ha > 244.0:
        ha = 244.0; wa = ha * ara
    ya = 30.0 if ha > 180.0 else 54.0
    xa = 0.0 if left else PW - wa
    p.pic(a['src'], xa, ya, wa, a.get('box'), tag + '0')
    capx = ML if left else PW - wa
    p.m(min(capx, R(6)) if not left else ML, ya + ha + 2.8, W(6),
        e(where(a)), 'g' if left else 'g')
    wb, hb = fit(W(3), ratio(b['src'], b.get('box')), 132.0)
    xb = ML + MEASURE - wb if left else ML
    p.pic(b['src'], xb, ya + 6.0, wb, b.get('box'), tag + '1')
    p.m(ML + MEASURE - W(3) if left else ML, ya + 6.0 + hb + 2.8, W(3),
        e(where(b)), 'g rt' if left else 'g')


def c_row(p, w, ds, tag):
    """Uc gorsel bir sirada, ayni yukseklikte, alt kenarlari bir cizgide."""
    ars = [ratio(d['src'], d.get('box')) for d in ds[:3]]
    h = min(132.0, (MEASURE - GUT * 4) / sum(ars))
    ybot = 246.0
    x = ML
    for k, d in enumerate(ds[:3]):
        wd = h * ars[k]
        p.pic(d['src'], x, ybot - h, wd, d.get('box'), tag + str(k))
        p.m(x, ybot + 2.8, max(wd, W(3)), e(where(d)), 'g')
        x += wd + GUT * 2
    return p


def c_ladder(p, w, ds, tag):
    a, b, c = ds[0], ds[1], ds[2]
    wa, ha = fit(W(8), ratio(a['src'], a.get('box')), 118.0)
    p.pic(a['src'], ML + MEASURE - wa, DTOP, wa, a.get('box'), tag + '0')
    p.m(ML + MEASURE - max(wa, W(6)), DTOP + ha + 2.8, max(wa, W(6)),
        e(where(a)), 'g rt')
    wb, hb = fit(W(4), ratio(b['src'], b.get('box')), ha)
    p.pic(b['src'], ML, DTOP + ha - hb, wb, b.get('box'), tag + '1')
    p.m(ML, DTOP + ha + 2.8, W(5), e(where(b)), 'g')
    yc = DTOP + ha + 36.0
    wc, hc = fit(W(7), ratio(c['src'], c.get('box')), 268.0 - yc)
    p.pic(c['src'], ML, 268.0 - hc, wc, c.get('box'), tag + '2')
    p.m(ML, 270.8, W(7), e(where(c)), 'g')


def c_frieze(p, w, ds, tag):
    a, b, c = ds[0], ds[1], ds[2]
    wa, ha = fit(PW, ratio(a['src'], a.get('box')), 158.0)
    xa = (PW - wa) / 2
    p.pic(a['src'], xa, 0.0, wa, a.get('box'), tag + '0')
    p.m(ML, ha + 4.0, W(8), '%02d <i>&middot;</i> %s' % (w['n'], e(where(a))))
    p.m(R(2), ha + 4.0, W(2), 'Detail', 'rt g')
    p.rule(ML, ha + 14.0, MEASURE)
    yb = ha + 40.0
    hh = min(118.0, DBOT - 10.0 - yb)
    for i, d in enumerate((b, c)):
        wd, hd = fit(W(6), ratio(d['src'], d.get('box')), hh)
        x = ML if i == 0 else ML + MEASURE - wd
        p.pic(d['src'], x, yb, wd, d.get('box'), tag + str(i + 1))
        p.m(ML if i == 0 else R(6), yb + hd + 2.8, W(6), e(where(d)),
            'g' if i == 0 else 'g rt')

BLEEDS = {c_drop, c_frieze}
COMPS = {1: [c_solo],
         2: [c_stack, c_drop, c_pair, c_hero],
         3: [c_ladder, c_frieze, c_row]}
ROT = {1: 0, 2: 0, 3: 0}

def detail_sheet(w, ds, i):
    n = min(3, len(ds))
    ds = list(ds[:n])
    fns = COMPS[n]
    fn = fns[ROT[n] % len(fns)]
    ROT[n] += 1
    if fn in BLEEDS:
        wide = [k for k, d in enumerate(ds) if ratio(d['src'], d.get('box')) >= 1.15]
        if wide:
            ds.insert(0, ds.pop(wide[0]))
        else:
            fn = [f for f in fns if f not in BLEEDS][0]
    p = page(w['run'])
    if fn not in BLEEDS:
        sheet_head(p, w, 'Detail')
    fn(p, w, ds, 'w%02dd%d' % (w['n'], i))
    return p

def chunks(n):
    """Bir eserin detaylari sayfalara boyle dagilir: uceri ve ikiseri."""
    if n <= 3: return [n] if n else []
    out = []
    while n > 4:
        out.append(3); n -= 3
    if n == 4: out += [2, 2]
    elif n: out.append(n)
    return out

# ══ surec, etud, ara sayfa ═══════════════════════════════════════════

def process_sheet(w, part, i, total, base=0):
    """Bir tablonun asamalari. Kitapta izgaranin yeri yalniz burasi:
       bunlar levha degil bir siradir, ve bir kontak baski gibi sayfayi
       bastan asagi doldurur."""
    p = page(w['run'])
    sheet_head(p, w, 'Process')
    avail = (FRULE - 10.0) - DTOP
    ars = [ratio(d['src'], d.get('box')) for d in part]
    best = None
    for c in (2, 3, 4, 5):
        if c > len(part): break
        gap = 6.0
        cw = (MEASURE - (c - 1) * gap) / c
        rows = int(math.ceil(len(part) / float(c)))
        bs = [part[r * c:(r + 1) * c] for r in range(rows)]
        hs = [max(cw / ratio(d['src'], d.get('box')) for d in band) for band in bs]
        tot = sum(hs) + gap * (rows - 1)
        if tot > avail: continue
        if best is None or tot > best[0]: best = (tot, c, cw, gap, rows, hs, bs)
    if best is None:
        c, gap = 5, 6.0
        cw = (MEASURE - 4 * gap) / 5
        rows = int(math.ceil(len(part) / 5.0))
        bs = [part[r * 5:(r + 1) * 5] for r in range(rows)]
        hs = [cw / min(ars) for _ in range(rows)]
        best = (sum(hs) + gap * (rows - 1), c, cw, gap, rows, hs, bs)
    tot, c, cw, gap, rows, hs, bands = best
    y = DTOP + max(0.0, (avail - tot) / 2.0)
    note, k = None, 0
    for r, band in enumerate(bands):
        x = ML
        for d in band:
            p.pic(d['src'], x, y, cw, d.get('box'), 'w%02dp%02d' % (w['n'], base + k))
            note = CREDITS.get(d['src'].split('/')[-1]) or note
            x += cw + gap; k += 1
        y += hs[r] + gap
    p.rule(ML, FRULE, MEASURE)
    p.m(ML, FMICRO, W(7),
        ('Stages %d&ndash;%d of %d' % (base + 1, base + len(part), total))
        if total > len(part) else '%d stages, first to last' % total)
    if note: p.m(R(5), FMICRO, W(5), e(note), 'rt g')
    return p


def study_sheet(w, part, i):
    p = page(w['run'])
    sheet_head(p, w, 'Studies and versions')
    p.m(ML, 24.0, MEASURE, '', 'g')
    n = min(3, len(part))
    fn = {1: c_solo, 2: c_pair, 3: c_row}[n]
    fn(p, w, list(part[:n]), 'w%02ds%d' % (w['n'], i))
    return p


def interleaf(w, spare):
    """Sayfa sayisi denk gelmediginde acilan sayfa bos kalmaz. Elde
       kullanilmamis bir detay varsa tam genislikte o gelir; yoksa isin
       kendi cumlesi buyuk punto ile."""
    p = page(w['run'])
    if spare:
        d = spare
        ar = ratio(d['src'], d.get('box'))
        if ar >= 1.0:
            wd, h = fit(PW, ar, 240.0)
            x, y = (PW - wd) / 2, (PH - h) / 2 - 10
        else:
            h = 244.0; wd = h * ar
            x, y = (PW - wd) / 2, 32.0
        p.pic(d['src'], x, y, wd, d.get('box'), 'w%02di' % w['n'])
        p.m(ML, y + h + 3.2, W(8),
            '%02d <i>&middot;</i> %s' % (w['n'], e(where(d))), 'g')
    else:
        head(p, '%02d <i>&middot;</i> %s' % (w['n'], e(w['title'])), 'From the note', False)
        p.d(ML, 132.0, W(9), e(sentence(w, 1)), 'l')
        p.rule(ML, FRULE, MEASURE)
        p.m(ML, FMICRO, W(6), e(w['run']))
    return p

# ══ on sayfalar ══════════════════════════════════════════════════════
COVER_SRC = '/img/full/detail/7famboardgame_detail_3.jpg'

p = page('', 'dark')
p.folio = False
cpath, car = prep(COVER_SRC, 240, 'cover')
ch = 240.0 / car
p.raw('<img src="%s" style="left:0;top:0;width:240mm;height:%.2fmm">' % (cpath, ch))
p.m(ML, ch + 8.0, W(6), 'Yiğit Özen')
p.m(R(4), ch + 8.0, W(4), 'Thirty-five works', 'rt')
p.rule(ML, ch + 16.0, MEASURE, True)
p.d(ML, 208.0, W(10), 'Paintings<br>since 2019', 'l')
p.rule(ML, 292.0, MEASURE)
p.m(ML, 295.4, W(6), 'Istanbul <i>&middot;</i> Milan <i>&middot;</i> Luxembourg')
p.m(R(3), 295.4, W(3), 'yigitozen.xyz', 'rt')

p = page('Imprint')
head(p, 'Imprint', 'Yiğit Özen')
p.d(ML, 29.0, W(9), 'Thirty-five<br>paintings', 's')
p.rule(ML, 68.0, W(9))
p.m(ML, 71.4, W(7), '2019&ndash;2026 <i>&middot;</i> Istanbul, Milan and Luxembourg')
p.t(ML, 190.0, W(6), e(SHORT_BLURB if SHORT else BLURB))
p.rule(ML, 258.0, MEASURE)
p.m(ML, 261.6, W(4), '<b>Medium</b><br><i>Acrylic on canvas, on carton and on paper, '
    'and one drawing in charcoal</i>')
p.m(X(4), 261.6, W(4), '<b>Order</b><br><i>Newest first, so the seven years are read '
    'backwards</i>')
p.m(X(8), 261.6, W(4), '<b>Rights</b><br><i>All works &copy; Yiğit Özen. '
    'All rights reserved</i>')

p = page('Paintings since 2019')
p.m(ML, HEAD, W(6), 'Yiğit Özen')
p.m(R(4), HEAD, W(4), 'Istanbul <i>&middot;</i> Milan <i>&middot;</i> Luxembourg', 'rt g')
p.rule(ML, HRULE, MEASURE, True)
p.d(ML, 118.0, W(11), 'Paintings<br>since<br>2019', 'xl')
p.rule(ML, 262.0, MEASURE)
p.m(ML, 265.4, W(5), 'Thirty-five works')
p.m(R(4), 265.4, W(4), 'Newest first', 'rt g')

MEAS6 = W(6)
X6 = (PW - MEAS6) / 2
p = page('On the work')
p.m(X6, HEAD, MEAS6, 'On the work', 'ct')
p.t(X6, 30.0, MEAS6, '<p>%s</p><p>%s</p><p>%s</p>' % (e(P1), e(P2), e(P3)), 'j')
p.m(X6, 246.0, MEAS6, 'On the work', 'ct')
p.rule(X6 + MEAS6 / 2 - 12, 254.0, 24.0)
p.m(X6, 288.0, MEAS6, 'Text by the artist', 'ct g')

p = page('On the work', 'plate')
_esrc = '/img/full/detail/viperella_detail_1.jpg'
_ear = ratio(_esrc)
_eh = min(272.0, PW / _ear)
p.pich(_esrc, None, 24.0 + (272.0 - _eh) / 2, _eh, None, 'essay')
p.m(ML, 306.0, W(9), '15 <i>&middot;</i> Viperella, the head and the raised hand', 'g')

por = '/img/portrait.jpg'
p = page('Biography')
head(p, 'Biography', 'Yiğit Özen')
p.pic(por, R(6), 29.0, W(6), None, 'portrait')
p.d(ML, 29.0, W(5), 'Yiğit<br>Özen', 's')
p.rule(ML, 68.0, W(5))
p.m(ML, 71.4, W(5), 'Born 1994, Istanbul')
p.t(ML, 190.0, W(6), ''.join('<p>%s</p>' % e(x) for x in BIO))
p.rule(ML, FRULE, MEASURE)
p.m(ML, FMICRO, W(5), 'Painter and spatial designer')
p.m(R(4), FMICRO, W(4), 'Studio, Luxembourg', 'rt g')

p = page('Biography')
head(p, 'Exhibitions and talks', 'Selected')
y = 34.0
for h4, rows in CV:
    p.m(ML, y, W(4), h4)
    yy = y
    for a, b in rows:
        p.m(X(4), yy, W(7), e(a), 'g')
        p.m(R(1), yy, W(1), b, 'rt g')
        yy += 6.6
    y = yy + 14.0
    p.rule(ML, y - 8.0, MEASURE)
p.m(ML, FMICRO, W(8), 'The painting and the design practice are listed apart', 'g')
p.rule(ML, FRULE, MEASURE)

TOC = [page('Contents'), page('Contents')]

# ══ eserler ══════════════════════════════════════════════════════════
# Yil ayraci yok: yil zaten her sayfanin dibinde yazar. Isler kesintisiz,
# yeniden eskiye. Her is bir acilimla baslar ve acilim hep ayni yerdedir,
# yani her isin yazi sayfasi cift, tablosu tek sayfa numarasina duser.

def proc_chunks(n):
    if n <= 12: return [n] if n else []
    k = int(math.ceil(n / 12.0))
    base, rem = divmod(n, k)
    return [base + 1] * rem + [base] * (k - rem)

def split_one(cs):
    """Sayfa sayisini bir artirmak icin en buyuk yigini ikiye ayirir."""
    if not cs: return None
    i = max(range(len(cs)), key=lambda j: cs[j])
    if cs[i] < 2: return None
    out = list(cs)
    out[i] = cs[i] - 1
    out.insert(i + 1, 1)
    return out

SELECT = [1, 2, 3, 5, 8, 15, 22, 35]
SEQ = WORKS if not SHORT else [w for w in WORKS if w['n'] in SELECT]

for w in SEQ:
    FIRST[w['n']] = len(PAGES) + 1
    type_page(w)
    plate_page(w)
    if SHORT:
        if w['details']:
            detail_sheet(w, spread_out(w['details'])[:3], 0)
            detail_sheet(w, spread_out(w['details'])[3:5] or w['details'][:2], 1)
        continue

    ds = spread_out(w['details']) if len(w['details']) > 2 else list(w['details'])
    dc = chunks(len(ds))
    pc = proc_chunks(len(w['process']))
    ac = chunks(len(w['aside']))
    if (len(dc) + len(pc) + len(ac)) % 2:
        alt = split_one(dc)
        if alt: dc = alt
        else:
            alt = split_one(ac)
            if alt: ac = alt
    at = 0
    for i, k in enumerate(dc):
        detail_sheet(w, ds[at:at + k], i); at += k
    at = 0
    for i, k in enumerate(pc):
        process_sheet(w, w['process'][at:at + k], i, len(w['process']), at); at += k
    at = 0
    for i, k in enumerate(ac):
        study_sheet(w, w['aside'][at:at + k], i); at += k
    if len(PAGES) % 2 == 0:
        interleaf(w, None)

# ══ dizin ════════════════════════════════════════════════════════════
def index_grid(run):
    p = page(run)
    head(p, 'The thirty-five', 'Index', False)
    NC, Y0, CAP, RG, FT = 7, 34.0, 6.0, 10.0, 22.0
    rows = [WORKS[i:i + NC] for i in range(0, len(WORKS), NC)]
    nr = len(rows)
    step = MEASURE / NC
    cw = step - GUT
    bh = ((FRULE - FT - Y0) - nr * CAP - (nr - 1) * RG) / nr
    y = Y0
    for row in rows:
        for j, wk in enumerate(row):
            iw = min(cw, bh * wk['ar']); ih = iw / wk['ar']
            x = ML + j * step
            path, _ = prep(wk['plate']['src'], iw, 'ix%02d' % wk['n'],
                           wk['plate'].get('box'))
            p.raw('<img src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm">'
                  % (path, x, y + bh - ih, iw, ih))
            p.m(x, y + bh + 1.6, cw, '%02d' % wk['n'], 'g')
        p.rule(ML, y + bh + CAP + RG / 2 - 1.0, MEASURE)
        y += bh + CAP + RG
    p.rule(ML, FRULE, MEASURE)
    p.m(ML, FMICRO, W(8), 'Every plate at one height, in the order of the book')
    p.m(R(2), FMICRO, W(2), '35 works', 'rt g')
    return p

if not SHORT:
    p = page('Index')
    p.m(ML, HEAD, W(6), 'Index')
    p.m(R(4), HEAD, W(4), '2019&ndash;2026', 'rt g')
    p.rule(ML, HRULE, MEASURE, True)
    p.d(ML, 128.0, W(10), 'The<br>thirty-five', 'l')
    p.rule(ML, 262.0, MEASURE)
    p.m(ML, 265.4, W(9), 'Made across Istanbul, Milan and Luxembourg')
    index_grid('Index')

# ══ tekrar edenler ═══════════════════════════════════════════════════
def crop_of(wk, b):
    pb = wk['plate'].get('box') or [0, 0, 1, 1]
    return [pb[0] + b[0] * pb[2], pb[1] + b[1] * pb[3], b[2] * pb[2], b[3] * pb[3]]

def motif_text(sec):
    p = page(sec['name'])
    p.m(ML, HEAD, W(6), 'A recurring figure')
    p.m(R(4), HEAD, W(4), e(sec['range']), 'rt g')
    p.rule(ML, HRULE, MEASURE, True)
    p.d(ML, 118.0, W(8), e(sec['name']), 'l')
    p.t(ML, 186.0, W(7), '<p>%s</p><p>%s</p><p>%s</p>'
        % (e(sec['lead']), e(sec['a']), e(sec['b'])))
    p.rule(ML, FRULE, MEASURE)
    p.m(ML, FMICRO, W(4), '%d works' % len(sec['crops']))
    p.m(X(4), FMICRO, W(8),
        ' <i>&middot;</i> '.join('%02d' % c['n'] for c in sec['crops']), 'g')
    return p

def motif_pics(sec):
    p = page(sec['name'])
    head(p, e(sec['name']) + ', in every painting it appears in', 'Details', False)
    items = [(BY_N[c['n']], c) for c in sec['crops']]
    Y0, CAPH, RG, FT = 34.0, 9.6, 12.0, 20.0
    cols = 2
    rows = int(math.ceil(len(items) / float(cols)))
    cellw = (MEASURE - GUT * 2) / cols
    step = cellw + GUT * 2
    bh = ((FRULE - FT - Y0) - rows * CAPH - (rows - 1) * RG) / rows
    y = Y0
    for r in range(rows):
        band = items[r * cols:(r + 1) * cols]
        for j, (wk, c) in enumerate(band):
            bx = crop_of(wk, c['box'])
            ar = ratio(wk['plate']['src'], bx)
            iw = min(cellw, bh * ar); ih = iw / ar
            x = ML + j * step
            path, _ = prep(wk['plate']['src'], iw,
                           'm-%s%02d' % (sec['key'], r * cols + j), bx)
            p.raw('<img src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm">'
                  % (path, x, y + bh - ih, iw, ih))
            p.m(x, y + bh + 1.8, cellw,
                '%02d <i>&middot;</i> %s <i>&middot;</i> %s'
                % (c['n'], wk['year'], e(c['line'])), 'g')
        if r < rows - 1:
            p.rule(ML, y + bh + CAPH + RG / 2 - 1.0, MEASURE)
        y += bh + CAPH + RG
    return p

if not SHORT:
    p = page('The recurring')
    p.m(ML, HEAD, W(6), 'Six things that come back')
    p.m(R(4), HEAD, W(4), '2019&ndash;2026', 'rt g')
    p.rule(ML, HRULE, MEASURE, True)
    p.d(ML, 128.0, W(10), 'The<br>recurring', 'l')
    p.rule(ML, 262.0, MEASURE)
    p.m(ML, 265.4, W(10),
        ' <i>&middot;</i> '.join(x['name'] for x in MOTIFS['sections']))

    q = page('The recurring')
    head(q, 'What comes back', 'Contents', False)
    RY0, RG2 = 36.0, 13.0
    ns = len(MOTIFS['sections'])
    ih = ((FRULE - 10.0 - RY0) - (ns - 1) * RG2) / ns
    yy = RY0
    for sec in MOTIFS['sections']:
        c = sec['crops'][0]; wk = BY_N[c['n']]
        bx = crop_of(wk, c['box'])
        iw = min(W(5), ih * ratio(wk['plate']['src'], bx))
        path, _ = prep(wk['plate']['src'], iw, 'rc-' + sec['key'], bx)
        q.raw('<img src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm">'
              % (path, ML, yy, iw, ih))
        q.d(X(6), yy - 1.4, W(4), e(sec['name']), 's')
        q.m(X(6), yy + 9.0, W(5), e(sec['lead']), 'g')
        q.m(R(1), yy - 1.0, W(1), '%02d' % len(sec['crops']), 'rt g')
        if sec is not MOTIFS['sections'][-1]:
            q.rule(ML, yy + ih + RG2 / 2 - 1.0, MEASURE)
        yy += ih + RG2

for sec in (MOTIFS['sections'][:1] if SHORT else MOTIFS['sections']):
    motif_text(sec)
    motif_pics(sec)

# ══ kunye ════════════════════════════════════════════════════════════
p = page('Colophon')
head(p, 'Colophon', 'Yiğit Özen')
p.t(ML, 40.0, W(5),
    '<p>All works by Yiğit Özen, born 1994 in Istanbul and trained as an architect. '
    'Works are given newest first, so a paragraph that says a thing happens for the '
    'first time means the first time reading backwards through the book.</p>'
    '<p>Dimensions are width by height, in centimetres.</p>'
    '<p>Photography by the artist. Plates and details reproduce documentation of the '
    'paintings; colour and surface differ from the works themselves.</p>')
p.t(X(6), 40.0, W(6),
    '<p>Where a paragraph gives a proportion or a percentage, it was measured on the '
    'documentation file rather than on the painting, and it describes that file. No '
    'colour target was used in the photography, so the figures are a reading of the '
    'photograph and not a colorimetric claim about the paint.</p>'
    '<p>The epigraph on 03 is Tony Soprano, <em>The Sopranos</em>, HBO. The first frame '
    'of the process pages on 02 and 03 is a reference the painting was begun from and '
    'is credited on the page it appears.</p>'
    '<p>A technical catalogue of the same works, with the full index, is published '
    'separately.</p>'
    '<p>All works &copy; Yiğit Özen. All rights reserved.</p>')
p.rule(ML, FRULE, MEASURE)
p.m(ML, FMICRO, W(4), 'x@yigitozen.xyz')
p.m(X(4), FMICRO, W(4), 'Instagram @yjgjf')
p.m(R(4), FMICRO, W(4), 'yigitozen.xyz <i>&middot;</i> de-centralize.com', 'rt g')

if not SHORT:
    last = page('', 'plate')
    last.folio = False
    last.raw('<img class="mark" src="images/logo.svg">')

# ══ icindekiler ══════════════════════════════════════════════════════
def toc(p, items, head_t):
    head(p, head_t, 'Thirty-five works')
    y = 34.0
    for wk in items:
        p.m(ML, y, W(1), '%02d' % wk['n'])
        p.m(X(1), y, W(7), '<i>%s</i>' % e(wk['title']), '')
        p.m(X(8), y, W(2), e(wk['year']), 'g')
        p.m(R(1), y, W(1), str(FIRST.get(wk['n'], 0)), 'rt')
        p.rule(ML, y + (10.6 if len(wk['title']) > 52 else 6.0), MEASURE)
        y += 12.6 if len(wk['title']) > 52 else 8.0
    p.rule(ML, FRULE, MEASURE)
    p.m(ML, FMICRO, W(8), 'Each work opens on a spread: the note, then the painting')

half = 18
toc(TOC[0], WORKS[:half], 'Contents')
toc(TOC[1], WORKS[half:], 'Contents')

# ══ yaz ══════════════════════════════════════════════════════════════
out = ['<!doctype html>', '<html lang="en">', '<head>', '<meta charset="utf-8">',
       '<title>Yiğit Özen &mdash; Paintings since 2019</title>',
       '<link rel="stylesheet" href="book.css">', '</head>', '<body>', '']
for i, p in enumerate(PAGES, start=1):
    side = 'L' if i % 2 == 0 else 'R'
    foot = ''
    if p.folio:
        if side == 'L':
            foot = ('<div class="b f" style="left:%.2fmm;top:%.2fmm;width:%.2fmm">%d</div>'
                    '<div class="b m g" style="left:%.2fmm;top:%.2fmm;width:%.2fmm">%s</div>'
                    % (ML, FOLIO, W(3), i, X(2), FOLIO + 3.4, W(6), p.run or 'Yiğit Özen'))
        else:
            foot = ('<div class="b f rt" style="left:%.2fmm;top:%.2fmm;width:%.2fmm">%d</div>'
                    '<div class="b m g rt" style="left:%.2fmm;top:%.2fmm;width:%.2fmm">%s</div>'
                    % (R(3), FOLIO, W(3), i, R(9), FOLIO + 3.4, W(6), p.run or 'Yiğit Özen'))
    out.append('<section class="pg %s%s">%s%s</section>'
               % (side, (' ' + p.klass if p.klass else ''), ''.join(p.bits), foot))
    out.append('')
out += ['</body>', '</html>', '']
open(os.path.join(HERE, 'book-short.html' if SHORT else 'book.html'),
     'w', encoding='utf-8').write('\n'.join(out))

marks = [('Cover', 1), ('Imprint', 2), ('Paintings since 2019', 3),
         ('On the work', 4), ('Biography', 6), ('Contents', 8)]
marks = [(n, i) for n, i in marks if i <= len(PAGES)]
for wk in SEQ:
    marks.append(('%02d  %s' % (wk['n'], wk['title']), FIRST[wk['n']]))
first_run = {}
for i, p in enumerate(PAGES, start=1):
    if p.run and p.run not in first_run: first_run[p.run] = i
for name in ['Index', 'The recurring'] + [x['name'] for x in MOTIFS['sections']] + ['Colophon']:
    if name in first_run: marks.append((name, first_run[name]))
json.dump({'marks': marks, 'pages': len(PAGES), 'short': SHORT},
          open(os.path.join(HERE, 'outline-short.json' if SHORT else 'outline.json'),
               'w', encoding='utf-8'), ensure_ascii=False, indent=1)

print('pages: %d' % len(PAGES))
print('images: %d' % len(MADE))
