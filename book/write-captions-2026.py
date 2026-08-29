# -*- coding: utf-8 -*-
"""
2026 bolumunun altyazilarini yazar.

Duzenlemeden sonra bu bolumun onlarca sayfasi adsiz kaldi: Virgil'in on
sayfalik kesit dizisinde, gary grills cooper'in uc sayfasinda ve 7 fam
board game'in iki sayfasinda hicbir yazi yok. Gorselin ne oldugunu
soyleyen tek sey folyo.

Yazilanlar gorulen seydir: kesitin tabloda nerede durdugu ve elin orada
ne yaptigi. Gorulmeyen sey yazilmaz.

Yerlestirme kitabin kuralina uyar: kunye gorselin dort milimetre altinda,
gorselin genisliginde. Sayfayi dolduran ya da tasan bir gorselin altinda
yer olmadigi icin kunye sayfanin ayagina, dis kenardan olcu icine alinir.

    python3 write-captions-2026.py girdi.idml cikti.idml

Spreads/ icine yalniz yazi cercevesi eklenir. Bag kayitlari once-sonra
karsilastirilir; biri bile oynarsa dosya yazilmaz.
"""
import os, sys, re, zipfile, shutil, urllib.parse
import xml.etree.ElementTree as ET

if len(sys.argv) < 3:
    sys.exit('kullanim: write-captions-2026.py girdi.idml cikti.idml')
SRC, DST = sys.argv[1], sys.argv[2]

PT = 72 / 25.4
PW, PH = 240.0 * PT, 320.0 * PT
GAP = 4.0 * PT
FOOT = PH - 22.0 * PT + 6.0        # ayak olcusunun hemen ustu
OUTER, MEASURE = 16.0 * PT, 204.0 * PT

# Sayfa -> o sayfaya yazilacak kunyeler. Bir sayfada birden cok gorsel
# varsa kunyeler gorselin y sirasina gore eslesir.
CAPS = {
    # ── 01 · 7 fam board game ──────────────────────────────────────
    16: ['The board from the left · every cone wrapped, every head marked out'],
    17: ['The blue heads, crowded to the right edge · the cross is drawn twice '
         'on each'],
    # ── 02 · Virgil on Virtual Cage ────────────────────────────────
    19: ['The scene entire · the canopy laid in white line and left open'],
    20: ['The head under the wig · yellow carried over a ground kept dark'],
    21: ['The two figures held at the right · grey worked over yellow, no '
         'contour closing either'],
    23: ['The figure at the left, the hand brought up to the chin'],
    24: ['The red ground · one flat layer, then the strokes laid across it'],
    25: ['The winged figure, and the pair carried beneath it'],
    26: ['The cage from above · the white line stops before it closes',
         'The chair drawn on the pink panel'],
    27: ['The far corner of the same ceiling', 'The hand, opened, holding nothing'],
    # ── 03 · gary grills cooper ────────────────────────────────────
    33: ['The head and the cigar · the smoke is never drawn'],
    34: ['The hands, and the rod held between them'],
    35: ['The white cone at the shoulder',
         'The shoulder against the flat yellow'],
}

Z = zipfile.ZipFile(SRC)


def links_of(zf):
    out = []
    for n in sorted(zf.namelist()):
        if not n.startswith('Spreads/'): continue
        for el in ET.fromstring(zf.read(n)).iter('Link'):
            out.append((n, el.get('LinkResourceURI'), el.get('LinkResourceFormat')))
    return out


def bx(el, parent=(1, 0, 0, 1, 0, 0)):
    """Nesnenin yapraktaki kutusu.

    Geometri nesnenin kendi uzayinda yazilir; yaprakta nerede durdugunu
    ItemTransform soyler. Kendi urettigim dosyada bu birim donusumdu, ama
    InDesign dosyayi yeniden yazarken gercek donusumler koymus. Donusum
    uygulanmazsa koordinatlar sayfanin disina duser.
    """
    a, b, c, d, e, f = [float(v) for v in (el.get('ItemTransform') or
                                           '1 0 0 1 0 0').split()]
    pa, pb, pc, pd, pe, pf = parent
    # once nesnenin kendi donusumu, sonra kapsayanin
    m = (a * pa + b * pc, a * pb + b * pd,
         c * pa + d * pc, c * pb + d * pd,
         e * pa + f * pc + pe, e * pb + f * pd + pf)
    xs, ys = [], []
    for q in el.iter('PathPointType'):
        px, py = [float(v) for v in q.get('Anchor').split()]
        xs.append(m[0] * px + m[2] * py + m[4])
        ys.append(m[1] * px + m[3] * py + m[5])
    if not xs: return 0.0, 0.0, 0.0, 0.0
    return min(xs), min(ys), max(xs), max(ys)


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


