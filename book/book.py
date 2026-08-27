# -*- coding: utf-8 -*-
"""
YIĞIT ÖZEN — PAINTINGS SINCE 2019
Ikinci basim. Kitabi serim serim kuran motor.

Kitabin fikri denetimli kirilmadir: her sayfanin altinda ayni modernist
izgara durur — on iki kolon, 5 mm taban, dort register — ve bu izgara
bilerek, seyrek ve buyuk jestlerle kirilir. Birim sayfa degil serimdir:
her serimde bir egemen oge, sol ile sag arasinda bir iliski, karsisindaki
kutleye cevap veren bir bosluk vardir.

Her is bir acilim serimiyle girer: solda numara, baslik, kunye ve not,
sagda tablonun kirpilmamis kendisi, ustu hep ilk registerde, boyu tuvalin
gercek boyuna gore. Detaylar envanter degil tartisma olarak basilir; her
kesit kitapta bir kez gorunur. Surec bir zaman dizisidir, esit kareler
degil. Tekrar edenler bolumu alti ayri davranistir, tek sablon degil.

    python3 book.py ../../yigit/works.json
    node print.js && python3 post.py
"""
import os, sys, re, json, math, hashlib
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', 'yigit'))
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
SHORT = '--short' in sys.argv
PRINT = '--print' in sys.argv     # baski ustasi: 300 ppi ve gercek tasma
SRC = os.path.abspath(ARGS[0]) if ARGS else os.path.join(ROOT, 'works.json')
OUT = os.path.join(HERE, "images-print" if PRINT else "images")
if not os.path.isdir(OUT): os.makedirs(OUT)

# ── izgara ───────────────────────────────────────────────────────────
# Kesim 240 x 320. Olcu genisligi iki sayfada da 204 mm; ic ve dis kenar
# farkli, yani sol ve sag sayfa ayni sayfa degildir.
PW, PH = 240.0, 320.0
MT, MB = 18.0, 22.0
MOUT, MIN_ = 16.0, 20.0
MEASURE = PW - MOUT - MIN_          # 204
COLS, GUT = 12, 4.0
COLW = (MEASURE - (COLS - 1) * GUT) / COLS
BLEED = 5.0

LINE = 5.0
REG = [MT, MT + 13 * LINE, MT + 26 * LINE, MT + 39 * LINE]   # 18 83 148 213
REG_END = MT + 52 * LINE                                     # 278
BAND_T, BAND_H = MT, REG_END - MT
DBOT = REG_END
HEAD, HRULE = 11.6, 16.4
FRULE, FMICRO = 284.0, 287.4
FOLIO_Y = 302.6

def W(n):  return n * COLW + (n - 1) * GUT

# Uc gorsel sinifi: MON tam sayfaya yakin ya da tasar; SUP 65-153 mm;
# INDEX 48 mm ve yalniz dizin isi gorur. 49-64 mm arasi urkek ara boydur
# ve yasaktir; denetim bunu olcer.
XS, S, M, L, XL = W(3), W(4), W(6), W(9), W(12)   # 48 65 100 153 204

# Bir gorsel ya ipucudur ya ikincildir ya da egemen. Arasi yoktur:
# sayfa alaninin %4 ile %19'u arasinda duran, kenara da yaslanmayan
# tikiz bir gorsel kararsizdir ve denetim onu yakalar.
PAGE_AREA = PW * PH

def w_area(frac, ar, cap=None):
    """Sayfa alaninin verilen oranini kaplayacak genislik."""
    return min(math.sqrt(frac * PAGE_AREA * ar), cap or MEASURE)

PUNCTUM   = 0.028      # ipucu: 240 x 320'de yaklasik 57 mm eninde
SECONDARY = 0.300      # ikincil: karsisindakiyle konusacak kadar buyuk

# ── gorsel hazirligi ─────────────────────────────────────────────────
# Basilacak genislige gore kesilir. Serit gibi cok genis basilan parcalar
# icin tavan yukselir; kaynakta olmayan piksel uydurulmaz, buyutme yoktur.
CACHE, MADE, MANIFEST = {}, set(), {}

# Kagit icin milimetreye 11.81 piksel, yani 300 ppi; ekran icin 8.0, yani
# 203 ppi. Ekran sayisi bir zamanlar 5.4 idi, 137 ppi: ekranda yeterli,
# ama editorde bir resim buyutuldugunde ya da o dosyadan cikti alindiginda
# elde olmayan piksel gorunuyordu. Hicbir dosya buyutulmez: kaynakta
# olmayan piksel uydurulmaz, yalnizca var olan piksel atilmaz.
PPMM  = 11.811 if PRINT else 8.0
SCALE = PPMM / 5.4
QUAL  = 88 if PRINT else 76

# Site turevleri ekran icin kesilmistir; ayni kesitlerin arsiv dosyalari
# bu depoda durur ve cogu daha genistir. Basimda hangisi genisse o
# kullanilir, ama yalniz en-boy orani birebir tutuyorsa.
ARCH = {}

def _stem(path):
    return re.sub(r'[^a-z0-9]', '', os.path.basename(path).rsplit('.', 1)[0].lower())

def _index_archive():
    import glob as _g
    base = os.path.abspath(os.path.join(HERE, os.pardir))
    for f in _g.glob(os.path.join(base, '**', '*'), recursive=True):
        if not os.path.isfile(f): continue
        if f.rsplit('.', 1)[-1].lower() not in ('jpg', 'jpeg', 'png'): continue
        if (os.sep + 'book' + os.sep) in f: continue
        try: wpx, hpx = Image.open(f).size
        except Exception: continue
        st = _stem(f)
        if st not in ARCH or wpx > ARCH[st][1]:
            ARCH[st] = (f, wpx, wpx / float(hpx))
_index_archive()

# Bazi ustalar depoda parcali durur ya da adi tutmaz; elle eslenir.
# Birlestirilmis dosya .masters/ icinde onbelleklenir, depoya girmez.
MASTERS = {
    'virgil-on-virtual-cage-final-final-finalv9.jpg':
        ('masters', 'virgil-on-virtual-cage-RESOLUTION.png'),
}

def _joined_master(folder, name):
    base = os.path.abspath(os.path.join(HERE, os.pardir))
    whole = os.path.join(base, folder, name)
    if os.path.isfile(whole): return whole
    cache = os.path.join(HERE, '.masters')
    out = os.path.join(cache, name)
    if os.path.isfile(out): return out
    import glob as _g
    parts = sorted(_g.glob(whole + '.part*'))
    if not parts: return None
    if not os.path.isdir(cache): os.makedirs(cache)
    with open(out, 'wb') as o:
        for pt in parts:
            with open(pt, 'rb') as f: o.write(f.read())
    return out

BEST = {}

def best_src(src):
    """Ayni kesitin daha genis bir arsiv dosyasi varsa onun yolu."""
    if src in BEST: return BEST[src]
    base = src.split('/')[-1]
    if PRINT and base in MASTERS:
        m = _joined_master(*MASTERS[base])
        if m:
            try:
                site = os.path.join(ROOT, src.lstrip('/'))
                sw, sh = Image.open(site).size
                mw, mh = Image.open(m).size
                if mw > sw and abs(mw / float(mh) - sw / float(sh)) / (sw / float(sh)) < 0.01:
                    BEST[src] = m
                    return m
            except Exception:
                pass
    hit = ARCH.get(_stem(src))
    out = None
    if hit:
        site = os.path.join(ROOT, src.lstrip('/'))
        try:
            sw, sh = Image.open(site).size
            if hit[1] > sw and abs(hit[2] - sw / float(sh)) / (sw / float(sh)) < 0.01:
                out = hit[0]
        except Exception:
            out = hit[0]
    BEST[src] = out
    return out

def prep(src, mm, tag, box=None, hi=1360):
    # Istenen: basilacak milimetrenin ppi karsiligi. Tavan yalnizca
    # dosyayi sinirlamak icindir; kaynakta olmayan piksel uydurulmaz.
    px = int(max(360, min(hi * SCALE * (2.2 if not PRINT else 1.0),
                          round(mm * PPMM))))
    key = (src, px, tuple(box) if box else None)
    if key in CACHE: return CACHE[key]
    path = best_src(src) or os.path.join(ROOT, src.lstrip('/'))
    im = Image.open(path)
    src_w = im.size[0]
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
                           quality=QUAL, optimize=True,
                           subsampling=0 if PRINT else 2)
    MADE.add(name)
    # Kunye: bu kesitin nereden, hangi kadrajla ve kaynakta kac pikselle
    # alindigi. Duzenleyicide bir gorsel buyutulunce onceden kesilmis
    # dosya yetmez; layout-export.py bunu okuyup kaynaktan yeniden keser.
    MANIFEST[name] = {'src': src, 'box': list(box) if box else None,
                      'from': os.path.relpath(path, os.path.dirname(HERE))
                              if path.startswith(os.path.dirname(HERE))
                              else path,
                      'srcpx': src_w, 'px': im.size[0]}
    CACHE[key] = (os.path.basename(OUT) + '/' + name, ar)
    return CACHE[key]

RATIO_CACHE = {}

def ratio(src, box=None):
    key = (src, tuple(box) if box else None)
    if key not in RATIO_CACHE:
        im = Image.open(os.path.join(ROOT, src.lstrip('/')))
        w, h = im.size
        RATIO_CACHE[key] = (box[2] * w) / (box[3] * h) if box else w / float(h)
    return RATIO_CACHE[key]

NM = 'YİĞİT ÖZEN'

def e(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('&amp;middot;', '&middot;').replace('&amp;ndash;', '&ndash;')
            .replace('&amp;nbsp;', '&nbsp;').replace('&amp;amp;', '&amp;')
            .replace('&amp;copy;', '&copy;').replace('&lt;em&gt;', '<em>')
            .replace('&lt;/em&gt;', '</em>').replace('&lt;br&gt;', '<br>')
            .replace('&lt;i&gt;', '<i>').replace('&lt;/i&gt;', '</i>'))

# ── kesit sicili ─────────────────────────────────────────────────────
# Her kesit kitapta bir kez basilir. Levhanin butunu yalniz uc baglamda
# gorunebilir: acilim, dizin, kapanis. Sicil bunu derleme aninda tutar;
# ihlal sayfa degil hata uretir.
USED = {}
PLATE_CTX = ('open', 'index', 'close')

def register(src, box, role, hint=''):
    key = (src.split('/')[-1], tuple(round(v, 3) for v in box) if box else None)
    if role == 'plate':
        got = USED.setdefault(key, set())
        if not isinstance(got, set):
            raise SystemExit('levha ile kesit karisti: %s' % (key,))
        if hint not in PLATE_CTX:
            raise SystemExit('levhanin butunu burada basilmaz: %s %s' % (key, hint))
        if hint in got:
            raise SystemExit('levha ayni baglamda iki kez: %s %s' % (key, hint))
        got.add(hint)
    else:
        if key in USED:
            raise SystemExit('kesit iki kez basiliyor: %s (%s / %s)'
                             % (key, USED[key], hint))
        USED[key] = hint or role

# ── sayfa ────────────────────────────────────────────────────────────
PAGES = []
CUR = [None]

class Page(object):
    def __init__(self, run='', klass=''):
        self.run, self.klass, self.bits = run, klass, []
        self.folio = True
        self.fam = 'E'
        self.no = len(PAGES) + 1
        self.verso = (self.no % 2 == 0)
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
    def sans(self, x, y, w, s, cls='', ex=''):
        return self.box(x, y, w, s, ('sans ' + cls).strip(), ex)
    def d(self, x, y, w, s, cls='', ex=''):
        return self.box(x, y, w, s, ('d ' + cls).strip(), ex)
    def rule(self, x, y, w, thick=False):
        self.bits.append('<div class="r%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm"></div>'
                         % (' t' if thick else '', x, y, w))
        return self
    def vrule(self, x, y, h):
        self.bits.append('<div class="r v" style="left:%.2fmm;top:%.2fmm;height:%.2fmm;width:.35pt"></div>'
                         % (x, y, h))
        return self
    def frame(self, x, y, w, h):
        self.bits.append('<div class="fr" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm"></div>'
                         % (x, y, w, h))
        return self
    def img(self, src, x, y, w, h=None, box=None, tag=None, cls='', hi=1360):
        t = tag or hashlib.md5((src + str(box)).encode()).hexdigest()[:8]
        path, ar = prep(src, w, t, box, hi)
        if h is None: h = w / ar
        self.raw('<img %ssrc="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm">'
                 % (('class="%s" ' % cls) if cls else '', path, x, y, w, h))
        return y + h
    def cover_img(self, src, x, y, w, h, box=None, tag=None, pos='50% 45%', hi=1600):
        t = tag or hashlib.md5((src + str(box) + 'c').encode()).hexdigest()[:8]
        path, _ = prep(src, w, t, box, hi)
        self.raw('<img class="cut" src="%s" style="left:%.2fmm;top:%.2fmm;'
                 'width:%.2fmm;height:%.2fmm;object-position:%s">'
                 % (path, x, y, w, h, pos))
        return y + h

