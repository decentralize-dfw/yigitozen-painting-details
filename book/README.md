# Paintings since 2019

The art book, second edition. Thirty-five paintings, built spread by
spread from the site's `works.json` and the photographs in this
repository.

`Yigit-Ozen-Paintings-since-2019.pdf` — 129 pages, 240 × 320 mm.
`Yigit-Ozen-Paintings-Short.pdf` — 24 pages, eight works and one recurring
figure, for sending cold.

Set in Inter and Newsreader, both under the SIL Open Font License; the
files are in `fonts/` and are embedded in the PDF.

## The one idea

Controlled rupture. One modernist grid runs under every page — twelve
columns, a 5 mm baseline, four registers — and it is broken on purpose, a
few times per sequence, by scale, by a crop crossing the spine, by a
sentence set at the size of a painting. The unit is the spread, never the
page: each carries one dominant element and one deliberate relation
between left and right, and the white answers whatever it faces.

`DIRECTION.md` is the art direction — the statement, the structure, what
was merged from the 163-page first edition, the five spread families and
eight built examples. `GUIDE.md` is the binding specification, and
`audit.js` checks it on the rendered file.

## What is in it

- **35 openings** — every work enters on a spread: number, title,
  dimensions, note and facets on the left, the painting whole on the
  right, top on the first register, its printed size following the
  physical size of the canvas. Six minor works share three paired
  spreads, both paintings whole.
- **Year thresholds as numerals** — 2026, 2023, 2020, 2019 enter as
  108 pt figures on the first work of the year; the 2023 spread carries
  the one commission and states the gap in the painting years.
- **Detail arguments** — one dominant cut against one or two
  counter-images: face against face, above against below, eye against
  mouth. Every exact crop is printed once in the whole book; `book.py`
  refuses a duplicate at build time.
- **Process as time** — the Leonardo that became *Virgil on Virtual
  Cage*, the Soprano still that became *gary grills cooper*, the notebook
  page, the face painted three times; the decisive stage large, the rest
  a numbered strip that says how many stages there were.
- **Two pauses** — "it could be about to strike…" facing the reaching
  arm; "Deeply ordered chaos." facing the pencil study it is inscribed
  on.
- **An index** of the thirty-five at one width, with page numbers.
- **What comes back** — six recurring figures, each spread behaving
  differently (dispersal, absence, ascent, framing, accumulation,
  confrontation), in cuts that appear nowhere else in the book.
- **A closing page** that marks, on the painting itself, exactly where
  the cover was cut from.

## Making it

```
python3 book.py ../../yigit/works.json      # book.html + images/
node audit.js                               # the specification, measured
node print.js && python3 post.py            # the PDF, its metadata and bookmarks

python3 book.py ../../yigit/works.json --short
node print.js --short && python3 post.py --short
```

`print.js` and `audit.js` take `playwright` or `playwright-core`,
whichever is installed, and honour `PLAYWRIGHT_CHROMIUM` when the browser
lives outside the package. `book.css` holds the type; `book.py` holds
every position in millimetres and every editorial decision in one
curation script per work.

The pictures are cut to 5.4 pixels per millimetre of printed width
(137 dpi on the page), with a higher cap for the spreads-wide bands.
Unused derivatives are pruned on every full build.

## The rules it will not break

The full list is in `GUIDE.md`. The short form: every painting whole,
uncropped and undistorted in its opening; plate size follows canvas size;
every exact crop printed once; the whole plate only in opening, index and
closing; one dominant per spread and at least half the image area in B/C
spreads; three image classes with the 49–64 mm middle forbidden; no family
more than twice in a row; no filler pages; titles in the artist's own
spelling.
