# -*- coding: utf-8 -*-
"""
booklet-layout.json -> iki PDF

Duzenleyicide "Düzeni indir" dedigin dosyayi alir ve kitabi ayni duzenle
iki kez basar:

  Yigit-Ozen-Paintings-Print-Master.pdf   246 x 326 mm, 3 mm tasma payi,
                                          her gorsel yerlestirildigi
                                          olcude 300 ppi hedefiyle
  Yigit-Ozen-Paintings-Web.pdf            240 x 320 mm, ekran seti

Onemli olan sudur: onceden kesilmis dosyalari oldugu gibi kullanmaz.
Duzeni okur, her gorselin sayfada kac milimetre oldugunu gorur, kunyeden
o kesitin hangi kaynaktan hangi kadrajla alindigini bulur ve kaynak
yetiyorsa o olcu icin yeniden keser. Boylece editorde bir resmi
buyuttugunde cikti da buyur; kucultursen dosya kucultulur. Kaynakta
olmayan piksel hicbir kosulda uydurulmaz.

    python3 layout-export.py booklet-layout.json
    python3 layout-export.py booklet-layout.json --double   # web acilim
    python3 layout-export.py booklet-layout.json --only web
    python3 layout-export.py booklet-layout.json --ppi 400  # baski hedefi
"""
import os, sys, json, re, subprocess, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, os.pardir))
SITE = os.path.abspath(os.path.join(REPO, os.pardir, 'yigit'))
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
DOUBLE = '--double' in sys.argv
ONLY = None
TARGET = 300.0
for i, a in enumerate(sys.argv):
    if a == '--only' and i + 1 < len(sys.argv): ONLY = sys.argv[i + 1]
    if a == '--ppi' and i + 1 < len(sys.argv): TARGET = float(sys.argv[i + 1])

SRC = ARGS[0] if ARGS else os.path.join(REPO, 'editor', 'model.json')
PW, PH = 240.0, 320.0
WEB_PPI = 203.0

from PIL import Image
Image.MAX_IMAGE_PIXELS = None

# ── nerede ne var ───────────────────────────────────────────────────
# Duzen sitedeki kopyadan da gelebilir: orada yollar 'img/x.jpg',
# depoda 'editor/img/x.jpg'. Ikisi de ayni dosyayi gosterir.
CAND = [os.path.join(REPO, 'editor'), os.path.join(REPO, 'book'),
        os.path.join(SITE, 'booklet-editor')]
ROOTS = [d for d in CAND if os.path.isdir(os.path.join(d, 'img'))]
SETS = [os.path.join(HERE, 'images-print'), os.path.join(HERE, 'images')]
if not ROOTS and not any(os.path.isdir(d) for d in SETS):
    sys.exit('gorsel klasoru bulunamadi')

CSS = next((os.path.join(d, 'book.css') for d in ROOTS + [HERE]
            if os.path.isfile(os.path.join(d, 'book.css'))), None)
if not CSS: sys.exit('book.css bulunamadi')

# ── kunye: hangi kesit hangi kaynaktan, hangi kadrajla ──────────────
MAN = {}
for d in SETS:
    p = os.path.join(d, 'manifest.json')
    if os.path.isfile(p):
        for k, v in json.load(open(p, encoding='utf-8')).items():
            # Kaynakta en genis olani tut
            if k not in MAN or v.get('srcpx', 0) > MAN[k].get('srcpx', 0):
                MAN[k] = v

CUT = os.path.join(HERE, '.cut')
if not os.path.isdir(CUT): os.makedirs(CUT)

STAT = {'recut': 0, 'reused': 0, 'capped': [], 'missing': set(), 'gained': []}


def source_of(rec):
    """Kunyedeki kaynagi diskte bul: once depo, sonra site."""
    f = rec.get('from') or ''
    for base in (REPO, HERE, SITE):
        p = os.path.join(base, f)
        if os.path.isfile(p): return p
    s = (rec.get('src') or '').lstrip('/')
    p = os.path.join(SITE, s)
    return p if os.path.isfile(p) else None


def precut(base, hq):
    """Onceden kesilmis dosya, varsa."""
    folders = (['img-print', 'img'] if hq else ['img'])
    for d in ROOTS:
        for f in folders:
            p = os.path.join(d, f, base)
            if os.path.isfile(p): return p
    for d in (SETS if hq else SETS[::-1]):
        p = os.path.join(d, base)
        if os.path.isfile(p): return p
    return None


