# -*- coding: utf-8 -*-
"""
Bir IDML'i, baglarina dokunmadan duzenler.

InDesign'dan gelen bir belgede duzeltilecek sey yazi oldugunda gorsellerin
riske girmesi icin hicbir sebep yok. Bu betik yalniz Stories/ altindaki
parcalara dokunur; paketteki diger her giris bayt bayt oldugu gibi
kopyalanir, sirasi da korunur. Yani Spreads/ hic acilmaz, dolayisiyla
hicbir Link kaydi degismez: gorseller nerede duruyorsa orada kalir,
yeniden baglamak gerekmez.

Dosyanin kendisi zaten gorsel tasimaz — 129 sayfalik kitap 0.6 MB'tir,
icindeki gorsel sayisi sifirdir, her gorsel bir yol olarak durur. Bu
yuzden paketlemeye ve yuz megabaytlik Links klasorune gerek yoktur.

    python3 idml-edit.py girdi.idml cikti.idml            # yalniz denetler
    python3 idml-edit.py girdi.idml cikti.idml --caps     # kunyelerdeki
                                                          # yerel All Caps
                                                          # iptalini kaldirir

Her calismada bag guvenligi olculur: once ve sonra butun Link kayitlari
karsilastirilir, bir tanesi bile degismisse betik durur ve dosyayi yazmaz.
"""
import os, sys, re, zipfile, shutil
import xml.etree.ElementTree as ET

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
if len(ARGS) < 2:
    sys.exit(__doc__.strip().splitlines()[-6])
SRC, DST = ARGS[0], ARGS[1]
CAPS = '--caps' in sys.argv

def links_of(zf):
    """Paketteki butun bag kayitlari, karsilastirilabilir bicimde."""
    out = []
    for n in sorted(zf.namelist()):
        if not n.startswith('Spreads/'): continue
        for el in ET.fromstring(zf.read(n)).iter('Link'):
            out.append((n, el.get('LinkResourceURI'), el.get('LinkResourceFormat')))
    return out


zin = zipfile.ZipFile(SRC)
before = links_of(zin)

changed, touched = 0, 0
parts = []
for info in zin.infolist():
    data = zin.read(info.filename)
    if info.filename.startswith('Stories/'):
        touched += 1
        if CAPS:
            s = data.decode('utf-8')
            # Kunye kademesinde buyuk harf, yazilan metnin degil stilin
            # isidir: Capitalization="AllCaps". InDesign'da bir cerceve bu
            # ozelligi yerel olarak kaybedince metin yazildigi gibi cikar ve
            # kitabin yarisi bir turlu, yarisi obur turlu gorunur. Dogru
            # duzeltme metni buyuk harfe cevirmek degil — o geri donulmez ve
            # stil degisince iki kez buyur — yerel iptali kaldirmaktir.
            new = re.sub(r'\s+Capitalization="Normal"', '', s)
            if new != s:
                data = new.encode('utf-8'); changed += 1
    parts.append((info, data))

# mimetype ilk giris ve sikistirilmamis olmak zorunda; sira korunur.
tmp = DST + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for info, data in parts:
        if info.filename == 'mimetype':
            zi = zipfile.ZipInfo('mimetype')
            zi.compress_type = zipfile.ZIP_STORED
            zo.writestr(zi, data)
        else:
            zo.writestr(info.filename, data)

zout = zipfile.ZipFile(tmp)
after = links_of(zout)
same_names = zin.namelist() == zout.namelist()
zin.close(); zout.close()

if before != after:
    os.remove(tmp)
    d = [(a, b) for a, b in zip(before, after) if a != b]
    sys.exit('DURDU: %d bag kaydi degismis, dosya yazilmadi\n  %s'
             % (len(d), d[:2]))
if not same_names:
    os.remove(tmp)
    sys.exit('DURDU: paketin giris listesi degismis, dosya yazilmadi')

shutil.move(tmp, DST)
print('%s -> %s' % (os.path.basename(SRC), os.path.basename(DST)))
print('  hikaye parcasi %d · degistirilen %d' % (touched, changed))
print('  bag kaydi %d · hepsi birebir ayni' % len(before))
print('  paket girisleri ayni sirada ve ayni adlarla')
