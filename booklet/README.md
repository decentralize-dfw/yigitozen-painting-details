# Artbooklet

The catalogue next door is a document: one work to a page, an index, a
caption at a fixed height. This is not that. Same paintings, same details,
same words, set as an art booklet.

240 x 320 mm, 123 pages. The cover stands alone, so a viewer that shows
spreads pairs an even page on the left with an odd page on the right.

## The rule

**Every work has one page and that page is the same for all thirty-five.**
The number at the top, the painting whole in a band of fixed depth so that a
wide canvas and a tall one end at the same height, a strip giving the medium
and the year, the title and the note centred, and along the foot three notes
on colour, composition and hand. Nothing else is allowed on it, and nothing
is added or taken away because a work has more photographs or fewer.

A work whose only photograph is of the whole painting stops there. Blowing
that one photograph up to fill a facing page shows nothing the work page has
not already shown, and shows it worse.

A work that was photographed in detail carries every one of those details
after its page, each one full bleed and one to a page. The only thing
written on a detail is the work's number and where in the painting it is:
the mouth, the near corner of the board, the hands and the rod between them.
Medium and year are not repeated, since the work's own page said them.

Around all that: an imprint and a line set large, the essay, the biography
and the list of shows, the contents, and a divider for each year. Page
numbers are the heaviest mark on a page, in the outer corner.

## Making it

`booklet.html` is generated, not hand written. It is built from the site's
`works.json`, which holds every title, year, medium, dimension, place, note
and the three facets, along with the paths of the paintings and their
details.

```
python3 build.py ../../yigit/works.json     # writes booklet.html + images/
node print-pdf.js                           # writes Yigit-Ozen-Artbooklet.pdf
```

`build.py` needs Pillow and reads the pictures from the site repository
beside this one. Two things it does that are easy to miss:

- Most of the stored photographs carry the wall around the canvas. The
  record's `box` says where the painting sits inside the photograph, and
  every picture is cut to it before it is reduced, so no plate shows a wall.
- It measures the top and bottom band of every full-bleed picture. Where the
  paint underneath is pale the white type on that page turns dark by itself.
- `where.json` holds the one line each detail carries. It is keyed by the
  detail's file name, so a new photograph needs a line there and nothing
  else. A detail with no line falls back to the word Detail.

Pictures are reduced into `images/`: 1300 px on the long side for a full
bleed, 1250 px for a plate. Layout lives in `booklet.css`; the sequence of
pages lives in `build.py`.

## Reading it

`yigitozen.xyz/artbook` reads the same file as a book, cover alone and then
spreads, in a page-turning viewer carried over from veawork. The viewer
takes `?pdf=` if another file needs to be read in it.
