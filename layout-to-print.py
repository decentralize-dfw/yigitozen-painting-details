# -*- coding: utf-8 -*-
"""
booklet-layout.json -> baskiya hazir HTML

Duzenleyicide "Düzeni indir" dedigin dosyayi alir ve kitabi ayni olculerle
yeniden kurar: 246 x 326 mm, yani 240 x 320 kesim ve her kenarda 3 mm tasma
payi, gorseller 300 ppi'lik setten. Tarayicidan cikan dosyanin ayni sinden
cikar; fark, bunun bir komutla ve her seferinde ayni bicimde uretilmesidir.

    python3 layout-to-print.py booklet-layout.json            # tek sayfa
    python3 layout-to-print.py booklet-layout.json --double   # acilim
    python3 layout-to-print.py booklet-layout.json --web      # kesim olcusu

Sonra:
    node -e "require('playwright-core').chromium.launch(...)"  # ya da print.js
"""
import os, sys, json, re

HERE = os.path.dirname(os.path.abspath(__file__))
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
DOUBLE = '--double' in sys.argv
WEB = '--web' in sys.argv
SRC = ARGS[0] if ARGS else os.path.join(HERE, 'editor', 'model.json')
OUT = os.path.join(HERE, 'layout-print.html')

PW, PH = 240.0, 320.0
BL = 0.0 if WEB else 3.0
SW = PW * 2 if DOUBLE else PW

m = json.load(open(SRC, encoding='utf-8'))
pages = m['pages']

def hi(src):
    """Baski setine cevirir; adlar ayni oldugu icin klasor degisir."""
    return src if WEB else re.sub(r'(^|/)img/', r'\1img-print/', src)

def draw(e):
    if e['t'] == 'img':
        cls = (' class="%s"' % e['cls']) if e.get('cls') else ''
        pos = (';object-position:%s' % e['pos']) if e.get('pos') else ''
        return ('<img%s src="%s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;'
                'height:%.2fmm%s">' % (cls, hi(e['src']), e['x'], e['y'],
                                       e['w'], e['h'], pos))
    if e['t'] == 'txt':
        extra = (';' + e['style']) if e.get('style') else ''
        return ('<div class="b %s" style="left:%.2fmm;top:%.2fmm;width:%.2fmm%s">'
                '%s</div>' % (e.get('cls', ''), e['x'], e['y'], e['w'], extra,
                              e.get('html', '')))
    if e['t'] == 'rule':
        wh = ''
        if e.get('w'): wh += ';width:%.2fmm' % e['w']
        if e.get('h'): wh += ';height:%.2fmm;width:.35pt' % e['h']
        return ('<div class="%s" style="left:%.2fmm;top:%.2fmm%s"></div>'
                % (e.get('cls', 'r'), e['x'], e['y'], wh))
    if e['t'] == 'frame':
        return ('<div class="fr" style="left:%.2fmm;top:%.2fmm;width:%.2fmm;'
                'height:%.2fmm"></div>' % (e['x'], e['y'], e['w'], e['h']))
    return '<div class="shade"></div>'

def page_html(i):
    p = pages[i]
    return ('<section class="pg %s"><div class="tp">%s</div></section>'
            % (p.get('cls', ''), ''.join(draw(e) for e in p['els'])))

# Kitap tek yapraklik bir kapakla acilir, sonrasi ciftler halinde gider.
groups = [[0]] + [[i, i + 1] if i + 1 < len(pages) else [i]
                  for i in range(1, len(pages), 2)] if DOUBLE \
         else [[i] for i in range(len(pages))]

sheets = []
for g in groups:
    inner = ''
    if DOUBLE and len(g) == 1:
        inner += '<div class="pg" style="background:#fff"></div>'
    inner += ''.join(page_html(i) for i in g)
    sheets.append('<div class="sheet"><div class="sheetin">%s</div></div>' % inner)

html = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Yigit Ozen &mdash; Paintings since 2019</title>
<link rel="stylesheet" href="editor/book.css">
<style>
html,body{margin:0;padding:0;background:#fff}
@page{size:%.0fmm %.0fmm;margin:0}
.sheet{width:%.0fmm;height:%.0fmm;position:relative;overflow:hidden;background:#fff;
  page-break-after:always;break-after:page}
.sheet:last-child{page-break-after:auto;break-after:auto}
.sheetin{position:absolute;left:%.0fmm;top:%.0fmm;width:%.0fmm;height:%.0fmm;display:flex}
.pg{color:#111}.pg.dark{color:#fff}
</style></head><body>
%s
</body></html>
""" % (SW + 2 * BL, PH + 2 * BL, SW + 2 * BL, PH + 2 * BL, BL, BL, SW, PH,
       '\n'.join(sheets))

open(OUT, 'w', encoding='utf-8').write(html)
print('%s  sayfa=%d  levha=%d  olcu=%.0f x %.0f mm  %s'
      % (os.path.basename(OUT), len(pages), len(sheets), SW + 2 * BL, PH + 2 * BL,
         'web' if WEB else 'baski 300 ppi + 3 mm tasma'))
