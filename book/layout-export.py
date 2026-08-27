# -*- coding: utf-8 -*-
"""
booklet-layout.json -> iki PDF

Duzenleyicide "Düzeni indir" dedigin dosyayi alir ve kitabi ayni duzenle
iki kez basar:

  Yigit-Ozen-Paintings-Print-Master.pdf   246 x 326 mm, 300 ppi'lik set,
                                          her kenarda 3 mm tasma payi
  Yigit-Ozen-Paintings-Web.pdf            240 x 320 mm, ekran seti

Tarayicinin yazdir penceresinden gecmez: dosyalar burada, her seferinde
ayni bicimde uretilir. Yazi yazi olarak kalir, gorsel buyutulmez.

    python3 layout-export.py booklet-layout.json
    python3 layout-export.py booklet-layout.json --double   # web dosyasi acilim
    python3 layout-export.py booklet-layout.json --only web

Duzeni sitedeki duzenleyiciden de, depodakinden de alabilirsin: gorsel
yollari iki bicimde de taninir.
"""
import os, sys, json, re, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, os.pardir))
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
DOUBLE = '--double' in sys.argv
ONLY = None
for i, a in enumerate(sys.argv):
    if a == '--only' and i + 1 < len(sys.argv): ONLY = sys.argv[i + 1]

SRC = ARGS[0] if ARGS else os.path.join(REPO, 'editor', 'model.json')
PW, PH = 240.0, 320.0

# ── gorsel klasorleri: duzen sitedeki kopyadan da gelebilir ─────────
# Sitede yollar 'img/x.jpg', depoda 'editor/img/x.jpg'. Ikisi de ayni
# dosyayi gosterir; burada mutlak yola cevrilir ki HTML nerede durursa
# dursun gorsel bulunsun.
CAND = [os.path.join(REPO, 'editor'), os.path.join(REPO, 'book'),
        os.path.abspath(os.path.join(REPO, os.pardir, 'yigit', 'booklet-editor'))]
ROOTS = [d for d in CAND if os.path.isdir(os.path.join(d, 'img'))]
if not ROOTS:
    sys.exit('gorsel klasoru bulunamadi: editor/img aranan yerlerde yok')

CSS = None
for d in ROOTS + [HERE]:
    if os.path.isfile(os.path.join(d, 'book.css')):
        CSS = os.path.join(d, 'book.css'); break
if not CSS: sys.exit('book.css bulunamadi')


def find(src, hq):
    """Gorselin diskteki yeri. hq ise once baski seti aranir."""
    base = os.path.basename(src)
    folders = (['img-print', 'img'] if hq else ['img'])
    for d in ROOTS:
        for f in folders:
            p = os.path.join(d, f, base)
            if os.path.isfile(p): return p
    return None


MISSING, FELLBACK = set(), set()


def url(src, hq):
    p = find(src, hq)
    if not p:
        MISSING.add(os.path.basename(src)); return src
    if hq and os.sep + 'img' + os.sep in p and 'img-print' not in p:
        FELLBACK.add(os.path.basename(src))
    return 'file://' + p


def draw(e, hq):
    t = e.get('t')
    if t == 'img':
        cls = (' class="%s"' % e['cls']) if e.get('cls') else ''
        pos = (';object-position:%s' % e['pos']) if e.get('pos') else ''
        return ('<img%s src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;'
                'height:%.2fmm%s">' % (cls, url(e['src'], hq), e['x'], e['y'],
                                       e['w'], e['h'], pos))
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
  await p.goto('file://'+path.resolve(file),{waitUntil:'load',timeout:600000});
  await p.waitForFunction(()=>Array.from(document.images)
    .every(i=>i.complete&&i.naturalWidth>0),{timeout:600000});
  await p.evaluate(()=>document.fonts&&document.fonts.ready);
  // Kagida dusen gercek cozunurluk, yerlestirildigi olcuye gore.
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
print('duzen: %s  —  %d sayfa' % (os.path.basename(SRC), len(pages)))

pr = os.path.join(HERE, '_printer.js')
open(pr, 'w', encoding='utf-8').write(PRINTER)

JOBS = [
    ('print', 'Yigit-Ozen-Paintings-Print-Master.pdf', True, 3.0, False,
     'baski ustasi · 300 ppi set · 3 mm tasma'),
    ('web', 'Yigit-Ozen-Paintings-Web.pdf', False, 0.0, DOUBLE,
     'web · ekran seti · kesim olcusu'),
]
env = dict(os.environ)
env.setdefault('NODE_PATH', os.path.join(HERE, 'node_modules'))

for name, fn, hq, bleed, dbl, label in JOBS:
    if ONLY and ONLY != name: continue
    MISSING.clear(); FELLBACK.clear()
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
    if FELLBACK:
        print('  ! baski seti yok, ekran dosyasi kullanildi: %d (%s)'
              % (len(FELLBACK), ', '.join(sorted(FELLBACK)[:3])))
    if MISSING:
        print('  ! bulunamayan gorsel: %d (%s)'
              % (len(MISSING), ', '.join(sorted(MISSING)[:3])))
    os.remove(tmp)

os.remove(pr)
