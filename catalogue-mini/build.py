# -*- coding: utf-8 -*-
"""Mini katalogu kurar: sayfaya uc is, resimler zikzak.

Buyuk katalog sayfaya bir is koyuyor. Burada uc tane var, ve uclu her
sayfada resim bir sagda bir solda duruyor; karsi sayfa ise ters basliyor,
boylece acilmis serimde resimler capraz iner. Duzen buyuk katalogun
duzenidir: ayni harfler, ayni gri, ayni alt bilgi.

    python3 build.py          # catalogue-mini.html yazar
"""
import json, os, re, html, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROWS = json.load(open(os.path.join(HERE, 'works.json'), encoding='utf-8'))

# Listedeki tarif elle yazilmis; birkac yerde duzelti notu ve olcuden
# arta kalan birim kalmis.
def clean(m):
    m = re.sub(r'\s*\b(DUZALT|DUZALY|DUZELT)\b\s*', ' ', m or '', flags=re.I)
    m = re.sub(r'^(?:on\s+)?cm\s+', '', m.strip(), flags=re.I)
    m = re.sub(r'\bon\s+cm\b', 'on', m, flags=re.I)
    return re.sub(r'\s{2,}', ' ', m).strip(' ,')

for r in ROWS:
    r['medium'] = clean(r['medium'])

# Buyuk katalog gibi: yenisi once.
ROWS.sort(key=lambda r: (-(r['yr'] or 0), r['id']))
for i, r in enumerate(ROWS, 1):
    r['no'] = '%03d' % i
    r['img'] = 'images/%s' % r['file']

E = lambda s: html.escape(s or '', quote=True)
PER = 3                       # sayfaya kac is


def meta(r):
    out = []
    if r['yr']: out.append(('Year', str(r['yr'])))
    if r['medium']: out.append(('Medium', r['medium']))
    if r['dim']: out.append(('Dimensions', r['dim']))
    return ''.join('<div><dt>%s</dt><dd>%s</dd></div>' % (k, E(v)) for k, v in out)


def band(r, right):
    """Bir is. right ise resim sagda, kunye solda."""
    pic = '<div class="pic"><img src="%s" alt="%s"></div>' % (E(r['img']), E(r['name']))
    inf = ('<div class="info"><div class="cat">Cat. %s</div><h3>%s</h3>'
           '<dl class="meta">%s</dl></div>' % (r['no'], E(r['name']), meta(r)))
    return '<div class="band%s">%s</div>' % (
        ' r' if right else '', (inf + pic) if right else (pic + inf))


def page(inner, foot_r, cls=''):
    return ('<section class="page%s"><div class="mark"><img src="images/logo.svg" alt=""></div>\n'
            '%s\n  <div class="foot"><span>Yiğit Özen &middot; Paintings 2018&ndash;2024</span>'
            '<span>%s</span></div>\n</section>\n' % (cls, inner, foot_r))


parts = []
parts.append('<section class="page cover"><div class="emblem">'
             '<img src="images/logo.svg" alt="Yiğit Özen"></div></section>\n')

years = sorted({r['yr'] for r in ROWS if r['yr']})
parts.append(page(
    '  <div class="sheet">\n    <div class="imprint">\n'
    '      <div class="ti">Paintings 2018&ndash;2024</div>\n'
    '      <div class="who">Yiğit Özen</div>\n'
    '      <p>One hundred and fifteen paintings, drawings and painted objects '
    'made between %d and %d, none of which appears in <em>Paintings since '
    '2019</em>. Acrylic, pastel, pencil, marker and watercolour on canvas, '
    'paper, carton, whiteboard and on packaging taken apart. They are set '
    'three to a page, the plate falling first to one side and then to the '
    'other, so a spread reads as a single descending line.</p>\n'
    '      <div class="line">%d Works &middot; Mini Catalogue &middot; yigitozen.xyz</div>\n'
    '    </div>\n  </div>' % (min(years), max(years), len(ROWS)), 'Imprint'))

# ── indeks ─────────────────────────────────────────────────────────
IDX = 34
chunks = [ROWS[i:i + IDX] for i in range(0, len(ROWS), IDX)]
for k, ch in enumerate(chunks):
    rows = ''.join(
        '<tr><td class="no">%s</td><td class="ti">%s</td><td class="yr">%s</td>'
        '<td class="md">%s</td><td class="dm">%s</td><td class="pg">%d</td></tr>'
        % (r['no'], E(r['name']), r['yr'] or '', E(r['medium']), E(r['dim'] or ''),
           # kapak + kunye + indeks sayfalari, sonra levhalar
           2 + len(chunks) + (int(r['no']) - 1) // PER + 1)
        for r in ch)
    parts.append(page(
        '  <div class="sheet">\n    <h2 class="sect">Index of Works%s</h2>'
        '<div class="sect-rule"></div>\n    <table class="idx">\n'
        '      <thead><tr><th></th><th>Title</th><th>Year</th><th>Medium</th>'
        '<th>Dimensions</th><th>Page</th></tr></thead>\n      <tbody>%s</tbody>\n'
        '    </table>\n  </div>'
        % (' <span class="cont">continued</span>' if k else '', rows),
        'Index %d/%d' % (k + 1, len(chunks))))

# ── levhalar: sayfaya uc, resim zikzak ─────────────────────────────
pages = [ROWS[i:i + PER] for i in range(0, len(ROWS), PER)]
for p, group in enumerate(pages):
    # p cift sayfada resim sag-sol-sag, tek sayfada sol-sag-sol
    bands = ''.join(band(r, (p + b) % 2 == 0) for b, r in enumerate(group))
    parts.append(page('  <div class="plates">%s</div>' % bands,
                      'Cat. %s&ndash;%s' % (group[0]['no'], group[-1]['no'])))

doc = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
       '<title>Yiğit Özen &mdash; Paintings 2018–2024, Mini Catalogue</title>\n'
       '<link rel="stylesheet" href="catalogue-mini.css">\n</head>\n<body>\n\n'
       + '\n'.join(parts) + '\n</body>\n</html>\n')
open(os.path.join(HERE, 'catalogue-mini.html'), 'w', encoding='utf-8').write(doc)
print('is %d · levha sayfasi %d · indeks sayfasi %d · toplam sayfa %d'
      % (len(ROWS), len(pages), len(chunks), 2 + len(chunks) + len(pages)))