def page(run='', klass=''):
    p = Page(run, klass); PAGES.append(p); CUR[0] = p; return p

def spread(run=''):
    """Bir serim: sol (cift) ve sag (tek) sayfa birlikte acilir. Bir is
       her zaman cift sayfada basladigi icin bu denklik yapisaldir."""
    if len(PAGES) % 2 != 1:
        raise SystemExit('serim tek sayfada acilamaz: sayfa %d' % (len(PAGES) + 1))
    pl = page(run); pr = page(run)
    return pl, pr

def use(p):
    CUR[0] = p; return p

def X(i):  return CUR[0].X(i)
def R(n):  return CUR[0].R(n)

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

def det(w, i):
    suf = '_detail_%d.jpg' % i
    for d in w['details'] + w['aside']:
        if d['src'].endswith(suf): return d
    raise SystemExit('detay yok: %02d %s' % (w['n'], suf))

def proc(w, i):
    return w['process'][i - 1]

def aside(w, name):
    for a in w['aside']:
        if name in a['src']: return a
    raise SystemExit('etud yok: %02d %s' % (w['n'], name))

def where(d):
    if isinstance(d, dict) and d.get('line'): return d['line']
    b = d['src'].split('/')[-1]
    return NOT_DETAIL.get(b) or WHERE.get(b, d.get('label', 'Detail'))

def crop_of(wk, b):
    """Motif ya da okuma kutusu kirpilmis tuvalin icinde verilir;
       fotograf icindeki yerine cevirir."""
    pb = wk['plate'].get('box') or [0, 0, 1, 1]
    return [pb[0] + b[0] * pb[2], pb[1] + b[1] * pb[3], b[2] * pb[2], b[3] * pb[3]]

def clause(w, k):
    f = w['facets'][k % 3]
    for sep in (', the ', '; ', ', and ', ', with '):
        f = f.split(sep)[0]
    if len(f) > 46: f = f[:44].rsplit(' ', 1)[0]
    return f[0].upper() + f[1:]

def cap_line(w, d, k=0, prefix=''):
    loc = where(d)
    t = loc[0].upper() + loc[1:] + ' — ' + clause(w, k)
    if len(t) > 96: t = t[:94].rsplit(' ', 1)[0] + '…'
    return (prefix + ' <i>&middot;</i> ' if prefix else '') + e(t)

def loc_line(d):
    """Karsi-gorselin kunyesi yalniz konumdur: el notu egemene aittir."""
    loc = where(d)
    return e(loc[0].upper() + loc[1:])

# ── olcek: tuvalin gercek boyu sayfadaki boyunu belirler ─────────────
# 100 x 160 cm bant boyu basilir, 29.7 x 42 cm kucuk kalir. Dogruluk
# hiyerarsinin kendisidir; hicbir levha bandin ortasinda yuzmez, ustu
# hep ilk registerdedir.
def plate_size(w, k=1.0):
    m = re.findall(r'([\d.]+)', w['dim'])
    wcm, hcm = float(m[0]), float(m[1])
    ar = w['ar']
    if ar <= 1.05:
        h = min(BAND_H, 111.0 + 0.93 * hcm)
        if w['n'] == 20: h = BAND_H          # anitsal: kitabin en buyuk tuvali
        wd = h * ar
        if wd > MEASURE: wd = MEASURE; h = wd / ar
    else:
        wd = min(MEASURE, 111.0 + 0.93 * wcm)
        h = wd / ar
    return wd * k, h * k

def put_plate(p, w, k=1.0, ctx='open', outer=True):
    register(w['plate']['src'], None, 'plate', ctx)
    wd, h = plate_size(w, k)
    if w['ar'] > 1.05:
        x = p.X(0)
    else:
        x = (PW - p.mr - wd) if (outer and not p.verso) else p.X(0)
    p.img(w['plate']['src'], x, REG[0], wd, None, w['plate'].get('box'),
          'p%02d' % w['n'] if k == 1.0 else 'p%02dk' % w['n'], cls='pl')
    return x, wd, h

# ── yazi bloklari ────────────────────────────────────────────────────
def title_size(t):
    n = len(t)
    return 42 if n <= 14 else 32 if n <= 26 else 25 if n <= 40 else 19 if n <= 62 else 15

def title_lines(t, fs, wmm):
    cpl = wmm / (0.176 * fs)
    words, lines, cur = t.split(' '), 1, 0
    for wd in words:
        add = len(wd) + (1 if cur else 0)
        if cur + add > cpl and cur:
            lines += 1; cur = len(wd)
        else:
            cur += add
    return lines

def serif_h(chars, wmm, pt=10.8):
    cpl = wmm / (0.170 * pt)
    return math.ceil(chars / cpl) * (0.494 * pt)

def micro_h(chars, wmm):
    cpl = wmm / 1.57
    return math.ceil(chars / cpl) * 3.92

QUOTE_SRC = {3: 'Tony Soprano, <i>The Sopranos</i>, HBO, season one, 1999'}

def work_block(p, w, y, x0=None, meas=None, tfs=None):
    """Isin kunye blogu: numara, baslik, olculer, not, uc not. Tek dikey
       kutle; artan bosluk sayfanin dibine toplanir, ortasina degil."""
    x0 = p.X(0) if x0 is None else x0
    meas = W(7) if meas is None else meas
    p.m(x0, y, meas, '%02d' % w['n'], 'wn')
    y += 7.0
    fs = tfs or title_size(w['title'])
    tl = title_lines(w['title'], fs, meas)
    p.box(x0, y, meas, e(w['title']), 'd', 'font-size:%dpt' % fs)
    y += tl * 0.367 * fs + 5.5
    p.rule(x0, y, min(meas, W(7)))
    y += 3.2
    meta = '%s <i>&middot;</i> %s <i>&middot;</i> %s <i>&middot;</i> %s' % (
        e(w['medium']), e(w['dim']), e(w.get('dim_in', '')), e(w['run']))
    p.m(x0, y, meas, meta, 'g')
    y += micro_h(len(re.sub(r'<[^>]*>', '', meta)), meas) + 5.0
    note = w['note']
    if note.lstrip().startswith('“') and w['n'] in QUOTE_SRC:
        cut = note.find('”') + 1
        q, rest = note[:cut], note[cut:].strip(' .')
        p.box(x0, y, meas, e(q), 'q')
        y += serif_h(len(q), meas, 13.4) * 1.02 + 4.0
        p.m(x0, y, meas, QUOTE_SRC[w['n']], 'g')
        y += 8.0
        if rest:
            p.t(x0, y, meas, e(rest) + '.')
            y += serif_h(len(rest), meas) + 4.0
    else:
        p.t(x0, y, meas, e(note))
        y += serif_h(len(note), meas) + 4.0
    y += 2.0
    p.rule(x0, y, meas)
    y += 3.2
    fac = '<br>'.join('<b>%s</b> — %s' % (h, e(f))
                      for h, f in zip(('Colour', 'Composition', 'Hand'), w['facets']))
    p.m(x0, y, meas, fac, 'g')
    y += sum(micro_h(len(f) + 12, meas) for f in w['facets']) + 4.0
    return y

# ══ A · ACILIM ═══════════════════════════════════════════════════════
# Solda yazi, sagda tablonun kendisi. Yil esikleri ayri sayfa degildir:
# yilin ilk isinde iri bir rakam olarak baslik blogunun ustune girer.
def f_open(w, thresh=None, thresh_line='', gap_note='', integrate=None,
           int_cap=''):
    pl, pr = spread(w['run'])
    pl.fam = pr.fam = 'A'
    FIRST.setdefault(w['n'], pl.no)
    use(pl)
    y = 29.0
    if thresh:
        pl.d(X(0), 20.0, W(10), thresh, 'yr')
        pl.m(X(0), 62.0, W(8), thresh_line, 'g')
        y = REG[1]
    y = work_block(pl, w, y)
    if gap_note:
        y += 4.0
        pl.t(X(0), y, W(7), '<em>%s</em>' % e(gap_note))
        y += serif_h(len(gap_note), W(7)) + 4.0
    if integrate:
        y += 5.0
        src, box, tag = integrate
        register(src, box, 'crop', 'open %02d' % w['n'])
        ar = ratio(src, box)
        ih = min(S / ar, 84.0)
        iw = ih * ar
        pl.img(src, X(0), y, iw, None, box, tag, cls='ix')
        pl.m(X(0) + iw + 4.0, y + 0.4, max(W(3), W(7) - iw - 4.0), e(int_cap), 'g')
    use(pr)
    put_plate(pr, w)
    return pl, pr

def f_pair(wa, wb, ka=0.71, int_a=None, int_a_cap=''):
    """Iki kucuk is tek serimde: sagda buyuk olan, solda kucugu. Ikisi de
       butun, ikisi de kendi kunyesiyle; olcek farki iliskinin kendisi.
       Dik levhada kunye yandaki kolona, yatikta levhanin altina girer."""
    pl, pr = spread(wa['run'])
    pl.fam = pr.fam = 'A'
    FIRST.setdefault(wa['n'], pl.no)
    FIRST.setdefault(wb['n'], pl.no + 1)

    def one(p, wk, k, sub):
        use(p)
        register(wk['plate']['src'], None, 'plate', 'open')
        wd, h = plate_size(wk, k)
        if wk['ar'] <= 1.05:
            x = p.X(0) if sub else (p.ml + MEASURE - wd)
            p.img(wk['plate']['src'], x, REG[0], wd, None, wk['plate'].get('box'),
                  'p%02d' % wk['n'] if k == 1.0 else 'p%02dk' % wk['n'], cls='pl')
            bx = (x + wd + 8.0) if sub else p.X(0)
            bw = p.ml + MEASURE - bx if sub else (x - 8.0 - p.X(0))
            y2 = work_block(p, wk, REG[0], x0=bx, meas=max(bw, W(3)), tfs=15)
        else:
            x = p.X(0)
            p.img(wk['plate']['src'], x, REG[0], wd, None, wk['plate'].get('box'),
                  'p%02d' % wk['n'] if k == 1.0 else 'p%02dk' % wk['n'], cls='pl')
            y2 = work_block(p, wk, REG[0] + h + 10.0, meas=W(7),
                            tfs=min(19, title_size(wk['title'])))
        return y2

    ya = one(pl, wa, ka, sub=True)
    if int_a:
        src, box, tag = int_a
        register(src, box, 'crop', 'open %02d' % wa['n'])
        ar = ratio(src, box)
        iw = min(XS, 64.0 * ar)
        use(pl)
        pl.img(src, X(0), REG[3], iw, None, box, tag, cls='ix')
        pl.m(X(0) + iw + 4.0, REG[3] + 0.4, W(7) - iw, e(int_a_cap), 'g')
    one(pr, wb, 1.0, sub=False)
    return pl, pr

