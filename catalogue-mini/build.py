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
PER = 4                        # sayfaya kac is
# Indeks sayfasi sabit sayida satir almiyor: uzun bir baslik ya da uzun bir
# malzeme adi iki satira sariyor ve o satiri yukseltiyor. Sayfa bu yuzden
# satirla degil yukseklikle dolduruluyor, boylece hicbir satir alt bilgiye
# inmiyor. Olculer sayfadan alindi: yazi alani, tek satirlik bir satirin
# adimi ve sarma basina eklenen yukseklik.
BODY  = 640.0                  # basligin altindan alt bilgiye kalan, punto
STEP  = 20.1                   # tek satirlik bir indeks satirinin adimi
WRAP  = 11.2                   # her sarmanin ekledigi
TI_CH = 32                     # baslik sutununa sigan karakter
MD_CH = 26                     # malzeme sutununa sigan karakter
SUP = {'canvas': 'Canvas', 'paper': 'Paper', 'object': 'Object'}


def words(n):
    """Kunyede sayilar yaziyla geciyor; 999'a kadar yeter."""
    one = ('zero one two three four five six seven eight nine ten eleven twelve '
           'thirteen fourteen fifteen sixteen seventeen eighteen nineteen').split()
    ten = 'x x twenty thirty forty fifty sixty seventy eighty ninety'.split()
    if n < 20: return one[n]
    if n < 100:
        return ten[n // 10] + ('-' + one[n % 10] if n % 10 else '')
    return one[n // 100] + ' hundred' + (' and ' + words(n % 100) if n % 100 else '')


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


def blank():
    """Denklik icin birakilan sayfa: uzerinde hicbir sey yok."""
    return '<section class="page"></section>\n'


def closing():
    """Kitabin son sayfasi: yalniz kus, sol altta."""
    return ('<section class="page end"><div class="bird">'
            '<img src="images/logo.svg" alt="Yiğit Özen"></div></section>\n')


def page(inner, foot_r, cls=''):
    return ('<section class="page%s"><div class="mark"><img src="images/logo.svg" alt=""></div>\n'
            '%s\n  <div class="foot"><span>%s</span><span>%s</span></div>\n</section>\n'
            % (cls, inner, FOOT_L, foot_r))


FOOT_L = 'Yiğit Özen &middot; Paintings 2018&ndash;2026'


def prose(title, paras, tail=''):
    return ('  <div class="sheet">\n    <h2 class="sect">%s</h2>'
            '<div class="sect-rule"></div>\n    <div class="prose">%s</div>%s\n  </div>'
            % (title, ''.join('<p>%s</p>' % t for t in paras), tail))


def rows(title, items):
    return ('<h2 class="sect run">%s</h2><div class="sect-rule"></div>'
            '<div class="rows">%s</div>'
            % (title, ''.join('<div><span class="yr">%s</span>'
                              '<span class="wh">%s</span></div>' % (y, E(w))
                              for y, w in items)))


BIO = [
    'Yiğit Özen was born in 1994 in Istanbul and trained as an architect.',
    'The paintings date from 2018 onward and were made across Istanbul, Milan '
    'and Luxembourg.',
    'Alongside the paintings, Özen works as an XR and spatial web designer, and '
    'is the founder of decentralize design in Milan and Virtually Ever After in '
    'Luxembourg. That practice has been shown at Kunsthalle Zürich, the Royal '
    'Institution in London, Holy Art Gallery London and Art Basel Miami.',
]
FACTS = [('Born', '1994, Istanbul'),
         ('Lives and works', 'Istanbul, Milan, Luxembourg'),
         ('Practice', 'Painting, spatial and XR design'),
         ('Shown at', 'Kunsthalle Zürich, the Royal Institution London, '
                      'Holy Art Gallery London, Art Basel Miami')]

ON_WORK = [
    'In Özen&rsquo;s paintings a body appears as rounded units settle on top of one '
    'another. The contour arrives late and often does not arrive. Scale gives the '
    'verdict. A shape held large enough becomes somebody, and the same shape beside '
    'it becomes a row. Most of the ground stays unpainted, and that emptiness '
    'decides how far the figure gets to build.',
    'The same parts have been turning up since the beginning. A figure present in '
    'the scene and not looking. A chair nobody sits in. A frame drawn over the '
    'scene and left open. A bird that arrives under its own power, carrying '
    'something never unwrapped. These are working parts. Nothing in them waits to '
    'be solved. The one helping and the one crushing are made of the same heap.',
    'Titles do not name the picture. A greeting, a game, a file name, a line taken '
    'from elsewhere. They set a second language beside the image and tilt it. '
    'Decisions are taken in wet paint, colour is held as a distribution. Over the '
    'years the parts stay where they are and the temperature changes.',
]

AWARDS = [
    (2022, 'Creatorverse Buildathon by Parcel x PangeaDAO, Music Venue, Winner'),
    (2022, 'Creatorverse Buildathon by Parcel x PangeaDAO, Meeting Space, Runner-up'),
    (2022, 'Grant Program by EnterDAO’s Landworks, Fashion Venue, Winner'),
    (2022, 'Grant Program by EnterDAO’s Landworks, Headquarters, Winner'),
    (2023, 'Top 50 Creators of Metaverse by Metamundo'),
    (2023, 'CryptoCubes by Han, Runner-up'),
    (2023, 'VCA x Draup Virtual Fashion Residency, 1st Prize, selected by RedDAO'),
    (2024, 'MONA 3D Objects Buildathon, Center Pieces, Honorable Mention'),
]
TALKS = [
    (2023, 'Virtual Show & Tell at Hyperfy, hosted by untitled, xyz'),
    (2023, 'VCA Mentorship, 6th Cohort, Architecture in the Metaverse'),
    (2024, 'Opening Keynote, Digital Fashion Summit, Lifestyle Design Cluster, Creative Denmark'),
]
SHOWS = [
    (2019, 'Power of the Nature, Fabbrica del Vapore, Milan'),
    (2019, 'The Arts Special Projects, Fabbrica del Vapore, Milan'),
    (2021, 'Communitas III: Digital Community by Kollektiv Kollektiv, Kunsthaus Steffisburg'),
    (2022, 'New Freedom Think, Mads Gallery, Milan'),
    (2022, 'Art Design, Holy Art Gallery, London'),
    (2022, 'Klein Metaverse Event, BabylonsNFT, Yachtingverse'),
    (2022, 'DYOR, Kunsthalle Zürich, Zurich'),
    (2022, 'Creators of the Metaverse by Metamundo, Art Basel Miami, Miami'),
    (2023, 'First Look Metaverse Watch Party, MONA'),
    (2023, 'KODA by Polkadot, Factory Berlin, Berlin'),
    (2023, 'New Codes Exhibition by VCA, Draup and Mad Global, Royal Institution, London'),
]
def lines(r):
    """Bir indeks satirinin kac satira yayildigi."""
    from math import ceil
    return max(1, ceil(len(str(r['name'])) / TI_CH), ceil(len(str(r['medium'])) / MD_CH))


def pack(rows):
    """Satirlari yukseklige gore sayfalara boler."""
    out, cur, h = [], [], 0.0
    for r in rows:
        need = STEP + WRAP * (lines(r) - 1)
        if cur and h + need > BODY:
            out.append(cur); cur, h = [], 0.0
        cur.append(r); h += need
    if cur: out.append(cur)
    return out


chunks = pack(ROWS)
sheets = [ROWS[i:i + PER] for i in range(0, len(ROWS), PER)]

# ── sayfa duzeni ───────────────────────────────────────────────────
# Kapak, kunye, indeks, sonra uc yazi sayfasi. Levhalar indeksin hemen
# yanindan baslamasin, sol sayfadan bassin: acilmis serimde is once sol
# elde durur. Denklik tutmazsa bir sayfa bos birakilir. Sonda kitap
# katalogla bitmesin diye kus sayfasi var, ve o sag sayfaya dussun diye
# gerekirse orada da bir bos sayfa. Tek sayfa numaralari sag, cift olanlar
# soldur.
BEFORE = 2 + len(chunks) + 3
PAD_A  = 1 if BEFORE % 2 == 0 else 0          # ilk levha sayfasi cift olsun
FIRST  = BEFORE + PAD_A                       # ilk levha sayfasinin numarasi - 1
LASTPL = FIRST + len(sheets)                  # son levha sayfasi
PAD_B  = 0 if (LASTPL + 1) % 2 else 1         # kus sayfasi tek olsun
TOTAL  = LASTPL + PAD_B + 1

parts = ['<section class="page cover"><div class="emblem">'
         '<img src="images/logo.svg" alt="Yiğit Özen"></div></section>\n']

years = sorted({r['yr'] for r in ROWS if r['yr']})
n_main = sum(1 for r in ROWS if r['main'])
c = {k: sum(1 for r in ROWS if r['sup'] == k) for k in SUP}
parts.append(page(
    '  <div class="sheet">\n    <div class="imprint">\n'
    '      <div class="ti">Paintings %d&ndash;%d</div>\n'
    '      <div class="who">Yiğit Özen</div>\n'
    '      <p>%s works: the %d of the catalogued sequence and the %d that '
    'had not been catalogued. They are ordered by what they are made on '
    'rather than by when — %d on canvas, then %d on paper, carton and print, '
    'then %d that are objects — and within each the catalogued work leads. '
    'Four to a page, the plate falling to one side and then the other down '
    'the page, and the page facing it keeping the same beat rather than '
    'answering it.</p>\n'
    '      <div class="line">%d Works &middot; Mini Catalogue &middot; yigitozen.xyz</div>\n'
    '    </div>\n  </div>'
    % (min(years), max(years), words(len(ROWS)).capitalize(), n_main,
       len(ROWS) - n_main,
       c['canvas'], c['paper'], c['object'], len(ROWS)), 'Imprint'))

# ── indeks ─────────────────────────────────────────────────────────
for k, ch in enumerate(chunks):
    rows_html = ''.join(
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
        % (' <span class="cont">continued</span>' if k else '', rows_html),
        'Index %d/%d' % (k + 1, len(chunks))))

# ── yazi sayfalari ─────────────────────────────────────────────────
parts.append(page(prose('Biography', BIO,
    '<dl class="facts">%s</dl>' % ''.join(
        '<div><dt>%s</dt><dd>%s</dd></div>' % (k, E(v)) for k, v in FACTS)),
    'Biography'))
parts.append(page(prose('On the Work', ON_WORK), 'On the work'))
parts.append(page('  <div class="sheet">\n%s%s%s\n  </div>'
                  % (rows('Awards and Mentions', AWARDS),
                     rows('Talks', TALKS), rows('Exhibitions', SHOWS)),
                  'Curriculum'))

parts.extend([blank()] * PAD_A)

# ── levhalar: sayfaya dort, resim zikzak ───────────────────────────
for group in sheets:
    # Her sayfa ayni: resim sag-sol-sag-sol. Karsi sayfa aynalanmaz,
    # onu izler; serim boyunca ayni ritim surer.
    bands = ''.join(band(r, b % 2 == 0) for b, r in enumerate(group))
    sups = [SUP[s] for s in dict.fromkeys(r['sup'] for r in group)]
    parts.append(page('  <div class="plates">%s</div>' % bands,
                      '%s &middot; Cat. %s&ndash;%s'
                      % (' &ndash; '.join(sups), group[0]['no'], group[-1]['no'])))

parts.extend([blank()] * PAD_B)
parts.append(closing())

doc = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
       '<title>Yiğit Özen &mdash; Paintings 2018–2026, Mini Catalogue</title>\n'
       '<link rel="stylesheet" href="catalogue-mini.css">\n</head>\n<body>\n\n'
       + '\n'.join(parts) + '\n</body>\n</html>\n')
open(os.path.join(HERE, 'catalogue-mini.html'), 'w', encoding='utf-8').write(doc)
print('is %d (ana %d) · indeks %d · yazi 3 · levha %d · bos %d · toplam sayfa %d'
      % (len(ROWS), n_main, len(chunks), len(sheets), PAD_A + PAD_B, TOTAL))
print('ilk levha sayfasi %d (%s) · son levha %d · kus sayfasi %d (%s)'
      % (FIRST + 1, 'sol' if (FIRST + 1) % 2 == 0 else 'SAG',
         LASTPL, TOTAL, 'sag' if TOTAL % 2 else 'SOL'))
