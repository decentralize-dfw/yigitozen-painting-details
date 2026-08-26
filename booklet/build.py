#!/usr/bin/env python3
"""
ARTBOOKLET — Yigit Ozen

booklet.html'i works.json'dan uretir ve gorselleri images/ altina hazirlar.
Kaynak veri katalogla ayni: ayni resimler, ayni yazilar. Fark duzende.

    python3 build.py            # ../../yigit/works.json okur
    python3 build.py PATH       # baska bir works.json okur

Sonra:  node print-pdf.js
"""
import json, os, sys, html, re
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
IMG  = os.path.join(HERE, 'images')
SRC  = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', '..', 'yigit', 'works.json')
ROOT = os.path.dirname(os.path.abspath(SRC))          # site kokunde /img/... duruyor

e = lambda t: html.escape(str(t), quote=True)

# ── gorsel hazirligi ─────────────────────────────────────────────────
made = {}
def prep(src, long_side, tag, box=None):
    """Site kokundeki bir dosyayi booklet/images altina indirger.

       Tablolarin bir cogunda saklanan fotograf duvari ve tuvalin disini da
       tasiyor; kayittaki `box` tuvalin o fotograf icindeki yeridir, sol,
       ust, genislik ve yukseklik olarak kesirle verilir. Once oradan
       kesilir, sonra kucultulur; yoksa levhaya duvar da girer."""
    key = (src, long_side, tuple(box) if box else None)
    if key in made: return made[key]
    path = os.path.join(ROOT, src.lstrip('/'))
    im = Image.open(path).convert('RGB')
    if box:
        W, H = im.size
        x, y, bw, bh = box
        im = im.crop((round(x * W), round(y * H), round((x + bw) * W), round((y + bh) * H)))
    w, h = im.size
    s = min(1.0, long_side / max(w, h))
    if s < 1.0: im = im.resize((round(w*s), round(h*s)), Image.LANCZOS)
    out = tag + '.jpg'
    im.save(os.path.join(IMG, out), quality=82, subsampling=1, optimize=True)
    made[key] = 'images/' + out
    return made[key]

# ── veri ─────────────────────────────────────────────────────────────
WORKS = json.load(open(SRC, encoding='utf-8'))
for w in WORKS:
    w['plates']  = [i for i in w['images'] if not i.get('hidden')]
    w['details'] = [i for i in w['plates'][1:] if i.get('label') == 'Detail']

BY_N = {w['n']: w for w in WORKS}
BLEED, PLACED = 1700, 1300

def paint(w, big=False):
    return prep(w['images'][0]['src'], BLEED if big else PLACED,
                'w%02d%s' % (w['n'], '-lg' if big else ''), w['images'][0].get('box'))

def det(w, k, big=False):
    d = w['details'][k % len(w['details'])]
    tag = 'w%02d-d%d%s' % (w['n'], k % len(w['details']), '-lg' if big else '')
    return prep(d['src'], BLEED if big else PLACED, tag)

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
BLURB = ('Thirty-five paintings made since 2019 across Istanbul, Milan and Luxembourg. '
         'Acrylic on canvas, carton and paper, with one charcoal drawing. The decisions '
         'are taken in wet paint, on the spot, and layer goes over layer like a '
         'palimpsest: colour clusters of movement, energy, aura and feeling rather than '
         'of light and shadow.')

# ── sayfa parcalari ──────────────────────────────────────────────────
def strip(w, kind=None):
    if kind:
        return ('<div class="strip"><span>%s</span><span class="q">&ldquo;%s&rdquo;</span>'
                '<span>%s</span><span class="y">&rsquo;%s</span></div>'
                % (e(kind), e(w['title']), e(w['medium']), e(w['year'])))
    return ('<div class="strip"><span>%s</span><span>%s</span><span class="y">%s</span></div>'
            % (e(w['medium']), e(w['dim']), e(w.get('place', ''))))


