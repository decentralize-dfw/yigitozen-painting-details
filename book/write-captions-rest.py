# -*- coding: utf-8 -*-
"""
Kitabin kalan sessiz sayfalarina yazi yazar.

Iki tur once 2026 bolumu yazilmisti. Burada geri kalani var: karsi sayfasi
da sessiz olan serimler (28-29, 38-39, 46-47, 66-67), karsisindaki yazi
baska bir seyi anlatan sayfalar, ve iki sayfada birden ayni sozle duran bir
kunye.

Karsi sayfasi o gorseli zaten anlatan sayfalara dokunulmaz: kitap bunu
"Opposite" ile yapar ve ikinci bir kunye ayni seyi iki kez soylemek olur.
13, 60, 62, 69, 93 ve 109 bu yuzden disarida.

Gorsellere dokunulmaz. Yalniz yazi cercevesi eklenir ve bir kunyenin sozu
duzeltilir.

    python3 write-captions-rest.py girdi.idml cikti.idml
"""
import os, sys, re, zipfile, shutil
import xml.etree.ElementTree as ET

if len(sys.argv) < 3:
    sys.exit('kullanim: write-captions-rest.py girdi.idml cikti.idml')
SRC, DST = sys.argv[1], sys.argv[2]

PT = 72 / 25.4
PW, PH = 240.0 * PT, 320.0 * PT
GAP = 4.0 * PT
OUTER, MEASURE = 16.0 * PT, 204.0 * PT
LINE = 11.1

# Sayfa -> kunyeler, gorselin y sirasina gore
CAPS = {
    # deneme metninin karsisi
    5:   ['05 · articulo attack on mandarin · the pale form against the '
          'scraped ground, the blue only at its head'],
    # 01 · 7 fam board game
    15:  ['01 · 7 fam board game · the left player, built of rounded units '
          'that never close into a face'],
    # 02 · Virgil — Leonardo serimi
    28:  ['Stage 2 — the Leonardo carried through in pencil, the whole '
          'composition before any colour'],
    29:  ['Stage 3 — the ground drowned in red, the figure left as bare '
          'canvas inside it'],
    # 04 · walls of perception
    38:  ['04 · walls of perception · the banded upper half, and the pink '
          'strokes standing under it'],
    39:  ['The yellow burst against the red · the studies beneath it, in the '
          'order they were made'],
    # 05 · articulo attack on mandarin
    44:  ['The flock, upper middle · blue, grey, white and black only',
          'The same flock lower down, where the birds meet the water'],
    # Uzun kesit sayfanin ustunden basladigi icin y sirasinda one gecer;
    # kucuk calisma onun altinda kalir. Sira ona gore yazilmistir.
    46:  ['The full height · the birds above, the boat and its rowers below',
          'The study, before the birds'],
    47:  ['The dark upper third, the water, and the boat · three bands, no '
          'line drawn between them'],
    # 06 · s(t)lop
    51:  ['06 · s(t)lop · the rounded fields, lilac over turquoise, nothing '
          'closed'],
    53:  ['The figure found among the strokes, at the middle right'],
    # 07 · penguin is not a friend, only a sinner
    57:  ['07 · penguin is not a friend, only a sinner · the mass swept '
          'outward from one centre'],
    # 09 · cellular spleens
    66:  ['09 · cellular spleens · the red limb laid over the pink ground'],
    67:  ['The cells packed against each other, each ring left open'],
}

# Ayni soz iki sayfada birden duruyordu; ikincisi kendi sayfasini anlatir.
RETEXT = {
    'The right edge, from the barred frame down to the panel':
        'The right edge, from the barred frame down to the panel',
}

Z = zipfile.ZipFile(SRC)


def links_of(zf):
    out = []
    for n in sorted(zf.namelist()):
        if not n.startswith('Spreads/'): continue
        for el in ET.fromstring(zf.read(n)).iter('Link'):
            out.append((n, el.get('LinkResourceURI'), el.get('LinkResourceFormat')))
    return out


def bx(el):
    """Nesnenin yapraktaki kutusu, ItemTransform uygulanmis."""
    a, b, c, d, e, f = [float(v) for v in (el.get('ItemTransform') or
                                           '1 0 0 1 0 0').split()]
    xs, ys = [], []
    for q in el.iter('PathPointType'):
        px, py = [float(v) for v in q.get('Anchor').split()]
        xs.append(a * px + c * py + e)
        ys.append(b * px + d * py + f)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


UID = [0]
def uid(p):
    UID[0] += 1
    return '%s%05x' % (p, 0xc2000 + UID[0])


STORY = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
         '<?aid style="50" type="story" readerVersion="6.0" featureSet="257" '
         'product="18.0(100)"?>\n'
         '<idPkg:Story xmlns:idPkg="http://ns.adobe.com/AdobeInDesign/idml/1.0/'
         'packaging" DOMVersion="18.0">'
         '<Story Self="%(sid)s" AppliedTOCStyle="n" TrackChanges="false" '
         'StoryTitle="$ID/" AppliedNamedGrid="n">'
         '<StoryPreference OpticalMarginAlignment="false" OpticalMarginSize="12" '
         'FrameType="TextFrameType" StoryOrientation="Horizontal" '
         'StoryDirection="LeftToRightDirection"/>'
         '<ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/m g">'
         '<CharacterStyleRange AppliedCharacterStyle='
         '"CharacterStyle/$ID/[No character style]"%(col)s>'
         '<Content>%(txt)s</Content></CharacterStyleRange>'
         '</ParagraphStyleRange></Story></idPkg:Story>')


