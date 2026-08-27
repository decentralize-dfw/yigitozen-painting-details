# -*- coding: utf-8 -*-
"""
IDML paketinin denetimi.

Burada InDesign yok, o yuzden dosyanin acildigini gozle goremem. Gorulebilen
her sey olculur: paketin duzeni, her XML'in ayristigi, designmap'in isaret
ettigi her parcanin gercekten bulundugu, her yazi cercevesinin bir hikayeye,
her hikayenin var olan bir paragraf stiline, her gorselin diskteki bir dosyaya
baglandigi, kimliklerin tek oldugu ve hicbir nesnenin sayfanin disina
dusmedigi.

    python3 idml-audit.py [paket-klasoru]

Sifir donmeyen her sey bir hatadir.
"""
import os, sys, re, zipfile, json
import xml.etree.ElementTree as ET

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir,
    'Yigit-Ozen-Paintings-InDesign')
ROOT = os.path.abspath(ROOT)
IDML = next((os.path.join(ROOT, f) for f in os.listdir(ROOT)
             if f.endswith('.idml')), None)
if not IDML: sys.exit('paket icinde .idml yok: %s' % ROOT)

PKG = 'http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging'
bad = []
note = []

z = zipfile.ZipFile(IDML)
names = z.namelist()

# 1 · paketin duzeni: mimetype ilk giris ve sikistirilmamis olmali
if names[0] != 'mimetype':
    bad.append('mimetype ilk giris degil (ilk: %s)' % names[0])
elif z.getinfo('mimetype').compress_type != zipfile.ZIP_STORED:
    bad.append('mimetype sikistirilmis; STORED olmali')
elif z.read('mimetype').decode() != 'application/vnd.adobe.indesign-idml-package':
    bad.append('mimetype icerigi yanlis')
for need in ('designmap.xml', 'META-INF/container.xml', 'Resources/Styles.xml',
             'Resources/Fonts.xml', 'Resources/Graphic.xml',
             'Resources/Preferences.xml', 'XML/BackingStory.xml'):
    if need not in names: bad.append('eksik parca: %s' % need)

# 2 · her XML ayrisiyor mu
trees = {}
for n in names:
    if not n.endswith('.xml'): continue
    try:
        trees[n] = ET.fromstring(z.read(n))
    except ET.ParseError as e:
        bad.append('XML ayrismadi: %s (%s)' % (n, e))

# 3 · designmap'in isaret ettigi her parca pakette var mi
dm = trees.get('designmap.xml')
refs = []
if dm is not None:
    for el in dm:
        src = el.get('src')
        if src:
            refs.append(src)
            if src not in names: bad.append('designmap eksik parcayi gosteriyor: %s' % src)
for n in names:
    if n.endswith('.xml') and n.startswith(('Spreads/', 'Stories/', 'MasterSpreads/')):
        if n not in refs: bad.append('parca designmap"te yok: %s' % n)

# 4 · kimlikler tek mi
selfs = {}
for n, t in trees.items():
    for el in t.iter():
        s = el.get('Self')
        if not s: continue
        if s in selfs and not s.startswith(('$ID', 'ParagraphStyle/$ID',
                                            'CharacterStyle/$ID', 'ObjectStyle/$ID',
                                            'Color/$ID', 'Swatch/$ID', 'StrokeStyle/$ID')):
            bad.append('kimlik iki kez: %s (%s ve %s)' % (s, selfs[s], n))
        selfs[s] = n

# 5 · stiller: kullanilan her paragraf ve karakter stili tanimli mi
st = trees.get('Resources/Styles.xml')
pdef = set(); cdef = set()
if st is not None:
    for el in st.iter():
        if el.tag == 'ParagraphStyle': pdef.add(el.get('Self'))
        if el.tag == 'CharacterStyle': cdef.add(el.get('Self'))
used_p, used_c = set(), set()
for n, t in trees.items():
    if not n.startswith('Stories/'): continue
    for el in t.iter():
        if el.tag == 'ParagraphStyleRange': used_p.add(el.get('AppliedParagraphStyle'))
        if el.tag == 'CharacterStyleRange': used_c.add(el.get('AppliedCharacterStyle'))
for u in sorted(used_p - pdef): bad.append('tanimsiz paragraf stili: %s' % u)
for u in sorted(used_c - cdef): bad.append('tanimsiz karakter stili: %s' % u)

# 6 · renkler: her FillColor / StrokeColor tanimli mi
gr = trees.get('Resources/Graphic.xml')
cols = set()
if gr is not None:
    for el in gr.iter():
        if el.tag in ('Color', 'Swatch', 'Gradient', 'StrokeStyle'):
            cols.add(el.get('Self'))