def ink(src, box=None):
    """Tam sayfa bir gorselin ust ve alt seridi acik mi koyu mu. Beyaz yazi
       acik bir boyanin uzerinde kayboluyor; o sayfada murekkep koyuya doner."""
    im = Image.open(os.path.join(ROOT, src.lstrip('/'))).convert('L')
    if box:
        W, H = im.size
        x, y, bw, bh = box
        im = im.crop((round(x * W), round(y * H), round((x + bw) * W), round((y + bh) * H)))
    w, h = im.size
    band = lambda b: sum(im.crop(b).resize((24, 6)).getdata()) / (24 * 6 * 255.0)  # noqa
    k = ''
    if band((0, 0, w, int(h * .13))) > .58: k += ' ink-t'
    if band((0, int(h * .87), w, h)) > .58: k += ' ink-b'
    return k

def cap(title, text):
    return '<div class="cap"><h3>%s</h3><p>%s</p></div>' % (e(title), e(text))

HEADS = ('Colour', 'Composition', 'Hand')
def notes(facets):
    """renk, kurgu ve el uzerine uc not, dipte bir sira halinde"""
    return ('<ul class="notes">' +
            ''.join('<li><b>%s</b>%s</li>' % (HEADS[i], e(x)) for i, x in enumerate(facets)) +
            '</ul>')

def bcap(w, kind='Detail'):
    """tam sayfa gorselin ustundeki beyaz kunye; numara ciftin baginidir"""
    return ('<div class="bcap"><span>%02d</span><span>%s</span>'
            '<span class="q">&ldquo;%s&rdquo;</span><span>&rsquo;%s</span></div>'
            % (w['n'], e(kind), e(w['title']), e(w['year'])))

MARK = '<div class="mark"><img src="images/logo.svg" alt=""></div>'

# ── sayfa listesi ────────────────────────────────────────────────────
pages = []                      # her biri: (run, body, extra-class)
first_page = {}                 # n -> sayfa numarasi

def add(run, body, klass=''):
    pages.append((run, body, klass))
    return len(pages)

def bleed_page(run, src, klass='dark', tag='', probe=None, box=None):
    return add(run, '<div class="bleed"><img src="%s" alt=""></div>%s' % (src, tag),
               klass + (ink(probe, box) if probe else ''))

# 1 ── kapak
cover_img = prep('/img/full/detail/7famboardgame_detail_3.jpg', BLEED, 'cover')
add('', '<div class="bleed"><img src="%s" alt=""></div>'
        '<div class="scrim t"></div><div class="scrim"></div>'
        '<div class="hd"><span>Artbooklet</span><span>Thirty-five works</span>'
        '<span>Istanbul &middot; Milan &middot; Luxembourg</span></div>'
        '<div class="ti">YIĞIT<br>ÖZEN</div>'
        '<div class="sub">Paintings since 2019</div>'
        '<div class="edge">yigitozen.xyz<br>de-centralize.com</div>' % cover_img, 'cover dark')

# 2-3 ── kunye | bagirti
add('Imprint', MARK +
    '<div class="imprint"><div class="ti">Paintings<br>since 2019</div>'
    '<div class="who">Yiğit Özen</div><p>%s</p>'
    '<div class="line">35 works &middot; Artbooklet &middot; yigitozen.xyz</div></div>' % e(BLURB))
add('On the work',
    '<div class="shout"><div class="lbl">On the work</div>'
    '<div class="big">The decisions<br>are taken in<br>wet paint,<br>'
    '<em>on the spot.</em></div></div>')

# 4-5 ── yazi | tasan gorsel
add('On the work',
    '<div class="essay"><h2 class="sect">On the work</h2><div class="sect-rule"></div>'
    '<p class="lead">A body accumulates out of clusters of rounded cells and bubbles that '
    'lean against one another, and it may close or stay open.</p>'
    '<div class="cols"><p>%s</p><p>%s</p><p>%s</p></div></div>' % (e(P1), e(P2), e(P3)))
bleed_page('On the work', det(BY_N[2], 4, True), tag=bcap(BY_N[2]),
           probe=BY_N[2]['details'][4 % len(BY_N[2]['details'])]['src'])

# 6-7 ── ozgecmis | calisma listesi
BIO = ['Yiğit Özen was born in 1994 in Istanbul and trained as an architect.',
       'The paintings date from 2018 onward and were made across Istanbul, Milan and '
       'Luxembourg.',
       'Alongside the paintings, Özen works as an XR and spatial web designer, and is the '
       'founder of decentralize design in Milan and Virtually Ever After in Luxembourg. '
       'That practice has been shown at Kunsthalle Zürich, the Royal Institution in '
       'London, Holy Art Gallery London and Art Basel Miami.']
