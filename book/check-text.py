# -*- coding: utf-8 -*-
"""Belgedeki her yaziyi okur ve yarim kalmis olani gosterir.

Bir cumle virgulle, baglacla ya da tire ile bitiyorsa orada bir sey
kesilmistir. Ayni sozun iki yerde durmasi da hatadir: kunye o sayfayi
anlatmalidir, komsusunu degil.

    python3 check-text.py belge.idml
"""
import os, sys, re, zipfile, collections
import xml.etree.ElementTree as ET

if len(sys.argv) < 2: sys.exit('kullanim: check-text.py belge.idml')
Z = zipfile.ZipFile(sys.argv[1])

CUT = re.compile(r'[,;:]$|\b(and|or|the|a|an|of|to|in|with|that|which|from|'
                 r'for|at|on|by|as|but|its|his|her|their|is|are|was|were)$'
                 r'|[—–-]$', re.I)
SKIP = {'f', 'f rt', 'm wn'}

rows, seen = [], collections.defaultdict(list)
for n in sorted(Z.namelist()):
    m = re.match(r'Stories/Story_(\w+)\.xml$', n)
    if not m: continue
    st = ET.fromstring(Z.read(n))
    t = re.sub(r'\s+', ' ', ''.join((c.text or '') for c in st.iter('Content'))).strip()
    sty = next((q.get('AppliedParagraphStyle', '').split('/')[-1]
                for q in st.iter('ParagraphStyleRange')), '')
    if not t or sty in SKIP: continue
    rows.append((m.group(1), sty, t))
    if len(t) > 24: seen[t.lower()].append(m.group(1))

cut = [r for r in rows if CUT.search(r[2]) and len(r[2]) > 24]
dup = {k: v for k, v in seen.items() if len(v) > 1}

print('yazi %d' % len(rows))
print('YARIM KALMIS: %d' % len(cut))
for sid, sty, t in cut:
    print('  %-9s %-7s %s' % (sid, sty, t[:150]))
print('IKI YERDE AYNI SOZ: %d' % len(dup))
for k, v in dup.items():
    print('  %s  %s' % (', '.join(v), k[:110]))
sys.exit(1 if (cut or dup) else 0)
