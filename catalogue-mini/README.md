# Mini Catalogue

One hundred and fifty works at three to a page: the 35 of `../catalogue/`
and the 115 that had never been catalogued.

`list-mobile-2.html` in `decentralize-dfw/decentralize` records 577 works;
147 carry `type: "painting"`. 32 of those are already the main catalogue's,
so 115 were new. The main catalogue's own 35 are read back out of
`../catalogue/catalogue.html`, with their plates.

`catalogue-mini.html` is the source. `Yigit-Ozen-Paintings-Mini-Catalogue.pdf`
is printed from it.

## The order

Not by year. By what the work is made on, and within that by whether it has
been catalogued before:

| | | |
|---|---|---|
| **Canvas** | Cat. 001–032 | 26 catalogued, then 6 |
| **Paper**  | Cat. 033–141 | 9 catalogued, then 100 — paper, carton, print, whiteboard |
| **Object** | Cat. 142–150 | 9 — assemblages, and work made on packaging taken apart |

Each group runs newest first. The running foot names the group, so a page
that straddles two says so.

## The page

- A4 portrait, three works to a page, in three bands.
- The plate falls to one side and then the other — right, left, right on one
  page, left, right, left on the page facing it — so an opened spread reads
  as a single descending line. The caption always sits opposite its plate,
  and the plate hangs on the outer margin.
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

`trim.py` cuts the empty ground from around a plate — the archive
photographs are wider than the work — and refuses when the ground is dark or
when what is left would be under half the frame. It has been run over the
115; the main catalogue's plates were already cropped.

Requires Playwright with Chromium.