CV = [('Awards and mentions', [
        ('Creatorverse Buildathon by Parcel x PangeaDAO, Music Venue, Winner', '2022'),
        ('Creatorverse Buildathon by Parcel x PangeaDAO, Meeting Space, Runner-up', '2022'),
        ('Grant Program by EnterDAO’s Landworks, Fashion Venue, Winner', '2022'),
        ('Grant Program by EnterDAO’s Landworks, Headquarters, Winner', '2022'),
        ('Top 50 Creators of Metaverse by Metamundo', '2023'),
        ('CryptoCubes by Han, Runner-up', '2023'),
        ('VCA x Draup Virtual Fashion Residency, 1st Prize, selected by RedDAO', '2023'),
        ('MONA 3D Objects Buildathon, Center Pieces, Honorable Mention', '2024')]),
      ('Talks', [
        ('Virtual Show &amp; Tell at Hyperfy, hosted by untitled, xyz', '2023'),
        ('VCA Mentorship, 6th Cohort, Architecture in the Metaverse', '2023'),
        ('Opening Keynote, Digital Fashion Summit, Creative Denmark', '2024')]),
      ('Exhibitions', [
        ('Power of the Nature, Fabbrica del Vapore, Milan', '2019'),
        ('The Arts Special Projects, Fabbrica del Vapore, Milan', '2019'),
        ('Communitas III by Kollektiv Kollektiv, Kunsthaus Steffisburg', '2021'),
        ('New Freedom Think, Mads Gallery, Milan', '2022'),
        ('Art Design, Holy Art Gallery, London', '2022'),
        ('Klein Metaverse Event, BabylonsNFT, Yachtingverse', '2022'),
        ('DYOR, Kunsthalle Zürich, Zurich', '2022'),
        ('Creators of the Metaverse by Metamundo, Art Basel Miami', '2022'),
        ('First Look Metaverse Watch Party, MONA', '2023'),
        ('KODA by Polkadot, Factory Berlin, Berlin', '2023'),
        ('New Codes by VCA, Draup and Mad Global, Royal Institution, London', '2023')])]

add('Biography',
    '<div class="bio"><div class="por"><img src="%s" alt="Yiğit Özen"></div>'
    '<h2>Yiğit<br>Özen</h2>%s</div>'
    % (prep('/img/portrait.jpg', 900, 'portrait'),
       ''.join('<p>%s</p>' % e(x) for x in BIO)))
add('Biography', '<div class="cv">' + ''.join(
    '<section><h4>%s</h4><ul>%s</ul></section>'
    % (h, ''.join('<li><span class="w">%s</span><span class="y">%s</span></li>' % (a, b)
                  for a, b in rows))
    for h, rows in CV) + '</div>')

# 8-9 ── icindekiler (numaralar sonra doldurulur)
toc_a = add('Contents', '@@TOC1@@')
toc_b = add('Contents', '@@TOC2@@')

# ── bolumler ─────────────────────────────────────────────────────────
def chapter_of(w): return w['year']
YEARS = []
for w in WORKS:
    if w['year'] not in YEARS: YEARS.append(w['year'])

RICH = {1, 2, 3, 15}                       # detay fotografi en bol olanlar

def wk_page(w):
    """her eserin sayfasi. Otuz besinde de ayni."""
    return ('<div class="wk">'
            '<div class="hdr"><span class="no">%02d</span><span class="yr">%s</span></div>'
            '<div class="band-plate"><img src="%s" alt=""></div>'
            '%s'
            '<div class="say"><h3>%s</h3><p>%s</p></div>'
            '</div>%s'
            % (w['n'], e(w['year']), paint(w), strip(w),
               e(w['title']), e(w['note']), notes(w['facets'])))


