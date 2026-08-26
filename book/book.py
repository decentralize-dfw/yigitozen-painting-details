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
import os, sys, re, json, math, hashlib
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', 'yigit'))
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
SHORT = '--short' in sys.argv
SRC = os.path.abspath(ARGS[0]) if ARGS else os.path.join(ROOT, 'works.json')
OUT = os.path.join(HERE, 'images')
if not os.path.isdir(OUT): os.makedirs(OUT)

# ── izgara ───────────────────────────────────────────────────────────
# Kesim 240 x 320. Kenar boslugu ic ve dista farklidir, yani sol ve sag
# sayfanin olcusu ayni degildir; olcu genisligi ikisinde de 204 mm.
PW, PH = 240.0, 320.0
MT, MB = 18.0, 22.0            # ust, alt
MOUT, MIN_ = 16.0, 20.0        # dis, ic (sirt)
MEASURE = PW - MOUT - MIN_     # 204
COLS, GUT = 12, 4.0
COLW = (MEASURE - (COLS - 1) * GUT) / COLS      # 13.333
BLEED = 5.0

# Dort yatay register. Her gorselin ust kenari bunlardan birine oturur.
LINE = 5.0                     # taban cizgisi
REG = [MT, MT + 13 * LINE, MT + 26 * LINE, MT + 39 * LINE]   # 18, 83, 148, 213
REG_END = MT + 52 * LINE       # 278

HEAD   = 11.6
HRULE  = 16.4
FRULE  = 284.0
FMICRO = 287.4
FOLIO  = 299.0

BAND_T, BAND_H = MT, REG_END - MT          # levha bandi: 18..278
BAND_B = BAND_T + BAND_H
DTOP, DBOT = REG[0], REG_END               # detay sayfasinin calisma alani

def W(n):  return n * COLW + (n - 1) * GUT

# Olcek yasasi: alti kademe, arasi yok.
STEPS = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
STEP_COL = {'XS': 3, 'S': 4, 'M': 6, 'L': 9, 'XL': 12, 'XXL': None}
STEP_MM = dict((k, (PW + 2 * BLEED) if v is None else W(v))
               for k, v in STEP_COL.items())

def step_area(step, ar):
    """Kademenin sayfada kapladigi alan, mm kare."""
    if step == 'XXL': return (PW + 2 * BLEED) * (PH + 2 * BLEED)
    w = STEP_MM[step]
    return w * (w / ar)

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

# Buyuk harfe cevrilen her yerde ad elle yazilir: CSS'in uppercase'i
# Turkce i'yi noktasiz I yapar ve ad yanlis cikar.
NM = 'Y\u0130\u011e\u0130T \u00d6ZEN'


def e(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('&amp;middot;', '&middot;').replace('&amp;ndash;', '&ndash;')
            .replace('&amp;nbsp;', '&nbsp;').replace('&amp;amp;', '&amp;')
            .replace('&amp;copy;', '&copy;').replace('&amp;lt;em&amp;gt;', '<em>')
            .replace('&lt;em&gt;', '<em>').replace('&lt;/em&gt;', '</em>')
            .replace('&lt;br&gt;', '<br>'))

# ── sayfa ────────────────────────────────────────────────────────────
PAGES = []
CUR = [None]

class Page(object):
    def __init__(self, run='', klass=''):
        self.run, self.klass, self.bits = run, klass, []
        self.folio = True
        self.no = len(PAGES) + 1
        self.verso = (self.no % 2 == 0)          # cift sayfa: sol
        self.ml = MOUT if self.verso else MIN_
        self.mr = MIN_ if self.verso else MOUT
    def X(self, i): return self.ml + i * (COLW + GUT)
    def R(self, n): return self.ml + MEASURE - W(n)
    def raw(self, s):
        self.bits.append(s); return self
    def box(self, x, y, w, inner, cls, extra=''):
        self.bits.append('<div class="b %s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;%s">%s</div>'
                         % (cls, x, y, w, extra, inner))
        return self
    def m(self, x, y, w, s, cls='', ex=''):
        return self.box(x, y, w, s, ('m ' + cls).strip(), ex)
    def t(self, x, y, w, s, cls='', ex=''):
        return self.box(x, y, w, s, ('t ' + cls).strip(), ex)
    def d(self, x, y, w, s, cls='', ex=''):
        return self.box(x, y, w, s, ('d ' + cls).strip(), ex)
    def rule(self, x, y, w, thick=False):
        self.bits.append('<div class="r%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm"></div>'
                         % (' t' if thick else '', x, y, w))
        return self
    def img(self, src, x, y, w, h=None, box=None, tag=None):
        t = tag or hashlib.md5((src + str(box)).encode()).hexdigest()[:8]
        path, ar = prep(src, w, t, box)
        if h is None: h = w / ar
        self.raw('<img src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm">'
                 % (path, x, y, w, h))
        return y + h
    def pic(self, src, x, y, w, box=None, tag=None, cap=None, capw=None):
        y2 = self.img(src, x, y, w, None, box, tag)
        if cap:
            self.m(max(x, self.ml), y2 + 2.4, capw or max(w, W(4)), e(cap), 'g')
        return y2
    def pich(self, src, x, y, h, box=None, tag=None, cap=None):
        ar = ratio(src, box)
        w = h * ar
        if x is None: x = (PW - w) / 2
        self.img(src, x, y, w, h, box, tag)
        if cap: self.m(max(x, self.ml), y + h + 2.4, W(6), e(cap), 'g')
        return x, w

def page(run='', klass=''):
    p = Page(run, klass); PAGES.append(p); CUR[0] = p; return p

def use(p):
    CUR[0] = p; return p

def X(i):  return CUR[0].X(i)
def R(n):  return CUR[0].R(n)

def head(p, left, right=None, thick=True):
    p.rule(X(0), HRULE, MEASURE, thick)
    p.m(X(0), HEAD, W(8), left)
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
      'left underneath the stack. At the edges a small onlooker sits with an X drawn over each eye, and '
      'in one painting its mouth is stitched shut as well, so the witness is cancelled '
      'before anything can be reported. Scale works as a verdict, one face given as a person and the rest reduced '
      'to signs, sometimes a face replaced by a number.')
BLURB = ('Thirty-five works made since 2019 across Istanbul, Milan and Luxembourg: '
         'acrylic on canvas, on carton and on paper, and one drawing in charcoal on the '
         'reverse of a canvas. They are given here newest first, and a small figure with '
         'crossed eyes runs through them from one end of the seven years to the other.')
SHORT_BLURB = ('Eight of thirty-five works made since 2019 across Istanbul, Milan and '
               'Luxembourg. The whole book, with every detail and the stages of the '
               'newest paintings, is at yigitozen.xyz/artbook.')
