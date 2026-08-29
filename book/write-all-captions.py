# -*- coding: utf-8 -*-
"""
Kitabin butun yeni kunyelerini, hicbirinin uzerine binmeden yazar.

Onceki iki betik kunyeyi gorselin dort milimetre altina koyuyordu ve orada
baska bir sey olup olmadigina bakmiyordu. Bergman kunyesi folyonun tam
ustune oturdu. Burada once sayfada dolu olan her yer toplanir, sonra kunye
bos bir yere konur; hicbir yerde yer yoksa o kunye yazilmaz ve raporda
soylenir. Yanlis yere konmus bir kunye hic konmamistan kotudur.

    python3 write-all-captions.py girdi.idml cikti.idml

Gorsellere dokunulmaz: Spreads/ icine yalniz yazi cercevesi eklenir ve her
Link kaydi once-sonra karsilastirilir.
"""
import os, sys, re, json, zipfile, shutil, urllib.parse
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from place import transform, caption_height, occupied, place, PT, PW, PH

if len(sys.argv) < 4:
    sys.exit('kullanim: write-all-captions.py girdi.idml oturmus.json cikti.idml')
SRC, OCC, DST = sys.argv[1], sys.argv[2], sys.argv[3]
# Sayfadaki gercek dolu yerler: fix-stack'in olctugu, oturmus duzendeki
# basili satirlar. Belgede yazan cerceve olcusu buyumeden oncekidir ve
# onunla kacinilirsa kunye yazinin ustune oturur.
TAKEN = {int(k): v for k, v in json.load(open(OCC)).items()}

# ── dosya adiyla eslenen kunyeler ───────────────────────────────────
BYFILE = {
    'Image-1.jpg':
        'The source — Ingmar Bergman, The Seventh Seal, 1957 · a game '
        'played against something that does not lose. Copyright remains '
        'with the rights holder',
    'feb1f60715851a01a850fb30e4f1d516.jpg':
        'The source — John William Waterhouse, Ulysses and the Sirens, '
        '1891 · the rowers hold their line while the birds come down the '
        'diagonal. Public domain',
    'IMG_0294.jpg':
        'The studio, Luxembourg · the ground worked flat with a knife '
        'before any figure is found',
    'Stlop-full copy.png':
        '06 · s(t)lop · the painting whole, after the four details',
    '3.jpg':
        '07 · penguin is not a friend, only a sinner · the one commission '
        'of the painting years',
}

# ── sayfayla eslenen kunyeler, gorselin y sirasina gore ─────────────
BYPAGE = {
    5:  ['05 · articulo attack on mandarin · the pale form against the '
         'scraped ground, the blue only at its head'],
    15: ['01 · 7 fam board game · the left player, built of rounded units '
         'that never close into a face'],
    16: ['The board from the left · every cone wrapped, every head marked out'],
    17: ['The blue heads, crowded to the right edge · the cross is drawn '
         'twice on each'],
    19: ['The scene entire · the canopy laid in white line and left open'],
    20: ['The head under the wig · yellow carried over a ground kept dark'],
    21: ['The two figures held at the right · grey worked over yellow, no '
         'contour closing either'],
    23: ['The figure at the left, the hand brought up to the chin'],
    24: ['The red ground · one flat layer, then the strokes laid across it'],
    25: ['The winged figure, and the pair carried beneath it'],
    26: ['The cage from above · the white line stops before it closes',
         'The chair drawn on the pink panel'],
    27: ['The far corner of the same ceiling',
         'The hand, opened, holding nothing'],
    28: ['Stage 2 — the Leonardo carried through in pencil, the whole '
         'composition before any colour'],
    29: ['Stage 3 — the ground drowned in red, the figure left as bare '
         'canvas inside it'],
    33: ['The head and the cigar · the smoke is never drawn'],
    34: ['The hands, and the rod held between them'],
    35: ['The white cone at the shoulder',
         'The shoulder against the flat yellow'],
    38: ['04 · walls of perception · the banded upper half, and the pink '
         'strokes standing under it'],
    39: ['The yellow burst against the red · the studies beneath it, in the '
         'order they were made'],
    44: ['The flock, upper middle · blue, grey, white and black only',
         'The same flock lower down, where the birds meet the water'],
    46: ['The full height · the birds above, the boat and its rowers below',
         'The study, before the birds'],
    47: ['The dark upper third, the water, and the boat · three bands, no '
         'line drawn between them'],
    51: ['06 · s(t)lop · the rounded fields, lilac over turquoise, nothing '
         'closed'],
    53: ['The figure found among the strokes, at the middle right'],
    57: ['07 · penguin is not a friend, only a sinner · the mass swept '
         'outward from one centre'],
    66: ['09 · cellular spleens · the red limb laid over the pink ground'],
    67: ['The cells packed against each other, each ring left open'],
}