# ══ B · TARTISMA ═════════════════════════════════════════════════════
# Bir egemen kesit, karsisinda bir ila uc karsi-gorsel. Egemen tam sayfa
# tasar, tam boy kolon olur ya da sirt guvenliyse serime yayilan bant.
def f_argument(w, dom, secs=(), side='R', pos='50% 40%', mode='page',
               frag=None, band_h=108.0, focal=0.5, tagk='a',
               frag_big=False, frag_src='', frag_note=''):
    pl, pr = spread(w['run'])
    pl.fam = pr.fam = 'B'
    dp = pr if side == 'R' else pl
    tp = pl if side == 'R' else pr

    if mode == 'page':
        register(dom['src'], dom.get('box'), 'crop', 'w%02d dom' % w['n'])
        use(dp)
        dp.cover_img(dom['src'], -BLEED, -BLEED, PW + 2 * BLEED, PH + 2 * BLEED,
                     dom.get('box'), 'w%02d%sD' % (w['n'], tagk), pos)
        dp.folio = False
        use(tp)
        # Karsi-gorseller sirta yaslanir: egemene dogru egilirler.
        toward = tp.verso                     # solda: sag kenara hizala
        y, k = REG[0], 0
        for sc in secs:
            register(sc['src'], sc.get('box'), 'crop', 'w%02d sec' % w['n'])
            ar = ratio(sc['src'], sc.get('box'))
            wd = M if k == 0 else S
            if y + wd / ar > DBOT:
                wd = S if k == 0 else XS
            if y + wd / ar > DBOT:
                wd = (DBOT - y) * ar
            h = wd / ar
            x = (tp.ml + MEASURE - wd) if toward else tp.X(0)
            tp.img(sc['src'], x, y, wd, None, sc.get('box'),
                   'w%02d%s%d' % (w['n'], tagk, k),
                   cls='ix' if wd < S else '')
            cw = max(wd, W(4))
            cx = (tp.ml + MEASURE - cw) if toward else x
            tp.m(cx, y + h + 2.6, cw, loc_line(sc), 'g',
                 'text-align:right' if toward else '')
            nxt = next((r for r in REG if r > y + h + 16.0), None)
            y = nxt if nxt is not None else y + h + 18.0
            k += 1
        if frag:
            tp.t(X(0), 238.0, W(5.5), '<em>%s</em>' % e(frag))
        tp.rule(X(0), 262.0, W(6))
        tp.m(X(0), 265.4, W(10), '%02d <i>&middot;</i> %s <i>&middot;</i> %s'
             % (w['n'], e(w['title']), cap_line(w, dom, 0, prefix='Opposite')), 'g')

    elif mode == 'band':
        # Serit kaynagin butun genisligini alir, yalniz boyu kesilir;
        # sirt ortasina yuz dusmeyen kesitler icindir.
        b = dom.get('box') or [0.0, 0.0, 1.0, 1.0]
        SPAN = PW * 2 + 2 * BLEED
        full_ar = ratio(dom['src'], b)
        want = SPAN / band_h
        if full_ar < want:
            keep = (full_ar / want) * b[3]
            top = min(max(b[1], b[1] + (b[3] - keep) * focal), b[1] + b[3] - keep)
            b = [b[0], top, b[2], keep]
        register(dom['src'], b, 'crop', 'w%02d band' % w['n'])
        top = REG[1]
        path, _ = prep(dom['src'], SPAN, 'w%02d%sB' % (w['n'], tagk), b, hi=1800)
        pl.raw('<img src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm">'
               % (path, -BLEED, top, SPAN, band_h))
        pr.raw('<img src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;height:%.2fmm">'
               % (path, -BLEED - PW, top, SPAN, band_h))
        use(pl)
        pl.m(pl.X(0), top + band_h + 3.0, W(9), cap_line(w, dom, 0), 'g')
        if frag:
            pl.t(pl.X(0), REG[0] + 8.0, W(6), '<em>%s</em>' % e(frag))
        use(pr)
        pr.m(pr.X(0), top + band_h + 3.0, W(6),
             '%02d <i>&middot;</i> %s' % (w['n'], e(w['title'])), 'g')
        y, k = REG[3], 1
        for sc in secs:
            register(sc['src'], sc.get('box'), 'crop', 'w%02d sec' % w['n'])
            ar = ratio(sc['src'], sc.get('box'))
            wd = M
            if y + wd / ar > 280.0:
                wd = (280.0 - y) * ar
            h = wd / ar
            pr.img(sc['src'], pr.X(0), y, wd, None, sc.get('box'),
                   'w%02d%s%d' % (w['n'], tagk, k))
            pr.m(pr.X(0) + wd + 4.0, y + 0.4, W(4), loc_line(sc), 'g')
            k += 1

    elif mode == 'column':
        # Tam boy dusey kesit; karsi sayfada nottan bir cumle ve bosluk.
        register(dom['src'], dom.get('box'), 'crop', 'w%02d dom' % w['n'])
        ar = ratio(dom['src'], dom.get('box'))
        h = BAND_H
        wd = h * ar
        if wd > MEASURE: wd = MEASURE; h = wd / ar
        use(dp)
        x = dp.X(0) if side == 'R' else (dp.ml + MEASURE - wd)
        dp.img(dom['src'], x, REG[0], wd, h, dom.get('box'),
               'w%02d%sC' % (w['n'], tagk), hi=1600)
        use(tp)
        if frag and frag_big:
            tp.box(tp.X(0), REG[1], W(9), e(frag), 'pq mid')
            fy = REG[1] + math.ceil(len(frag) / 45.0) * 9.5 + 9.0
            tp.m(tp.X(0), fy, W(8), frag_src, 'g')
            if frag_note:
                tp.m(tp.X(0), fy + 12.0, W(7), e(frag_note), 'g')
        elif frag:
            tp.t(X(0), REG[1], W(5), '<em>%s</em>' % e(frag))
        tp.rule(X(0), 262.0, W(6))
        tp.m(X(0), 265.4, W(10), '%02d <i>&middot;</i> %s <i>&middot;</i> %s'
             % (w['n'], e(w['title']), cap_line(w, dom, 0, prefix='Opposite')), 'g')
    return pl, pr

# ── B'nin cesitleri: her biri baska bir uzamsal iliski ───────────────
# Ayni jest kitapta ucten fazla tekrar etmez. Tam tasan bir gorselin
# karsisina ne konuldugu her seferinde ayri bir karardir: bir ipucu, bir
# ikincil, dar bir dusey kolon, tek taban cizgisinde parcalar, bir dosya,
# sirtta kaynamis iki yarim, ya da serime yayilan yatay bir cumle.

def _bleed(dp, w, dom, pos, tagk):
    register(dom['src'], dom.get('box'), 'crop', 'w%02d dom' % w['n'])
    use(dp)
    dp.cover_img(dom['src'], -BLEED, -BLEED, PW + 2 * BLEED, PH + 2 * BLEED,
                 dom.get('box'), 'w%02d%sD' % (w['n'], tagk), pos)
    dp.folio = False


def _foot(tp, w, dom, extra=''):
    use(tp)
    tp.rule(tp.X(0), 262.0, W(6))
    tp.m(tp.X(0), 265.4, W(10), '%02d <i>&middot;</i> %s <i>&middot;</i> %s%s'
         % (w['n'], e(w['title']), cap_line(w, dom, 0, prefix='Opposite'),
            extra), 'g')


def f_clue(w, dom, clues, side='R', pos='50% 40%', tagk='a'):
    """Tam tasan bir yuz, karsisinda bir ya da iki ipucu. Ipucu kucuktur,
       hepsi tek bir dusey eksende durur ve yerini karsi sayfadaki bakisa
       gore alir: susleme degil, sezdirme."""
    pl, pr = spread(w['run'])
    pl.fam = pr.fam = 'B'
    dp = pr if side == 'R' else pl
    tp = pl if side == 'R' else pr
    _bleed(dp, w, dom, pos, tagk)
    use(tp)
    toward = tp.verso                      # sol sayfada ipucu sirta yaslanir
    axis = (tp.ml + MEASURE) if toward else tp.X(0)
    for i, (clue, y) in enumerate(clues):
        register(clue['src'], clue.get('box'), 'crop', 'w%02d clue' % w['n'])
        ar = ratio(clue['src'], clue.get('box'))
        cw = w_area(PUNCTUM, ar)
        ch = cw / ar
        x = (axis - cw) if toward else axis
        tp.img(clue['src'], x, y, cw, ch, clue.get('box'),
               'w%02d%sc%d' % (w['n'], tagk, i))
        capw = max(cw, W(4))
        cx = (axis - capw) if toward else axis
        tp.m(cx, y + ch + 2.4, capw, loc_line(clue), 'g',
             'text-align:right' if toward else '')
    _foot(tp, w, dom)
    return pl, pr


def f_wide(w, dom, sec, side='R', pos='50% 40%', sec_y=None, tagk='a'):
    """Tam tasan gorselin karsisinda kararli bir ikincil: kucuk bir kesit
       degil, karsisindakiyle boy olcusen bir okuma."""
    pl, pr = spread(w['run'])
    pl.fam = pr.fam = 'B'
    dp = pr if side == 'R' else pl
    tp = pl if side == 'R' else pr
    _bleed(dp, w, dom, pos, tagk)
    use(tp)
    register(sec['src'], sec.get('box'), 'crop', 'w%02d sec' % w['n'])
    ar = ratio(sec['src'], sec.get('box'))
    sw = w_area(SECONDARY, ar)
    sh = sw / ar
    x = tp.ml + MEASURE - sw               # dis kenara hizali
    y = REG[1] if sec_y is None else sec_y
    tp.img(sec['src'], x, y, sw, sh, sec.get('box'),
           'w%02d%ss' % (w['n'], tagk), hi=1800)
    tp.m(x, y + sh + 2.6, sw, loc_line(sec), 'g')
    _foot(tp, w, dom)
    return pl, pr


def f_narrow(w, dom, box, line, side='R', pos='50% 40%', tagk='a'):
    """Tam tasan gorselin karsisinda tablonun dar bir dusey kolonu:
       kenara yaslanir, sayfa boyunca iner, mimari ve kesindir."""
    pl, pr = spread(w['run'])
    pl.fam = pr.fam = 'B'
    dp = pr if side == 'R' else pl
    tp = pl if side == 'R' else pr
    _bleed(dp, w, dom, pos, tagk)
    use(tp)
    src = w['plate']['src']
    bx = crop_of(w, box)
    register(src, bx, 'crop', 'w%02d narrow' % w['n'])
    ar = ratio(src, bx)
    nw = 48.0                              # sayfa genisliginin %20'si
    nh = nw / ar
    if nh > DBOT - REG[0]:
        nh = DBOT - REG[0]; nw = nh * ar
    x = tp.ml + MEASURE - nw               # dis kenar
    tp.img(src, x, REG[0], nw, nh, bx, 'w%02d%sn' % (w['n'], tagk), hi=1800)
    tp.m(tp.X(0), REG[0] + nh + 2.6, W(6), e(line), 'g')
    _foot(tp, w, dom)
    return pl, pr


def f_baseline(w, dom, frags, side='L', pos='50% 40%', base=250.0, tagk='a'):
    """Tam tasan gorselin karsisinda iki parca, tek ve kati bir taban
       cizgisinde. Boylari degisir, altlari degismez: sira boyle kurulur."""
    pl, pr = spread(w['run'])
    pl.fam = pr.fam = 'B'
    dp = pr if side == 'R' else pl
    tp = pl if side == 'R' else pr
    _bleed(dp, w, dom, pos, tagk)
    use(tp)
    x = tp.X(0)
    for i, (d, fw) in enumerate(frags):
        register(d['src'], d.get('box'), 'crop', 'w%02d frag' % w['n'])
        ar = ratio(d['src'], d.get('box'))
        h = fw / ar
        tp.img(d['src'], x, base - h, fw, h, d.get('box'),
               'w%02d%sf%d' % (w['n'], tagk, i), hi=1800)
        tp.m(x, base + 2.6, max(fw, W(4)), loc_line(d), 'g')
        x += fw + 6.0
    _foot(tp, w, dom)
    return pl, pr


def f_dossier(w, dom, pair, side='R', pos='50% 40%', tagk='a'):
    """Karsi sayfa bir dosya: ayni genislikte iki okuma, ust uste, ayni
       sol kenarda. Sol sayfa kanit, sag sayfa dalma."""
    pl, pr = spread(w['run'])
    pl.fam = pr.fam = 'B'
    dp = pr if side == 'R' else pl
    tp = pl if side == 'R' else pr
    _bleed(dp, w, dom, pos, tagk)
    use(tp)
    dw = M                                 # iki gorsel de tam ayni genislikte
    y = REG[0]
    for i, d in enumerate(pair):
        register(d['src'], d.get('box'), 'crop', 'w%02d dossier' % w['n'])
        ar = ratio(d['src'], d.get('box'))
        h = dw / ar
        tp.img(d['src'], tp.X(0), y, dw, h, d.get('box'),
               'w%02d%sd%d' % (w['n'], tagk, i), hi=1600)
        tp.m(tp.X(0) + dw + 4.0, y + 0.4, W(5), loc_line(d), 'g')
        y += h + 8.0
    tp.rule(tp.X(0), y + 2.0, dw)
    tp.m(tp.X(0), y + 5.4, W(6), 'Two readings at one width', 'g')
    _foot(tp, w, dom)
    return pl, pr


