# Paintings since 2019

The art book. Thirty-five paintings, one spread each, built from the site's
`works.json` and the photographs in this repository.

`Yigit-Ozen-Paintings-since-2019.pdf` — 151 pages, 240 × 320 mm, 23 MB.
`Yigit-Ozen-Paintings-Short.pdf` — 24 pages, eight works and one recurring
figure, for sending cold.

Set in Inter, under the SIL Open Font License; the files are in `fonts/`
and are embedded in the PDF.

## The one idea

Every work is a spread. The left page is writing and is nearly empty: the
number and the medium on a rule at the head, the title under it, the
paragraph low, the three notes on colour, composition and hand at the foot,
and the page number set large in the outer corner. The right page is the
painting, and it fills the sheet.

All thirty-five paintings are reproduced inside one band, 20 mm from the
head and 272 mm deep. An upright painting takes the height of that band; a
wide one takes the width of the page and sits centred in it. That is the
whole plate rule, and it means the reader compares the paintings honestly
rather than comparing the layouts.

Nothing is cropped. A picture may lie against the edge of the sheet; it may
not lose any of itself to get there. The cover is the only exception, and
even there the plate is set to the width of the page rather than filled to
it.

## What is in it

- **35 spreads**, one to a work, all the same shape.
- **71 details**, on sheets of one, two or three. Seven hand-built
  compositions decide where they go, and no two sheets in a row use the
  same one. Every detail carries one line: where in the painting it is.
- **49 process stages** across five works, as contact sheets. The only
  grid of that kind in the book.
- **10 studies and versions**, each captioned for what it is.
- **An index** of all thirty-five, every plate on one baseline.
- **Six recurring figures**, a spread each: text on the left, and on the
  right a crop from every painting the thing appears in.
- Cover, imprint, title, the essay, the biography, the exhibitions, a page
  on how the book is arranged, the contents on one sheet, the colophon.

Where a work's note is a quotation it is set apart, italic, with its source
directly beneath it, and the artist's own paragraph follows in roman. That
is the only italic body text in the book.

Where the page count would otherwise come out wrong, the spare page is not
filler: it shows which of the six recurring figures appears in that
painting, with the crop and the page the chapter on it begins. There are no
blank pages.

## Making it

```
python3 book.py ../../yigit/works.json      # book.html + images/
node print.js && python3 post.py            # the PDF, its metadata and 50 bookmarks

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

1. No cropping, except the width of the cover plate.
2. No gradient, veil, shadow or rounded corner anywhere.
3. Three type sizes and nothing between them: 6.4 pt micro, 8.8 pt body,
   and display from 19 pt up.
4. One work to a spread; a work never shares a spread with another.
5. No blank pages, and no picture printed twice at the same size.
6. A grid only on the process sheets, the index, and the recurring.
7. Titles keep the artist's own spelling and case, in the contents as well
   as on the page. The name is set YİĞİT, never YIĞIT: CSS uppercase turns
   a Turkish i into a dotless I, so the name is written out by hand
   wherever it is set in capitals.