Z = zipfile.ZipFile(SRC)


def links_of(zf):
    out = []
    for n in sorted(zf.namelist()):
        if not n.startswith('Spreads/'): continue
        for el in ET.fromstring(zf.read(n)).iter('Link'):
            out.append((n, el.get('LinkResourceURI'), el.get('LinkResourceFormat')))
    return out


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


UID = [0]
def uid(p):
    UID[0] += 1
    return '%s%05x' % (p, 0xd3000 + UID[0])


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


def frame(sid, box):
    x1, y1, x2, y2 = box
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
stories, spread_new, placed, skipped = {}, {}, [], []

for n in Z.namelist():
    if not n.startswith('Spreads/'): continue
    raw = Z.read(n).decode('utf-8')
    sp = ET.fromstring(raw).find('.//Spread')
    pages = {}
    for p in sp.findall('Page'):
        g = [float(v) for v in p.get('GeometricBounds').split()]
        it = [float(v) for v in (p.get('ItemTransform') or '1 0 0 1 0 0').split()]
        if p.get('Name', '').isdigit():
            pages[int(p.get('Name'))] = (g[1] + it[4], g[0] + it[5],
                                         g[3] + it[4], g[2] + it[5])
    # Sayfadaki gorseller
    imgs = {}
    for r in sp.iter('Rectangle'):
        im = r.find('Image')
        if im is None: continue
        b = transform(r)
        if not b: continue
        cx = (b[0] + b[2]) / 2.0
        for pn, (px1, pty, px2, pby) in pages.items():
            if px1 - 1 <= cx <= px2 + 1:
                f = urllib.parse.unquote(
                    im.find('Link').get('LinkResourceURI') or '').split('/')[-1]
                imgs.setdefault(pn, []).append((b, f))
                break
    # Dolu yerler: bu yapraktaki basili her satir, sayfa yerinden yaprak
    # yerine tasinmis olarak.
    taken = []
    for pn, (px1, pty, px2, pby) in pages.items():
        for x1, y1, x2, y2 in TAKEN.get(pn, []):
            taken.append((x1 + px1, y1 + pty, x2 + px1, y2 + pty))
    adds = []

    def put(pn, box_img, text):
        box = place(box_img, pages[pn], taken, text)
        if box is None:
            skipped.append((pn, text[:52])); return
        sid = uid('cn')
        stories['Stories/Story_%s.xml' % sid] = STORY % {
            'sid': sid, 'txt': esc(text), 'col': ''}
        adds.append(frame(sid, box))
        taken.append(box)
        placed.append((pn, round((box[1] - pages[pn][1]) / PT), text[:52]))

    # dosya adiyla eslenenler
    for pn in sorted(imgs):
        for b, f in imgs[pn]:
            if f in BYFILE: put(pn, b, BYFILE[f])
    # sayfayla eslenenler
    for pn in sorted(imgs):
        if pn not in BYPAGE: continue
        order = sorted(imgs[pn], key=lambda t: t[0][1])
        for k, text in enumerate(BYPAGE[pn]):
            if k >= len(order): break
            put(pn, order[k][0], text)

    if adds:
        spread_new[n] = raw.replace('</Spread>', ''.join(adds) + '</Spread>', 1)

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
for pn, y, t in sorted(placed):
    print('     s.%-4d y=%4dmm  %r' % (pn, y, t))
if skipped:
    print('  YER BULUNAMADI, yazilmadi: %d' % len(skipped))
    for pn, t in skipped: print('     s.%-4d %r' % (pn, t))
print('  bag kaydi %d · hepsi birebir ayni' % len(before))
