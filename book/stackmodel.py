# -*- coding: utf-8 -*-
"""Sayfadaki yazi yiginini okur: her cerceve, her cizgi, her gorsel.

Cercevede yazan yukseklik gercek degil — belgedeki 748 cercevenin hepsi
AutoSizing ile buyur, yani IDML'de duran olcu buyumeden oncekidir. Bu
yuzden her cercevenin gercek yeri ciktidan alinir.

Satirlari cerceveye dagitirken konuma bakilmaz — cerceveler ust uste
bindigi icin konum yaniltir. Cercevenin kendi oykusundeki yazi ne ise
ciktida o yazinin durdugu satirlar onundur. Belgede hecelemek kapali,
bu yuzden esleme birebir.
"""
import zipfile, collections, re
import xml.etree.ElementTree as ET
import pymupdf
from place import transform
from ink import band

PT = 72 / 25.4
ASC, DESC = 0.78, 0.27      # gorunen harfin yazi cizgisine gore siniri
SIZE = {'f': 8.2, 'f rt': 8.2, 'm wn': 10.4, 't': 10.8, 'sans': 9.6,
        'd': 26.0, 'd s': 19.0, 'd l': 44.0, 'd xl': 64.0, 'd yr': 108.0}
ROLE = {'d': 'title', 'm wn': 'num', 't': 'body', 'sans': 'body'}


def role_of(style):
    if style in ROLE: return ROLE[style]
    if style.startswith('d'): return 'title'
    if style.startswith('f'): return 'folio'
    if style.startswith('pq') or style == 'q': return 'quote'
    if style.startswith('m'): return 'label'
    return 'misc'


def norm(s):
    return re.sub(r'[\s­-]+', '', s or '').lower()


