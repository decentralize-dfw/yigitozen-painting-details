#!/usr/bin/env python3
"""PDF'e kunye ve yer imi ekler. print.js'ten sonra calisir.

Chromium'un bastigi PDF'te ne metadata ne de outline var; 96 sayfada otuz
bes ise atlayabilmek icin ikisi de gerekli.

    node print.js && python3 post.py
"""
import json, os
from pypdf import PdfReader, PdfWriter

import sys
HERE  = os.path.dirname(os.path.abspath(__file__))
SHORT = '--short' in sys.argv
PDF   = os.path.join(HERE, 'Yigit-Ozen-Paintings-Short.pdf' if SHORT
                     else 'Yigit-Ozen-Paintings-since-2019.pdf')
o     = json.load(open(os.path.join(HERE, 'outline-short.json' if SHORT else 'outline.json'),
                       encoding='utf-8'))

r = PdfReader(PDF)
w = PdfWriter()
for p in r.pages: w.add_page(p)

w.add_metadata({
    '/Title':    ('Yiğit Özen — Paintings since 2019, short' if SHORT
                  else 'Yiğit Özen — Paintings since 2019'),
    '/Author':   'Yiğit Özen',
    '/Subject':  ('Eight of thirty-five works made since 2019 across Istanbul, Milan and '
                  'Luxembourg' if SHORT else
                  'Thirty-five works made since 2019 across Istanbul, Milan and Luxembourg'),
    '/Keywords': ('Yiğit Özen, painting, acrylic on canvas, contemporary painting, '
                  'figurative painting, Istanbul, Milan, Luxembourg, artbook, catalogue'),
    '/Creator':  'yigitozen.xyz',
})

for name, page in o['marks']:
    if 1 <= page <= len(r.pages):
        w.add_outline_item(name, page - 1)

with open(PDF, 'wb') as f: w.write(f)
print('metadata and %d bookmarks written' % len(o['marks']))
