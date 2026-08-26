# Artbooklet

The catalogue next door is a document: one work per page, an index, a fixed
caption at a fixed height. This is not that. Same paintings, same details,
same words, set as an art booklet.

- 240 x 320 mm, 79 pages. The cover stands alone, so from page 2 on an even
  page is always the left of a spread and an odd page the right.
- Full-bleed details, thin metadata strips, one plate whole on the facing
  page, three notes on colour, composition and hand along the bottom.
- Page numbers are the heaviest mark on a page, in the outer corner.
- Ink over an image turns dark by itself where the paint underneath is pale;
  `build.py` measures the top and bottom band of every full-bleed picture.

## Making it

`booklet.html` is generated, not hand written. It is built from the site's
`works.json`, which holds every title, year, medium, dimension, note and the
three facets, along with the paths of the paintings and their details.

```
python3 build.py ../../yigit/works.json     # writes booklet.html + images/
node print-pdf.js                           # writes Yigit-Ozen-Artbooklet.pdf
```

`build.py` needs Pillow and reads the pictures from the site repository
beside this one. It reduces every picture it needs into `images/`: 1900 px on
the long side for a full-bleed page, 1400 px for a plate. Layout lives in
`booklet.css`; the sequence of pages lives in `build.py`.
