# Artbooklet

The catalogue next door is a document: one work to a page, an index, a
caption at a fixed height. This is not that. Same paintings, same details,
same words, set as an art booklet.

240 x 320 mm, 97 pages. The cover stands alone, so from page 2 on an even
page is always the left of a spread and an odd page the right.

## The rule

Every work gets one spread and every spread is built the same way.

- **Left**: one picture, full bleed, edge to edge. A detail where there is
  detail photography, otherwise a crop taken from the painting itself.
  Across the top, in white, the catalogue number, the title and the year.
- **Right**: the work page. A rule under the catalogue number and the year,
  the painting whole in a band 148 mm deep, a strip giving medium,
  dimensions and place, then the title and the note, and along the foot
  three notes on colour, composition and hand.

The work page is identical for all thirty-five, whether the work has nine
details or none. Nothing else is allowed on it. What changes from spread to
spread is the painting.

Around that: an imprint and a line set large, the essay, the biography and
the list of shows, the contents, a divider for each year, and for the four
works with the most detail photography one extra spread of nothing but
detail. Page numbers are the heaviest mark on a page, in the outer corner.

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

Pictures are reduced into `images/`: 1550 px on the long side for a full
bleed, 1200 px for a plate. Layout lives in `booklet.css`; the sequence of
pages lives in `build.py`.
