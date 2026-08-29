# -*- coding: utf-8 -*-
"""
Yazi yerlestirmenin ortak kurallari.

Bir kunyeyi gorselin dort milimetre altina koymak yetmiyor: orada baska
bir sey duruyor olabilir. Folyo, kosan etiket, baska bir kunye. Onlarin
uzerine oturunca iki yazi da okunmaz olur.

Buradaki yerlestirici once sayfada dolu olan her yeri toplar — gorseller
degil, yazilar — sonra kunyeyi gorselinin yaninda bos bir yere koyar.
Bos yer yoksa yukari dogru arar; hicbir yerde yer yoksa geri doner ve
cagiran betik o kunyeyi atlar. Yanlis yere konmus bir kunye, hic
konmamis kunyeden kotudur.

Yukseklik de tahmin edilmez: yazinin kac satir tutacagi kendi genisligi
ve puntosuyla hesaplanir, sonra bir satir pay birakilir.
"""

PT = 72 / 25.4
PW, PH = 240.0 * PT, 320.0 * PT
GAP = 4.0 * PT
OUTER = 16.0 * PT
HEAD, FOOT = 18.0 * PT, 22.0 * PT   # kitabin ust ve alt kenar payi
PAD = 2.0 * PT          # iki yazi arasinda birakilan en az bosluk


def transform(el, parent=(1, 0, 0, 1, 0, 0)):
    """Nesnenin yapraktaki kutusu, ItemTransform uygulanmis."""
    a, b, c, d, e, f = [float(v) for v in (el.get('ItemTransform') or
                                           '1 0 0 1 0 0').split()]
    pa, pb, pc, pd, pe, pf = parent
    m = (a * pa + b * pc, a * pb + b * pd,
         c * pa + d * pc, c * pb + d * pd,
         e * pa + f * pc + pe, e * pb + f * pd + pf)
    xs, ys = [], []
    for q in el.iter('PathPointType'):
        px, py = [float(v) for v in q.get('Anchor').split()]
        xs.append(m[0] * px + m[2] * py + m[4])
        ys.append(m[1] * px + m[3] * py + m[5])
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def caption_height(text, width_pt, size=7.6, leading=11.1):
    """Kunyenin gercekte kac punto tutacagi.

    Genislige kac harf sigdigi puntodan cikarilir; kunye buyuk harfle
    dizildigi icin ortalama harf genisligi normalden genistir.
    """
    per = size * 0.62                      # buyuk harf, genis aralikli
    cpl = max(8, int(width_pt / per))
    lines = max(1, -(-len(text) // cpl))
    return lines * leading + 2.0


def occupied(spread_el, transform_fn):
    """Yapraktaki butun yazi cerceveleri: dolu sayilan yerler."""
    out = []
    for f in spread_el.iter('TextFrame'):
        b = transform_fn(f)
        if b: out.append(b)
    return out


def clashes(box, taken):
    x1, y1, x2, y2 = box
    for a1, b1, a2, b2 in taken:
        if x1 < a2 + PAD and a1 < x2 + PAD and y1 < b2 + PAD and b1 < y2 + PAD:
            return True
    return False


def place(img, page, taken, text, want_w=None):
    """Gorselin yanina cakismayan bir kutu bulur.

    img  : (x1, y1, x2, y2) gorselin yapraktaki kutusu
    page : (left, top, right, bottom) sayfanin yapraktaki siniri
    taken: dolu kutular
    Doner: (x1, y1, x2, y2) ya da yer yoksa None.
    """
    px1, pty, px2, pby = page
    ix1, iy1, ix2, iy2 = img
    gx1 = max(ix1, px1)
    gx2 = min(ix2, px2)
    w = want_w or max(min(gx2 - gx1, px2 - px1 - 2 * OUTER), 120)
    h = caption_height(text, w)
    # Gorselin uzerine konan kunye iceriden baslar; genisligi de o kadar
    # daralmalidir, yoksa kutu gorselin sag kenarindan tasar ve yazi
    # kagida dokulur.
    wi = max(min(w - 2 * OUTER, gx2 - OUTER - (gx1 + OUTER)), 110)
    hi = caption_height(text, wi)

    cand = [
        (gx1, iy2 + GAP, w, h),                          # gorselin alti
        (gx1 + OUTER, min(iy2, pby) - OUTER - hi, wi, hi),  # gorselin ayagi
        (gx1, iy1 - GAP - h, w, h),                      # gorselin ustu
        (gx1 + OUTER, max(iy1, pty) + OUTER, wi, hi),    # ust ic kose
    ]
    step = 6.0
    y = min(iy2, pby) - OUTER - hi
    while y > max(iy1, pty) + OUTER:
        cand.append((gx1 + OUTER, y, wi, hi)); y -= step
    narrow = min(wi, (px2 - px1) * 0.55)
    hn = caption_height(text, narrow)
    y = min(iy2, pby) - OUTER - hn
    while y > max(iy1, pty) + OUTER:
        cand.append((gx1 + OUTER, y, narrow, hn)); y -= step

    # Kunye once kitabin yazi alaninin icinde aranir: ustte on sekiz,
    # altta yirmi iki milimetre pay. Kesim payi baskida degisir, kenara
    # yakin duran bir kunye kirpilir. Hicbir yere sigmazsa sinir sayfanin
    # kendisine gevsetilir; hic yazilmamis kunye daha kotudur.
    for lo, hi in ((pty + HEAD, pby - FOOT), (pty, pby)):
        for cx, cy, cw, ch in cand:
            box = (cx, cy, cx + cw, cy + ch)
            if box[0] < px1 or box[2] > px2: continue
            if box[1] < lo or box[3] > hi: continue
            if clashes(box, taken): continue
            return box
    return None
