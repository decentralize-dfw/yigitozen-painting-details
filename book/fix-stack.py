# -*- coding: utf-8 -*-
"""Sayfadaki yazi yiginini asagi dogru oturtur: hicbir sey hicbir seyin
ustune binmez.

Kitabin duzeni bir satirlik baslik varsayiyor. Basligi iki ya da uc satira
tasan yirmi kadar sayfada altindaki her sey yerinde kaldi: cizgi basligin
harflerinin icinden geciyor, kunye basligin son satirinin altina giriyor,
bir yerde de metnin ilk satiri basligin uzerine oturuyor.

Burada yigin asagi dogru oturtulur. Bir nesne yalniz gerektigi kadar iner;
onunden yeterince bosluk varsa hic kimildamaz. Acilan boslugun olcusu
uydurulmaz — kitabin duzgun dizilmis sayfalarindan olculur (bkz. gaptable).

Gorsellere dokunulmaz: yalniz yazi cercevesinin ve cizginin ItemTransform
oteleme degeri degisir, gorsel dikdortgenleri hic acilmaz.

    python3 fix-stack.py girdi.idml cikti.pdf cikti.idml [--rapor]
"""
import os, sys, re, zipfile, shutil
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stackmodel import read
from gaptable import xover

PT = 72 / 25.4
FOOT = 320.0 * PT - 22.0 * PT        # yazi alaninin alt siniri
MOVABLE = {'title', 'rule', 'label', 'body', 'num', 'quote', 'misc'}

# Kitabin kendi bosluklari; duzgun dizilmis sayfalardan olculdu.
GAP = {
    ('num', 'title'): 11.9, ('title', 'rule'): 16.7, ('title', 'label'): 9.1,
    ('title', 'body'): 20.0, ('rule', 'label'): 10.2, ('rule', 'body'): 20.0,
    ('label', 'body'): 26.5, ('label', 'label'): 9.3, ('label', 'rule'): 4.2,
    ('body', 'rule'): 16.7, ('body', 'body'): 7.2, ('body', 'label'): 12.0,
    ('rule', 'rule'): 8.0, ('label', 'num'): 12.0, ('title', 'title'): 4.0,
}
DEFAULT = 8.0


from fix_stack_lib import lineboxes, hits, settle, grow_changed


