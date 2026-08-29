# -*- coding: utf-8 -*-
"""
Folyolari otomatik sayfa numarasina cevirir.

Kitabin folyolari duz yaziydi: sayfaya hangi sayi yazildiysa o kaliyordu.
Duzenlerken araya sayfa girince hepsi bayatladi — yuz yirmi dokuz folyonun
yuz on dokuzu yanlis sayiyi basiyor, bazilari da ayni sayiyi iki kez.

Duz sayi yerine InDesign'in kendi sayfa numarasi imi konur: IDML'de
<?ACE 18?>. Bundan sonra sayfa eklense de cikarilsa da folyo dogruyu
gosterir; bir daha elle duzeltmek gerekmez.

    python3 fix-folios.py girdi.idml cikti.idml

Spreads/ acilmaz, Link kayitlari once-sonra karsilastirilir.
"""
import os, sys, re, zipfile, shutil
import xml.etree.ElementTree as ET

if len(sys.argv) < 3:
    sys.exit('kullanim: fix-folios.py girdi.idml cikti.idml')
SRC, DST = sys.argv[1], sys.argv[2]

Z = zipfile.ZipFile(SRC)
ACE = '<?ACE 18?>'          # gecerli sayfa numarasi


def links_of(zf):
    out = []
    for n in sorted(zf.namelist()):
        if not n.startswith('Spreads/'): continue
        for el in ET.fromstring(zf.read(n)).iter('Link'):
            out.append((n, el.get('LinkResourceURI'), el.get('LinkResourceFormat')))
    return out


before = links_of(Z)
done = skipped = 0
parts = []
for info in Z.infolist():
    data = Z.read(info.filename)
    if info.filename.startswith('Stories/'):
        s = data.decode('utf-8')
        # Yalniz folyo stilini tasiyan hikayeler
        if re.search(r'AppliedParagraphStyle="ParagraphStyle/f(?: rt)?"', s):
            if ACE in s:
                skipped += 1
            else:
                # Sayfa numarasi, hikayedeki ILK salt sayidan ibaret Content'tir.
                # Yanindaki yil ve yer adina dokunulmaz.
                new, cnt = re.subn(r'(<Content>)\s*\d{1,3}\s*(</Content>)',
                                   lambda m: m.group(1) + ACE + m.group(2),
                                   s, count=1)
                if cnt:
                    data = new.encode('utf-8'); done += 1
                else:
                    skipped += 1
    parts.append((info, data))

tmp = DST + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for info, d in parts:
        if info.filename == 'mimetype':
            zi = zipfile.ZipInfo('mimetype'); zi.compress_type = zipfile.ZIP_STORED
            zo.writestr(zi, d)
        else:
            zo.writestr(info.filename, d)

z2 = zipfile.ZipFile(tmp)
after = links_of(z2)
same = Z.namelist() == z2.namelist()
ok = True
for n in z2.namelist():
    if n.endswith('.xml'):
        try: ET.fromstring(z2.read(n))
        except Exception as e: ok = False; print('AYRISMADI', n, e)
z2.close()
if before != after: os.remove(tmp); sys.exit('DURDU: bag kaydi degismis')
if not same: os.remove(tmp); sys.exit('DURDU: paket girisleri degismis')
if not ok: os.remove(tmp); sys.exit('DURDU: XML bozuldu')
shutil.move(tmp, DST)

print('%s -> %s' % (os.path.basename(SRC), os.path.basename(DST)))
print('  folyo otomatige cevrildi: %d · dokunulmayan: %d' % (done, skipped))
print('  bag kaydi %d · hepsi birebir ayni' % len(before))
