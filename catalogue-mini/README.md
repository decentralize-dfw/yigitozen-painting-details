# Mini Catalogue

One hundred and fifty-one works at four to a page: the 36 of the catalogued
sequence and the 115 that had never been catalogued. The newest, *sept neuf*,
leads at Cat. 001; the printed `../catalogue/` still holds the earlier 35
until it is set again.

`list-mobile-2.html` in `decentralize-dfw/decentralize` records 577 works;
147 carry `type: "painting"`. 32 of those are already the main catalogue's,
so 115 were new. The catalogued works are read back out of
`../catalogue/catalogue.html`, with their plates.

`catalogue-mini.html` is the source. `Yigit-Ozen-Paintings-Mini-Catalogue.pdf`
is printed from it.

## The order of the book

Cover, imprint, the index, then three pages of text — a biography, On the
work, and the curriculum — and then the plates. Odd page numbers fall on
the right and even ones on the left, so two rules hold: the plates open on
a left page rather than beside the last page of the text, and the book does
not end on a plate. A page is left blank wherever the count does not come
out, and the last page carries the bird alone, low on the left.

## The order

Not by year. By what the work is made on, and within that by whether it has
been catalogued before:

| | | |
|---|---|---|
| **Canvas** | Cat. 001–033 | 27 catalogued, then 6 |
| **Paper**  | Cat. 034–142 | 9 catalogued, then 100 — paper, carton, print, whiteboard |
| **Object** | Cat. 143–151 | 9 — assemblages, and work made on packaging taken apart |

Each group runs newest first. The running foot names the group, so a page
that straddles two says so.

## The page

- A4 portrait, four works to a page, in four bands.
- The plate falls to one side and then the other down the page — right, left,
  right, left — and the page facing it keeps the same beat rather than
  answering it. The caption always sits opposite its plate, and the plate
  hangs on the outer margin.
- No rule is drawn around a plate: most of the archive files are PNGs with a
  transparent ground, and a hairline there reads as the edge of the work.
- Dimensions are omitted where the record has none, Location likewise; the
  115 carry no location.

## Rebuilding

```
python3 build.py          # works.json -> catalogue-mini.html
node print-pdf.js         # catalogue-mini.html -> PDF
```

`works.json` is the merged record — number, title, year, medium, dimensions,
location, support and plate file. For the 115 it is parsed out of the single
sentence each work carries in `list-mobile-2.html`
(`"acrylic on 120x120 canvas, 2023"`); for the 35 it comes from the main
catalogue.

114 of the 115 archive files carry an alpha channel. Converting one straight
to RGB drops that alpha onto **black**, which is why several plates first
printed with a black ground or a black edge; the fetch composites onto white
instead, which is what the page is.

`trim.py` then cuts the empty ground from around a plate — the archive
photographs are wider than the work — and refuses when the ground is dark or
when what is left would be under half the frame. It has been run over the
115; the main catalogue's plates were already cropped. The plates that still
read dark at the edge are dark works: black paper, black ground.

Requires Playwright with Chromium.
