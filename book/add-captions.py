# -*- coding: utf-8 -*-
"""
Yeni gorsellere altyazi yazar ve yerine koyar.

Duzenlerken kitaba giren gorsellerin bir kismi altyazisiz kaldi, bir kismi
da yerinde duran eski altyaziyla eslesmiyor. Bu betik altyazilari kitabin
kendi kademesinde — kunye stili, buyuk harf, gri — yazar ve her birini ait
oldugu gorselin sol alt kosesine, dort milimetre altina koyar; kitabin
kurali budur.

Odunc alinan iki gorsel icin kunye zorunludur: kimin, hangi is, hangi yil.
Kitap bunu Leonardo icin zaten yapiyordu; Bergman ve Waterhouse da ayni
bicimde anilir.

    python3 add-captions.py girdi.idml cikti.idml

Yeni yazi cercevesi eklemek Spreads/ icine dokunmayi gerektirir. Bag
kayitlari yine once-sonra karsilastirilir: biri bile oynarsa dosya
yazilmaz. Gorseller ne yer degistirir ne yeniden baglanir.
"""
import os, sys, re, zipfile, shutil, urllib.parse
import xml.etree.ElementTree as ET

if len(sys.argv) < 3:
    sys.exit('kullanim: add-captions.py girdi.idml cikti.idml')
SRC, DST = sys.argv[1], sys.argv[2]

PT = 72 / 25.4
GAP = 4.0 * PT          # kunye gorselin dort milimetre altinda durur
LINE = 11.1             # kunye satir araligi

# Dosya adi -> yazilacak altyazi. Kitabin sesi: buyuk harf stilden gelir,
# burada duz yazilir; nokta yerine orta nokta, kisa ve olculu.
CAPTIONS = {
    # Odunc alinanlar — kunye zorunlu
    'Image-1.jpg':
        'The source — Ingmar Bergman, The Seventh Seal, 1957 · a game '
        'played against something that does not lose. Copyright remains '
        'with the rights holder',
    'feb1f60715851a01a850fb30e4f1d516.jpg':
        'The source — John William Waterhouse, Ulysses and the Sirens, '
        '1891 · the rowers hold their line while the birds come down the '
        'diagonal. Public domain',
    # Atolye
    'IMG_0294.jpg':
        'The studio, Luxembourg · the ground worked flat with a knife '
        'before any figure is found',
    # Altyazisiz kalan levhalar
    'Stlop-full copy.png':
        '06 · s(t)lop · the painting whole, after the four details',
    '3.jpg':
        '07 · penguin is not a friend, only a sinner · the one commission '
        'of the painting years',
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
    pts = [q.get('Anchor').split() for q in el.iter('PathPointType')]
    xs = [float(q[0]) for q in pts]; ys = [float(q[1]) for q in pts]
    return min(xs), min(ys), max(xs), max(ys)


def esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


UID = [0]
def uid(p):
    UID[0] += 1
    return '%s%05x' % (p, 0x9a000 + UID[0])


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
         '"CharacterStyle/$ID/[No character style]">'
         '<Content>%(txt)s</Content></CharacterStyleRange>'
         '</ParagraphStyleRange></Story></idPkg:Story>')


def frame_xml(sid, x1, y1, x2, y2):
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
new_stories = {}
spread_add = {}
placed = []

for n in Z.namelist():
    if not n.startswith('Spreads/'): continue
    raw = Z.read(n).decode('utf-8')
    t = ET.fromstring(raw)
    sp = t.find('.//Spread')
    rng = []
    for p in sp.findall('Page'):
        g = [float(v) for v in p.get('GeometricBounds').split()]
        rng.append((g[1], g[3], p.get('Name')))
    adds = []
    for r in sp.iter('Rectangle'):
        im = r.find('Image')
        if im is None: continue
        f = urllib.parse.unquote(im.find('Link').get('LinkResourceURI') or '').split('/')[-1]
        if f not in CAPTIONS: continue
        x1, y1, x2, y2 = bx(r)
        pn = next((q for lo, hi, q in rng if lo - 1 <= x1 <= hi + 1), '?')
        # Kunye gorselin sol alt kosesinden dort milimetre asagida baslar,
        # genisligi gorselin genisligi kadardir.
        cx1, cy1 = x1, y2 + GAP
        cx2, cy2 = max(x2, x1 + 120), y2 + GAP + LINE * 3
        sid = uid('cs')
        new_stories['Stories/Story_%s.xml' % sid] = (
            STORY % {'sid': sid, 'txt': esc(CAPTIONS[f])})
        adds.append(frame_xml(sid, cx1, cy1, cx2, cy2))
        placed.append((pn, f, CAPTIONS[f][:52]))
    if adds:
        spread_add[n] = raw.replace('</Spread>', ''.join(adds) + '</Spread>', 1)

# ── yaz ─────────────────────────────────────────────────────────────
parts = []
for info in Z.infolist():
    data = Z.read(info.filename)
    if info.filename in spread_add:
        data = spread_add[info.filename].encode('utf-8')
    if info.filename == 'designmap.xml':
        s = data.decode('utf-8')
        extra = ''.join('<idPkg:Story src="%s"/>' % k for k in new_stories)
        s = s.replace('<idPkg:BackingStory', extra + '<idPkg:BackingStory', 1)
        if extra not in s:      # BackingStory yoksa belgenin sonuna
            s = s.replace('</Document>', extra + '</Document>', 1)
        data = s.encode('utf-8')
    parts.append((info.filename, data, info))

tmp = DST + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for name, data, info in parts:
        if name == 'mimetype':
            zi = zipfile.ZipInfo('mimetype'); zi.compress_type = zipfile.ZIP_STORED
            zo.writestr(zi, data)
        else:
            zo.writestr(name, data)
    for k, v in new_stories.items():
        zo.writestr(k, v.encode('utf-8'))

z2 = zipfile.ZipFile(tmp)
after = links_of(z2)
ok = True
for n in z2.namelist():
    if n.endswith('.xml'):
        try: ET.fromstring(z2.read(n))
        except Exception as e: ok = False; print('AYRISMADI', n, e)
z2.close()
if before != after:
    os.remove(tmp); sys.exit('DURDU: bag kaydi degismis, dosya yazilmadi')
if not ok:
    os.remove(tmp); sys.exit('DURDU: XML bozuldu, dosya yazilmadi')
shutil.move(tmp, DST)

print('%s -> %s' % (os.path.basename(SRC), os.path.basename(DST)))
print('  yeni altyazi: %d' % len(placed))
for pn, f, c in placed:
    print('     s.%-4s %-34s %r' % (pn, f[:34], c))
print('  bag kaydi %d · hepsi birebir ayni · her XML ayrisiyor' % len(before))
