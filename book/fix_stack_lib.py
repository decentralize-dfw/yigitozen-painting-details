# -*- coding: utf-8 -*-
"""fix-stack.py icindeki yerlestirme kurallari, ayri okunabilsin diye.
Tek kaynak: bu dosya fix-stack.py tarafindan da kullanilir."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gaptable import xover

PT = 72 / 25.4
FOOT = 320.0 * PT - 22.0 * PT
MOVABLE = {'title', 'rule', 'label', 'body', 'num', 'quote', 'misc'}

GAP = {
    ('num', 'title'): 11.9, ('title', 'rule'): 16.7, ('title', 'label'): 9.1,
    ('title', 'body'): 20.0, ('rule', 'label'): 10.2, ('rule', 'body'): 20.0,
    ('label', 'body'): 26.5, ('label', 'label'): 9.3, ('label', 'rule'): 4.2,
    ('body', 'rule'): 16.7, ('body', 'body'): 7.2, ('body', 'label'): 12.0,
    ('rule', 'rule'): 8.0, ('label', 'num'): 12.0, ('title', 'title'): 4.0,
}
DEFAULT = 8.0


def lineboxes(it):
    """Nesnenin kutulari: yazi cercevesi icin satir satir."""
    if it['kind'] == 'rule' or not it['lines']:
        return [it['ren']]
    return [(l['x1'], l['y1'], l['x2'], l['y2']) for l in it['lines']]


def hits(a, b):
    """Iki nesnenin harfleri birbirine biniyor mu.

    Cizgide olcu satir satir alinmaz: uc satirlik bir basligin iki satiri
    arasindan gecen cizgi hicbir harfe degmiyor olabilir, ama basligin
    icinden geciyordur. Cizgi karsisindaki cerceveyi butun sayar.
    """
    A = [a['ren']] if b['role'] == 'rule' else lineboxes(a)
    B = [b['ren']] if a['role'] == 'rule' else lineboxes(b)
    for p in A:
        for q in B:
            ox = min(p[2], q[2]) - max(p[0], q[0])
            oy = min(p[3], q[3]) - max(p[1], q[1])
            tx = min(0.4, 0.6 * min(p[2] - p[0], q[2] - q[0]))
            ty = min(0.4, 0.6 * min(p[3] - p[1], q[3] - q[1]))
            if ox > tx and oy > ty: return True
    return False


def settle(P):
    """Nesnelerin yeni ust kenarlari. Yalniz asagi iner, yalniz gerektigi
    kadar.

    Kural iki tanedir. Bir: ust uste binen bir cift varsa alttaki, kitabin
    o iki rol icin kendi boslugu kadar asagi iner. Iki: ustundeki bir sey
    indiyse altindaki de iner, ama aralarindaki eski boslugu koruyacak
    kadar — yani duzen sikismaz ve acilmaz, oldugu gibi asagi kayar.

    Cakisma yoksa sayfada hicbir sey kimildamaz.
    """
    it = P['items']
    new = [i['ren'][1] for i in it]
    moved = {}
    for j in range(len(it)):
        b = it[j]
        if b['role'] not in MOVABLE or b.get('pin') or b.get('approx'): continue
        need = new[j]
        for i in range(j):
            a = it[i]
            abot = new[i] + (a['ren'][3] - a['ren'][1])
            # Cakisma her zaman cozulur, iki nesne yanyana bile olsa: bir
            # cizginin sol ucu yan sutunun son sozcugunu kesiyorsa bu da
            # cakismadir. Ust uste inme ise ancak ayni sutunda tasinir.
            if hits(a, b):
                need = max(need, abot + GAP.get((a['role'], b['role']), DEFAULT))
            elif not xover(a['ren'], b['ren']):
                continue
            elif new[i] > it[i]['ren'][1] + 0.05:
                # Ustundeki indi. Aralarindaki eski boslugu sikistirmadan,
                # ama bos yeri de bosuna asagi surumeden: gerekli olan,
                # ikisinden kucugu. Boylece altta zaten bos duran bir
                # kunye yerinde kalir, sikisik duran bir tanesi iner.
                was = b['ren'][1] - a['ren'][3]
                if was >= -0.05:
                    keep = min(was, GAP.get((a['role'], b['role']), DEFAULT))
                    need = max(need, abot + keep)
        if need > new[j] + 0.05:
            moved[b['self']] = need - new[j]
        new[j] = need
    return new, moved




def grow_changed(pages, ch):
    """Yazisi degistirilen cerceveleri yeni yazinin tutacagi boya getirir.

    Cikti hala eski yaziyla basildi; yeni yazi daha uzunsa cerceve bir
    satir daha tutacaktir. Kac satir tutacagi cercevenin kendi olcusuyle
    bulunur: eski yazinin kac harfi kac satira sigdiysa yenisi de o
    hesapla siger. Yalniz uzatir, hicbir cerceveyi kisaltmaz.
    """
    grew = []
    for q, P in pages.items():
        for it in P['items']:
            if it.get('story') not in ch: continue
            old, new = ch[it['story']]
            nl = len(it['lines'])
            if not nl or len(new) <= len(old): continue
            pitch = ((it['ren'][3] - it['ren'][1]) / nl if nl > 1
                     else it['lines'][0]['span']['size'] * 1.46)
            # Satir sayisi cercevenin gercek genisligiyle hesaplanir.
            # Basilan satirin genisligi cercevenin genisligi degildir —
            # son satir yarim kalir — ama harf basina genislik oradan
            # dogru cikar.
            wide = sum(l['x2'] - l['x1'] for l in it['lines'])
            per = wide / max(1, len(old))
            box = max(60.0, it['box'][2] - it['box'][0])
            want = max(nl, -(-int(len(new) * per) // int(box)))
            if want <= nl: continue
            add = (want - nl) * pitch
            base = it['ren'][3]
            it['ren'] = (it['ren'][0], it['ren'][1], it['ren'][2], base + add)
            it['lines'] = it['lines'] + [
                {'x1': it['ren'][0], 'x2': it['ren'][2],
                 'y1': base + k * pitch, 'y2': base + (k + 1) * pitch - 1.0,
                 't': '', 'sz': 0, 'span': it['lines'][0]['span']}
                for k in range(want - nl)]
            grew.append((q, it['self'], nl, want))
    return grew
