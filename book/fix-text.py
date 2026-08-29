# -*- coding: utf-8 -*-
"""Yarim kalmis ve iki yerde tekrarlanan yazilari duzeltir.

Uc kunye ilk virgulde kesilmis: kitabin renk notundan alinirken cumlenin
yarisi birakilmis. Iki kunye iki ayri sayfada ayni sozu soyluyor, oysa
her biri kendi sayfasindaki kesiti anlatmali. Bir sayfada da kafes notu
duruyor, ama o sayfada kafes yok — kafes iki serim ilerideki sayfada.

    python3 fix-text.py girdi.idml cikti.idml
"""
import os, sys, re, zipfile, shutil
import xml.etree.ElementTree as ET

if len(sys.argv) < 3:
    sys.exit('kullanim: fix-text.py girdi.idml cikti.idml')
SRC, DST = sys.argv[1], sys.argv[2]

# oyku -> (beklenen eski yazi, yeni yazi)
FIX = {
    # s.12 · ilk virgulde kesilmisti; kitabin renk notu boyle devam ediyor
    'u154a': ("01 · 7 fam board game · Opposite · The right player's head "
              "— Warm and cool level at about a third each,",
              "01 · 7 fam board game · Opposite · The right player's head "
              "— Warm and cool level at about a third each, cyan the "
              "largest family"),
    # s.50 · hem kesilmis hem s.52 ile ayni; karsi sayfa yuvarlak alanlar
    'u1fb3': ("06 · s(t)lop · Opposite · The eye, and the red notches "
              "— Less than one per cent below mid value,",
              "06 · s(t)lop · Opposite · The rounded fields, lilac over "
              "turquoise — Less than one per cent below mid value, "
              "mustard gold rather than the pastels"),
    # s.52 · karsi sayfa turuncu zemin ve pembe kama
    'u5320': ("06 · s(t)lop · Opposite · The eye, and the red notches "
              "— Less than one per cent below mid value,",
              "06 · s(t)lop · Opposite · The orange ground, and the pink "
              "blade laid across it — Less than one per cent below mid "
              "value, mustard gold rather than the pastels"),
    # s.50 · s.52'deki dikey kesitin sozu buraya da konmustu; bu sayfadaki
    # kesit yatay bir bant, altinda bir sira centik var
    'u1f9d': ("The right edge, from the barred frame down to the panel",
              "The horizontal band, and the row of notches standing under it"),
    # s.22 · kafes notu; kafes bu sayfada degil, 26'da. Bu sayfa iki bas.
    'u5383': ("A cage drawn from above, its walls never arriving; a chair "
              "outlined where no one will sit.",
              "A head under a yellow wig, and opposite it a second, greener "
              "face; neither is given a contour that closes."),
    # s.09 · icindekiler girisi de ayni kesik sozu tasiyordu
    'u1531': ("01 · 7 fam board game · Opposite · The right player's head "
              "— Warm and cool level at about a third each,",
              "01 · 7 fam board game · Opposite · The right player's head "
              "— Warm and cool level at about a third each, cyan the "
              "largest family"),
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


before = links_of(Z)
done, missing = [], []
parts = []
for info in Z.infolist():
    d = Z.read(info.filename)
    m = re.match(r'Stories/Story_(\w+)\.xml$', info.filename)
    if m and m.group(1) in FIX:
        old, new = FIX[m.group(1)]
        s = d.decode('utf-8')
        cur = re.sub(r'\s+', ' ', ''.join(
            (c.text or '') for c in ET.fromstring(d).iter('Content'))).strip()
        if cur != old:
            missing.append((m.group(1), cur[:70])); parts.append((info.filename, d)); continue
        # Yazi birden cok Content'e bolunmus olabilir: ilkine yeni yaziyi
        # koy, kalanlari bosalt ki eski parcalar geride kalmasin.
        n = [0]
        def one(mm):
            n[0] += 1
            return '<Content>%s</Content>' % (esc(new) if n[0] == 1 else '')
        s = re.sub(r'<Content>[\s\S]*?</Content>', one, s)
        d = s.encode('utf-8')
        done.append((m.group(1), new[:70]))
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
after = links_of(z2); z2.close()
if before != after: os.remove(tmp); sys.exit('DURDU: bag kaydi degisti')
if not ok: os.remove(tmp); sys.exit('DURDU: XML bozuldu')
shutil.move(tmp, DST)

import json
with open(os.path.join(os.path.dirname(os.path.abspath(DST)),
                       'degisen.json'), 'w') as fh:
    json.dump({sid: FIX[sid] for sid, _ in done}, fh)

print('%s -> %s' % (os.path.basename(SRC), os.path.basename(DST)))
print('  duzeltilen yazi: %d' % len(done))
for sid, t in done: print('     %-9s %s' % (sid, t))
if missing:
    print('  BEKLENEN YAZI BULUNAMADI: %d' % len(missing))
    for sid, t in missing: print('     %-9s simdi: %r' % (sid, t))