UID = [0]
def uid(p):
    UID[0] += 1
    return '%s%05x' % (p, 0xb1000 + UID[0])


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
    t = ET.fromstring(raw)
    sp = t.find('.//Spread')
    rng = []
    for p in sp.findall('Page'):
        # y1 x1 y2 x2 — yapragin dikey basi her belgede sifir degildir,
        # bazilarinda sayfa dikeyde ortalanmis durur. Sayfanin kendi
        # sinirlari okunur, varsayilmaz.
        g = [float(v) for v in p.get('GeometricBounds').split()]
        it = [float(v) for v in (p.get('ItemTransform') or '1 0 0 1 0 0').split()]
        rng.append((g[1] + it[4], g[3] + it[4], p.get('Name'),
                    g[0] + it[5], g[2] + it[5]))
    bypage = {}
    for r in sp.iter('Rectangle'):
        if r.find('Image') is None: continue
        x1, y1, x2, y2 = bx(r)
        # Sayfayi asan bir gorselin sol kenari komsu sayfaya duser; hangi
        # sayfada durdugunu ortasi soyler, kenari degil.
        cx = (x1 + x2) / 2.0
        for lo, hi, q, ty, by in rng:
            if lo - 1 <= cx <= hi + 1 and q.isdigit():
                bypage.setdefault(int(q), []).append((y1, x1, x2, y2, lo, ty, by))
                break
    adds = []
    for pn, caps in CAPS.items():
        if pn not in bypage: continue
        imgs = sorted(bypage[pn])
        for k, cap in enumerate(caps):
            if k >= len(imgs): break
            y1, x1, x2, y2, lo, ptop, pbot = imgs[k]
            # Sayfayi dolduran gorselin altinda yer yok: kunye ayaga iner.
            fills = (y2 - y1) > PH * 0.86 or (x2 - x1) > PW * 0.92
            if fills or y2 + GAP + 34 > pbot:
                # Gorselin altinda yer yok. Kunye sayfanin ayagina degil,
                # GORSELIN kendi ayagina konur: sayfayi asan bir kesitte
                # sayfa ayagi baska sayfaya dusebilir ve kunye yanlis
                # resmin altinda kalir. Kendi kesitinin icinde durursa
                # hangi resmi anlattigi hicbir kosulda kaymaz.
                # Kesit kesim cizgisinin disina tasabilir; kunye tasmaz.
                # Once gorselin kutusu sayfaya kirpilir, kunye ondan sonra
                # yerlestirilir, yoksa sayfanin disinda kalir.
                gx1, gy2 = max(x1, lo), min(y2, pbot)
                cx1 = gx1 + OUTER
                cy1 = gy2 - 16.0 * PT - 34.0
                cx2 = min(cx1 + MEASURE, gx1 + PW - OUTER)
            else:
                cx1, cy1 = max(x1, lo), y2 + GAP
                cx2 = min(max(x2, x1 + 150), lo + PW)
            sid = uid('cw')
            # Sayfayi dolduran koyu gorselin ustunde kunye kagit rengi olur.
            col = ' FillColor="Color/paper"' if fills else ''
            stories['Stories/Story_%s.xml' % sid] = STORY % {
                'sid': sid, 'txt': esc(cap), 'col': col}
            adds.append(frame(sid, cx1, cy1, cx2, cy1 + 34))
            placed.append((pn, 'ayak' if fills else 'gorsel alti', cap[:58]))
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
for pn, where, c in sorted(placed):
    print('     s.%-4d %-14s %r' % (pn, where, c))
print('  bag kaydi %d · hepsi birebir ayni' % len(before))