def resolve(src, mm, hq):
    """Bu yerlestirme icin kullanilacak dosyanin yolu.

    Sayfada mm genisliginde basilacaksa hedef cozunurluk kadar piksel
    istenir. Onceden kesilmis dosya yetiyorsa o kullanilir; yetmiyor ve
    kaynak daha genisse kaynaktan yeniden kesilir; kaynak da yetmiyorsa
    elde ne varsa o basilir ve rapora yazilir.
    """
    base = os.path.basename(src)
    if base.endswith('.svg'):
        p = precut(base, hq)
        return p or src
    ppi = TARGET if hq else WEB_PPI
    need = int(round(mm / 25.4 * ppi))
    have_p = precut(base, hq)
    have = 0
    if have_p:
        try: have = Image.open(have_p).size[0]
        except Exception: have = 0
    rec = MAN.get(base)
    if not rec:
        if not have_p: STAT['missing'].add(base)
        else: STAT['reused'] += 1
        return have_p or src
    # Kadrajdan sonra kaynakta gercekten kalan genislik
    boxw = (rec['box'][2] if rec.get('box') else 1.0)
    limit = int(rec.get('srcpx', 0) * boxw)
    if have >= need or limit <= have:
        STAT['reused'] += 1
        if have < need:
            STAT['capped'].append((base, mm, have, need))
        return have_p or src
    want = min(need, limit)
    key = hashlib.md5(('%s|%d|%s' % (base, want, hq)).encode()).hexdigest()[:10]
    out = os.path.join(CUT, '%s-%d-%s.jpg' % (os.path.splitext(base)[0], want, key))
    if not os.path.isfile(out):
        sp = source_of(rec)
        if not sp:
            STAT['missing'].add(base); return have_p or src
        im = Image.open(sp)
        if im.mode not in ('RGB', 'L'): im = im.convert('RGB')
        if rec.get('box'):
            b, (w, h) = rec['box'], im.size
            im = im.crop((int(b[0] * w), int(b[1] * h),
                          int((b[0] + b[2]) * w), int((b[1] + b[3]) * h)))
        if im.size[0] > want:
            ar = im.size[0] / float(im.size[1])
            im = im.resize((want, max(1, int(round(want / ar)))), Image.LANCZOS)
        im.convert('RGB').save(out, 'JPEG', quality=88 if hq else 78,
                               optimize=True, subsampling=0 if hq else 2)
    STAT['recut'] += 1
    STAT['gained'].append((base, have, want))
    if want < need: STAT['capped'].append((base, mm, want, need))
    return out


def url(p):
    return ('file://' + p) if os.path.isabs(p) else p


def draw(e, hq):
    t = e.get('t')
    if t == 'img':
        cls = (' class="%s"' % e['cls']) if e.get('cls') else ''
        pos = (';object-position:%s' % e['pos']) if e.get('pos') else ''
        return ('<img%s src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;'
                'height:%.2fmm%s">' % (cls, url(resolve(e['src'], e['w'], hq)),
                                       e['x'], e['y'], e['w'], e['h'], pos))
    if t == 'txt':
        extra = (';' + e['style']) if e.get('style') else ''
        return ('<div class="b %s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm%s">'
                '%s</div>' % (e.get('cls', ''), e['x'], e['y'], e['w'], extra,
                              e.get('html', '')))
    if t == 'rule':
        wh = ''
        if e.get('w'): wh += ';width:%.2fmm' % e['w']
        if e.get('h'): wh += ';height:%.2fmm;width:.35pt' % e['h']
        return ('<div class="%s" style="left:%.2fmm;top:%.2fmm%s"></div>'
                % (e.get('cls', 'r'), e['x'], e['y'], wh))
    if t == 'frame':
        return ('<div class="fr" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;'
                'height:%.2fmm"></div>' % (e['x'], e['y'], e['w'], e['h']))
    return '<div class="shade"></div>'


def build(pages, hq, bleed, double, out):
    def page_html(i):
        p = pages[i]
        return ('<section class="pg %s"><div class="tp">%s</div></section>'
                % (p.get('cls', ''), ''.join(draw(e, hq) for e in p['els'])))

    # Kitap tek yapraklik bir kapakla acilir, sonrasi ciftler halinde gider.
    if double:
        groups = [[0]] + [[i, i + 1] if i + 1 < len(pages) else [i]
                          for i in range(1, len(pages), 2)]
    else:
        groups = [[i] for i in range(len(pages))]

    sw = PW * 2 if double else PW
    sheets = []
    for g in groups:
        inner = ''
        if double and len(g) == 1 and g[0] != 0:
            inner += '<div class="pg" style="background:#fff"></div>'
        inner += ''.join(page_html(i) for i in g)
        sheets.append('<div class="sheet"><div class="sheetin">%s</div></div>' % inner)

    html = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Yigit Ozen &mdash; Paintings since 2019</title>