def read(idml, pdf, changed=None, synthetic=None):
    """changed: {oyku -> eski yazi}. Yazisi sonradan degistirilen
    cerceveler ciktida hala eski yaziyla duruyor; eslesme eski yaziyla
    kurulur, yoksa o cerceveler yerlerini kaybeder.

    synthetic: ciktida hic bulunmayan ya da baska bir sayfaya tasinmis
    oykuler. Bunlar yaziyla eslenmez — eski yerlerindeki satirlari
    kapardi — kutulari belgeden alinir, boylari yazinin genisligine gore
    hesaplanir."""
    changed = changed or {}
    synthetic = set(synthetic or ())
    Z, D = zipfile.ZipFile(idml), pymupdf.open(pdf)
    names = set(Z.namelist())

    def story(sid):
        p = 'Stories/Story_%s.xml' % sid
        if p not in names: return '', ''
        st = ET.fromstring(Z.read(p))
        txt = ''.join((c.text or '') for c in st.iter('Content'))
        sty = next((q.get('AppliedParagraphStyle', '').split('/')[-1]
                    for q in st.iter('ParagraphStyleRange')), '')
        return txt, sty

    lines = collections.defaultdict(list)
    for i, pg in enumerate(D):
        for b in pg.get_text('dict')['blocks']:
            for l in b.get('lines', []):
                bb = [s['bbox'] for s in l['spans']]
                t = ''.join(s['text'] for s in l['spans'])
                if not t.strip(): continue
                # Fontun satir kutusu harften genistir: Inter'in kutusu
                # punto x 1,44, gorunen harf ise punto x 1,05 kadardir.
                # Cakismayi harfin kendisiyle olcmek gerekir, kutusuyla
                # degil; bu yuzden kutu yazi cizgisinden yeniden kurulur.
                up, dn = band(t, l['spans'][0]['size'])
                base = l['spans'][0]['origin'][1]
                lines[i + 1].append({
                    'x1': min(q[0] for q in bb), 'y1': base - up,
                    'x2': max(q[2] for q in bb), 'y2': base + dn,
                    'sz': round(l['spans'][0]['size'], 1), 't': t.strip(),
                    'span': l['spans'][0], 'used': False})
    for q in lines: lines[q].sort(key=lambda l: (round(l['y1'], 1), l['x1']))

    pages = {}
    for n in sorted(names):
        if not n.startswith('Spreads/'): continue
        sp = ET.fromstring(Z.read(n)).find('.//Spread')
        if sp is None: continue
        pg = {}
        for p in sp.findall('Page'):
            g = [float(v) for v in p.get('GeometricBounds').split()]
            it = [float(v) for v in (p.get('ItemTransform') or '1 0 0 1 0 0').split()]
            if p.get('Name', '').isdigit():
                pg[int(p.get('Name'))] = (g[1] + it[4], g[0] + it[5],
                                          g[3] + it[4], g[2] + it[5])
        for q in pg:
            pages.setdefault(q, {'items': [], 'imgs': [], 'part': n,
                                 'org': (pg[q][0], pg[q][1]), 'box': pg[q]})

        def onpage(b):
            c = (b[0] + b[2]) / 2.0
            for q, (a1, b1, a2, b2) in pg.items():
                if a1 - 1 <= c <= a2 + 1: return q
            return None

        for r in sp.iter('Rectangle'):
            b = transform(r)
            if not b: continue
            q = onpage(b)
            if q is None: continue
            ox, oy = pg[q][0], pg[q][1]
            loc = (b[0] - ox, b[1] - oy, b[2] - ox, b[3] - oy)
            if r.find('Image') is not None:
                pages[q]['imgs'].append(loc)
            elif (b[3] - b[1]) <= 3.0:
                pages[q]['items'].append(
                    {'kind': 'rule', 'self': r.get('Self'), 'part': n,
                     'box': loc, 'role': 'rule', 'txt': '', 'lines': [],
                     'ren': loc})

        for f in sp.iter('TextFrame'):
            b = transform(f)
            if not b: continue
            q = onpage(b)
            if q is None: continue
            ox, oy = pg[q][0], pg[q][1]
            txt, sty = story(f.get('ParentStory'))
            pages[q]['items'].append(
                {'kind': 'text', 'self': f.get('Self'), 'part': n,
                 'story': f.get('ParentStory'), 'style': sty,
                 'role': role_of(sty),
                 'txt': re.sub(r'\s+', ' ', txt).strip(),
                 'match': re.sub(r'\s+', ' ',
                                 changed.get(f.get('ParentStory'), txt)).strip(),
                 'box': (b[0] - ox, b[1] - oy, b[2] - ox, b[3] - oy),
                 'lines': [], 'ren': None})

    # ── ciktidaki satirlari oykusune gore cerceveye ver ─────────────
    # Satirlar y sirasindadir ama bir cercevenin satirlari arada baska
    # bir cercevenin satiriyla bolunebilir: uzun bir baslik asagi tasip
    # kunyenin satirini arasina alir. Bu yuzden esleme bitisik satir
    # aramaz, uymayan satiri atlar.
    miss = []
    for q, P in pages.items():
        L = lines.get(q, [])
        tf = sorted([i for i in P['items'] if i['kind'] == 'text'],
                    key=lambda i: i['box'][1])

        def inside(l, it):
            return (l['x1'] >= it['box'][0] - 2.5 and l['x2'] <= it['box'][2] + 2.5)

        # Kisa sayilar once yerine gore eslenir. Icindekiler sayfasindaki
        # sayfa numaralarini bu tur duzeltti; ciktida hala eski sayilar
        # duruyor, dolayisiyla yaziya bakarak eslemek onlari birbirine
        # karistirir. Yerleri ise degismedi.
        for it in tf:
            if it.get('story') in synthetic: continue
            t = it['match']
            if not t or len(t) > 6 or ' ' in t: continue
            c = [l for l in L if not l['used'] and inside(l, it)
                 and l['y1'] >= it['box'][1] - 3.5
                 and l['y1'] <= it['box'][1] + max(it['box'][3] - it['box'][1], 16)]
            if len(c) >= 1:
                a = min(c, key=lambda l: l['y1'])
                a['used'] = True; it['lines'] = [a]

        for it in tf:
            if it['lines'] or it.get('story') in synthetic: continue
            want = norm(it['match'])
            if not want: continue
            runs = []
            for s0 in range(len(L)):
                if L[s0]['used']: continue
                acc, run = '', []
                for k in range(s0, len(L)):
                    if L[k]['used']: continue
                    nk = norm(L[k]['t'])
                    if not nk: continue
                    if want.startswith(acc + nk):
                        acc += nk; run.append(L[k])
                        if acc == want: break
                    elif run and not want.startswith(acc):
                        break
                if acc == want: runs.append(run)
            if runs:
                fx1, fx2, fy = it['box'][0], it['box'][2], it['box'][1]
                run = min(runs, key=lambda r: abs(min(l['x1'] for l in r) - fx1)
                                            + abs(max(l['x2'] for l in r) - fx2)
                                            + abs(min(l['y1'] for l in r) - fy))
                for l in run: l['used'] = True
                it['lines'] = run
            else:
                miss.append((q, it['self'], it['style'], it['match'][:44]))

        # Son care: bir cercevenin yazisi ciktida kendi satirini kurmuyor
        # olabilir — folyo numarasi ile yer adi tek satira diziliyor, ve
        # numara belgede otomatik alan olarak duruyor, dolayisiyla oykude
        # yazi yok. Bunlar icin satir yeriyle bulunur ve paylasilir; olcu
        # icin yeterlidir, ama yerlesim denetimine sokulmaz.
        for it in tf:
            if it['lines'] or it.get('story') in synthetic: continue
            b = it['box']
            near = [l for l in L
                    if l['x2'] > b[0] - 3 and l['x1'] < b[2] + 3
                    and l['y2'] > b[1] - 3
                    and l['y1'] < b[1] + max(b[3] - b[1], 16) + 3]
            if near:
                it['lines'] = near
                it['approx'] = True
        for it in P['items']:
            if it['kind'] != 'text': continue
            if it['lines']:
                it['ren'] = (min(l['x1'] for l in it['lines']),
                             min(l['y1'] for l in it['lines']),
                             max(l['x2'] for l in it['lines']),
                             max(l['y2'] for l in it['lines']))
            else:
                # Eslesmedi: ciktida kendi satiri yok (folyo yaniyla ayni
                # satira dizilenler), yeni eklenmis ya da baska sayfaya
                # tasinmis. Belgedeki kutu konum icin dogrudur, boyu kisa.
                from place import caption_height
                b = it['box']
                pt = SIZE.get(it['style'], 7.6)
                h = (caption_height(it['txt'], b[2] - b[0], pt, pt * 1.46)
                     if (it['self'].startswith('tf')
                         or it.get('story') in synthetic)
                     else (b[3] - b[1]) + 4.0)
                it['ren'] = (b[0], b[1], b[2], b[1] + max(h, b[3] - b[1]))
                it['guess'] = True
                it['fresh'] = it.get('story') in synthetic
        P['items'] = [i for i in P['items'] if i['ren']]
        P['items'].sort(key=lambda i: (round(i['ren'][1], 1), i['ren'][0]))
    return pages, lines, miss