def f_weld(w, a, b, cap_a, cap_b, pos_a='50% 40%', pos_b='50% 40%'):
    """Iki yarim sirtta birbirine yapisir ve tek bir gorsel gibi okunur.
       Ayak beyaz kalir, kunye resmin uzerine binmez."""
    pl, pr = spread(w['run'])
    pl.fam = pr.fam = 'W'
    H = 258.0 + BLEED
    for p, d, x, pos in ((pl, a, -BLEED, pos_a), (pr, b, 0.0, pos_b)):
        use(p)
        register(d['src'], d.get('box'), 'crop', 'w%02d weld' % w['n'])
        p.cover_img(d['src'], x, -BLEED, PW + BLEED, H, d.get('box'),
                    'w%02dwl%s' % (w['n'], 'a' if d is a else 'b'), pos, hi=1800)
    use(pl)
    pl.m(pl.X(0), 266.0, W(7), e(cap_a), 'g')
    pl.m(pl.X(0), 274.0, W(9), '%02d <i>&middot;</i> %s <i>&middot;</i> '
         'the two figures, brought together across the spine'
         % (w['n'], e(w['title'])), 'g')
    use(pr)
    pr.m(pr.R(6), 266.0, W(6), e(cap_b), 'g rt')
    return pl, pr


def f_across(w, items, base=250.0, lead=''):
    """Serime yayilan yatay bir cumle. Kesitler tek taban cizgisinde durur,
       soldan saga okunur; olcek degisir, taban degismez."""
    pl, pr = spread(w['run'])
    pl.fam = pr.fam = 'S'
    for i, (d, fw, side, x) in enumerate(items):
        p = pl if side == 'L' else pr
        use(p)
        register(d['src'], d.get('box'), 'crop', 'w%02d across' % w['n'])
        ar = ratio(d['src'], d.get('box'))
        h = fw / ar
        p.img(d['src'], x, base - h, fw, h, d.get('box'),
              'w%02dac%d' % (w['n'], i), hi=1800)
        p.m(x, base + 2.6, max(fw, W(4)), loc_line(d), 'g')
    use(pl)
    if lead:
        pl.t(pl.X(0), REG[0], W(5), '<em>%s</em>' % e(lead))
    pl.m(pl.X(0), 266.0, W(9),
         '%02d <i>&middot;</i> %s' % (w['n'], e(w['title'])), 'g')
    return pl, pr


# ══ C · DIZI ═════════════════════════════════════════════════════════
# Surec zaman olarak basilir: karar ani buyuk, kalan asamalar sirali ve
# numarali. Kac asamadan kacinin gosterildigi her seferinde soylenir.
def stage_no(w, d):
    return w['process'].index(d) + 1

def put_frame(p, w, d, x, y, wd, tagx, cap=None, bleed=False):
    register(d['src'], d.get('box'), 'frame', 'w%02d seq' % w['n'])
    bot = p.img(d['src'], x, y, wd, None, d.get('box'),
                'w%02ds%s' % (w['n'], tagx),
                cls='bl' if bleed else ('ix' if wd < S else ''))
    if cap:
        p.m(x, bot + 2.2, max(wd, W(5)), e(cap), 'g')
    note = CREDITS.get(d['src'].split('/')[-1])
    if note:
        p.m(x, bot + (7.6 if cap else 2.2), max(wd, W(5)), e(note), 'g')
    return bot

def strip_row(p, w, frames, y, fh, tail, x0=None):
    """Asamalar tek yukseklikte yan yana; numaralar tek bir cizgide,
       kac asamadan kacinin gosterildigi de onlarin altinda."""
    x = p.X(0) if x0 is None else x0
    for d in frames:
        fw = fh * ratio(d['src'], d.get('box'))
        put_frame(p, w, d, x, y, fw, '%d' % stage_no(w, d))
        p.m(x, y + fh + 2.2, max(fw, W(2)), '%d' % stage_no(w, d), 'g')
        x += fw + 4.0
    if tail:
        p.m(p.X(0), y + fh + 10.0, W(9), tail, 'g')
    return y + fh


def shown_line(w, n):
    return 'Of %d stages, %d <i>&middot;</i> in order' % (len(w['process']), n)

