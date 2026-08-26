# Editorial guide

Read before touching `build.py` or `booklet.css`. Everything below is taken
from five books and magazines set beside each other, and from what they do
that this booklet did not.

---

## 1. What the five references actually do

**A. The blue art book** (six spreads, "HER").
A hairline runs across the head of a section page with three or four micro
labels hung under it. Pictures are placed as blocks and never cropped to the
page: one medium picture on a page with two thirds of the sheet left empty,
or a 3 × 2 grid of small ones with thin white gutters. One spread turns
black and the same grid logic continues in white on it. A page can carry a
single stamp-sized picture at the bottom and nothing else. Big serif numeral
"03." marks a section. Page numbers are tiny, in the outer corner.

**B. The Russian design magazine.**
Display type is enormous, condensed, all caps, tight leading, ragged right,
set flush to the margin, and it is the only large thing on the sheet. Body
text is tiny beside it. Pictures are sized to the column grid, never to the
type.

**C. The photography book contents.**
A contents spread can carry pictures: two columns of entries with thumbnails
scattered around them at different sizes, each with its own page number. Air
between everything.

**D. The gallery catalogue.**
Two-up and three-up picture grids with micro captions marked by a small
square. A black spread with one line of large white type. A mosaic page
where small pictures tile the whole sheet. One accent colour, used four or
five times in the whole book and nowhere else.

**E. The concrete zine.**
A quotation set large in bold caps is the whole right page; pictures stack
on the left. Footnotes sit at the foot in micro type behind a small square
marker.

**What they share.** Pictures whole, laid on a grid, at many different
sizes. White space used as structure, not as leftover. Type in two registers
only, micro and huge, with nothing in between. Hairlines and label rows.
Asymmetry: the same page never happens twice, but every page comes off the
same grid.

---

## 2. The grid

240 × 320 mm. Margins 16 mm left and right, 15 mm top, 18 mm foot.

Twelve columns, 4 mm gutters. Column = 13.67 mm. A span of n columns is
`n × 13.67 + (n − 1) × 4`. Every left edge and every width in the book is a
column position. Vertical positions are free millimetres, because pictures
have their own heights, but they are chosen, not fallen into.

## 3. Pictures

- **Never cropped.** A width is given, the height follows from the picture's
  own proportion. A wide detail stays wide. If a wide picture will not sit
  where the layout wants it, the layout moves.
- **Bled only when it costs nothing.** A full-page picture fills the sheet
  edge to edge only when its proportion is within about two per cent of the
  page's own 0.75; anything further from that is set to the page instead,
  bleeding on one axis and leaving an even margin on the other. Nothing is
  ever cut by more than a hair to make it fit.
- **One caption line for a full page.** Number, middle dot, where in the
  painting it is; always at the same height, always on paper, never in three
  different formats on three different sheets.
- Placed at the size its content asks for: a whole painting large, a detail
  large enough to read, a stage of the work small.
- Files are cut to about 13 pixels per millimetre of placed width, capped at
  1500 px. A picture that prints 40 mm wide does not carry a 1500 px file.

## 4. Type

Three registers. Nothing between 8 pt and 26 pt.

| register | size | use |
|---|---|---|
| micro | 6.2 pt, .18 em, caps, bold | labels, captions, folio, facets |
| note | 7.6 pt / 1.5 | the paragraph on a work, the essay |
| display | 26–96 pt, bold, −.03 em | numerals, years, the title, one shout |

Micro type is black for a label and grey for a caption. Display type is
flush left to a column edge and ragged right. Nothing is centred except a
caption under a picture narrower than 60 mm.

## 5. Furniture

- **Head rule**: 1 pt rule across the measure with micro labels hung 2.4 mm
  under it. It opens a work, a set of details, a process page, a section.
- **Foot rule**: 0.5 pt, above the three facets on a work page.
- **Folio**: micro, outer foot corner, number then running label. Small.
  The page number is not a graphic element.
- **Section numeral**: the work's catalogue number set in display size on
  its opening page, in the outer column.
- **Marker**: `▪` before a caption that names a kind (Detail, Study,
  Process).

## 6. Colour

Paper white, ink `#101010`, hairline `#ddd8d2`, grey `#7a736c`. Chapter
dividers are black sheets with white type. That is all. **No gradient, no
scrim, no shadow, no rounded corner, no tint over a picture.** Colour comes
from the paintings.

## 7. Composition

Every page is built from its own material.

- **Work opening.** Tall painting: picture in seven columns on one side,
  numeral and title and note in four on the other. Wide painting: picture
  across ten columns, numeral in the outer column, title and note under it.
  Square: picture in eight columns, centred, text under. The side alternates
  with the work's number, so no two openings in a row lean the same way.
- **Details.** The first detail of a work gets a page to itself, large:
  eleven columns if it is wide, seven if it is tall. The rest run two or
  three to a page in a grid, each with the line that says where in the
  painting it is.
- **Process.** All stages of a work on one sheet, four or five to a row,
  small, no captions. It is a sequence, not a set of plates.
