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
if os.path.isfile(ROOT) and ROOT.endswith('.idml'):
    IDML, ROOT = ROOT, os.path.dirname(ROOT)
else:
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
# InDesign'in kendi hazir kunyeleri Graphic.xml'de yazili olmaz.
BUILTIN = {'Swatch/$ID/[None]', 'Color/$ID/[Black]', 'Color/$ID/[Paper]',
           'Color/$ID/[Registration]', 'Swatch/None'}
for u in sorted(used_col - cols - BUILTIN):
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

# 9 · yazi tipleri: her stilin istedigi aile+kesim cifti, pakette o adi
#     gercekten tasiyan bir dosyaya karsilik geliyor mu. Dosya adina degil,
#     dosyanin kendi ad tablosuna bakilir: Inter'in SemiBold kesimi 'Inter'
#     ailesinde 'SemiBold' diye degil, 'Inter SemiBold' ailesinde 'Regular'
#     diye durur. Yanlis sorulursa InDesign bulamaz ve yaziyi pembe zeminle
#     isaretler; bu denetim tam olarak onu yakalar.
def ttf_names(path):
    import struct
    d = open(path, 'rb').read()
    n = struct.unpack('>H', d[4:6])[0]
    tab = {}
    for i in range(n):
        o = 12 + 16 * i
        off, ln = struct.unpack('>II', d[o + 8:o + 16])
        tab[d[o:o + 4].decode('latin1')] = (off, ln)
    if 'name' not in tab: return ('', '')
    off = tab['name'][0]
    cnt, so = struct.unpack('>HH', d[off + 2:off + 6])
    got = {}
    for i in range(cnt):
        r = off + 6 + 12 * i
        pid, eid, lid, nid, sl, so2 = struct.unpack('>HHHHHH', d[r:r + 12])
        raw = d[off + so + so2: off + so + so2 + sl]
        try:
            v = raw.decode('utf-16-be') if pid == 3 else raw.decode('latin1')
        except Exception:
            continue
        if nid in (1, 2) and nid not in got: got[nid] = v
    return (got.get(1, ''), got.get(2, 'Regular'))

dfonts = os.path.join(ROOT, 'Document fonts')
have_f = set()
if os.path.isdir(dfonts):
    for f in os.listdir(dfonts):
        if f.lower().endswith(('.ttf', '.otf')):
            have_f.add(ttf_names(os.path.join(dfonts, f)))
else:
    bad.append('Document fonts klasoru yok')

def pairs(tree):
    """Bir stildeki AppliedFont + FontStyle ciftleri."""
    out = set()
    for el in tree.iter():
        if el.tag not in ('ParagraphStyle', 'CharacterStyle'): continue
        fam = el.find('.//AppliedFont')
        sty = el.find('FontStyle')
        if fam is None or sty is None: continue
        out.add(((fam.text or '').strip(), (sty.text or '').strip()))
    return out

want_f = pairs(st) if st is not None else set()
for fam, sty in sorted(want_f - have_f):
    bad.append('bu aile+kesim pakette yok: %r + %r  (pakette: %s)'
               % (fam, sty, ', '.join('%s/%s' % h for h in sorted(have_f))[:120]))
note.append('yazi tipi cifti: %d istendi, %d pakette' % (len(want_f), len(have_f)))

# 10 · geometri: hicbir nesne sayfalarin disina dusmesin
# Olcu ItemTransform uygulanarak alinir — PathPointType degerleri nesnenin
# kendi uzayindadir — ve sinir yapragin kendi sayfa dikdortgenlerinden
# okunur; varsayilan bir sayfa boyu bu belgeye uymuyor.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from place import transform
PT = 72 / 25.4
SLACK = 40.0
out = 0; items = 0; outlist = []
for n, t in trees.items():
    if not n.startswith('Spreads/'): continue
    sp = t.find('.//Spread')
    if sp is None: continue
    pg = []
    for p in sp.findall('Page'):
        g = [float(v) for v in p.get('GeometricBounds').split()]
        it = [float(v) for v in (p.get('ItemTransform') or '1 0 0 1 0 0').split()]
        pg.append((g[1] + it[4], g[0] + it[5], g[3] + it[4], g[2] + it[5]))
    if not pg: continue
    lo, top = min(q[0] for q in pg), min(q[1] for q in pg)
    hi, bot = max(q[2] for q in pg), max(q[3] for q in pg)
    for el in list(t.iter('Rectangle')) + list(t.iter('TextFrame')):
        bx = transform(el)
        if not bx: continue
        items += 1
        if (bx[2] < lo - SLACK or bx[0] > hi + SLACK
                or bx[3] < top - SLACK or bx[1] > bot + SLACK):
            out += 1
            if len(outlist) < 8: outlist.append((n.split('/')[-1], el.get('Self')))
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