def f_sequence(w, spec):
    pl, pr = spread(w['run'])
    pl.fam = pr.fam = 'C'
    lay = spec['layout']

    if lay == 'rows':
        # Solda karar ani tam olcude; sagda iki sira secilmis asama.
        use(pl)
        bot = put_frame(pl, w, spec['dom'], X(0), REG[0], XL, 'd', spec['domcap'])
        pl.t(X(0), bot + 14.0, W(7), '<em>%s</em>' % e(spec['line']))
        use(pr)
        strip = spec['strip']
        FH = (S * 1.12) / 1.25          # kare boyu sabit, en-boy korunur
        GAP, PERROW, RG = 4.0, 3, 13.0
        rows = int(math.ceil(len(strip) / float(PERROW)))
        top = 262.0 - rows * (FH + RG)
        for i, d in enumerate(strip):
            fw = FH * ratio(d['src'], d.get('box'))
            x = pr.X(0) + (i % PERROW) * (fw + GAP)
            y = top + (i // PERROW) * (FH + RG)
            cut = x + fw > PW - 1.0
            put_frame(pr, w, d, x, y, fw, '%d' % stage_no(w, d), bleed=cut)
            pr.m(x, y + FH + 2.2, min(fw, PW - 6.0 - x),
                 '%d' % stage_no(w, d), 'g')
        pr.m(pr.X(0), 264.0, W(9), shown_line(w, len(strip) + 1), 'g')

    elif lay == 'source':
        # Kaynak ciftin solunda buyuk cizim; sagda kaynak, kirmizi ve dizi.
        use(pl)
        bot = put_frame(pl, w, spec['dom'], X(0), REG[0], XL, 'd', spec['domcap'])
        use(pr)
        b1 = put_frame(pr, w, spec['src_frame'], X(0), REG[0], S, 'src',
                       spec.get('srccap'))
        strip_row(pr, w, spec['strip'], REG[0], 42.0, None, x0=X(4))
        pr.t(X(0), 118.0, W(6), '<em>%s</em>' % e(spec['line']))
        b3 = put_frame(pr, w, spec['mid'], X(0), REG[2], M, 'm')
        pr.m(X(0) + M + 4.0, REG[2] + 0.4, W(5), e(spec.get('midcap', '')), 'g')
        pr.m(X(0) + M + 4.0, b3 - 3.2, W(5), shown_line(w, len(spec['strip']) + 3), 'g')

    elif lay == 'still':
        # Kaynak tek basina solda, bosluk icinde; sagda cizim buyuk ve dizi.
        use(pl)
        sf = spec['src_frame']
        register(sf['src'], None, 'frame', 'w%02d seq' % w['n'])
        sw = min(w_area(0.215, ratio(sf['src'])), 118.0)
        x = pl.ml + MEASURE - sw
        bot = pl.img(sf['src'], x, REG[1], sw, None, None,
                     'w%02dsstill' % w['n'], hi=1800)
        pl.m(x, bot + 2.6, sw, e(spec.get('srccap', '')), 'g')
        ty = bot + 2.6 + micro_h(len(spec.get('srccap', '')), sw)
        note = CREDITS.get(sf['src'].split('/')[-1])
        if note:
            pl.m(x, ty + 2.0, sw, e(note), 'g')
            ty += 2.0 + micro_h(len(note), sw)
        pl.t(X(0), ty + 6.0, W(6), '<em>%s</em>' % e(spec['line']))
        use(pr)
        ar_d = ratio(spec['dom']['src'], spec['dom'].get('box'))
        wd_d = L if L / ar_d <= 190.0 else 190.0 * ar_d
        bot = put_frame(pr, w, spec['dom'], X(0), REG[0], wd_d, 'd', spec['domcap'])
        strip_row(pr, w, spec['strip'], 216.0, 46.0,
                  shown_line(w, len(spec['strip']) + 2))

    elif lay == 'faces':
        # Egemen bir detay tam sayfa; karsisinda ayni yerin uc asamasi.
        register(spec['dom']['src'], spec['dom'].get('box'), 'crop',
                 'w%02d dom' % w['n'])
        use(pl)
        pl.cover_img(spec['dom']['src'], -BLEED, -BLEED, PW + 2 * BLEED,
                     PH + 2 * BLEED, spec['dom'].get('box'),
                     'w%02dsD' % w['n'], spec.get('pos', '50% 40%'))
        pl.folio = False
        use(pr)
        y = REG[0]
        for dd in spec['strip']:
            b2 = put_frame(pr, w, dd, X(0), y, S, '%d' % stage_no(w, dd))
            pr.m(X(0) + S + 4.0, y + 0.4, W(2), '%d' % stage_no(w, dd), 'g')
            y = b2 + 8.0
        pr.t(X(6), REG[1], W(5), '<em>%s</em>' % e(spec['line']))
        pr.rule(X(6), 262.0, W(6))
        pr.m(X(6), 265.4, W(6), '%02d <i>&middot;</i> %s <i>&middot;</i> %s'
             % (w['n'], e(w['title']), e(spec['domcap'])), 'g')

    elif lay == 'stagger':
        # Egemen tam olcude solda; asamalar sagda basamak basamak iner.
        use(pl)
        bot = put_frame(pl, w, spec['dom'], X(0), REG[0], XL, 'd', spec['domcap'])
        pl.t(X(0), bot + 14.0, W(6), '<em>%s</em>' % e(spec['line']))
        use(pr)
        n = len(spec['strip'])
        for i, dd in enumerate(spec['strip']):
            x = X(i * 3)
            y = REG[0] + i * ((DBOT - 46.0 - REG[0]) / max(1, n - 1))
            b2 = put_frame(pr, w, dd, x, y, XS, '%d' % stage_no(w, dd))
            pr.m(x, b2 + 2.2, XS, '%d' % stage_no(w, dd), 'g')
        pr.m(X(0), DBOT + 2.0, W(9), shown_line(w, n + 1), 'g')

    elif lay == 'versions':
        # Ayni sahnenin baska halleri: kronoloji iddiasiz, yan yana.
        use(pl)
        a = spec['dom']
        register(a['src'], a.get('box'), 'crop', 'w%02d ver' % w['n'])
        bot = pl.img(a['src'], X(0), REG[0], L, None, a.get('box'), 'w%02dv0' % w['n'])
        pl.m(X(0), bot + 2.6, L, e(where(a)), 'g')
        pl.t(X(0), min(bot + 14.0, 250.0), W(7), '<em>%s</em>' % e(spec['line']))
        use(pr)
        y = REG[0]
        for i, (vv, wd) in enumerate(zip(spec['strip'], (M, S, S))):
            register(vv['src'], vv.get('box'), 'crop', 'w%02d ver' % w['n'])
            bot = pr.img(vv['src'], X(0), y, wd, None, vv.get('box'),
                         'w%02dv%d' % (w['n'], i + 1))
            pr.m(X(0) + wd + 4.0, y + 0.4, W(4), e(where(vv)), 'g')
            nxt = next((r for r in REG if r > bot + 14.0), None)
            y = nxt if nxt is not None else bot + 16.0

    elif lay == 'study':
        # Etud solda buyuk; sagda etudun tabloda vardigi yer.
        use(pl)
        a = spec['dom']
        register(a['src'], a.get('box'), 'crop', 'w%02d study' % w['n'])
        wd = spec.get('domw', L)
        ar_s = ratio(a['src'], a.get('box'))
        if wd / ar_s > 196.0: wd = 196.0 * ar_s
        bot = pl.img(a['src'], X(0), REG[0], wd, None, a.get('box'),
                     'w%02dst' % w['n'], hi=1800)
        pl.m(X(0), bot + 2.6, W(9), e(where(a)), 'g')
        pl.t(X(0), bot + 12.0, W(7), '<em>%s</em>' % e(spec['line']))
        use(pr)
        y = REG[1]
        for i, (vv, wd2, cp) in enumerate(spec['after']):
            register(vv['src'], vv.get('box'), 'crop', 'w%02d after' % w['n'])
            ar2 = ratio(vv['src'], vv.get('box'))
            if wd2 is None:
                # Etudun vardigi yer okunacak kadar buyuk, etudu gecmeyecek
                # kadar kucuk: bir kademe asagida durur.
                wd2 = w_area(0.24, ar2)
            x2 = pr.ml + MEASURE - wd2
            bot = pr.img(vv['src'], x2, y, wd2, None, vv.get('box'),
                         'w%02dsa%d' % (w['n'], i), hi=1800)
            pr.m(x2, bot + 2.6, wd2, e(cp), 'g')
            y = bot + 18.0
        pr.rule(X(0), 262.0, W(6))
        pr.m(X(0), 265.4, W(9), '%02d <i>&middot;</i> %s' % (w['n'], e(w['title'])), 'g')
    return pl, pr

# ══ D · DURAK ════════════════════════════════════════════════════════
# Sanatcinin bir cumlesi resim boyunda; geri kalani kararli bosluk.
# Kitapta iki kez, ikisinde de baska kurulur.
def f_pause(w, text, attrib, img=None, img_box=None, img_cap='', kind='reach'):
    pl, pr = spread(w['run'])
    pl.fam = pr.fam = 'D'
    use(pl)
    if kind == 'reach':
        # Soz sol ustte biter; kol sag alt koseden girer, soze uzanir.
        pl.box(X(0), REG[0] + 16.0, W(9), e(text), 'pq')
        pl.m(X(0), REG[0] + 16.0 + math.ceil(len(text) / 33.0) * 12.6 + 8.0,
             W(8), attrib, 'g')
        use(pr)
        if img:
            register(img, img_box, 'crop', 'pause %02d' % w['n'])
            ar = ratio(img, img_box)
            wd = w_area(PUNCTUM, ar)
            h = wd / ar
            x = PW - MOUT - wd             # dis kenar
            y = PH - MB - h                # ayak marji
            pr.img(img, x, y, wd, h, img_box, 'w%02dpz' % w['n'], hi=1600)
            pr.m(x - W(4) - 6.0, y + h - 4.4, W(4), e(img_cap), 'g rt')
    elif kind == 'inscribe':
        # Yazit solda tek basina; etud sagda, kagit beyazi sayfa beyazina.
        pl.box(X(0), REG[1], W(9), e(text), 'pq big')
        pl.m(X(0), REG[1] + 24.0, W(8), attrib, 'g')
        use(pr)
        if img:
            register(img, img_box, 'crop', 'pause %02d' % w['n'])
            ar = ratio(img, img_box)
            wd = L
            h = wd / ar
            if h > 236.0: h = 236.0; wd = h * ar
            x = pr.ml + MEASURE - wd
            pr.img(img, x, REG[0], wd, h, img_box, 'w%02dpz' % w['n'], hi=1600)
            pr.m(x, REG[0] + h + 2.6, wd, e(img_cap), 'g')
    return pl, pr

# ── metinler ─────────────────────────────────────────────────────────
P1 = ('In Özen\'s paintings a body appears as rounded units settle on top of one '
      'another. The contour arrives late and often does not arrive. Scale gives '
      'the verdict. A shape held large enough becomes somebody, and the same '
      'shape beside it becomes a row. Most of the ground stays unpainted, and '
      'that emptiness decides how far the figure gets to build.')
P2 = ('The same parts have been turning up since the beginning. A figure present '
      'in the scene and not looking. A chair nobody sits in. A frame drawn over '
      'the scene and left open. A bird that arrives under its own power, carrying '
      'something never unwrapped. These are working parts. Nothing in them waits '
      'to be solved. The one helping and the one crushing are made of the same '
      'heap.')
P3 = ('Titles do not name the picture. A greeting, a game, a file name, a line '
      'taken from elsewhere. They set a second language beside the image and tilt '
      'it. Decisions are taken in wet paint, colour is held as a distribution. '
      'Over the years the parts stay where they are and the temperature changes.')
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

TOC = None
SECTIONS = []

# ══ on sayfalar ══════════════════════════════════════════════════════
COVER_SRC = '/img/full/detail/7famboardgame_detail_3.jpg'
COVER_ON_PLATE = [0.125, 0.375, 0.550, 0.458]   # kapagin 01 uzerindeki yeri

def front_matter():
    # Kapak: kesit ustte, koyu zeminde baslik. Kesitin tablodaki yeri
    # kitabin son sayfasinda isaretlenir.
    p = page('', 'dark')
    p.folio = False
    p.fam = 'F'
    register(COVER_SRC, None, 'crop', 'cover')
    cpath, car = prep(COVER_SRC, 240, 'cover')
    ch = 240.0 / car
    p.raw('<img src="%s" style="left:0;top:0;width:240mm;height:%.2fmm">' % (cpath, ch))
    p.m(X(0), ch + 8.0, W(6), NM)
    p.m(R(4), ch + 8.0, W(4), 'Thirty-five works', 'rt g')
    p.rule(X(0), ch + 16.0, MEASURE, True)
    p.d(X(0), 206.0, W(10), 'Paintings<br>since 2019', 'l')
    p.rule(X(0), 292.0, MEASURE)
    p.m(X(0), 295.4, W(6), 'Istanbul <i>&middot;</i> Milan <i>&middot;</i> Luxembourg')
    p.m(R(3), 295.4, W(3), 'yigitozen.xyz', 'rt')

    p = page('Imprint')
    p.fam = 'F'
    p.m(X(0), HEAD, W(6), 'Imprint')
    p.m(R(4), HEAD, W(4), NM, 'rt g')
    p.rule(X(0), HRULE, MEASURE, True)
    p.d(X(0), 29.0, W(9), 'Thirty-five<br>paintings', 's')
    p.rule(X(0), 66.0, W(9))
    p.m(X(0), 69.4, W(7), '2019&ndash;2026 <i>&middot;</i> Istanbul, Milan and Luxembourg')
    p.t(X(0), 196.0, W(6), e(SHORT_BLURB if SHORT else BLURB))
    p.rule(X(0), 258.0, MEASURE)
    p.m(X(0), 261.6, W(4), '<b>Medium</b><br>Acrylic on canvas, on carton and on '
        'paper, and one drawing in charcoal', 'g')
    p.m(X(4), 261.6, W(4), '<b>Order</b><br>Newest first, so the seven years are '
        'read backwards', 'g')
    p.m(X(8), 261.6, W(4), '<b>Rights</b><br>All works &copy; Yiğit Özen. '
        'All rights reserved', 'g')

    p = page('Paintings since 2019')
    p.fam = 'F'
    p.m(X(0), HEAD, W(6), NM)
    p.m(R(4), HEAD, W(4), 'Istanbul <i>&middot;</i> Milan <i>&middot;</i> Luxembourg', 'rt g')
    p.rule(X(0), HRULE, MEASURE, True)
    p.d(X(0), 118.0, W(11), 'Paintings<br>since<br>2019', 'xl')
    p.rule(X(0), 262.0, MEASURE)
    p.m(X(0), 265.4, W(5), 'Thirty-five works' if not SHORT else 'Eight works')
    p.m(R(4), 265.4, W(4), 'Newest first', 'rt g')

    if SHORT: return

    # Deneme serimi: solda sanatcinin metni iki kolonda, sagda tam tasan
    # bir kesit. Metin ile resim ayni serimde karsi karsiya.
    pl, pr = spread('On the work')
    pl.fam = pr.fam = 'F'
    use(pl)
    pl.m(X(0), HEAD, W(6), 'On the work')
    pl.m(R(4), HEAD, W(4), 'Text by the artist', 'rt g')
    pl.rule(X(0), HRULE, MEASURE, True)
    cw = W(5.8)
    pl.t(X(0), 34.0, cw, '<p>%s</p><p>%s</p>' % (e(P1), e(P2)))
    pl.t(X(6.2), 34.0, cw, '<p>%s</p>' % e(P3))
    pl.rule(X(0), 262.0, MEASURE)
    pl.m(X(0), 265.4, W(8), 'Thirty-five works, 2019&ndash;2026, read newest first')
    pl.m(R(3), 265.4, W(3), '15 <i>&middot;</i> viperella', 'rt g')
    use(pr)
    _esrc = '/img/full/detail/viperella_detail_1.jpg'
    register(_esrc, None, 'crop', 'essay')
    pr.cover_img(_esrc, -BLEED, -BLEED, PW + 2 * BLEED, PH + 2 * BLEED, None,
                 'essay', '30% 30%')
    pr.folio = False

    pl, pr = spread('Biography')
    pl.fam = pr.fam = 'F'
    use(pl)
    pl.m(X(0), HEAD, W(6), 'Biography')
    pl.m(R(4), HEAD, W(4), NM, 'rt g')
    pl.rule(X(0), HRULE, MEASURE, True)
    pl.img('/img/portrait.jpg', pl.ml + MEASURE - L, REG[1], L, None, None,
           'portrait')
    pl.d(X(0), 29.0, W(5), 'Yiğit<br>Özen', 's')
    pl.rule(X(0), 66.0, W(5))
    pl.m(X(0), 69.4, W(5), 'Born 1994, Istanbul')
    pl.t(X(0), 190.0, W(6), ''.join('<p>%s</p>' % e(x) for x in BIO))
    pl.rule(X(0), FRULE, MEASURE)
    pl.m(X(0), FMICRO, W(5), 'Painter and spatial designer')
    pl.m(R(4), FMICRO, W(4), 'Studio, Luxembourg', 'rt g')
    use(pr)
    pr.m(X(0), HEAD, W(8), 'Exhibitions and talks')
    pr.m(R(2), HEAD, W(2), 'Selected', 'rt g')
    pr.rule(X(0), HRULE, MEASURE, True)
    y = 34.0
    for gi, (h4, rows) in enumerate(CV):
        pr.m(X(0), y, W(4), h4)
        yy = y
        for a2, b2 in rows:
            pr.m(X(4), yy, W(7), e(a2), 'g')
            pr.m(R(1), yy, W(1), b2, 'rt g')
            yy += 6.6
        y = yy + 12.0
        if gi < len(CV) - 1:
            pr.rule(X(0), y - 6.0, MEASURE)
    pr.rule(X(0), FRULE, MEASURE)
    pr.m(X(0), FMICRO, W(8),
         'The painting and the design practice are kept apart, and the rules '
         'between them say where one ends')

    # Duzen sayfasi + icindekiler: bir serim, iki is goren sayfa.
    pl, pr = spread('How to read this')
    pl.fam = pr.fam = 'F'
    use(pl)
    pl.m(X(0), HEAD, W(8), 'How this book is arranged')
    pl.rule(X(0), HRULE, MEASURE, True)
    pl.t(X(0), 34.0, W(6),
         '<p>The thirty-five paintings are given newest first, so the seven '
         'years are read backwards. A paragraph that says a thing happens for '
         'the first time means the first time reading backwards through the '
         'book.</p>'
         '<p>Every work opens on a spread: the number, the title, the '
         'dimensions and the note on the left, the painting whole on the '
         'right. The top of every painting sits on the same line throughout '
         'the book, and its size on the page follows the size of the canvas, '
         'so the largest canvas prints largest. The first work of each year '
         'carries the year as a numeral; nothing else marks the thresholds.</p>'
         '<p>Where a work was photographed in detail or in progress, one or '
         'two spreads follow. Details are chosen, not collected: one cut is '
         'set large against one or two others, each printed once in the whole '
         'book, each captioned with where it is and what the hand did there. '
         'The stages of a painting are given in order with the decisive stage '
         'large, and the caption says how many stages there were.</p>'
         '<p>Six recurring figures are followed in a chapter at the end, in '
         'cuts that appear nowhere else. Dimensions are width by height, in '
         'centimetres, then in inches.</p>')
    pl.rule(X(0), 262.0, MEASURE)
    pl.m(X(0), 265.4, W(6), 'Newest first')
    pl.m(R(4), 265.4, W(4), '2026 to 2019', 'rt g')
    global TOC
    use(pr)
    TOC = pr

def toc_fill(p):
    use(p)
    p.m(X(0), HEAD, W(6), 'Contents')
    p.m(R(4), HEAD, W(4), 'Thirty-five works', 'rt g')
    p.rule(X(0), HRULE, MEASURE, True)
    y = 26.0
    for wk in WORKS:
        p.m(X(0), y + 0.4, W(1), '%02d' % wk['n'], 'g')
        p.sans(X(1), y, W(8), e(wk['title']), '', 'font-size:8.0pt;line-height:1.3')
        p.m(X(9), y + 0.4, W(1), e(wk['year']), 'g')
        p.m(R(1), y + 0.4, W(1), str(FIRST.get(wk['n'], 0)), 'rt')
        y += 6.1
    y += 2.4
    p.rule(X(0), y, MEASURE)
    y += 3.2
    for name, pg in SECTIONS:
        p.sans(X(1), y, W(7), name, '', 'font-size:8.0pt;line-height:1.3')
        p.m(R(1), y + 0.4, W(1), str(pg), 'rt')
        y += 6.1
    p.rule(X(0), FRULE, MEASURE)
    p.m(X(0), FMICRO, W(8),
        'Each work opens on a spread: the note on the left, the painting on the right')
    p.m(R(2), FMICRO, W(2), 'Page', 'rt g')

# ══ kitabin kurgusu ══════════════════════════════════════════════════
# Yeniden eskiye: 2026 surecle yogun, 2023 tek is ve gorunur bir sessizlik,
# 2020 sikisir, 2019 arsive acilir. Ayni aile ust uste en cok iki serim.
def build_works():
    N = BY_N

    # 2026 — alti is
    w = N[1]
    f_open(w, thresh='2026', thresh_line='Six works <i>&middot;</i> Luxembourg')
    # Tek ipucu: karsidaki yuzun altina, orta-alt registere.
    f_clue(w, det(w, 2), [(det(w, 5), REG[2])], side='R', pos='50% 32%')
    f_sequence(w, {'layout': 'rows', 'dom': proc(w, 1),
                   'domcap': 'Stage 1 — the board and both players, drawn before any colour',
                   'strip': [proc(w, i) for i in (3, 6, 9, 12, 14)],
                   'line': 'Fourteen stages. The board is drawn first and the far '
                           'player worked in black and white; the colour comes '
                           'over it, and the blue family arrives last, after both '
                           'heads are already fixed.'})

    w = N[2]
    f_open(w)
    f_wide(w, det(w, 3), det(w, 2), side='L', pos='50% 32%')
    f_argument(w, det(w, 7), [det(w, 5)], mode='band', focal=0.1,
               frag='A cage drawn from above, its walls never arriving; a chair '
                    'outlined where no one will sit.')
    f_sequence(w, {'layout': 'source', 'dom': proc(w, 2),
                   'domcap': 'Stage 2 — the Leonardo taken through in pencil',
                   'src_frame': proc(w, 1), 'srccap': 'Stage 1 — the source',
                   'mid': proc(w, 4),
                   'midcap': 'Stage 4 — the ground drowned in red',
                   'strip': [proc(w, i) for i in (9, 13)],
                   'line': 'Thirteen stages. A Leonardo is taken, traced in '
                           'pencil, buried under a field of red, and Virgil is '
                           'assembled on top of the grave.'})

    w = N[3]
    f_open(w)
    f_clue(w, det(w, 2), [(det(w, 9), REG[1]), (det(w, 6), REG[3])],
           side='R', pos='50% 30%')
    f_sequence(w, {'layout': 'still', 'src_frame': proc(w, 1),
                   'srccap': 'Stage 1 — the source',
                   'dom': proc(w, 2),
                   'domcap': 'Stage 2 — the still, redrawn in blue line',
                   'strip': [proc(w, i) for i in (3, 6, 8, 12)],
                   'line': 'Twelve stages. A television still is redrawn in '
                           'blue, the ground goes orange, and the body is '
                           'rebuilt from lobes until the face arrives, last.'})

    w = N[4]
    f_open(w, integrate=(proc(w, 1)['src'], None, 'w04sk'),
           int_cap='The first stage, in pencil')
    f_sequence(w, {'layout': 'faces', 'dom': det(w, 1), 'pos': '50% 42%',
                   'strip': [proc(w, i) for i in (3, 4, 5)],
                   'domcap': 'Under the brim of the hat',
                   'line': 'The face is made three times: left blank in the '
                           'blocking, given a moustache, then ringed in red. '
                           'The teeth under the brim arrive last of all.'})

    w = N[5]
    f_open(w)
    f_argument(w, det(w, 1), [det(w, 5)], mode='band', focal=0.35,
               frag='The attack comes down the diagonal; the rowers hold their line.')
    f_sequence(w, {'layout': 'stagger', 'dom': proc(w, 1),
                   'domcap': 'Stage 1 — begun as an ink page in a notebook',
                   'strip': [proc(w, i) for i in (2, 3, 4, 5)],
                   'line': 'Five stages. The dark ground first, then the '
                           'mountains, then the boat; the crew and the flock '
                           'are drawn in white at the end.'})

    w = N[6]
    f_open(w)
    f_narrow(w, det(w, 1), [0.70, 0.02, 0.26, 0.96],
             'The right edge, from the barred frame down to the panel',
             side='R', pos='45% 45%')

    # 2023 — bosluk: tek is, tek serim. Sol sayfanin ucte ikisi bos ve
    # bunu kastediyor.
    w = N[7]
    f_open(w, thresh='2023', thresh_line='One commission <i>&middot;</i> Istanbul',
           gap_note='From 2020 the studio work went largely to XR and spatial '
                    'design, and the canvases thin out to this one commission '
                    'before the painting resumes in 2026.')

    # 2020 — on is
    w = N[8]
    f_open(w, thresh='2020', thresh_line='Ten works <i>&middot;</i> Milan')
    f_baseline(w, det(w, 1), [(det(w, 2), 96.0), (det(w, 3), 68.0)],
               side='L', pos='50% 28%')
    f_sequence(w, {'layout': 'versions', 'dom': det(w, 8),
                   'strip': [det(w, 6), det(w, 7)],
                   'line': 'The pair, three times: in ink before the colour, on '
                           'green and blue, and in blue and grey. Which came '
                           'first the studio does not say.'})

    w = N[9]
    f_open(w)
    f_dossier(w, det(w, 1), [det(w, 4), det(w, 3)], side='R', pos='50% 40%')

    f_pair(N[10], N[11])

    w = N[12]
    f_open(w)
    f_weld(w, det(w, 3), det(w, 4),
           'The kneeling figure, on its knee',
           'The standing figure, at the pole',
           pos_a='50% 35%', pos_b='50% 30%')

    f_open(N[13])

    w = N[14]
    f_open(w)
    f_pause(w, 'it could be about to strike, it could be reached out to hold '
               'something.',
            'From the note on 14 <i>&middot;</i> When the Darkness surrounds, '
            'be among those who burn the Great Fire',
            img=det(w, 2)['src'], img_cap='The shoulder, and the reaching arm',
            kind='reach')

    w = N[15]
    f_open(w, integrate=(det(w, 8)['src'], None, 'w15sig'),
           int_cap='The red mark in the top right corner')
    # Govdenin inisi soldan saga: gogus, kalca, ayak. Tek taban cizgisi.
    f_across(w, [(det(w, 5), 72.0, 'L', 20.0),
                 (det(w, 3), 88.0, 'L', 100.0),
                 (det(w, 2), 118.0, 'R', 62.0)],
             lead='A body read from the chest down to the floor, in three '
                  'cuts on one line.')

    f_pair(N[17], N[16], ka=0.78)

    # 2019 — on sekiz is
    w = N[18]
    f_open(w, thresh='2019',
           thresh_line='Eighteen works <i>&middot;</i> Milan and Istanbul',
           integrate=(aside(w, 'sinoverblacmatter')['src'], None, 'w18v'),
           int_cap='An earlier painting of the same scene, the room still red '
                   'and the seat still blue')

    w = N[19]
    f_open(w)
    f_argument(w, {'src': w['plate']['src'],
                   'box': crop_of(w, [0.04, 0.14, 0.44, 0.83]),
                   'line': 'The body on the divan, from the feet'},
               side='R', mode='column', frag_big=True,
               frag='We look at the body on the blue divan from the feet; the '
                    'knees push forward and swell into two large lumps, the '
                    'body foreshortened backward, the head a dark patch so far '
                    'off it nearly vanishes.',
               frag_src='From the note on 19 <i>&middot;</i> '
                        'the assassination of the crow',
               frag_note='The crow itself is kept for the chapter on what '
                         'comes back.')

    f_open(N[20])
    f_open(N[21])
    f_pair(N[22], N[23])

    w = N[24]
    f_open(w)
    f_sequence(w, {'layout': 'study', 'dom': aside(w, 'goodppl'), 'domw': XL,
                   'after': [({'src': w['plate']['src'],
                               'box': crop_of(w, [0.02, 0.0, 0.55, 0.45]),
                               'line': 'The same arm and heap, in paint'},
                              None, 'The same arm and heap, in paint on black paper')],
                   'line': 'The winged figure and the row of small onlookers '
                           'are set in charcoal before any paint; the heap '
                           'keeps the pose and the black takes the rest.'})

    f_pair(N[25], N[26])

    w = N[27]
    f_open(w)
    f_argument(w, det(w, 1),
               [{'src': w['plate']['src'],
                 'box': crop_of(w, [0.0, 0.06, 0.36, 0.4]),
                 'line': 'The left head, near a skull'}],
               side='R', pos='55% 35%')

    f_open(N[28])

    w = N[29]
    f_open(w)
    f_pause(w, 'Deeply ordered chaos.',
            'Inscribed at the top of the pencil study for 29 <i>&middot;</i> '
            'wings of abyss',
            img=aside(w, 'wingsofabbyss')['src'],
            img_cap='Pencil study, inscribed at the top', kind='inscribe')

    f_pair(N[31], N[30], ka=0.71,
           int_a=(aside(N[31], 'societyscrewingbalance')['src'], None, 'w31st'),
           int_a_cap='Pencil study; the hanging head, the seated group and '
                     'the grid behind them')

    f_pair(N[32], N[33])

    w = N[34]
    f_open(w)
    f_sequence(w, {'layout': 'study', 'dom': aside(w, 'luciddrowning-v1'),
                   'domw': XL,
                   'after': [(aside(w, 'lucid-drowning-v2'), None,
                              'An earlier painted version, taken through in '
                              'pink, green and blue')],
                   'line': 'Annotated in pencil with the colours to be used — '
                           'pink, green, grey — then taken through in paint '
                           'twice; in the final canvas the border between body '
                           'and water is given up.'})

    f_open(N[35])

# ══ dizin ════════════════════════════════════════════════════════════
def index_spread():
    pl, pr = spread('Index')
    pl.fam = pr.fam = 'E'
    SECTIONS.append(('Index — the thirty-five at one width', pl.no))
    halves = (WORKS[:18], WORKS[18:])
    for p, items, lead in ((pl, halves[0], True), (pr, halves[1], False)):
        use(p)
        if lead:
            p.m(X(0), HEAD, W(8), 'The thirty-five, at one width')
        else:
            p.m(R(4), HEAD, W(4), 'Index <i>&middot;</i> 2019&ndash;2026', 'rt g')
        p.rule(X(0), HRULE, MEASURE, True)
        NC = 5
        rows = [items[i:i + NC] for i in range(0, len(items), NC)]
        stepx = MEASURE / NC
        cw = stepx - GUT
        Y0, CAP = 30.0, 7.0
        bh = ((FRULE - Y0) - len(rows) * (CAP + 6.0)) / len(rows)
        y = Y0
        for row in rows:
            for j, wk in enumerate(row):
                register(wk['plate']['src'], None, 'plate', 'index')
                ar = wk['ar']
                iw = min(cw, bh * ar); ih = iw / ar
                x = X(0) + j * stepx
                p.img(wk['plate']['src'], x, y + bh - ih, iw, ih,
                      wk['plate'].get('box'), 'ix%02d' % wk['n'], cls='ix')
                p.m(x, y + bh + 1.6, cw, '%02d <i>&middot;</i> %d'
                    % (wk['n'], FIRST.get(wk['n'], 0)), 'g')
            y += bh + CAP + 6.0
        p.rule(X(0), FRULE, MEASURE)
        if lead:
            p.m(X(0), FMICRO, W(8), 'Every plate at one width, in the order of the book')
        else:
            p.m(R(4), FMICRO, W(4), 'Work <i>&middot;</i> page', 'rt g')

# ══ tekrar edenler ═══════════════════════════════════════════════════
# Alti figur, alti ayri davranis. Buradaki kesitler kitabin baska hicbir
# yerinde gorunmez; bir yer geri geldiginde baska ya da daha genis bir
# kadrajla gelir.
MOTIF_AT = {}
RECUR_TOC = None

def msec(key):
    return next(s for s in MOTIFS['sections'] if s['key'] == key)

def mcrop(sec, n):
    c = next(c for c in sec['crops'] if c['n'] == n)
    wk = BY_N[n]
    return wk, crop_of(wk, c['box']), c['line']

def mcap(n, line):
    wk = BY_N[n]
    t = line[0].upper() + line[1:]
    return '%02d <i>&middot;</i> %s — %s' % (n, wk['year'], e(t))

def put_crop(p, sec, n, x, y, wd, tagx, widen_k=1.0, bottom=None, cap=True,
             capw=None, hi=1360, maxh=None):
    wk, bx, line = mcrop(sec, n)
    if widen_k != 1.0:
        cx, cy = bx[0] + bx[2] / 2, bx[1] + bx[3] / 2
        lim = wk['plate'].get('box') or [0, 0, 1, 1]
        nw, nh = min(lim[2], bx[2] * widen_k), min(lim[3], bx[3] * widen_k)
        bx = [min(max(lim[0], cx - nw / 2), lim[0] + lim[2] - nw),
              min(max(lim[1], cy - nh / 2), lim[1] + lim[3] - nh), nw, nh]
    register(wk['plate']['src'], bx, 'crop', 'motif %s %d' % (sec['key'], n))
    ar = ratio(wk['plate']['src'], bx)
    h = wd / ar
    if maxh and h > maxh:
        h = maxh; wd = h * ar
    if bottom is not None:
        y = bottom - h
    p.img(wk['plate']['src'], x, y, wd, h, bx,
          'm%s%02d%s' % (sec['key'][:2], n, tagx),
          cls='ix' if wd < S else '', hi=hi)
    if cap == 'short':
        # Dip siradaki tanik yalniz numarasini tasir; satiri anahtardadir.
        p.m(x, y + h + 2.0, wd, '%02d <i>&middot;</i> %s' % (n, BY_N[n]['year']), 'g')
    elif cap:
        p.m(x, y + h + 2.0, capw or max(wd, W(3.6)), mcap(n, line), 'g')
    return y, h

def motif_head(p, sec, y=18.0, tw=4.6):
    p.d(X(0), y, W(5), e(sec['name']), 's')
    p.m(X(0), y + 11.0, W(6), e(sec['lead']), 'g')
    p.t(X(0), y + 19.0, W(tw), '<p>%s</p><p>%s</p>' % (e(sec['a']), e(sec['b'])))

def recur_section():
    # Bolum acilisi: tam tasan kesit, ustunde bolumun adi; sagda alti
    # figurun tipografik icindekileri.
    pl, pr = spread('What comes back')
    pl.fam = pr.fam = 'R'
    SECTIONS.append(('What comes back — six recurring figures', pl.no))
    use(pl)
    sec0 = MOTIFS['sections'][0]
    wk0, bx0, _ = mcrop(sec0, 1)
    register(wk0['plate']['src'], bx0, 'crop', 'recur open')
    pl.cover_img(wk0['plate']['src'], -BLEED, -BLEED, PW + 2 * BLEED,
                 PH + 2 * BLEED, bx0, 'recur-open', '50% 60%')
    pl.raw('<div class="shade"></div>')
    pl.m(X(0), HEAD, W(6), 'Six things that come back', 'wh')
    pl.m(R(4), HEAD, W(4), '2019&ndash;2026', 'rt wh')
    pl.d(X(0), 224.0, W(10), 'What<br>comes back', 'l wh')
    pl.folio = False
    use(pr)
    pr.m(X(0), HEAD, W(6), 'What comes back')
    pr.m(R(4), HEAD, W(4), 'Contents', 'rt g')
    pr.rule(X(0), HRULE, MEASURE, True)
    global RECUR_TOC
    RECUR_TOC = pr

    m_onlooker(); m_chair(); m_crow(); m_cage(); m_body(); m_face()

def recur_toc_fill(p):
    use(p)
    y = 38.0
    for sec in MOTIFS['sections']:
        p.d(X(0), y, W(6), e(sec['name']), 's')
        p.m(X(0), y + 11.0, W(8),
            e(sec['lead']) + ' <i>&middot;</i> in %d paintings <i>&middot;</i> %s'
            % (len(sec['crops']),
               ' '.join('%02d' % c['n'] for c in sec['crops'])), 'g')
        p.m(R(1), y + 0.6, W(1), str(MOTIF_AT.get(sec['key'], 0)), 'rt')
        y += 37.4
        if sec is not MOTIFS['sections'][-1]:
            p.rule(X(0), y - 10.0, MEASURE)
    p.rule(X(0), FRULE, MEASURE)
    p.m(X(0), FMICRO, W(8),
        'Every cut in this chapter appears nowhere else in the book')
    p.m(R(2), FMICRO, W(2), 'Page', 'rt g')

def m_onlooker():
    # Dagilmis tanik: yedi kesit serimin dibinde ayni zeminde durur, biri
    # yukari alinmistir; egemen kesit ucunun dibinde durdugu yigindir.
    sec = msec('onlooker')
    pl, pr = spread(sec['name'])
    pl.fam = pr.fam = 'R'
    MOTIF_AT[sec['key']] = pl.no
    use(pl)
    motif_head(pl, sec)
    put_crop(pl, sec, 31, X(6), 0, S, 'r', bottom=REG[1] + 46.0)
    # 20 22 23 | 05 29 01: alti tanik, her biri bir oncekinden bir basamak
    # asagida. Genislik figurun tablodaki agirligini soyler.
    x = pl.X(0)
    for nn, ww, bs in ((20, 78.0, 240.0), (22, 54.0, 248.0), (23, 62.0, 256.0)):
        put_crop(pl, sec, nn, x, 0, ww, 'g', bottom=bs, maxh=96.0, capw=ww)
        x += ww + 5.0
    # Sirada duranlarin satirlari: metnin altinda bir anahtar
    use(pr)
    pr.m(X(6), 18.0, W(6),
         'The witness, in every painting it stands in: ranged across a board, '
         'along a boat, at the foot of the heap. Along the foot of the '
         'spread: 20, 22 and 23; 05, 29 and 01.', 'g')
    put_crop(pr, sec, 24, X(0), REG[1], L, 'd')
    x = pr.X(0)
    for nn, ww, bs, wk_ in ((5, 54.0, 262.0, 1.0), (29, 70.0, 268.0, 1.0),
                            (1, 48.0, 274.0, 1.5)):
        put_crop(pr, sec, nn, x, 0, ww, 'g', bottom=bs, widen_k=wk_,
                 maxh=96.0, capw=ww)
        x += ww + 5.0

def m_chair():
    # Yokluk: dort kesit, dordu de yalniz. Egemen olan bosluktur.
    sec = msec('chair')
    pl, pr = spread(sec['name'])
    pl.fam = pr.fam = 'R'
    MOTIF_AT[sec['key']] = pl.no
    use(pl)
    motif_head(pl, sec)
    FLOOR = 244.0
    put_crop(pl, sec, 35, X(0), 0, 70.0, 'b', bottom=FLOOR, maxh=120.0)
    put_crop(pl, sec, 22, X(7), 0, 48.0, 'a', bottom=FLOOR, maxh=120.0)
    use(pr)
    put_crop(pr, sec, 2, X(0), 0, 104.0, 'c', bottom=FLOOR, maxh=120.0)
    put_crop(pr, sec, 23, X(9), 0, 48.0, 'd', bottom=FLOOR, maxh=120.0)

def m_crow():
    # Yon: kus bedeni solda tam boy; ucus sag sayfada soldan saga,
    # asagidan yukari, son kesit ust kenardan tasarak cikar.
    sec = msec('crow')
    pl, pr = spread(sec['name'])
    pl.fam = pr.fam = 'R'
    MOTIF_AT[sec['key']] = pl.no
    use(pl)
    wk, bx, line = mcrop(sec, 19)
    register(wk['plate']['src'], bx, 'crop', 'motif crow 19')
    ar = ratio(wk['plate']['src'], bx)
    h = BAND_H; wd = h * ar
    if wd > W(9): wd = W(9); h = wd / ar
    pl.img(wk['plate']['src'], X(0), REG[0], wd, h, bx, 'mcr19', hi=1600)
    pl.m(X(0), REG[0] + h + 2.4, W(9), mcap(19, line), 'g')
    use(pr)
    motif_head(pr, sec, y=18.0, tw=4.2)
    for i, (nn, ww) in enumerate(((16, 68.0), (5, 62.0), (29, 56.0))):
        put_crop(pr, sec, nn, pr.X(3 + 2 * i), 0, ww, 'ab'[i:i + 1] or 'c',
                 bottom=262.0 - i * 74.0, maxh=66.0, capw=W(4))

def m_cage():
    # Cerceve: cizilen kurallar kapanmadan biter; kesitler uzerine oturur.
    sec = msec('cage')
    pl, pr = spread(sec['name'])
    pl.fam = pr.fam = 'R'
    MOTIF_AT[sec['key']] = pl.no
    use(pl)
    motif_head(pl, sec, tw=4.0)
    wk, bx, line = mcrop(sec, 15)
    register(wk['plate']['src'], bx, 'crop', 'motif cage 15')
    ar = ratio(wk['plate']['src'], bx)
    h = BAND_H; wd = h * ar
    x15 = pl.ml + MEASURE - wd
    pl.img(wk['plate']['src'], x15, REG[0], wd, h, bx, 'mcg15', hi=1600)
    pl.m(X(0), DBOT + 2.0, W(5), mcap(15, line), 'g')
    use(pr)
    pr.raw('<div class="r" style="left:%.2fmm;top:78.00mm;width:%.2fmm"></div>'
           % (-BLEED, pr.X(9) + BLEED))
    pr.vrule(pr.X(9), 78.0, 158.0)
    pr.rule(pr.X(3), 258.0, pr.ml + MEASURE - pr.X(3))
    WA, WB = W(6), W(5)
    put_crop(pr, sec, 2, X(0), 0, WA, 'a', bottom=112.0, maxh=88.0)
    put_crop(pr, sec, 6, X(7), 0, WB, 'd', bottom=112.0, maxh=88.0)
    put_crop(pr, sec, 35, X(0), 0, WB, 'b', bottom=252.0, maxh=118.0)
    put_crop(pr, sec, 20, X(7), 0, WB, 'c', bottom=252.0, maxh=118.0)

def m_body():
    # Birikim: alti kesit sifir olukla tek kutle, serimin dibinde, sirtta
    # yukselen bir hoyuk gibi; ustler duzensiz, hucre hucre bir siluet.
    sec = msec('body')
    pl, pr = spread(sec['name'])
    pl.fam = pr.fam = 'R'
    MOTIF_AT[sec['key']] = pl.no
    use(pl)
    motif_head(pl, sec)
    left  = [(3, 85.0), (8, 60.0), (17, 100.0)]
    right = [(24, 100.0), (9, 75.0), (27, 70.0)]
    keyed = []
    x = -BLEED
    for n, wd in left:
        wk, bx, line = mcrop(sec, n)
        register(wk['plate']['src'], bx, 'crop', 'motif body %d' % n)
        h = wd / ratio(wk['plate']['src'], bx)
        pl.img(wk['plate']['src'], x, DBOT - h, wd, h, bx, 'mbd%02d' % n, cls='butt')
        keyed.append((n, line)); x += wd
    use(pr)
    x = 0.0
    for n, wd in right:
        wk, bx, line = mcrop(sec, n)
        register(wk['plate']['src'], bx, 'crop', 'motif body %d' % n)
        h = wd / ratio(wk['plate']['src'], bx)
        pr.img(wk['plate']['src'], x, DBOT - h, wd, h, bx, 'mbd%02d' % n, cls='butt')
        keyed.append((n, line)); x += wd
    pr.m(X(6), 18.0, W(6), '<br>'.join(mcap(n, l) for n, l in keyed), 'g')
    pr.m(X(6), 18.0 + sum(micro_h(len(l) + 12, W(6)) for _, l in keyed) + 4.0,
         W(6), 'Left to right along the foot of the spread', 'g')

def m_face():
    # Yuzlesme: yuzu olmayan bas ile ustune cizile cizile yapilmis yuz
    # sirtta goz goze; kalan dort yuz iki dogrudan cift olarak altta.
    sec = msec('face')
    pl, pr = spread(sec['name'])
    pl.fam = pr.fam = 'R'
    MOTIF_AT[sec['key']] = pl.no
    use(pl)
    motif_head(pl, sec, tw=4.4)
    wk, bx, line = mcrop(sec, 18)
    register(wk['plate']['src'], bx, 'crop', 'motif face 18')
    ar = ratio(wk['plate']['src'], bx)
    wd = W(10); h = wd / ar
    x = pl.ml + MEASURE - wd
    y = DBOT - h
    pl.img(wk['plate']['src'], x, y, wd, h, bx, 'mfc18', hi=1600)
    pl.m(x, y - 6.0, wd, mcap(18, line), 'g')
    use(pr)
    wk2, bx2, line2 = mcrop(sec, 32)
    register(wk2['plate']['src'], bx2, 'crop', 'motif face 32')
    ar2 = ratio(wk2['plate']['src'], bx2)
    wd2 = MEASURE; h2 = wd2 / ar2
    pr.img(wk2['plate']['src'], X(0), REG[0], wd2, h2, bx2, 'mfc32', hi=1600)
    pr.m(X(0), REG[0] + h2 + 2.4, W(11), mcap(32, line2) +
         ' <i>&middot;</i> facing it, ' + mcap(18, line), 'g')
    yb = 224.0
    hh = 30.0
    x = X(0)
    caps = []
    for a, b in ((1, 12), (21, 27)):
        x0 = x
        for n in (a, b):
            wk3, bx3, line3 = mcrop(sec, n)
            register(wk3['plate']['src'], bx3, 'crop', 'motif face %d' % n)
            ar3 = ratio(wk3['plate']['src'], bx3)
            wd3 = hh * ar3
            pr.img(wk3['plate']['src'], x, yb, wd3, hh, bx3, 'mfcp%02d' % n,
                   cls='butt ix')
            x += wd3
        caps.append((x0, x - x0, '%02d against %02d' % (a, b)))
        x += 10.0
    for x0, wd0, t in caps:
        pr.m(x0, yb + hh + 2.0, wd0 + 10.0, t, 'g')
    pr.m(X(0), yb + hh + 8.0, W(11),
         'The face is where the painting decides whether there is a person '
         'here, and often declines to decide', 'g')

# ══ kapanis ══════════════════════════════════════════════════════════
def closing():
    pl, pr = spread('Colophon')
    pl.fam = pr.fam = 'E'
    SECTIONS.append(('Colophon', pl.no))
    use(pl)
    pl.m(X(0), HEAD, W(6), 'Colophon')
    pl.m(R(4), HEAD, W(4), NM, 'rt g')
    pl.rule(X(0), HRULE, MEASURE, True)
    pl.sans(X(0), 34.0, W(5),
        '<p>All works by Yiğit Özen, born 1994 in Istanbul and trained as an '
        'architect. They are given newest first, so a paragraph that says a '
        'thing happens for the first time means the first time reading '
        'backwards through the book.</p>'
        '<p>Dimensions are width by height, in centimetres and then in inches.</p>'
        '<p>Photography by the artist. Plates and details reproduce documentation '
        'of the paintings; colour and surface differ from the works themselves. '
        'The files are set at about 137 pixels to the inch of printed width, '
        'made for reading and for screens rather than for offset printing.</p>'
        '<p>Detail photography exists for fourteen of the thirty-five. Where it '
        'does not, the work is shown through its plate alone; where a cut is '
        'taken from a plate — in the chapter on what comes back, and three '
        'times in the work sections — the caption says where it is.</p>')
    pl.sans(X(6), 34.0, W(6),
        '<p>Where a paragraph gives a proportion or a percentage, it was measured '
        'on the documentation file rather than on the painting, and it describes '
        'that file. No colour target was used in the photography, so the figures '
        'are a reading of the photograph and not a colorimetric claim about the '
        'paint.</p>'
        '<p>Titles are set as the artist writes them, in his spelling and his '
        'punctuation. <em>il sbagliato di rompipalle</em>, <em>sono squalo</em> '
        'and <em>caprocorn</em> are his, not slips of the setting.</p>'
        '<p>Sources for the two borrowed reference images and for the epigraph '
        'on 03 are given on the pages they appear on.</p>'
        '<p>A caption gives where in the painting the cut is, and then what the '
        'hand did there, taken from that work&rsquo;s own note on colour, '
        'composition or hand. Every cut is printed once in the book; when a '
        'place returns in the chapter on what comes back, it returns as a '
        'different or a wider cut.</p>'
        '<p>A picture that bleeds is cut by the sheet; every painting treated '
        'this way is also printed whole in its own opening and in the index.</p>'
        '<p>Set in Inter and in Newsreader, both under the SIL Open Font '
        'License; the files are embedded. A short selection of the same works '
        'is published separately for sending; the thirty-five are also at '
        'yigitozen.xyz, where every photograph can be seen at full size.</p>'
        '<p>All works &copy; Yiğit Özen. All rights reserved.</p>')
    pl.rule(X(0), FRULE, MEASURE)
    pl.m(X(0), FMICRO, W(4), 'x@yigitozen.xyz')
    pl.m(X(4), FMICRO, W(4), 'Instagram @yjgjf')
    pl.m(R(4), FMICRO, W(4), 'yigitozen.xyz <i>&middot;</i> de-centralize.com', 'rt g')

    # Kapanis: kapak kesitinin tablodaki yeri. Kitap nereden acildiysa
    # orayi gostererek kapanir.
    use(pr)
    w1 = BY_N[1]
    register(w1['plate']['src'], None, 'plate', 'close')
    wd = W(8)
    h = wd / w1['ar']
    x = pr.ml + (MEASURE - wd) / 2.0
    y = REG[1]
    pr.img(w1['plate']['src'], x, y, wd, h, w1['plate'].get('box'), 'closep01',
           cls='pl')
    pr.frame(x + COVER_ON_PLATE[0] * wd, y + COVER_ON_PLATE[1] * h,
             COVER_ON_PLATE[2] * wd, COVER_ON_PLATE[3] * h)
    pr.m(x, y + h + 3.0, wd,
         'The cover, marked where it was cut from 01 <i>&middot;</i> '
         '7 fam board game', 'g')
    pr.raw('<img class="mark" src="images/logo.svg" '
           'style="left:%.2fmm;top:250mm;width:26mm">' % (PW / 2 - 13))

# ══ kurulum ══════════════════════════════════════════════════════════
SELECT = [1, 2, 5, 8, 15, 22, 34, 35]

front_matter()

if SHORT:
    for n in SELECT:
        f_open(BY_N[n])
    m_face()
    p = page('Index')
    use(p)
    p.m(X(0), HEAD, W(8), 'The thirty-five, at one width')
    p.rule(X(0), HRULE, MEASURE, True)
    NC, Y0, CAP = 7, 30.0, 6.0
    rows = [WORKS[i:i + NC] for i in range(0, len(WORKS), NC)]
    stepx = MEASURE / NC
    cw = stepx - GUT
    bh = ((FRULE - Y0) - len(rows) * (CAP + 4.0)) / len(rows)
    y = Y0
    for row in rows:
        for j, wk in enumerate(row):
            ar = wk['ar']
            iw = min(cw, bh * ar); ih = iw / ar
            p.img(wk['plate']['src'], X(0) + j * stepx, y + bh - ih, iw, ih,
                  wk['plate'].get('box'), 'ix%02d' % wk['n'], cls='ix')
            p.m(X(0) + j * stepx, y + bh + 1.6, cw, '%02d' % wk['n'], 'g')
        y += bh + CAP + 4.0
    p.rule(X(0), FRULE, MEASURE)
    p.m(X(0), FMICRO, W(8), 'Every plate at one width, in the order of the book')
    p = page('Colophon')
    p.m(X(0), HEAD, W(6), 'Colophon')
    p.rule(X(0), HRULE, MEASURE, True)
    p.sans(X(0), 34.0, W(6), '<p>%s</p><p>All works &copy; Yiğit Özen. All '
           'rights reserved. Set in Inter and Newsreader, under the SIL Open '
           'Font License.</p>' % e(SHORT_BLURB))
    last = page('', 'plate')
    last.folio = False
    last.raw('<img class="mark" src="images/logo.svg" '
             'style="left:%.2fmm;top:139mm;width:42mm">' % (PW / 2 - 21))
else:
    SECTIONS.append(('On the work', 4))
    SECTIONS.append(('Biography and exhibitions', 6))
    build_works()
    index_spread()
    recur_section()
    closing()
    SECTIONS.sort(key=lambda s: s[1])
    toc_fill(TOC)
    recur_toc_fill(RECUR_TOC)

# ── aile ritmi: ayni aile ust uste en cok iki serim ──────────────────
if not SHORT:
    fams = []
    for i in range(9, len(PAGES) - 1, 2):
        fams.append((i + 1, PAGES[i].fam))
    run_f, run_n = None, 0
    for pno, f in fams:
        if f == run_f:
            run_n += 1
            if f in 'BCD' and run_n > 2:
                raise SystemExit('aile uc kez ust uste: %s, sayfa %d' % (f, pno))
        else:
            run_f, run_n = f, 1

# ══ yaz ══════════════════════════════════════════════════════════════
out = ['<!doctype html>', '<html lang="en">', '<head>', '<meta charset="utf-8">',
       '<title>Yiğit Özen &mdash; Paintings since 2019</title>',
       '<link rel="stylesheet" href="book.css">', '</head>',
       '<body class="bleed">' if PRINT else '<body>', '']
for i, p in enumerate(PAGES, start=1):
    side = 'L' if i % 2 == 0 else 'R'
    foot = ''
    if p.folio:
        if side == 'L':
            foot = ('<div class="b f" style="left:%.2fmm;top:%.2fmm;width:%.2fmm">'
                    '%d&ensp;<span>%s</span></div>'
                    % (p.X(0), FOLIO_Y, W(6), i, p.run or 'Yiğit Özen'))
        else:
            foot = ('<div class="b f rt" style="left:%.2fmm;top:%.2fmm;width:%.2fmm">%d</div>'
                    % (p.R(2), FOLIO_Y, W(2), i))
    out.append('<section class="pg %s%s" data-fam="%s"><div class="tp">%s%s</div></section>'
               % (side, (' ' + p.klass if p.klass else ''), p.fam,
                  ''.join(p.bits), foot))
    out.append('')
out += ['</body>', '</html>', '']
HTML = 'book-print.html' if PRINT else ('book-short.html' if SHORT else 'book.html')
open(os.path.join(HERE, HTML), 'w', encoding='utf-8').write('\n'.join(out))

marks = [('Cover', 1), ('Imprint', 2), ('Paintings since 2019', 3),
         ('On the work', 4), ('Biography', 6), ('Contents', 9)]
marks = [(n, i) for n, i in marks if i <= len(PAGES) and not SHORT or n == 'Cover']
if SHORT:
    marks = [('Cover', 1), ('Imprint', 2), ('Paintings since 2019', 3)]
for wk in (WORKS if not SHORT else [BY_N[n] for n in SELECT]):
    if wk['n'] in FIRST:
        marks.append(('%02d  %s' % (wk['n'], wk['title']), FIRST[wk['n']]))
first_run = {}
for i, p in enumerate(PAGES, start=1):
    if p.run and p.run not in first_run: first_run[p.run] = i
for name in ['Index', 'What comes back'] + [x['name'] for x in MOTIFS['sections']] + ['Colophon']:
    if name in first_run: marks.append((name, first_run[name]))
json.dump({'marks': marks, 'pages': len(PAGES), 'short': SHORT},
          open(os.path.join(HERE, 'outline-short.json' if SHORT else 'outline.json'),
               'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# Kesitlerin kunyesi, uretildikleri klasorun yaninda durur. Duzeni disari
# aktaran betik bunu okur: bir gorsel sayfada buyutulmusse onceden kesilmis
# dosya yetmez, kaynaga donup yeniden keser.
if not SHORT:
    json.dump(MANIFEST, open(os.path.join(OUT, 'manifest.json'), 'w',
                             encoding='utf-8'), ensure_ascii=False, indent=0)

# Kullanilmayan gorseller ayiklanir; kisa basim ayni adlari kullanir.
if not SHORT:
    for f in os.listdir(OUT):
        if f.endswith('.jpg') and f not in MADE:
            os.remove(os.path.join(OUT, f))

if not SHORT and not (126 <= len(PAGES) <= 146):
    raise SystemExit('sayfa sayisi hedef disi: %d' % len(PAGES))

print('pages: %d' % len(PAGES))
print('images: %d' % len(MADE))
