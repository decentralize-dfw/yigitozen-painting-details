# -*- coding: utf-8 -*-
"""Kunyenin rengini altindaki zemine gore secer.

Ayni gri, beyaz kagit uzerinde okunur, koyu bir tablonun uzerinde
okunmaz. Her yeni kunyenin oturdugu yer ciktidan orneklenir; zemin
koyuysa kunye kagit rengine cevrilir.

Gorseller degismedigi icin eldeki cikti bu olcum icin gecerlidir.

    python3 caption-colour.py girdi.idml cikti.pdf cikti.idml
"""
import os, sys, re, zipfile, shutil
import xml.etree.ElementTree as ET
import pymupdf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from place import transform

if len(sys.argv) < 4:
    sys.exit('kullanim: caption-colour.py girdi.idml cikti.pdf cikti.idml')
SRC, PDF, DST = sys.argv[1], sys.argv[2], sys.argv[3]
Z, D = zipfile.ZipFile(SRC), pymupdf.open(PDF)
NEW = re.compile(r'^(cn|cw|cs|cr)')


def links_of(zf):
    out = []
    for n in sorted(zf.namelist()):
        if not n.startswith('Spreads/'): continue
        for el in ET.fromstring(zf.read(n)).iter('Link'):
            out.append((n, el.get('LinkResourceURI'), el.get('LinkResourceFormat')))
    return out


before = links_of(Z)
dark, light = [], []
for n in Z.namelist():
    if not n.startswith('Spreads/'): continue
    sp = ET.fromstring(Z.read(n)).find('.//Spread')
    pages = {}
    for p in sp.findall('Page'):
        g = [float(v) for v in p.get('GeometricBounds').split()]
        it = [float(v) for v in (p.get('ItemTransform') or '1 0 0 1 0 0').split()]
        if p.get('Name', '').isdigit():
            pages[int(p.get('Name'))] = (g[1] + it[4], g[0] + it[5],
                                         g[3] + it[4], g[2] + it[5])
    for f in sp.iter('TextFrame'):
        sid = f.get('ParentStory')
        if not NEW.match(sid or ''): continue
        b = transform(f)
        pn = next((q for q, (a1, b1, a2, b2) in pages.items()
                   if a1 - 1 <= (b[0] + b[2]) / 2 <= a2 + 1), None)
        if pn is None or pn > len(D): continue
        ox, oy = pages[pn][0], pages[pn][1]
        r = pymupdf.Rect(b[0] - ox, b[1] - oy, b[2] - ox, b[3] - oy) \
            & D[pn - 1].rect
        if r.is_empty: continue
        pm = D[pn - 1].get_pixmap(clip=r, colorspace=pymupdf.csGRAY)
        v = sorted(pm.pixel(i, j)[0] for j in range(pm.height)
                   for i in range(pm.width))
        med = v[len(v) // 2] if v else 255
        # Esik ortadan gecmez: kunye ya kagit rengine ya murekkebe
        # cevrilecek. Kagit 255, murekkep 30 civari; ikisinin zemine
        # uzakligi 142'de esitlenir, dolayisiyla ayrim orada durur.
        (dark if med < 142 else light).append((pn, sid, med))

want = {sid for _, sid, _ in dark}
parts = []
for info in Z.infolist():
    d = Z.read(info.filename)
    m = re.match(r'Stories/Story_(\w+)\.xml$', info.filename)
    if m and m.group(1) in want:
        s = d.decode('utf-8')
        s = s.replace('<CharacterStyleRange AppliedCharacterStyle='
                      '"CharacterStyle/$ID/[No character style]">',
                      '<CharacterStyleRange AppliedCharacterStyle='
                      '"CharacterStyle/$ID/[No character style]" '
                      'FillColor="Color/paper">')
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

z2 = zipfile.ZipFile(tmp)
ok = True
for nm in z2.namelist():
    if nm.endswith('.xml'):
        try: ET.fromstring(z2.read(nm))
        except Exception as e: ok = False; print('AYRISMADI', nm, e)
after = links_of(z2)
n = sum(1 for nm in z2.namelist()
        if re.match(r'Stories/Story_(cn|cw|cs|cr)', nm)
        and b'Color/paper' in z2.read(nm))
z2.close()
if before != after: os.remove(tmp); sys.exit('DURDU: bag kaydi degisti')
if not ok: os.remove(tmp); sys.exit('DURDU: XML bozuldu')
shutil.move(tmp, DST)

print('%s -> %s' % (os.path.basename(SRC), os.path.basename(DST)))
print('  koyu zemin, kagit rengine cevrildi: %d' % len(dark))
for pn, sid, med in sorted(dark): print('     s.%-4d %-8s parlaklik %d' % (pn, sid, med))
print('  acik zemin, oldugu gibi: %d' % len(light))
print('  dosyada kagit renkli kunye: %d · bag kaydi %d' % (n, len(before)))