BIO = ['Yiğit Özen was born in 1994 in Istanbul and trained as an architect.',
       'Özen has painted since 2018. The thirty-five works in this book were made between '
       '2019 and 2026, across Istanbul, Milan and Luxembourg.',
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


# Notu bir alintiyla baslayan isler icin kaynak. Kaynak alintinin altinda
# durur; yuz sayfa sonraki kunyede degil.
QUOTE_SRC = {3: 'Tony Soprano, <i>The Sopranos</i>, HBO, season one, 1999'}


def type_page(w):
    """Isin yazi sayfasi. Ustte kunye, baslik, olculer ve paragraf tek bir
       blok halinde; ortada beyaz; altta uc not ve iri folyo. Otuz bes
       yazi sayfasi bu ritmi tutar."""
    p = page(w['run'])
    head(p, '%02d <i>&middot;</i> %s' % (w['n'], e(w['medium'])), e(w['run']))

    fs = title_size(w['title'])
    p.box(X(0), 29.0, W(9), '<em>%s</em>' % e(w['title']), 'd',
          'font-size:%dpt' % fs)
    cpl = W(9) / (0.176 * fs)          # 1 mm'ye dusen harf: yaklasik
    lines = max(1, int(math.ceil(len(w['title']) / cpl)))
    ty = max(29.0 + lines * 0.367 * fs + 7.0, 50.0)
    p.rule(X(0), ty, W(9))
    p.m(X(0), ty + 3.4, W(7),
        e(w['dim']) + ' <i>&middot;</i> ' + e(w.get('dim_in', '')))

    y = ty + 17.0
    if w['note'].lstrip().startswith('\u201c'):
        # Alinti kitaptaki tek italik govdedir; yorum duz kalir.
        p.box(X(0), y, W(6), e(w['note']), 'q')
        qh = 5.2 * math.ceil(len(w['note']) / 45.0) + 2.0
        src = QUOTE_SRC.get(w['n'])
        if src:
            p.box(X(0), y + qh + 2.6, W(6), src, 'src')
            qh += 12.0
        if w.get('read'):
            p.t(X(0), y + qh + 5.0, W(6), e(w['read']))
            qh += 5.0 + 4.5 * math.ceil(len(w['read']) / 52.0)
    else:
        body = '<p>%s</p>' % e(w['note'])
        if w.get('read'):
            body += '<p>%s</p>' % e(w['read'])
        p.t(X(0), y, W(6), body)
        nch = len(w['note']) + (len(w.get('read') or '') + 26 if w.get('read') else 0)
        qh = math.ceil(nch / 52.0) * 4.5

    # 6.4 — metin bloğu dikeyde tek parcadir: baslik, olcu, not ve uc not
    # arasinda 12 mm'den fazla bosluk kalmaz. Artan bosluk sayfanin
    # altina toplanir, ortasina degil.
    fy = min(y + qh + 12.0, 236.0)
    p.rule(X(0), fy, MEASURE)
    for i, f in enumerate(FACETS):
        p.m(X(i * 4), fy + 3.6, W(4) - 3,
            '<b>%s</b><br><i>%s</i>' % (f, e(w['facets'][i])))
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
# Alti arketip vardir, yedincisi yoktur. Her gorsel alti kademeden birine
# atanir; ara boy yoktur. Her gorselin ust kenari bir register cizgisine
# oturur, alt kenar serbesttir. Bosluk tek parcadir ve en az iki sayfa
# kenarina dayanir; kosegen yerlesim yasaktir.

def crop_of(wk, b):
    """Motif kutusu kirpilmis tablonun icinde verilmistir; saklanan
       fotografin icindeki yerine cevirir."""
    pb = wk['plate'].get('box') or [0, 0, 1, 1]
    return [pb[0] + b[0] * pb[2], pb[1] + b[1] * pb[3], b[2] * pb[2], b[3] * pb[3]]


def in_motifs(w):
    return [(sec, c) for sec in MOTIFS['sections']
            for c in sec['crops'] if c['n'] == w['n']]


def px_of(src, box=None):
    im = Image.open(os.path.join(ROOT, src.lstrip('/')))
    return im.size[0] * (box[2] if box else 1.0)


def cap_step(c):
    """Kesit kagitta 3.8 piksel/mm'nin altina dusmez; tam sayfa levha
       icin 5.2, yani 250 mm'de 1300 piksel."""
    px = px_of(c['src'], c.get('box'))
    out = 'XS'
    for st in STEPS:
        need = 5.2 if st == 'XXL' else 3.8
        if STEP_MM[st] * need <= px: out = st
    return out


def widen(c, need_px):
    """Bir kesiti buyuk basmak icin kutusunu genisletir: buyutmek yerine
       daha genis bir alan alinir. Genisleme tablonun kendi sinirinda
       durur, yoksa fotografin icindeki duvar da kadraja girer."""
    b = c.get('box')
    if not b: return c
    lim = c.get('limit') or [0.0, 0.0, 1.0, 1.0]
    full = px_of(c['src'], lim)
    if px_of(c['src'], b) >= need_px or full < need_px: return c
    k = min(lim[2] / b[2], need_px / px_of(c['src'], b))
    nw = min(lim[2], b[2] * k); nh = min(lim[3], b[3] * k)
    nx = min(max(lim[0], b[0] - (nw - b[2]) / 2), lim[0] + lim[2] - nw)
    ny = min(max(lim[1], b[1] - (nh - b[3]) / 2), lim[1] + lim[3] - nh)
    d = dict(c); d['box'] = [nx, ny, nw, nh]
    d['tag'] = c['tag'] + 'w'
    d['cap'] = cap_step(d)
    return d


def clause(w, k):
    """Kunyenin ikinci yarisi: o kadrajda elin ne yaptigi. Isin kendi uc
       notundan alinir, sirayla, boylece ayni is icinde tekrarlanmaz."""
    f = w['facets'][k % 3]
    for sep in (', the ', '; ', ', and ', ', with '):
        f = f.split(sep)[0]
    if len(f) > 46: f = f[:44].rsplit(' ', 1)[0]
    return f[0].upper() + f[1:]


def caption(w, c, step):
    loc = c['loc']
    loc = loc[0].upper() + loc[1:]
    if c.get('again'):
        return e(loc) + ' &mdash; ' + c['again']
    if STEPS.index(step) < 2:                 # XS ve S: yalniz konum
        return e(loc) + (' &deg;' if c.get('echo') else '')
    t = loc + ' \u2014 ' + clause(w, c['k'])
    if len(t) > 90: t = t[:88].rsplit(' ', 1)[0] + '\u2026'
    return e(t) + (' &deg;' if c.get('echo') else '')


def material(w):
    """Bir isin detay malzemesi: cekilmis detaylar, sonra o tablonun
       tekrar eden figurleri. Ikincisi Recurring bolumunde de basilir, ve
       kunyesinde bir derece isareti tasir."""
    out = []
    for d in spread_out(w['details']) if len(w['details']) > 2 else w['details']:
        out.append({'src': d['src'], 'box': d.get('box'), 'loc': where(d),
                    'echo': None})
    for sec, c in in_motifs(w):
        out.append({'src': w['plate']['src'], 'box': crop_of(w, c['box']),
                    'loc': c['line'], 'echo': sec['key'],
                    'limit': w['plate'].get('box') or [0, 0, 1, 1]})
    for k, c in enumerate(out):
        c['k'] = k
        c['cap'] = cap_step(c)
        c['tag'] = 'w%02dc%d' % (w['n'], k)
    return out


def at_most(c, step):
    """Cozunurluk elverdigi en buyuk kademe."""
    i = min(STEPS.index(step), STEPS.index(c['cap']))
    return STEPS[max(i, 0)]


def place(p, c, step, x, y, w=None, h=None):
    """Bir kesiti verilen kademede yerlestirir. XXL sayfayi tasar ve
       kenarindan kesilir; oteki kademelerde kirpma yoktur."""
    if step == 'XXL':
        path, _ = prep(c['src'], 250, c['tag'] + 'X', c.get('box'))
        p.raw('<img class="cut" src="%s" style="left:%.2fmm;top:%.2fmm;'
              'width:%.2fmm;height:%.2fmm">' % (path, x, y, w, h))
        return y + h
    wd = STEP_MM[step]
    return p.img(c['src'], x, y, wd, None, c.get('box'), c['tag'] + step)


# ── A · THE PLATE ───────────────────────────────────────────────────
def a_plate(p, w, cs, tag):
    c = widen(cs[0], 250 * 5.2)
    IH = 288.0 + BLEED
    place(p, c, 'XXL', -BLEED, -BLEED, PW + 2 * BLEED, IH)
    p.m(p.X(0), 291.0, W(8), '%02d <i>&middot;</i> %s' % (w['n'], e(w['title'])))
    p.m(p.R(2), 291.0, W(2), 'Detail', 'rt g')
    p.m(p.X(0), 296.6, W(10), caption(w, c, 'XXL'), 'g')
    return ['XXL']


# ── B · THE JUMP ────────────────────────────────────────────────────
def b_jump(p, w, cs, tag, corner=False):
    """Ustte buyuk, altta XS, ayni sol kenara hizali; aralarinda en az
       26 mm. Bosluk saga dogru acilir. Nakarat kipinde buyuk asagi,
       kucuk sag ust kosedeki sabit yerine gecer: sol-ust'ten sag-alt'a
       kosegen kurulmaz."""
    big, small = cs[0], cs[1]
    ar = ratio(big['src'], big.get('box'))
    bs = 'M'
    for st in ('XL', 'L', 'M', 'S'):
        if STEPS.index(st) > STEPS.index(at_most(big, 'XL')): continue
        if STEP_MM[st] / ar <= 196.0: bs = st; break
    bw = STEP_MM[bs]; bh = bw / ar
    sw = STEP_MM['XS']
    sh = sw / ratio(small['src'], small.get('box'))

    if corner:
        by = DBOT - bh - 8.0
        p.img(big['src'], p.X(0), by, bw, None, big.get('box'), big['tag'] + bs)
        p.m(p.X(0), by + bh + 2.6, W(9), caption(w, big, bs), 'g')
        sy = REG[0]
        room = by - sy - 26.0
    else:
        p.img(big['src'], p.X(0), REG[0], bw, None, big.get('box'), big['tag'] + bs)
        p.m(p.X(0), REG[0] + bh + 2.6, W(9), caption(w, big, bs), 'g')
        sy = next((r for r in REG if r >= REG[0] + bh + 26.0), None)
        if sy is None: sy = min(REG[0] + bh + 30.0, DBOT - 60.0)
        room = DBOT - sy - 8.0

    sx = p.R(3) if corner else p.X(0)
    if sh > room:
        sh = max(24.0, min(room, sw * 1.4))
        path, _ = prep(small['src'], sw, small['tag'] + 'XSb', small.get('box'))
        p.raw('<img class="cut" src="%s" style="left:%.2fmm;top:%.2fmm;'
              'width:%.2fmm;height:%.2fmm">' % (path, sx, sy, sw, sh))
    else:
        p.img(small['src'], sx, sy, sw, None, small.get('box'), small['tag'] + 'XSb')
    p.m(p.R(4) if corner else sx, sy + sh + 2.6, W(4),
        caption(w, small, 'XS'), 'g rt' if corner else 'g')
    return [bs, 'XS']


# ── C · THE STACK ───────────────────────────────────────────────────
def c_stack(p, w, cs, tag):
    n = len(cs)
    for st in ('M', 'S', 'XS'):
        wd = STEP_MM[st]
        hs = [wd / ratio(c['src'], c.get('box')) for c in cs]
        if sum(hs) + (n - 1) * 4.0 + n * 5.0 <= DBOT - REG[0]: break
    y = REG[0]
    for c in cs:
        h = wd / ratio(c['src'], c.get('box'))
        p.img(c['src'], p.X(0), y, wd, None, c.get('box'), c['tag'] + st)
        p.m(p.X(0) + wd + 4.0, y, W(5), caption(w, c, st), 'g')
        y += h + 4.0 + 5.0
    return [st] * n


# ── D · THE STRIP ───────────────────────────────────────────────────
def d_strip(pl, pr, w, c, tag, again=None):
    """Serimi bastan basa gecen yatay bant. Kesitten bir serit alinir;
       serit, kesitin kendisi gibi, isin bir parcasidir."""
    H = 108.0
    SPAN = PW * 2 + 2 * BLEED
    # Serit kaynagin butun genisligini alir; yalnizca yukseklikten kirpilir.
    # Boylece 490 mm'ye yayilan bant en cok piksele sahip olur.
    b = c.get('box') or [0, 0, 1, 1]
    lim = c.get('limit') or ([0.0, 0.0, 1.0, 1.0] if c.get('box') is None
                             else [0.0, 0.0, 1.0, 1.0])
    b = [lim[0], b[1], lim[2], b[3]]
    full_ar = ratio(c['src'], b)
    want = SPAN / H
    if full_ar >= want:
        nb = list(b)
    else:
        keep_h = (full_ar / want) * b[3]
        nb = [lim[0], min(max(lim[1], b[1] + (b[3] - keep_h) / 2.0),
                          lim[1] + lim[3] - keep_h), lim[2], keep_h]
    top = REG[1]
    path, _ = prep(c['src'], SPAN, c['tag'] + 'D', nb)
    pl.raw('<img src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm">'
           % (path, -BLEED, top, SPAN, H))
    pr.raw('<img src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm">'
           % (path, -BLEED - PW, top, SPAN, H))
    if c.get('echo'): ECHO_STEP.setdefault((w['n'], c['echo']), 'XXL')
    cc = dict(c); cc['again'] = again
    use(pl)
    pl.m(pl.X(0), top + H + 3.0, W(9), caption(w, cc, 'XXL'), 'g')
    use(pr)
    pr.m(pr.X(0), top + H + 3.0, W(6),
         '%02d <i>&middot;</i> %s' % (w['n'], e(w['title'])))
    pr.m(pr.R(3), top + H + 3.0, W(3), 'A band across the spread', 'rt g')
    return ['XXL']


# ── E · THE FIELD ───────────────────────────────────────────────────
def e_field(p, w, cs, tag):
    n = len(cs)
    cols = 4
    cell = (MEASURE - (cols - 1) * 4.0) / cols          # 48
    rows = int(math.ceil(n / float(cols)))
    y = DBOT - 24.0 - rows * (cell + 4.0) + 4.0
    for i, c in enumerate(cs):
        x = p.X(0) + (i % cols) * (cell + 4.0)
        yy = y + (i // cols) * (cell + 4.0)
        path, _ = prep(c['src'], cell, c['tag'] + 'F', c.get('box'))
        p.raw('<img class="cut" src="%s" style="left:%.2fmm;top:%.2fmm;'
              'width:%.2fmm;height:%.2fmm">' % (path, x, yy, cell, cell))
    ybot = y + rows * (cell + 4.0) - 4.0
    p.rule(p.X(0), ybot + 4.0, MEASURE)
    per = int(math.ceil(n / 3.0))
    for col in range(3):
        part = cs[col * per:(col + 1) * per]
        if not part: continue
        p.m(p.X(col * 4), ybot + 7.0, W(4) - 3,
            '<br>'.join('%d <i>&middot;</i> %s%s'
                        % (col * per + j + 1, e(c['loc']),
                           ' &deg;' if c.get('echo') else '')
                        for j, c in enumerate(part)), 'g')
    return ['XS'] * n


# ── F · THE WELD ────────────────────────────────────────────────────
def f_weld(p, w, cs, tag):
    """Iki gorsel birebir ayni boyda, sifir oluk, birbirine yapisik ve
       iki yandan tasar: tek gorsel gibi okunur."""
    a, b = cs[0], cs[1]
    span = PW + 2 * BLEED
    wd = span / 2.0
    h = min(wd / ratio(a['src'], a.get('box')), wd / ratio(b['src'], b.get('box')))
    h = min(h, 210.0)
    top = REG[0]
    for i, c in enumerate((a, b)):
        path, _ = prep(c['src'], wd, c['tag'] + 'W', c.get('box'))
        p.raw('<img class="cut" src="%s" style="left:%.2fmm;top:%.2fmm;'
              'width:%.2fmm;height:%.2fmm">' % (path, -BLEED + i * wd, top, wd, h))
    p.m(p.X(0), top + h + 3.0, W(5), caption(w, a, 'M'), 'g')
    p.m(p.R(5), top + h + 3.0, W(5), caption(w, b, 'M'), 'g rt')
    return ['M', 'M']


ARCH = {'A': a_plate, 'B': b_jump, 'C': c_stack, 'E': e_field, 'F': f_weld}


def chunks(n):
    """Etudler sayfalara boyle dagilir: uceri ve ikiseri."""
    if n <= 3: return [n] if n else []
    out = []
    while n > 4:
        out.append(3); n -= 3
    if n == 4: out += [2, 2]
    elif n: out.append(n)
    return out


def sheet_head(p, w, label='Detail'):
    head(p, '%02d <i>&middot;</i> %s' % (w['n'], e(w['title'])), label, False)


ECHO_STEP = {}             # (is, motif) -> eserler bolumunde basildigi kademe

REFRAIN = (3, 15, 27)      # ucunde ayni kademe ayni kosede: hizli
                           # cevirmede nabiz


def detail_page(w, kind, cs, i, last=False):
    p = page(w['run'])
    if kind != 'A':
        sheet_head(p, w, 'Detail' if len(cs) == 1 else 'Details')
    if kind == 'B':
        steps = b_jump(p, w, cs, 'w%02dd%d' % (w['n'], i),
                       corner=(w['n'] in REFRAIN and last))
    else:
        steps = ARCH[kind](p, w, cs, 'w%02dd%d' % (w['n'], i))
    for c, st in zip(cs, steps + [steps[-1]] * 4):
        if c.get('echo'):
            ECHO_STEP.setdefault((w['n'], c['echo']), st)
    p.arch, p.steps = kind, steps
    return p


def allot(w, crops):
    """Detay sayfasi sayisi: yuzey, tekrar eden figur ve surec dizisi.
       Cekilmis detayi olan is en az bir sayfa alir; 2026 isleri, malzeme
       yetiyorsa, tekrar mekanigi icin dort alir."""
    m = re.findall(r'([\d.]+)', w['dim'])
    area = (float(m[0]) * float(m[1])) / 10000.0 if len(m) >= 2 else 0.0
    sc = (1 if area > 0.7 else 0) + len(in_motifs(w)) + (1 if w['process'] else 0)
    n = 0 if sc == 0 else 1 if sc <= 2 else 2 if sc <= 4 else 3
    if crops: n = max(n, 1)
    if w['year'] == '2026' and len(crops) >= 5: n = max(n, 4)
    return min(n, len(crops) + 1)


def detail_run(w, crops):
    """Bir isin detay dizisi. Her serimde tam sayfa bir levha ya da bir
       serit bulunur, yani her serimin bir oznesi vardir. Ayni arketip ne
       ayni serimde iki kez ne de art arda iki serimde gelir; dizi en
       kucuk gorselle biter; acilis kesiti bir kez daha, kucuk ve butun."""
    n = allot(w, crops)
    if not n or not crops: return []
    rest = list(crops)
    lead = max(rest, key=lambda c: (STEPS.index(c['cap']), -c['k']))
    rest.remove(lead)
    wide = (w['ar'] >= 1.3
            and px_of(lead['src'], lead.get('limit')) >= 1900)

    if n <= 1:
        return [('A', [lead])]

    out = [('A', [lead])]
    # ilk serimin sag sayfasi: eldeki malzemeye gore
    if len(rest) >= 6:
        out.append(('E', rest[:8])); rest = rest[8:]
    elif len(rest) >= 3:
        out.append(('C', rest[:4])); rest = rest[4:]
    elif len(rest) >= 2:
        out.append(('F', rest[:2])); rest = rest[2:]
    elif len(rest) == 1:
        out.append(('B', [rest[0], lead])); rest = []
    else:
        out.append(('B', [lead, lead]))

    while len(out) < n:
        if rest:
            second = rest.pop(0)
            out.append(('D', [second]) if wide else ('A', [second]))
            if len(out) < n:
                if len(rest) >= 2:
                    out.append(('B', rest[:2])); rest = rest[2:]
                elif rest:
                    out.append(('B', [rest.pop(0), lead]))
                else:
                    out.append(('B', [lead, lead]))
        else:
            break

    # 5.1 tekrar: acilis kesiti, son sayfada, kucuk ve butun halinde
    if len(out) >= 3:
        again = dict(lead)
        again['again'] = 'The same place, whole'
        again['tag'] = lead['tag'] + 'r'
        k, cs = out[-1]
        cs = list(cs)
        if k == 'B':
            out[-1] = (k, [cs[0], again])
        elif k in ('C', 'E') and len(cs) < (8 if k == 'E' else 5):
            out[-1] = (k, cs + [again])
    return out


# ══ surec, etud, ara sayfa ═══════════════════════════════════════════

def process_sheet(w, part, i, total, base=0):
    """Bir tablonun asamalari. Kitapta izgaranin yeri yalniz burasi:
       bunlar levha degil bir siradir, ve bir kontak baski gibi sayfayi
       bastan asagi doldurur."""
    p = page(w['run']); p.arch = 'P'
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
        x = X(0)
        for d in band:
            p.pic(d['src'], x, y, cw, d.get('box'), 'w%02dp%02d' % (w['n'], base + k))
            note = CREDITS.get(d['src'].split('/')[-1]) or note
            x += cw + gap; k += 1
        y += hs[r] + gap
    p.rule(X(0), FRULE, MEASURE)
    p.m(X(0), FMICRO, W(5), '%d stages <i>&middot;</i> %d&ndash;%d'
        % (total, base + 1, base + len(part)))
    if note: p.m(X(6), FMICRO, W(6), e(note), 'g')
    return p


def study_sheet(w, part, i):
    """Kokte duran calismalar. Bunlar detay degil, ayri resimlerdir;
       hicbiri kirpilmaz, ve ayni olcek yasasina uyarlar."""
    p = page(w['run']); p.arch = 'S'
    sheet_head(p, w, 'Studies and versions')
    cs = [{'src': a0['src'], 'box': a0.get('box'), 'loc': where(a0),
           'echo': None, 'k': j, 'cap': 'XXL',
           'tag': 'w%02ds%d%d' % (w['n'], i, j)} for j, a0 in enumerate(part)]
    n = len(cs)
    if n == 1:
        c = cs[0]
        ar = ratio(c['src'], c.get('box'))
        wd = STEP_MM['XL']
        if wd / ar > DBOT - REG[0] - 10.0:
            wd = (DBOT - REG[0] - 10.0) * ar
        p.img(c['src'], p.X(0), REG[0], wd, None, c.get('box'), c['tag'])
        p.m(p.X(0), REG[0] + wd / ar + 3.0, W(9), e(c['loc']), 'g')
        p.m(p.R(2), REG[0] + wd / ar + 3.0, W(2), kind(part[0]), 'rt g')
    elif n == 2:
        b_jump(p, w, cs, 'st')
    else:
        c_stack(p, w, cs, 'st')
    return p


INTERLEAVES = []          # sonradan doldurulur: motif sayfalari daha kurulmadi
MOTIF_AT = {}             # motif anahtari -> sayfa numarasi


def interleaf(w):
    """Sayfa sayisi denk gelmediginde acilan sayfa bos ya da tekrar olmaz.
       Isin icinde kitabin tekrar eden figurlerinden biri geciyorsa, o
       figur burada kendi kesitiyle ve bolumunun sayfasiyla verilir."""
    p = page(w['run']); p.arch = 'R'
    INTERLEAVES.append((p, w))
    return p


def fill_interleaf(p, w):
    hits = in_motifs(w)
    if not hits:
        head(p, '%02d <i>&middot;</i> %s' % (w['n'], e(w['title'])), 'From the note', False)
        p.d(X(0), 132.0, W(9), e(sentence(w, 1)), 'l')
        return
    head(p, '%02d <i>&middot;</i> %s' % (w['n'], e(w['title'])),
         'Recurring here', False)
    n = len(hits)
    Y0, TOP = 38.0, FRULE - 16.0
    IW = W(8) if n == 1 else W(6)
    maxh = ((TOP - Y0) - (n - 1) * 16.0) / n
    rows = []
    for sec, c in hits:
        bx = crop_of(w, c['box'])
        ar = ratio(w['plate']['src'], bx)
        iw = min(IW, maxh * ar)
        rows.append((sec, c, bx, iw, iw / ar))
    slack = (TOP - Y0) - sum(r[4] for r in rows)
    gap = max(16.0, slack / (n + 1)) if n > 1 else 0.0
    y = Y0 + (slack * .28 if n == 1 else gap * .5)
    for sec, c, bx, iw, hh in rows:
        path, _ = prep(w['plate']['src'], iw, 'il%02d%s' % (w['n'], sec['key']), bx)
        p.raw('<img src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm">'
              % (path, X(0), y, iw, hh))
        tx = X(9) if n == 1 else X(7)
        tw = W(3) if n == 1 else W(5)
        p.d(tx, y - 1.4, tw, e(sec['name']), 's')
        p.t(tx, y + 11.0, tw, e(c['line'][0].upper() + c['line'][1:]) + '.')
        pg = MOTIF_AT.get(sec['key'])
        if pg:
            p.m(tx, y + hh - 4.0, tw, 'Page %d' % pg, 'g')
        y += hh + gap
    p.rule(X(0), FRULE, MEASURE)
    p.m(X(0), FMICRO, W(9),
        'The figure is followed through all its appearances in the chapter '
        'on what comes back', 'g')


# ══ on sayfalar ══════════════════════════════════════════════════════
COVER_SRC = '/img/full/detail/7famboardgame_detail_3.jpg'

p = page('', 'dark')
p.folio = False
cpath, car = prep(COVER_SRC, 240, 'cover')
ch = 240.0 / car
p.raw('<img src="%s" style="left:0;top:0;width:240mm;height:%.2fmm">' % (cpath, ch))
p.m(X(0), ch + 8.0, W(6), NM)
p.m(R(4), ch + 8.0, W(4), 'Thirty-five works', 'rt')
p.rule(X(0), ch + 16.0, MEASURE, True)
p.d(X(0), 208.0, W(10), 'Paintings<br>since 2019', 'l')
p.rule(X(0), 292.0, MEASURE)
p.m(X(0), 295.4, W(6), 'Istanbul <i>&middot;</i> Milan <i>&middot;</i> Luxembourg')
p.m(R(3), 295.4, W(3), 'yigitozen.xyz', 'rt')

p = page('Imprint')
head(p, 'Imprint', NM)
p.d(X(0), 29.0, W(9), 'Thirty-five<br>paintings', 's')
p.rule(X(0), 68.0, W(9))
p.m(X(0), 71.4, W(7), '2019&ndash;2026 <i>&middot;</i> Istanbul, Milan and Luxembourg')
p.t(X(0), 190.0, W(6), e(SHORT_BLURB if SHORT else BLURB))
p.rule(X(0), 258.0, MEASURE)
p.m(X(0), 261.6, W(4), '<b>Medium</b><br><i>Acrylic on canvas, on carton and on paper, '
    'and one drawing in charcoal</i>')
p.m(X(4), 261.6, W(4), '<b>Order</b><br><i>Newest first, so the seven years are read '
    'backwards</i>')
p.m(X(8), 261.6, W(4), '<b>Rights</b><br><i>All works &copy; Yiğit Özen. '
    'All rights reserved</i>')

if not SHORT:
    p = page('Paintings since 2019')
    p.m(X(0), HEAD, W(6), NM)
    p.m(R(4), HEAD, W(4), 'Istanbul <i>&middot;</i> Milan <i>&middot;</i> Luxembourg', 'rt g')
    p.rule(X(0), HRULE, MEASURE, True)
    p.d(X(0), 118.0, W(11), 'Paintings<br>since<br>2019', 'xl')
    p.rule(X(0), 262.0, MEASURE)
    p.m(X(0), 265.4, W(5), 'Thirty-five works')
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
    p.m(X(0), 306.0, W(9), '15 <i>&middot;</i> Viperella, the head and the raised hand', 'g')

    por = '/img/portrait.jpg'
    p = page('Biography')
    head(p, 'Biography', NM)
    p.pic(por, R(6), 29.0, W(6), None, 'portrait')
    p.d(X(0), 29.0, W(5), 'Yiğit<br>Özen', 's')
    p.rule(X(0), 68.0, W(5))
    p.m(X(0), 71.4, W(5), 'Born 1994, Istanbul')
    p.t(X(0), 190.0, W(6), ''.join('<p>%s</p>' % e(x) for x in BIO))
    p.rule(X(0), FRULE, MEASURE)
    p.m(X(0), FMICRO, W(5), 'Painter and spatial designer')
    p.m(R(4), FMICRO, W(4), 'Studio, Luxembourg', 'rt g')

    p = page('Biography')
    head(p, 'Exhibitions and talks', 'Selected')
    y = 34.0
    for gi, (h4, rows) in enumerate(CV):
        p.rule(X(0), y - 4.0, MEASURE, gi == 0)
        p.m(X(0), y, W(4), h4)
        yy = y
        for a2, b2 in rows:
            p.m(X(4), yy, W(7), e(a2), 'g')
            p.m(R(1), yy, W(1), b2, 'rt g')
            yy += 6.6
        y = yy + 16.0
    p.rule(X(0), FRULE, MEASURE)
    p.m(X(0), FMICRO, W(8),
        'The painting and the design practice are kept apart, and the rules between '
        'them say where one ends')

p = page('How to read this')
MEAS7 = W(7)
X7 = (PW - MEAS7) / 2
p.m(X7, HEAD, MEAS7, 'How this book is arranged', 'ct')
p.t(X7, 34.0, MEAS7,
    '<p>The thirty-five paintings are given newest first, so the seven years '
    'are read backwards. A paragraph that says a thing happens for the first '
    'time means the first time reading backwards through the book.</p>'
    '<p>Every work has a spread of its own. The left page carries the number, '
    'the medium, the title, the dimensions and a paragraph, and at its foot '
    'three notes on colour, composition and hand. The right page carries the '
    'painting, and every painting in the book is reproduced inside one band, '
    'so their sizes on the page can be compared.</p>'
    '<p>Where a work was photographed in detail, its details follow on their '
    'own sheets, each with one line saying where in the painting it is. Where '
    'the stages of the work were photographed, they follow as a contact sheet. '
    'Sheets of paper and earlier paintings of the same scene are given as '
    'studies and versions.</p>'
    '<p>Dimensions are width by height, in centimetres, then in inches.</p>', 'j')
p.m(X7, 246.0, MEAS7, 'Newest first', 'ct')
p.rule(X7 + MEAS7 / 2 - 12, 254.0, 24.0)
p.m(X7, 288.0, MEAS7, '2026 to 2019', 'ct g')

TOC = page('Contents') if not SHORT else None

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

SELECT = [1, 2, 5, 8, 15, 22, 34, 35]
SEQ = WORKS if not SHORT else [w for w in WORKS if w['n'] in SELECT]

ARCH_LOG = []          # denetim icin: hangi sayfada hangi arketip

for w in SEQ:
    FIRST[w['n']] = len(PAGES) + 1
    type_page(w)
    plate_page(w)
    if SHORT:
        continue

    crops = material(w)
    run = detail_run(w, crops)
    pc = proc_chunks(len(w['process']))
    ac = chunks(len(w['aside']))

    # Sayfa sayisi cift olmali: is hep cift sayfada acilir. Denk gelmezse
    # once dizi bir sayfa uzar, olmuyorsa tekrar eden figur sayfasi gelir.
    def total(): return sum(2 if k == 'D' else 1 for k, _ in run) + len(pc) + len(ac)
    # Yatay bir isin tek detay sayfasi, serit olarak iki sayfaya yayilir:
    # hem sayfa sayisi denklesir hem tasma kotasi dolar.
    # Yatay bir isin tek detay sayfasi serit olarak iki sayfaya yayilir:
    # hem serime bir ozne kazandirir hem tasma kotasini doldurur.
    if (total() % 2 and len(run) == 1 and run[0][0] == 'A'
            and w['ar'] >= 1.3
            and px_of(run[0][1][0]['src'],
                      run[0][1][0].get('limit')) >= 1900):
        run = [('D', run[0][1])]
    # Sayfa sayisi denk gelmezse fazladan bir detay sayfasi uydurulmaz:
    # denklestirmeyi, kendi icerigi olan "burada tekrar eden" sayfasi yapar.

    order = list(run)
    procs = []
    if len(order) >= 4 and pc and len(pc) % 2:
        n0 = len(w['process'])
        half = n0 // 2
        pc = [n0 - half, half] if half else pc
    if len(order) >= 4 and pc and len(pc) % 2 == 0:
        procs = [('#P', None)]
        order = order[:2] + procs + order[2:]
    for i, (akind, acs) in enumerate(order):
        if akind == '#P':
            at0 = 0
            for j, k in enumerate(pc):
                process_sheet(w, w['process'][at0:at0 + k], j, len(w['process']), at0)
                at0 += k
            continue
        if akind == 'D':
            pl = page(w['run']); pr = page(w['run'])
            use(pl); sheet_head(pl, w, 'Detail')
            st = d_strip(pl, pr, w, acs[0], 'w%02dd%d' % (w['n'], i))
            pl.arch, pl.steps = 'D', st
            pr.arch, pr.steps = 'D', []
            ARCH_LOG.append((len(PAGES) - 1, w['n'], 'D', st))
        else:
            p = detail_page(w, akind, acs, i, last=(i == len(run) - 1))
            ARCH_LOG.append((len(PAGES), w['n'], akind, p.steps))
    if not procs:
        at = 0
        for i, k in enumerate(pc):
            process_sheet(w, w['process'][at:at + k], i, len(w['process']), at); at += k
    at = 0
    for i, k in enumerate(ac):
        study_sheet(w, w['aside'][at:at + k], i); at += k
    if len(PAGES) % 2 == 0:
        interleaf(w)

# ══ dizin ════════════════════════════════════════════════════════════
def index_grid(run):
    p = page(run); p.arch = 'R'
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
            x = X(0) + j * step
            path, _ = prep(wk['plate']['src'], iw, 'ix%02d' % wk['n'],
                           wk['plate'].get('box'))
            p.raw('<img src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm">'
                  % (path, x, y + bh - ih, iw, ih))
            p.m(x, y + bh + 1.6, cw, '%02d' % wk['n'], 'g')
        p.rule(X(0), y + bh + CAP + RG / 2 - 1.0, MEASURE)
        y += bh + CAP + RG
    p.rule(X(0), FRULE, MEASURE)
    p.m(X(0), FMICRO, W(8), 'Every plate at one width, in the order of the book')
    p.m(R(2), FMICRO, W(2), '35 works', 'rt g')
    return p

if not SHORT:
    p = page('Index')
    p.m(X(0), HEAD, W(6), 'Index')
    p.m(R(4), HEAD, W(4), '2019&ndash;2026', 'rt g')
    p.rule(X(0), HRULE, MEASURE, True)
    p.d(X(0), 128.0, W(10), 'The<br>thirty-five', 'l')
    p.rule(X(0), 262.0, MEASURE)
    p.m(X(0), 265.4, W(9), 'Made across Istanbul, Milan and Luxembourg')
    index_grid('Index')

# ══ tekrar edenler ═══════════════════════════════════════════════════
def motif_text(sec):
    p = page(sec['name']); p.arch = 'R'
    MOTIF_AT[sec['key']] = len(PAGES)
    p.m(X(0), HEAD, W(6), 'A recurring figure')
    p.m(R(4), HEAD, W(4), e(sec['range']), 'rt g')
    p.rule(X(0), HRULE, MEASURE, True)
    p.d(X(0), 118.0, W(8), e(sec['name']), 'l')
    p.t(X(0), 186.0, W(7), '<p>%s</p><p>%s</p><p>%s</p>'
        % (e(sec['lead']), e(sec['a']), e(sec['b'])))
    p.rule(X(0), FRULE, MEASURE)
    p.m(X(0), FMICRO, W(4), '%d works' % len(sec['crops']))
    p.m(X(4), FMICRO, W(8),
        ' <i>&middot;</i> '.join('%02d' % c['n'] for c in sec['crops']), 'g')
    return p

def motif_pics(sec):
    """Figurun gectigi butun tablolardan kesitler. Sayfa, ilk kesitin
       kenardan kenara giden bir bandiyla acilir."""
    p = page(sec['name']); p.arch = 'R'
    c0 = sec['crops'][0]; w0 = BY_N[c0['n']]
    bx0 = crop_of(w0, c0['box'])
    lim0 = w0['plate'].get('box') or [0, 0, 1, 1]
    band = [lim0[0], bx0[1], lim0[2], bx0[3]]
    bar = ratio(w0['plate']['src'], band)
    BH = 84.0
    want = (PW + 2 * BLEED) / BH
    if bar < want:
        kh = (bar / want) * band[3]
        band = [band[0], min(max(lim0[1], band[1] + (band[3] - kh) / 2.0),
                             lim0[1] + lim0[3] - kh), band[2], kh]
    bp0, _ = prep(w0['plate']['src'], PW + 2 * BLEED, 'mb-' + sec['key'], band)
    p.raw('<img class="cut" src="%s" style="left:-5mm;top:-5mm;'
          'width:250mm;height:%.2fmm">' % (bp0, BH + BLEED))
    p.m(X(0), BH + 4.0, W(8),
        e(sec['name']) + ', in every painting it appears')
    p.m(R(2), BH + 4.0, W(2), 'Details', 'rt g')
    p.rule(X(0), BH + 12.0, MEASURE)
    items = [(BY_N[c['n']], c) for c in sec['crops']]
    Y0, CAPH, RG, FT = BH + 18.0, 9.6, 12.0, 20.0
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
            st = ECHO_STEP.get((wk['n'], sec['key']))
            want = STEP_MM.get(st, cellw) if st and st != 'XXL' else cellw
            iw = min(cellw, want, bh * ar); ih = iw / ar
            x = X(0) + j * step
            path, _ = prep(wk['plate']['src'], iw,
                           'm-%s%02d' % (sec['key'], r * cols + j), bx)
            p.raw('<img src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm">'
                  % (path, x, y + bh - ih, iw, ih))
            p.m(x, y + bh + 1.8, cellw,
                '%02d <i>&middot;</i> %s <i>&middot;</i> %s'
                % (c['n'], wk['year'], e(c['line'])), 'g')
        if r < rows - 1:
            p.rule(X(0), y + bh + CAPH + RG / 2 - 1.0, MEASURE)
        y += bh + CAPH + RG
    return p

RECUR_TOC = None


def fill_recur_toc(q):
    head(q, 'What comes back', 'Contents', False)
    RY0, RG2 = 36.0, 13.0
    ns = len(MOTIFS['sections'])
    ih = ((FRULE - 10.0 - RY0) - (ns - 1) * RG2) / ns
    yy = RY0
    for sec in MOTIFS['sections']:
        c = sec['crops'][0]; wk = BY_N[c['n']]
        bx = crop_of(wk, c['box'])
        ar = ratio(wk['plate']['src'], bx)
        iw = min(W(5), ih * ar); hh = iw / ar
        path, _ = prep(wk['plate']['src'], iw, 'rc-' + sec['key'], bx)
        q.raw('<img src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm">'
              % (path, X(0), yy + (ih - hh) / 2, iw, hh))
        q.d(X(6), yy - 1.4, W(4), e(sec['name']), 's')
        q.m(X(6), yy + 9.0, W(5),
            e(sec['lead']) + ' <i>&middot;</i> in %d paintings' % len(sec['crops']), 'g')
        q.m(R(1), yy - 1.0, W(1), str(MOTIF_AT.get(sec['key'], 0)), 'rt')
        if sec is not MOTIFS['sections'][-1]:
            q.rule(X(0), yy + ih + RG2 / 2 - 1.0, MEASURE)
        yy += ih + RG2
    q.rule(X(0), FRULE, MEASURE)
    q.m(X(0), FMICRO, W(8),
        'Ordered by how many paintings the figure appears in, most first')
    q.m(R(2), FMICRO, W(2), 'Page', 'rt g')


if not SHORT:
    # Bolumun acilis sayfasi tam tasmali bir kesit; yazi onun uzerinde.
    p = page('The recurring', 'dark'); p.arch = 'A'
    _rc = MOTIFS['sections'][0]['crops'][0]
    _rw = BY_N[_rc['n']]
    _rp, _x = prep(_rw['plate']['src'], 250, 'recur-open', crop_of(_rw, _rc['box']))
    p.raw('<img class="cut" src="%s" style="left:-5mm;top:-5mm;'
          'width:250mm;height:330mm">' % _rp)
    p.m(X(0), HEAD, W(6), 'Six things that come back')
    p.m(R(4), HEAD, W(4), '2019&ndash;2026', 'rt')
    p.rule(X(0), HRULE, MEASURE, True)
    p.d(X(0), 196.0, W(10), 'The<br>recurring', 'l')
    p.rule(X(0), 262.0, MEASURE)
    p.m(X(0), 265.4, W(10),
        ' <i>&middot;</i> '.join(x['name'] for x in MOTIFS['sections']))

    RECUR_TOC = page('The recurring')

for sec in (MOTIFS['sections'][:1] if SHORT else MOTIFS['sections']):
    motif_text(sec)
    motif_pics(sec)

# ══ kunye ════════════════════════════════════════════════════════════
p = page('Colophon')
head(p, 'Colophon', NM)
p.t(X(0), 40.0, W(5),
    '<p>All works by Yiğit Özen, born 1994 in Istanbul and trained as an architect. '
    'They are given newest first, so a paragraph that says a thing happens for the '
    'first time means the first time reading backwards through the book.</p>'
    '<p>Dimensions are width by height, in centimetres and then in inches.</p>'
    '<p>Photography by the artist. Plates and details reproduce documentation of the '
    'paintings; colour and surface differ from the works themselves. The files are '
    'set at about 137 pixels to the inch of printed width, which is made for reading '
    'and for screens rather than for offset printing.</p>'
    '<p>Detail photography exists for fourteen of the thirty-five. Where it does not, '
    'the work is given its spread and nothing more; no detail has been cropped out of '
    'a plate to fill a page.</p>')
p.t(X(6), 40.0, W(6),
    '<p>Where a paragraph gives a proportion or a percentage, it was measured on the '
    'documentation file rather than on the painting, and it describes that file. No '
    'colour target was used in the photography, so the figures are a reading of the '
    'photograph and not a colorimetric claim about the paint.</p>'
    '<p>Titles are set as the artist writes them, in his spelling and his punctuation. '
    '<em>il sbagliato di rompipalle</em>, <em>sono squalo</em> and <em>caprocorn</em> '
    'are his, not slips of the setting.</p>'
    '<p>Sources for the two borrowed reference images and for the epigraph on 03 are '
    'given on the pages they appear on.</p>'
    '<p>A caption gives where in the painting the crop is, and then what the hand did '
    'there, taken from that work&rsquo;s own note on colour, composition or hand. A '
    'degree sign after a caption means the same crop is printed again in the chapter '
    'on what comes back, so the argument there can be checked against the painting '
    'it came from.</p>'
    '<p>Full-page plates are enlarged to the sheet and cut by its edges. Every one of '
    'them is also printed small and whole elsewhere in the same work, so nothing is '
    'shown only in part.</p>'
    '<p>Set in Inter, under the SIL Open Font License. A short selection of the same '
    'works is published separately for sending; the thirty-five are also at '
    'yigitozen.xyz, where every photograph can be seen at full size.</p>'
    '<p>All works &copy; Yiğit Özen. All rights reserved.</p>')
p.rule(X(0), FRULE, MEASURE)
p.m(X(0), FMICRO, W(4), 'x@yigitozen.xyz')
p.m(X(4), FMICRO, W(4), 'Instagram @yjgjf')
p.m(R(4), FMICRO, W(4), 'yigitozen.xyz <i>&middot;</i> de-centralize.com', 'rt g')

if SHORT:
    index_grid('Index')

if True:
    last = page('', 'plate')
    last.folio = False
    last.raw('<img class="mark" src="images/logo.svg">')

# ══ icindekiler ══════════════════════════════════════════════════════
def toc(p, items, head_t):
    """Otuz bes satir tek sayfada. Basliklar sanatcinin kendi yazimiyla,
       kucuk harfle; buyuk harfe cevrilirse s(t)lop, 7 fam ve otekiler
       kendi bicimlerini kaybeder."""
    head(p, head_t, 'Thirty-five works')
    y = 30.0
    for wk in items:
        two = len(wk['title']) > 76
        p.m(X(0), y + 0.6, W(1), '%02d' % wk['n'])
        p.t(X(1), y, W(7), '<em>%s</em>' % e(wk['title']),
            '', 'font-size:8.2pt;line-height:1.34')
        p.m(X(8), y + 0.6, W(2), e(wk['year']), 'g')
        p.m(R(1), y + 0.6, W(1), str(FIRST.get(wk['n'], 0)), 'rt')
        h = 6.0 + (4.0 if two else 0.0)
        p.rule(X(0), y + h - 1.6, MEASURE)
        y += h
    p.rule(X(0), FRULE, MEASURE)
    p.m(X(0), FMICRO, W(8),
        'Each work opens on a spread: the note on the left, the painting on the right')
    p.m(R(2), FMICRO, W(2), 'Page', 'rt g')

if TOC is not None:
    toc(TOC, WORKS, 'Contents')

# Motif bolumlerinin sayfalari artik belli; ara sayfalar simdi dolar.
for _p, _w in INTERLEAVES:
    fill_interleaf(_p, _w)
if RECUR_TOC is not None:
    fill_recur_toc(RECUR_TOC)

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
                    % (X(0), FOLIO, W(3), i, X(2), FOLIO + 3.4, W(6), p.run or 'Yiğit Özen'))
        else:
            foot = ('<div class="b f rt" style="left:%.2fmm;top:%.2fmm;width:%.2fmm">%d</div>'
                    '<div class="b m g rt" style="left:%.2fmm;top:%.2fmm;width:%.2fmm">%s</div>'
                    % (R(3), FOLIO, W(3), i, R(9), FOLIO + 3.4, W(6), p.run or 'Yiğit Özen'))
    out.append('<section class="pg %s%s" data-arch="%s">%s%s</section>'
               % (side, (' ' + p.klass if p.klass else ''),
                  getattr(p, 'arch', p.klass or 'text'), ''.join(p.bits), foot))
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