<link rel="stylesheet" href="file://%s">
<style>
html,body{margin:0;padding:0;background:#fff}
@page{size:%.0fmm %.0fmm;margin:0}
.sheet{width:%.0fmm;height:%.0fmm;position:relative;overflow:hidden;background:#fff;
  page-break-after:always;break-after:page}
.sheet:last-child{page-break-after:auto;break-after:auto}
.sheetin{position:absolute;left:%.0fmm;top:%.0fmm;width:%.0fmm;height:%.0fmm;display:flex}
.pg{width:%.0fmm;height:%.0fmm;color:#111}
.pg.dark{color:#fff}
.tp{left:0;top:0}
</style></head><body>
%s
</body></html>
""" % (CSS, sw + 2 * bleed, PH + 2 * bleed, sw + 2 * bleed, PH + 2 * bleed,
       bleed, bleed, sw, PH, PW, PH, '\n'.join(sheets))
    open(out, 'w', encoding='utf-8').write(html)
    return len(groups), sw + 2 * bleed, PH + 2 * bleed


PRINTER = r"""
const path=require('path');
function load(){for(const m of ['playwright','playwright-core']){try{return require(m);}catch(e){}}
  throw new Error('playwright yok: npm i -D playwright-core');}
const {chromium}=load();
const [,,file,out,wmm,hmm]=process.argv;
(async()=>{
  const b=await chromium.launch(process.env.PLAYWRIGHT_CHROMIUM
    ?{executablePath:process.env.PLAYWRIGHT_CHROMIUM,args:['--no-sandbox']}:{});
  const p=await b.newPage();
  await p.goto('file://'+path.resolve(file),{waitUntil:'load',timeout:900000});
  await p.waitForFunction(()=>Array.from(document.images)
    .every(i=>i.complete&&i.naturalWidth>0),{timeout:900000});
  await p.evaluate(()=>document.fonts&&document.fonts.ready);
  const ppi=await p.evaluate(()=>{const MM=96/25.4;
    return [...document.images].filter(i=>!i.src.endsWith('.svg'))
      .map(i=>i.naturalWidth/((i.getBoundingClientRect().width/MM)/25.4))
      .filter(x=>isFinite(x)&&x>0).sort((a,c)=>a-c);});
  await p.pdf({path:out,width:wmm+'mm',height:hmm+'mm',printBackground:true,
               margin:{top:'0',right:'0',bottom:'0',left:'0'},preferCSSPageSize:true});
  const q=f=>Math.round(ppi[Math.floor(f*(ppi.length-1))]);
  console.log(JSON.stringify({n:ppi.length,min:q(0),p10:q(.1),med:q(.5),max:q(1),
    under240:ppi.filter(x=>x<240).length,under150:ppi.filter(x=>x<150).length}));
  await b.close();})().catch(e=>{console.error(e);process.exit(2);});
"""

m = json.load(open(SRC, encoding='utf-8'))
pages = m['pages'] if isinstance(m, dict) and 'pages' in m else m
print('duzen: %s  —  %d sayfa  ·  kunye %d kesit'
      % (os.path.basename(SRC), len(pages), len(MAN)))

pr = os.path.join(HERE, '_printer.js')
open(pr, 'w', encoding='utf-8').write(PRINTER)

JOBS = [
    ('print', 'Yigit-Ozen-Paintings-Print-Master.pdf', True, 3.0, False,
     'baski ustasi · %d ppi hedef · 3 mm tasma' % TARGET),
    ('web', 'Yigit-Ozen-Paintings-Web.pdf', False, 0.0, DOUBLE,
     'web · %d ppi hedef · kesim olcusu' % WEB_PPI),
]
env = dict(os.environ)
env.setdefault('NODE_PATH', os.path.join(HERE, 'node_modules'))

for name, fn, hq, bleed, dbl, label in JOBS:
    if ONLY and ONLY != name: continue
    for k in ('recut', 'reused'): STAT[k] = 0
    STAT['capped'], STAT['gained'] = [], []
    STAT['missing'] = set()
    tmp = os.path.join(HERE, '_layout-%s.html' % name)
    out = os.path.join(REPO, fn)
    n, w, h = build(pages, hq, bleed, dbl, tmp)
    r = subprocess.run(['node', pr, tmp, out, '%.0f' % w, '%.0f' % h],
                       capture_output=True, text=True, env=env)
    if r.returncode:
        print('  %-6s BASARISIZ\n%s' % (name, r.stderr.strip()[:400])); continue
    s = json.loads(r.stdout.strip().splitlines()[-1])
    mb = os.path.getsize(out) / 1048576.0
    print('\n%s  (%s)' % (fn, label))
    print('  %d levha · %.0f x %.0f mm · %.1f MB' % (n, w, h, mb))
    print('  gorsel %d · ortanca %d ppi · en dusuk %d · 240 alti %d · 150 alti %d'
          % (s['n'], s['med'], s['min'], s['under240'], s['under150']))
    print('  kaynaktan yeniden kesilen %d · hazir dosyadan %d'
          % (STAT['recut'], STAT['reused']))
    big = sorted(STAT['gained'], key=lambda g: g[1] and -(g[2] / g[1]) or 0)[:3]
    for b0, was, now in big:
        if was and now > was * 1.05:
            print('     %-26s %d -> %d px' % (b0[:26], was, now))
    if STAT['capped']:
        worst = sorted(STAT['capped'], key=lambda c: c[2] / float(c[3]))[:3]
        print('  kaynak sinirli %d kesit, en kotu:' % len(STAT['capped']))
        for b0, mmw, hv, nd in worst:
            print('     %-26s %.0fmm icin %d px var, %d gerekli (%d ppi)'
                  % (b0[:26], mmw, hv, nd, round(hv / (mmw / 25.4))))
    if STAT['missing']:
        print('  ! bulunamayan: %d (%s)'
              % (len(STAT['missing']), ', '.join(sorted(STAT['missing'])[:3])))
    os.remove(tmp)

os.remove(pr)