def main():
    if len(sys.argv) < 4:
        sys.exit('kullanim: fix-stack.py girdi.idml cikti.pdf cikti.idml [--rapor]')
    SRC, PDF, DST = sys.argv[1], sys.argv[2], sys.argv[3]
    import json
    dj = os.path.join(os.path.dirname(os.path.abspath(SRC)), 'degisen.json')
    ch = json.load(open(dj)) if os.path.exists(dj) else {}
    yj = os.path.join(os.path.dirname(os.path.abspath(SRC)), 'yeni.json')
    yeni = json.load(open(yj)) if os.path.exists(yj) else []
    pages, lines, miss = read(SRC, PDF, {k: v[0] for k, v in ch.items()}, yeni)

    # Yazisi degistirilen cerceveler ciktida hala eski yaziyla duruyor.
    # Yeni yazi daha uzunsa cerceve bir satir daha tutacaktir; oturtma
    # bunu bilmezse acilan boslugu bir satir eksik acar. Kac satir
    # tutacagi cercevenin kendi olcusuyle hesaplanir: eski yazinin kac
    # harfi kac satira sigdiysa yenisi de o hesapla sigar.
    grew = grow_changed(pages, ch)
    if grew:
        print('  yazisi uzayan cerceve: %d' % len(grew))
        for q, sid, a, b in grew:
            print('     s.%-4d %-9s %d satir -> %d satir' % (q, sid, a, b))

    shifts, warn = {}, []
    for q, P in sorted(pages.items()):
        new, moved = settle(P)
        if not moved: continue
        for k, i in enumerate(P['items']):
            d = new[k] - i['ren'][1]
            if d <= 0.05: continue
            nb = (i['ren'][0], new[k], i['ren'][2],
                  new[k] + (i['ren'][3] - i['ren'][1]))
            if nb[3] > FOOT:
                warn.append((q, i['self'], 'yazi alaninin altina tasiyor',
                             round(nb[3] - FOOT, 1)))
            for g in P['imgs']:
                was = (min(i['ren'][2], g[2]) - max(i['ren'][0], g[0]) > 0 and
                       min(i['ren'][3], g[3]) - max(i['ren'][1], g[1]) > 0)
                now = (min(nb[2], g[2]) - max(nb[0], g[0]) > 0 and
                       min(nb[3], g[3]) - max(nb[1], g[1]) > 0)
                if now and not was:
                    warn.append((q, i['self'], 'gorselin uzerine geliyor',
                                 round(d, 1)))
            shifts.setdefault(i['part'], {})[i['self']] = d

    n = sum(len(v) for v in shifts.values())
    print('%s' % os.path.basename(SRC))
    print('  asagi inen nesne: %d (%d yaprakta)' % (n, len(shifts)))
    for q, P in sorted(pages.items()):
        new, moved = settle(P)
        for k, i in enumerate(P['items']):
            if new[k] - i['ren'][1] > 0.05:
                print('     s.%-4d %-9s %-6s +%5.1f pt  %s'
                      % (q, i['self'], i['role'], new[k] - i['ren'][1],
                         (i['txt'] or '(cizgi)')[:40]))
    if warn:
        print('  UYARI: %d' % len(warn))
        for w in warn: print('     s.%-4d %-9s %s (%.1f)' % w)

    # ── oturttuktan sonra kalan cakisma var mi ──────────────────────
    left = []
    for q, P in sorted(pages.items()):
        new, _ = settle(P)
        for k, i in enumerate(P['items']):
            d = new[k] - i['ren'][1]
            i['ren'] = (i['ren'][0], i['ren'][1] + d, i['ren'][2], i['ren'][3] + d)
            for l in i['lines']: l['y1'] += d; l['y2'] += d
        for x in range(len(P['items'])):
            for y in range(x + 1, len(P['items'])):
                a, b = P['items'][x], P['items'][y]
                if hits(a, b):
                    left.append((q, a['role'], a['self'], (a['txt'] or '(cizgi)')[:34],
                                 b['role'], b['self'], (b['txt'] or '(cizgi)')[:34]))
    print('  oturduktan sonra ust uste binen: %d' % len(left))
    for c in left:
        print('     s.%-4d %-6s %-9s %s\n              %-6s %-9s %s'
              % (c[0], c[1], c[2], c[3], c[4], c[5], c[6]))
    if left: sys.exit('DURDU: cakisma cozulmedi')

    # Oturmus duzenin gercek dolu yerleri. Kunyeleri yerlestiren betik
    # bunu okur: belgede yazan cerceve olcusu buyumeden oncekidir, oysa
    # kunyenin kacinacagi sey ciktida basilan yazidir.
    import json
    occ = {str(q): [[round(v, 2) for v in bx]
                    for i in P['items'] for bx in lineboxes(i)]
           for q, P in sorted(pages.items())}
    with open(os.path.join(os.path.dirname(os.path.abspath(DST)),
                           'oturmus.json'), 'w') as fh:
        json.dump(occ, fh)
    print('  dolu yer dosyasi: oturmus.json (%d sayfa)' % len(occ))

    if '--rapor' in sys.argv: return

    Z = zipfile.ZipFile(SRC)

    def links_of(zf):
        out = []
        for k in sorted(zf.namelist()):
            if not k.startswith('Spreads/'): continue
            for el in ET.fromstring(zf.read(k)).iter('Link'):
                out.append((k, el.get('LinkResourceURI'),
                            el.get('LinkResourceFormat')))
        return out

    before = links_of(Z)

    def apply(raw, targets):
        out = raw
        for sid, d in targets.items():
            m = re.search(r'<(?:TextFrame|Rectangle)\b[^>]*Self="%s"[^>]*>'
                          % re.escape(sid), out)
            if not m:
                sys.exit('DURDU: %s bulunamadi' % sid)
            tag = m.group(0)
            t = re.search(r'ItemTransform="([-\d.eE ]+)"', tag)
            if not t:
                sys.exit('DURDU: %s ItemTransform yok' % sid)
            v = [float(x) for x in t.group(1).split()]
            v[5] += d
            nt = tag.replace(t.group(0), 'ItemTransform="%s"'
                             % ' '.join('%.6g' % x for x in v))
            out = out[:m.start()] + nt + out[m.end():]
        return out

    parts = []
    for info in Z.infolist():
        d = Z.read(info.filename)
        if info.filename in shifts:
            d = apply(d.decode('utf-8'), shifts[info.filename]).encode('utf-8')
        parts.append((info.filename, d))

    tmp = DST + '.tmp'
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
        for name, d in parts:
            if name == 'mimetype':
                zi = zipfile.ZipInfo('mimetype')
                zi.compress_type = zipfile.ZIP_STORED
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
    print('  -> %s · bag kaydi %d, hepsi birebir ayni'
          % (os.path.basename(DST), len(before)))


main()