- **Studies and versions.** The work in another state, on its own sheet,
  captioned Study or Version.
- **Divider.** Black sheet. The year in display size, the city under it, the
  numbers of the works in that year along a rule at the foot.

## 8. Forbidden

1. Cropping a picture to fill a shape.
2. Any gradient or veil over a picture.
3. Repeating on a detail what the work's own page already said.
4. Filling a page because it looks empty.
5. Type between 8 pt and 26 pt.
6. The same composition twice in a row.
7. The same picture printed twice at the same size.
8. A picture floated at a size the page did not ask for, with the rest of
   the sheet left to fend for itself.

---

## 9. What the book must say about itself

A book that will be sent to people who do not know the work has to answer,
without being asked:

- **Why the years jump.** 2019, 2020, one canvas in 2023, then 2026. The
  biography says it: from 2020 the studio work went to XR and spatial
  design. Say it in the book rather than leaving a curator to guess.
- **What recurs.** The small figure with crossed eyes is in eight of the
  thirty-five, 2019 through 2026. It is named, given a spread, and every
  appearance is shown side by side.
- **Which shows were paintings.** The exhibition list is split: painting
  under one head, XR and spatial design under another. Unsplit, a reader
  takes the design shows for the painting's history.
- **Where a number comes from.** A percentage in a paragraph was measured
  on the documentation file, not on the canvas, and no colour target was
  used. The colophon says so.
- **Whose picture it is.** A quotation carries its speaker, a reference
  frame in a process sequence carries its source and its rights holder.
- **How to buy one.** An address, a city, a line that says enquiries.

## 10. One work to a spread

**No blank pages.** A blank is an admission that the material was not
arranged. Page counts are made to come out right by choosing how many sheets
the details are spread over, whether the process runs to one sheet or two,
and whether a spare slot on a detail sheet carries a line of the work's own
text, not by opening an empty one. Where a work has no detail photography at
all and would still leave a page over, that page takes one sentence of its
own text set large; the painting is never printed twice at the same size.

**No year dividers.** A year with one work in it made that work look like a
mistake, and the year already stands at the foot of every page.

**The opening of a work.** Left page: one of its own details, full page,
upright or wide alike. Right page: the number, the plate, the strip, the
title, the paragraph, the three notes. Then the rest of the details.

**Detail sheets: four slots, top to bottom.** A sheet carries at most four
pictures, stacked, centred, with an equal margin left and right and nothing
touching a corner. The slot count follows the number of pictures actually on
that sheet, so three or two do not sit small in a four-slot rhythm; they
grow. One slot may hold a line of the work's own text instead of a picture,
and one may be split into a smaller pair. An upright detail is not squeezed
into a slot: it takes a page to itself.

**Never a grid outside the process sheets.** A regular grid belongs on the
process sheets, where the pictures are a sequence, and on the three sheets
that are lists by nature: the index of thirty-five, the contents of the
recurring, and the figure sheets in that chapter. A detail sheet is not a
shelf, and nothing is scattered anywhere.

**Never two alike side by side.** Details are compared by a coarse
fingerprint before they are placed, and near-identical ones are moved apart.

**Studies and versions.** What is in the studio beside a work and is not a
detail of it, a sheet of paper or an earlier painting of the same scene, is
set on its own page in the same left-aligned stack: pictures down the left
at a common height, what each one is on the right. The caption says what it
is and what changed, never the word "detail".

## 10a. What the old rule was

No spread carries two different works. A work with detail photography opens
on a left page with one of its own details and its information stands on the
right page facing it. Which detail leads is set per work in `LEAD` and is
never whatever happened to be first.

The block that follows ends on a right page, so the next work starts clean.
Where the count comes out wrong the fix is a page of content, not a blank.
Works with no detail photography are set two to a spread, one page each.

## 11. The back of the book

The order is fixed: the works, then the index, then the recurring, then the
colophon. The index is a chapter of its own, not a page that fell into
another chapter. Its thirty-five plates are set to a common band: every
picture sits on its row's baseline, so the numbers run in a straight line
across the sheet and the page reads as one block rather than thirty-five
accidents.

Six things come back across the seven years: the onlooker, the chair, the
crow, the cage, the body, the face. The chapter opens on a spread of its
own, the title on the left and a contents list on the right, one crop per
figure at a common height. Then one spread each: **text on the left page,
pictures on the right**, facing each other rather than following each other.
The picture sheets are two columns, rows of a common height, each crop
sitting on its row's baseline so the captions line up.

Every crop was located in its painting and looked at before it was used. A
thing that is not the thing does not go in: a pastel body with a long form
coming out of it is not a crow, and a dark shape behind a sitter is not a
chair. Both were in and both came out.

## 12. Two lengths

The book exists at two lengths from one source. The long one is the whole
record: every work, every detail, every stage. The short one is seventeen
pages and is what gets attached to an email: eight works, the recurring
figure, the address, and a thumbnail of the thirty-five so the eight are
understood as a selection. Nothing in the short one is written for it. If a
sentence is not good enough for the short version it is not good enough for
the long one either.
