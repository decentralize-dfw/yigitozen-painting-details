# -*- coding: utf-8 -*-
"""Mini katalogu kurar: sayfaya uc is, resimler zikzak, sira tasiyicidan.

Buyuk katalog sayfaya bir is koyuyor ve yalniz otuz besini tasiyor.
Burada yuz elli is var — buyuk katalogun otuz besi ve arsivde duran yuz on
besi — sayfaya uc tane, ve uclu her sayfada resim bir sagda bir solda
duruyor; karsi sayfa ters basliyor, boylece acilmis serimde resimler
capraz iniyor.

Sira kurgudan gelir, yildan degil: once tuval, sonra kagit, en sonda
nesne. Her bandin icinde buyuk katalogun isleri one gecer, arkasindan
geri kalanlar; ikisi de yenisi once. Alt bilgi hangi banttaysa onu soyler.

    python3 build.py          # works.json -> catalogue-mini.html
"""
import json, os, html

HERE = os.path.dirname(os.path.abspath(__file__))
ROWS = json.load(open(os.path.join(HERE, 'works.json'), encoding='utf-8'))

E = lambda s: html.escape(str(s or ''), quote=True)
PER = 3                        # sayfaya kac is
IDX = 34                       # indeks sayfasina kac satir
SUP = {'canvas': 'Canvas', 'paper': 'Paper', 'object': 'Object'}


def meta(r):
    out = [('Year', r['yr']), ('Medium', r['medium']),
           ('Dimensions', r['dim']), ('Location', r['loc'])]
    return ''.join('<div><dt>%s</dt><dd>%s</dd></div>' % (k, E(v))
                   for k, v in out if v)


def band(r, right):
    """Bir is. right ise resim sagda, kunye solda."""
    pic = '<div class="pic"><img src="%s" alt="%s"></div>' % (E(r['img']), E(r['name']))
    inf = ('<div class="info"><div class="cat">Cat. %s</div><h3>%s</h3>'
           '<dl class="meta">%s</dl></div>' % (r['no'], E(r['name']), meta(r)))
    return '<div class="band%s">%s</div>' % (
        ' r' if right else '', (inf + pic) if right else (pic + inf))


def page(inner, foot_r, cls=''):
    return ('<section class="page%s"><div class="mark"><img src="images/logo.svg" alt=""></div>\n'
            '%s\n  <div class="foot"><span>%s</span><span>%s</span></div>\n</section>\n'
            % (cls, inner, FOOT_L, foot_r))


FOOT_L = 'Yiğit Özen &middot; Paintings 2018&ndash;2026'
chunks = [ROWS[i:i + IDX] for i in range(0, len(ROWS), IDX)]
FIRST = 2 + len(chunks)                 # ilk levha sayfasinin numarasi - 1

parts = ['<section class="page cover"><div class="emblem">'
         '<img src="images/logo.svg" alt="Yiğit Özen"></div></section>\n']

years = sorted({r['yr'] for r in ROWS if r['yr']})
n_main = sum(1 for r in ROWS if r['main'])
c = {k: sum(1 for r in ROWS if r['sup'] == k) for k in SUP}
parts.append(page(
    '  <div class="sheet">\n    <div class="imprint">\n'
    '      <div class="ti">Paintings %d&ndash;%d</div>\n'
    '      <div class="who">Yiğit Özen</div>\n'
    '      <p>One hundred and fifty works: the %d of <em>Paintings since '
    '2019</em> and the %d that had not been catalogued. They are ordered by '
    'what they are made on rather than by when — %d on canvas, then %d on '
    'paper, carton and print, then %d that are objects — and within each the '
    'catalogued work leads. Three to a page, the plate falling first to one '
    'side and then to the other, so a spread reads as a single descending '
    'line.</p>\n'
    '      <div class="line">%d Works &middot; Mini Catalogue &middot; yigitozen.xyz</div>\n'
    '    </div>\n  </div>'
    % (min(years), max(years), n_main, len(ROWS) - n_main,
       c['canvas'], c['paper'], c['object'], len(ROWS)), 'Imprint'))

# ── indeks ─────────────────────────────────────────────────────────
for k, ch in enumerate(chunks):
    rows = ''.join(
        '<tr><td class="no">%s</td><td class="ti">%s</td><td class="yr">%s</td>'
        '<td class="md">%s</td><td class="dm">%s</td><td class="sp">%s</td>'
        '<td class="pg">%d</td></tr>'
        % (r['no'], E(r['name']), E(r['yr']), E(r['medium']), E(r['dim']),
           SUP[r['sup']], FIRST + (int(r['no']) - 1) // PER + 1)
        for r in ch)
    parts.append(page(
        '  <div class="sheet">\n    <h2 class="sect">Index of Works%s</h2>'
        '<div class="sect-rule"></div>\n    <table class="idx">\n'
        '      <thead><tr><th></th><th>Title</th><th>Year</th><th>Medium</th>'
        '<th>Dimensions</th><th>On</th><th>Page</th></tr></thead>\n'
        '      <tbody>%s</tbody>\n    </table>\n  </div>'
        % (' <span class="cont">continued</span>' if k else '', rows),
        'Index %d/%d' % (k + 1, len(chunks))))

# ── levhalar: sayfaya uc, resim zikzak ─────────────────────────────
pages = [ROWS[i:i + PER] for i in range(0, len(ROWS), PER)]
for p, group in enumerate(pages):
    # cift sayfada resim sag-sol-sag, tek sayfada sol-sag-sol
    bands = ''.join(band(r, (p + b) % 2 == 0) for b, r in enumerate(group))
    sups = [SUP[s] for s in dict.fromkeys(r['sup'] for r in group)]
    parts.append(page('  <div class="plates">%s</div>' % bands,
                      '%s &middot; Cat. %s&ndash;%s'
                      % (' &ndash; '.join(sups), group[0]['no'], group[-1]['no'])))

doc = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
       '<title>Yiğit Özen &mdash; Paintings 2018–2026, Mini Catalogue</title>\n'
       '<link rel="stylesheet" href="catalogue-mini.css">\n</head>\n<body>\n\n'
       + '\n'.join(parts) + '\n</body>\n</html>\n')
open(os.path.join(HERE, 'catalogue-mini.html'), 'w', encoding='utf-8').write(doc)
print('is %d (ana %d) · levha sayfasi %d · indeks %d · toplam sayfa %d'
      % (len(ROWS), n_main, len(pages), len(chunks), 2 + len(chunks) + len(pages)))
