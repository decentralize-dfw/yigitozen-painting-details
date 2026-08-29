# -*- coding: utf-8 -*-
"""Sayfa numarasi ile yili ayirir: numara bir uca, yil obur uca.

Ikisi tek cercevede, aralarinda bir bosluk karakteriyle duruyordu.
Numara otomatik alan oldugu icin genisligi sayfadan sayfaya degisiyor ve
iki basamakli sayfalarda yil numaraya yapisiyor. Ayak cizgisi boyunca
numara solda, yil ve yer sagda durursa bu bir daha olmaz.

Yil metni kendi cercevesine alinir, olcunun sag ucuna konur ve saga
dayali dizilir. Numaranin cercevesinde yalniz otomatik alan kalir.

    python3 fix-folio-year.py girdi.idml cikti.idml
"""
import os, sys, re, zipfile, shutil
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from place import transform

if len(sys.argv) < 3:
    sys.exit('kullanim: fix-folio-year.py girdi.idml cikti.idml')
SRC, DST = sys.argv[1], sys.argv[2]
PT = 72 / 25.4
RIGHT = 635.0            # olcunun sag ucu, sayfa sol kenarina gore punto
WIDE = 283.5             # yil cercevesinin genisligi

Z = zipfile.ZipFile(SRC)
raw = {n: (Z.read(n).decode('utf-8')
           if n.startswith(('Spreads/', 'Stories/')) or n == 'designmap.xml'
           else Z.read(n)) for n in Z.namelist()}


def links_of(zf):
    out = []
    for n in sorted(zf.namelist()):
        if not n.startswith('Spreads/'): continue
        for el in ET.fromstring(zf.read(n)).iter('Link'):
            out.append((n, el.get('LinkResourceURI'), el.get('LinkResourceFormat')))
    return out


def txt_of(blk):
    return ''.join(re.sub(r'<[^>]*>', '',
                          m.group(1)) for m in
                   re.finditer(r'<Content>([\s\S]*?)</Content>', blk))


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


UID = [0]
def uid(p):
    UID[0] += 1
    return '%s%05x' % (p, 0xe4000 + UID[0])


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
         '<ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/f rt">'
         '<CharacterStyleRange AppliedCharacterStyle="CharacterStyle/place" '
         'FontStyle="Medium"%(col)s>'
         '<Properties><AppliedFont type="string">Inter</AppliedFont></Properties>'
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


stories, done = {}, []
for n in sorted(raw):
    if not n.startswith('Spreads/'): continue
    sp = ET.fromstring(raw[n]).find('.//Spread')
    if sp is None: continue
    pg = {}
    for p in sp.findall('Page'):
        g = [float(v) for v in p.get('GeometricBounds').split()]
        it = [float(v) for v in (p.get('ItemTransform') or '1 0 0 1 0 0').split()]
        if p.get('Name', '').isdigit():
            pg[int(p.get('Name'))] = (g[1] + it[4], g[0] + it[5],
                                      g[3] + it[4], g[2] + it[5])
    adds = []
    for f in sp.iter('TextFrame'):
        sid = f.get('ParentStory')
        p = 'Stories/Story_%s.xml' % sid
        if p not in raw: continue
        s = raw[p]
        if '<?ACE 18?>' not in s: continue
        st = ET.fromstring(s)
        sty = next((q.get('AppliedParagraphStyle', '').split('/')[-1]
                    for q in st.iter('ParagraphStyleRange')), '')
        if not sty.startswith('f'): continue
        txt = ''.join((c.text or '') for c in st.iter('Content')).strip()
        if not txt: continue                       # yalniz numara: dokunma
        b = transform(f)
        q = next((v for v, (a1, b1, a2, b2) in pg.items()
                  if a1 - 1 <= (b[0] + b[2]) / 2 <= a2 + 1), None)
        if q is None: continue
        ox, oy = pg[q][0], pg[q][1]
        # 1 · numaranin cercevesinde yalniz otomatik alan kalsin.
        # Sayfa numarasi <?ACE 18?> isaretiyle Content'in ICINDE durur;
        # Content'i bosaltmak numarayi da siler. Bu yuzden yalniz yer
        # adini tasiyan karakter araligi cikarilir.
        cut = None
        for m in re.finditer(r'<CharacterStyleRange\b[\s\S]*?</CharacterStyleRange>', s):
            blk = m.group(0)
            if '<?ACE' in blk: continue
            if re.search(r'<Content>\s*</Content>', blk): continue
            if txt_of(blk).strip() == txt: cut = m
        if cut is None:
            print('  ATLANDI (yer adi araligi bulunamadi):', sid); continue
        raw[p] = s[:cut.start()] + s[cut.end():]
        # 2 · yil ve yer kendi cercevesinde, olcunun sag ucunda
        col = re.search(r'<CharacterStyleRange[^>]*(\sFillColor="[^"]*")', s)
        ns = uid('fy')
        stories['Stories/Story_%s.xml' % ns] = STORY % {
            'sid': ns, 'txt': esc(txt), 'col': col.group(1) if col else ''}
        adds.append(frame(ns, ox + RIGHT - WIDE, b[1], ox + RIGHT, b[3]))
        done.append((q, f.get('Self'), ns, txt))
    if adds:
        raw[n] = raw[n].replace('</Spread>', ''.join(adds) + '</Spread>', 1)