used_col = set()
for n, t in trees.items():
    for el in t.iter():
        for a in ('FillColor', 'StrokeColor'):
            v = el.get(a)
            if v: used_col.add(v)
for u in sorted(used_col - cols):
    bad.append('tanimsiz renk: %s' % u)

# 7 · yazi cerceveleri: her biri var olan bir hikayeye baglaniyor mu
story_selfs = set()
for n, t in trees.items():
    if n.startswith('Stories/'):
        for el in t.iter():
            if el.tag == 'Story': story_selfs.add(el.get('Self'))
frames = 0
for n, t in trees.items():
    if not n.startswith('Spreads/'): continue
    for el in t.iter('TextFrame'):
        frames += 1
        ps = el.get('ParentStory')
        if ps not in story_selfs:
            bad.append('yazi cercevesi olmayan hikayeye bagli: %s' % ps)
orphan = story_selfs - set(
    el.get('ParentStory') for n, t in trees.items() if n.startswith('Spreads/')
    for el in t.iter('TextFrame'))
if orphan: note.append('cerceveye baglanmamis hikaye: %d' % len(orphan))

# 8 · gorseller: her bagin dosyasi diskte var mi
links = 0; miss = []
for n, t in trees.items():
    if not n.startswith('Spreads/'): continue
    for el in t.iter('Link'):
        links += 1
        uri = el.get('LinkResourceURI') or ''
        rel = uri[5:] if uri.startswith('file:') else uri
        if not os.path.isfile(os.path.join(ROOT, rel)): miss.append(rel)
for mm in sorted(set(miss))[:5]: bad.append('bag dosyasi yok: %s' % mm)
if len(set(miss)) > 5: bad.append('... ve %d bag daha' % (len(set(miss)) - 5))

# 9 · yazi tipleri: stillerin istedigi her aile Document fonts icinde mi
dfonts = os.path.join(ROOT, 'Document fonts')
have_f = set()
if os.path.isdir(dfonts):
    for f in os.listdir(dfonts): have_f.add(f.split('-')[0].lower())
want_f = set()
if st is not None:
    for el in st.iter('AppliedFont'):
        want_f.add((el.text or '').strip().lower())
for w in sorted(want_f - have_f):
    if w: bad.append('yazi tipi paketle gelmiyor: %s' % w)

# 10 · geometri: hicbir nesne yapragin makul sinirinin disina dusmesin
PT = 72 / 25.4
PWpt, PHpt = 240 * PT, 320 * PT
out = 0; items = 0
for n, t in trees.items():
    if not n.startswith('Spreads/'): continue
    sp = t.find('.//Spread')
    npages = len(sp.findall('Page')) if sp is not None else 1
    lo = -PWpt - 40 if npages > 1 else -40
    hi = PWpt + 40
    for el in list(t.iter('Rectangle')) + list(t.iter('TextFrame')):
        pts = [p.get('Anchor').split() for p in el.iter('PathPointType')]
        if not pts: continue
        items += 1
        xs = [float(p[0]) for p in pts]; ys = [float(p[1]) for p in pts]
        if min(xs) < lo or max(xs) > hi or min(ys) < -40 or max(ys) > PHpt + 40:
            out += 1
if out: bad.append('yaprak disina dusen nesne: %d / %d' % (out, items))

# 11 · sayfa sayisi ve yaprak duzeni
spreads = [n for n in names if n.startswith('Spreads/')]
pagecount = 0
for n in spreads:
    sp = trees[n].find('.//Spread')
    pagecount += len(sp.findall('Page')) if sp is not None else 0

print('paket : %s' % os.path.basename(IDML))
print('  yaprak %d · sayfa %d · nesne %d' % (len(spreads), pagecount, items))
print('  yazi cercevesi %d · hikaye %d · bag %d' % (frames, len(story_selfs), links))
print('  paragraf stili %d · karakter stili %d · renk %d'
      % (len(pdef), len(cdef), len(cols)))
print('  Links %d dosya · Document fonts %d dosya'
      % (len(os.listdir(os.path.join(ROOT, 'Links'))) if os.path.isdir(
          os.path.join(ROOT, 'Links')) else 0,
         len(os.listdir(dfonts)) if os.path.isdir(dfonts) else 0))
for nn in note: print('  not: %s' % nn)
for b in bad: print('  HATA: %s' % b)
print('DENETIM: %s' % ('temiz' if not bad else '%d bulgu' % len(bad)))
sys.exit(1 if bad else 0)