for yr in YEARS:
    group = [w for w in WORKS if w['year'] == yr]
    places = {}
    for w in group: places[w.get('place', '')] = places.get(w.get('place', ''), 0) + 1
    place = max(places, key=places.get)
    run = '%s &middot; %s' % (yr, place)
    span = ('%02d' % group[0]['n']) if len(group) == 1 else \
           ('%02d&ndash;%02d' % (group[0]['n'], group[-1]['n']))

    lead = group[0]
    add(run, '<div class="divider"><div class="yr">%s</div><div class="pl">%s</div>'
             '<div class="ct">%s &middot; %d work%s</div><div class="rule"></div></div>'
             % (e(yr), e(place), span, len(group), '' if len(group) == 1 else 's'))
    lead_src = (lead['details'][0]['src'] if lead['details'] else lead['images'][0]['src'])
    bleed_page(run, det(lead, 0, True) if lead['details'] else paint(lead, True),
               tag=bcap(lead, 'Detail' if lead['details'] else 'Painting'), probe=lead_src,
               box=None if lead['details'] else lead['images'][0].get('box'))

    for w in group:
        # sol sayfa tasan gorsel, sag sayfa eserin kendisi. Detayi olmayanda
        # tasan gorsel tablonun kendi icinden alinir; cift bozulmaz.
        src  = (w['details'][1 % len(w['details'])]['src'] if w['details']
                else w['images'][0]['src'])
        pic  = det(w, 1, True) if w['details'] else paint(w, True)
        bleed_page(run, pic, tag=bcap(w, 'Detail'), probe=src,
                   box=None if w['details'] else w['images'][0].get('box'))
        first_page[w['n']] = add(run, wk_page(w))

        if w['n'] in RICH:
            add(run, '<div class="bleed half"><img src="%s" alt=""></div>%s'
                     % (det(w, 3, True), strip(w, 'Detail')), 'halfimg')
            add(run, '<div class="bleed top"><img src="%s" alt=""></div>%s%s'
                     % (det(w, 5, True), strip(w, 'Detail'),
                        cap('In the hand', w['facets'][2])), 'topimg')

# ── kolofon ──────────────────────────────────────────────────────────
add('Colophon', MARK +
    '<div class="end"><p>All works by Yiğit Özen, born 1994 in Istanbul and trained as an '
    'architect. The paintings date from 2018 onward and were made across Istanbul, Milan '
    'and Luxembourg.</p><p>Dimensions are given as width by height. Plates reproduce '
    'documentation of the paintings; colour and surface differ from the works themselves. '
    'A technical catalogue of the same works, with the full index, is published '
    'separately.</p><p>All works &copy; Yiğit Özen. All rights reserved.</p>'
    '<div class="contact">yigitozen.xyz &middot; de-centralize.com<br>'
    'Instagram @yjgjf &middot; x@yigitozen.xyz</div></div>')
add('', '<img src="images/logo.svg" alt="">', 'last')

# ── icindekiler, sayfalar belli olunca ───────────────────────────────
def toc(items, head=None):
    rows = ''.join(
        '<li><span class="n">%02d</span><span class="t">%s</span>'
        '<span class="y">%s</span><span class="p">%d</span></li>'
        % (w['n'], e(w['title']), e(w['year']), first_page.get(w['n'], 0))
        for w in items)
    h = '<h2>%s</h2>' % head if head else ''
    return '<div class="toc">%s<ol>%s</ol></div>' % (h, rows)

pages[toc_a - 1] = (pages[toc_a - 1][0], toc(WORKS[:18], 'Contents'), '')
pages[toc_b - 1] = (pages[toc_b - 1][0], toc(WORKS[18:]), '')

# ── yaz ──────────────────────────────────────────────────────────────
out = ['<!doctype html>', '<html lang="en">', '<head>', '<meta charset="utf-8">',
       '<title>Yiğit Özen &mdash; Artbooklet</title>',
       '<link rel="stylesheet" href="booklet.css">', '</head>', '<body>', '']
for i, (run, body, klass) in enumerate(pages, start=1):
    side = '' if i == 1 else (' L' if i % 2 == 0 else ' R')
    folio = ('' if i == 1 else
             '<div class="folio"><span class="num">%d</span><span class="rule"></span>'
             '<span class="run">%s</span></div>' % (i, run))
    out.append('<section class="pg%s%s">%s%s</section>'
               % (side, (' ' + klass if klass else ''), body, folio))
    out.append('')
out += ['</body>', '</html>', '']
open(os.path.join(HERE, 'booklet.html'), 'w', encoding='utf-8').write('\n'.join(out))

print('pages: %d' % len(pages))
print('images: %d' % len(made))