extra = ''.join('<idPkg:Story src="%s"/>' % k for k in stories)
s = raw['designmap.xml']
raw['designmap.xml'] = (s.replace('<idPkg:BackingStory', extra + '<idPkg:BackingStory', 1)
                        if '<idPkg:BackingStory' in s
                        else s.replace('</Document>', extra + '</Document>', 1))

before = links_of(Z)
tmp = DST + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for info in Z.infolist():
        d = raw[info.filename]
        if isinstance(d, str): d = d.encode('utf-8')
        if info.filename == 'mimetype':
            zi = zipfile.ZipInfo('mimetype'); zi.compress_type = zipfile.ZIP_STORED
            zo.writestr(zi, d)
        else:
            zo.writestr(info.filename, d)
    for k, v in stories.items():
        zo.writestr(k, v.encode('utf-8'))

z2 = zipfile.ZipFile(tmp)
ok = True
for nm in z2.namelist():
    if nm.endswith('.xml'):
        try: ET.fromstring(z2.read(nm))
        except Exception as e: ok = False; print('AYRISMADI', nm, e)
after = links_of(z2)
ace = sum(z2.read(n).count(b'<?ACE 18?>') for n in z2.namelist()
          if n.startswith('Stories/'))
z2.close()
ace0 = sum(Z.read(n).count(b'<?ACE 18?>') for n in Z.namelist()
           if n.startswith('Stories/'))
if ace != ace0:
    os.remove(tmp); sys.exit('DURDU: folyo isareti %d -> %d' % (ace0, ace))
if before != after: os.remove(tmp); sys.exit('DURDU: bag kaydi degisti')
if not ok: os.remove(tmp); sys.exit('DURDU: XML bozuldu')
shutil.move(tmp, DST)

import json
yj = os.path.join(os.path.dirname(os.path.abspath(DST)), 'yeni.json')
old = set(json.load(open(yj))) if os.path.exists(yj) else set()
json.dump(sorted(old | {b for _, _, b, _ in done}), open(yj, 'w'))

print('%s -> %s' % (os.path.basename(SRC), os.path.basename(DST)))
print('  ayrilan folyo: %d · otomatik sayfa numarasi %d, hepsi yerinde'
      % (len(done), ace))
for q, a, b, t in done[:6]:
    print('     s.%-4d %-9s -> %-9s saga dayali  %r' % (q, a, b, t))
print('     ...')
print('  bag kaydi %d · hepsi birebir ayni' % len(before))