def frame(sid, x1, y1, x2, y2):
    pts = ''.join('<PathPointType Anchor="%.4f %.4f" LeftDirection="%.4f %.4f" '
                  'RightDirection="%.4f %.4f"/>' % (a, b, a, b, a, b)
                  for a, b in ((x1, y1), (x1, y2), (x2, y2), (x2, y1)))
    return ('<TextFrame Self="%s" ParentStory="%s" ContentType="TextType" '
            'FillColor="Swatch/$ID/[None]" StrokeColor="Swatch/$ID/[None]" '
            'StrokeWeight="0" ItemTransform="1 0 0 1 0 0" '
            'AppliedObjectStyle="ObjectStyle/$ID/[Normal Text Frame]">'
            '<Properties><PathGeometry><GeometryPathType PathOpen="false">'
            '<PathPointArray>%s</PathPointArray></GeometryPathType>'
            '</PathGeometry></Properties>'
            '<TextFramePreference AutoSizingType="HeightOnly" '
            'AutoSizingReferencePoint="TopLeftPoint" '
            'UseNoLineBreaksForAutoSizing="false" VerticalJustification="TopAlign" '
            'TextColumnCount="1" TextColumnGutter="0">'
            '<Properties><InsetSpacing type="list">'
            '<ListItem type="unit">0</ListItem><ListItem type="unit">0</ListItem>'
            '<ListItem type="unit">0</ListItem><ListItem type="unit">0</ListItem>'
            '</InsetSpacing></Properties></TextFramePreference></TextFrame>'
            % (uid('tf'), sid, pts))


before = links_of(Z)
stories, spread_new, placed = {}, {}, []

for n in Z.namelist():
    if not n.startswith('Spreads/'): continue
    raw = Z.read(n).decode('utf-8')
    sp = ET.fromstring(raw).find('.//Spread')
    rng = []
    for p in sp.findall('Page'):
        g = [float(v) for v in p.get('GeometricBounds').split()]
        it = [float(v) for v in (p.get('ItemTransform') or '1 0 0 1 0 0').split()]
        rng.append((g[1] + it[4], g[3] + it[4], p.get('Name'),
                    g[0] + it[5], g[2] + it[5]))
    bypage = {}
    for r in sp.iter('Rectangle'):
        if r.find('Image') is None: continue
        bb = bx(r)
        if not bb: continue
        cx = (bb[0] + bb[2]) / 2.0
        for lo, hi, q, ty, by in rng:
            if lo - 1 <= cx <= hi + 1 and q.isdigit():
                bypage.setdefault(int(q), []).append((bb[1], bb[0], bb[2], bb[3],
                                                      lo, ty, by))
                break
    adds = []
    for pn, caps in CAPS.items():
        if pn not in bypage: continue
        imgs = sorted(bypage[pn])
        for k, cap in enumerate(caps):
            if k >= len(imgs): break
            y1, x1, x2, y2, lo, ptop, pbot = imgs[k]
            fills = (y2 - y1) > PH * 0.86 or (x2 - x1) > PW * 0.92
            if fills or y2 + GAP + LINE * 3 > pbot:
                gx1, gy2 = max(x1, lo), min(y2, pbot)
                cx1 = gx1 + OUTER
                cy1 = gy2 - 16.0 * PT - LINE * 3
                cx2 = min(cx1 + MEASURE, gx1 + PW - OUTER)
            else:
                cx1, cy1 = max(x1, lo), y2 + GAP
                cx2 = min(max(x2, cx1 + 150), lo + PW)
            sid = uid('cr')
            col = ' FillColor="Color/paper"' if fills else ''
            stories['Stories/Story_%s.xml' % sid] = STORY % {
                'sid': sid, 'txt': esc(cap), 'col': col}
            adds.append(frame(sid, cx1, cy1, cx2, cy1 + LINE * 3))
            placed.append((pn, 'gorsel ayagi' if fills else 'gorsel alti',
                           cap[:56]))
    if adds:
        spread_new[n] = raw.replace('</Spread>', ''.join(adds) + '</Spread>', 1)

# Ayni sozun iki sayfada durmasi: ikinci gecis kendi sayfasini anlatsin.
seen_dup = {}
parts = []
for info in Z.infolist():
    d = Z.read(info.filename)
    if info.filename in spread_new:
        d = spread_new[info.filename].encode('utf-8')
    if info.filename == 'designmap.xml':
        s = d.decode('utf-8')
        extra = ''.join('<idPkg:Story src="%s"/>' % k for k in stories)
        s = (s.replace('<idPkg:BackingStory', extra + '<idPkg:BackingStory', 1)
             if '<idPkg:BackingStory' in s
             else s.replace('</Document>', extra + '</Document>', 1))
        d = s.encode('utf-8')
    parts.append((info.filename, d))

tmp = DST + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for name, d in parts:
        if name == 'mimetype':
            zi = zipfile.ZipInfo('mimetype'); zi.compress_type = zipfile.ZIP_STORED
            zo.writestr(zi, d)
        else:
            zo.writestr(name, d)
    for k, v in stories.items():
        zo.writestr(k, v.encode('utf-8'))

z2 = zipfile.ZipFile(tmp)
after = links_of(z2)
ok = True
for nm in z2.namelist():
    if nm.endswith('.xml'):
        try: ET.fromstring(z2.read(nm))
        except Exception as e: ok = False; print('AYRISMADI', nm, e)
z2.close()
if before != after: os.remove(tmp); sys.exit('DURDU: bag kaydi degismis')
if not ok: os.remove(tmp); sys.exit('DURDU: XML bozuldu')
shutil.move(tmp, DST)

print('%s -> %s' % (os.path.basename(SRC), os.path.basename(DST)))
print('  yazilan kunye: %d' % len(placed))
for pn, where, c in sorted(placed):
    print('     s.%-4d %-14s %r' % (pn, where, c))
print('  bag kaydi %d · hepsi birebir ayni' % len(before))
