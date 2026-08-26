# Paintings since 2019

The art book. Thirty-five paintings, one spread each, built from the site's
`works.json` and the photographs in this repository.

`Yigit-Ozen-Paintings-since-2019.pdf` — 163 pages, 240 × 320 mm.
`Yigit-Ozen-Paintings-Short.pdf` — 24 pages, eight works and one recurring
figure, for sending cold.

Set in Inter, under the SIL Open Font License; the files are in `fonts/`
and are embedded in the PDF.

## The one idea

Every work is a spread. The left page is writing and is nearly empty: the
number and the medium on a rule at the head, the title under it, the
dimensions, the paragraph, and the three notes on colour, composition and
hand — all one block, with the leftover white collected at the foot. The
right page is the painting, filling the sheet.

All thirty-five paintings are reproduced inside one band, 18 mm from the
head and 260 mm deep. An upright painting takes the band's height, a wide
one the page's width. That is the whole plate rule, and it means the reader
compares the paintings rather than the layouts.

The detail pages are not free. Six archetypes, a closed set, and six size
steps with nothing between them; every spread carries one picture that
takes more than half of it. `GUIDE.md` is the specification and `audit.js`
checks it on the rendered file.

## What is in it

- **35 spreads**, one to a work, all the same shape.
- **Detail sheets** allotted by what the work is — surface, recurring
  figures, whether its making was photographed — not by what happened to be
  in the camera. Where a work was never photographed in detail, its crops
  come from its own plate at the places the recurring chapter marks.
- **49 process stages** across five works, as contact sheets.
- **10 studies and versions**, each captioned for what it is.
- **An index** of all thirty-five, every plate at one width on one baseline.
- **Six recurring figures**, a spread each: text on the left, and on the
  right a crop from every painting the figure appears in. A crop marked with
  a degree sign in the works section is printed again there, so the argument
  can be checked against the painting it came from.
- Cover, imprint, title, the essay, the biography, the exhibitions, a page
  on how the book is arranged, the contents on one sheet, the colophon.

Where a work's sheets come out odd, the spare page is not filler: it shows
which recurring figures are in that painting, with the crop and the page its
chapter begins. There are no blank pages.

## Making it

```
python3 book.py ../../yigit/works.json      # book.html + images/
node audit.js                               # the specification, checked
node print.js && python3 post.py            # the PDF, its metadata and bookmarks

python3 book.py ../../yigit/works.json --short
node print.js --short && python3 post.py --short
```

`print.js` takes `playwright` or `playwright-core`, whichever is installed,
and honours `PLAYWRIGHT_CHROMIUM` when the browser lives outside the
package. `book.css` holds the type sizes and the rules; `book.py` holds
every position in millimetres.

The pictures are cut to 5.4 pixels per millimetre of printed width, capped
at 1360 px. That is 137 dpi on the page: below it the paper shows the
pixels, above it the file grows for nothing.

## The rules it will not break

The full list is in `GUIDE.md`. The short form: no cropping except on the
full-page plates, which are always also printed small and whole; three type
sizes and nothing between them; one work to a spread; no blank pages; six
archetypes and six size steps; one picture over half of every detail spread;
at least six bleeding pages in every 32; white in one block touching two
edges; and no picture under three columns.
