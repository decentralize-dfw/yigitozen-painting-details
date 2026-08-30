# Mini Catalogue

The paintings that are **not** in `../catalogue/`. `list-mobile-2.html` in
`decentralize-dfw/decentralize` records 577 works; 147 of them have
`type: "painting"`, and 32 of those are already the main catalogue's. The
remaining 115 are here.

`catalogue-mini.html` is the source. `Yigit-Ozen-Paintings-Mini-Catalogue.pdf`
is printed from it.

- A4 portrait, **three works to a page**, in three bands.
- The plate falls to one side and then the other — right, left, right on one
  page, left, right, left on the page facing it — so an opened spread reads
  as a single descending line. The caption always sits opposite its plate,
  and the plate hangs on the outer margin.
- Works run newest first. Cat. numbers and the index follow that order.
- Dimensions are omitted where the record has none (objects, and work made
  on packaging taken apart).

## Rebuilding

```
python3 build.py          # works.json -> catalogue-mini.html
node print-pdf.js         # catalogue-mini.html -> PDF
```

`works.json` is the parsed record: title, year, medium, dimensions and the
plate file, read out of the one-line description each work carries in
`list-mobile-2.html` (`"acrylic on 120x120 canvas, 2023"`).

`trim.py` cuts the empty ground from around a plate — the photographs are
wider than the work — and refuses to cut when the ground is dark or when
what is left would be under half the frame. It has already been run over
`images/`; running it again is harmless.

Requires Playwright with Chromium.
