# Artbooklet

The catalogue next door is a document: one work to a page, an index, a
caption at a fixed height. This is not that. Same paintings, same details,
same words, set as an art book.

**Read `GUIDE.md` before changing anything here.** It is the editorial spec
the layout answers to, drawn from the books this one is measured against.

240 x 320 mm, 105 pages, no blank ones. Everything sits on a twelve column grid with 16 mm
margins, and two rules hold on every page: no picture is ever cropped, and
nothing is ever laid over a picture. A width is given and the height follows
from the picture's own proportion, so a wide detail stays wide.

## What is in it

- **35 works.** A work with detail photography opens on a spread: one of its
  own details on the left at the largest size it can be without being cut,
  edge to edge on at least one axis, and its information on the right. The
  rest of its details follow, scattered rather than gridded. Works without
  detail photography are set two to a spread. No spread carries two
  different works, and there are no blank pages.
- **35 work openings.** The painting whole, its number in display size, the
  title and the paragraph, the medium and dimensions on a rule at the head,
  the three notes on colour, composition and hand at the foot. A tall
  painting, a wide one and a square one are each given the composition they
  need, and the side alternates with the number.
- **75 details**, every one that was photographed. The first of each work
  alone on a sheet, large, its foot on the same line as every other; the
  rest in grids whose shape is chosen so the sheet fills. Each carries one
  line: where in the painting it is.
- **49 process stages** across five works, a contact sheet to a work.
- **6 studies and versions**, the pictures that sit at the root of this
  repository, each on its own sheet.
- **Six recurring figures**, a spread each: the onlooker, the chair, the
  crow, the cage, the body, the face. Text on one sheet, and on the other a
  crop from every painting the thing appears in, thirty-five crops in all,
  each one located in its painting rather than guessed.
- Imprint, a line set large, the essay, the biography, the list of shows,
  the contents, and a black divider for each year.

## Making it

`booklet.html` is generated, not hand written. It is built from the site's
`works.json`, which holds every title, year, medium, dimension, place, note
and the three facets, along with the paths of the paintings and their
details.

```
python3 build.py ../../yigit/works.json     # booklet.html + images/
node print-pdf.js && python3 post.py        # Yigit-Ozen-Artbooklet.pdf, 95 pages

python3 build.py ../../yigit/works.json --short
node print-pdf.js --short && python3 post.py --short
```

`post.py` writes the PDF's title, author and keywords and the bookmarks, 44
of them in the long version, which is what makes ninety-five pages reachable.

## The short one

Nobody opens a ninety-five page PDF from a stranger. `--short` builds the
same book at seventeen pages and 3 MB: cover, imprint, the essay, the
biography, eight works one to a page, the spread on the recurring figure,
the colophon with the address, and facing it a thumbnail of all thirty-five
so the reader can see there is a body of work behind the eight. Which eight
is one line in `build.py`, `SELECT`.

`build.py` needs Pillow and reads the pictures from the site repository
beside this one. Three things it does that are easy to miss:

- Most of the stored photographs carry the wall around the canvas. The
  record's `box` says where the painting sits inside the photograph, and
  every picture is cut to it before it is reduced, so no plate shows a wall.
- Every picture file is cut to about ten pixels per millimetre of the width
  it will actually print at, capped at 1200. A stage that prints 40 mm wide
  does not carry a 1200 px file, which is what keeps 168 pictures inside
  23 MB.
- `where.json` holds the one line each detail carries. It is keyed by the
  detail's file name, so a new photograph needs a line there and nothing
  else. A detail with no line falls back to the word Detail.

Layout lives in `build.py`; `booklet.css` holds only type sizes, rule
weights and the colour of the paper. Page composition is not in the CSS.
bleed, 1250 px for a plate. Layout lives in `booklet.css`; the sequence of
pages lives in `build.py`.

## Reading it

`yigitozen.xyz/artbook` reads the same file as a book, cover alone and then
spreads, in a page-turning viewer carried over from veawork. The viewer
takes `?pdf=` if another file needs to be read in it.
