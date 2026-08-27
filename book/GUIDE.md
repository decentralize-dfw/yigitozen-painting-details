# Editorial specification — second edition

Binding rules for *Paintings since 2019*, the spread-built edition.
`DIRECTION.md` is the argument; this file is what can be checked.
`book.py` enforces the countable rules while composing; `audit.js` measures
the rendered file. A page that fails is rebuilt, not argued about.

## 1. Page and grid

Trim 240 × 320 mm. Margins: head 18, foot 22, outer 16, inner 20; the
measure is 204 mm on both pages of a spread and the two pages are not the
same page. Twelve columns, 4 mm gutters. Baseline 5 mm. Four horizontal
registers at 18, 83, 148 and 213 mm; the plate band runs 18–278 mm.
Bleed 5 mm.

## 2. The spread is the unit

- **2.1** Every composition is a spread. `book.py` opens pages in pairs and
  refuses to open a work on a recto; every work unit is a whole number of
  spreads, so parity is structural, not padded. There are no filler pages.
- **2.2** Every spread carries one dominant element — an image, a plate, a
  sentence, or a committed field of white — and one deliberate relation
  between its two pages (a confrontation across the gutter, a band through
  it, text answering an image, scale against scale).
- **2.3** White is committed: it collects at the foot of a text mass or
  opens against the dominant. Nothing floats in leftover space; small
  images are docked to the block they belong to.

## 3. Three image classes, by area

Scale is decided as a share of the page (240 × 320 mm = 76 800 mm²), not
by column count, because area is what the eye reads.

- **MON** — the dominant: a full-page bleed, a full-height column, a
  spine-crossing band, or a plate at 187–260 mm. Above 30 %.
- **SUP** — a secondary in stated relation to the dominant: 20–35 % of the
  page, captioned, aligned to an edge, axis or baseline.
- **PUNCTUM** — a clue: about 2.8 % of the page (≈ 57 mm at landscape
  proportions), placed exactly, never decorative.
- **INDEX** — small images whose function is indexical: contents, the
  index, docked studies, sequence frames, butted mass cells.

**The forbidden middle.** A compact image (drawn proportion between 1:2
and 2:1) that covers 4–19 % of the page and stands **alone** on that page
is the indecisive scale the second edition exists to remove. `audit.js`
flags it. Plates, index images, deliberate bleeds, butted masses and the
comparative chapter are outside the rule; two or more related fragments on
one page are a composition and are judged by eye, not by the rule.

## 3a. One gesture, three times

No distinctive layout may appear more than three times in the book. The
gesture "a small clue facing a full-bleed image" is kept for works 01, 03
and 27 and counted by `audit.js`; everywhere else a full-bleed dominant
takes a different partner:

| | relationship |
|---|---|
| `f_clue` | one or two puncta on a single axis |
| `f_wide` | a secondary large enough to answer back |
| `f_narrow` | a narrow vertical column on the outer edge |
| `f_baseline` | two fragments on one strict baseline |
| `f_dossier` | two readings at one width — evidence facing immersion |
| `f_weld` | two halves butted at the spine, read as one picture |
| `f_across` | a horizontal sentence spanning the spread |

## 4. Plates

- **4.1** Every painting is reproduced whole, uncropped, undistorted, in
  its opening spread. The top of every plate sits on the first register.
- **4.2** Plate size follows the physical canvas: printed size =
  111 + 0.93 × (cm of the governing side), capped at the measure/band.
  100 × 160 cm takes the full band; 29.7 × 42 cm prints small. Honesty is
  the hierarchy; nothing is centred vertically in a band.
- **4.3** The whole plate may appear in exactly three contexts — opening,
  index, closing locator — at most once each. Enforced by the register in
  `book.py`.
- **4.4** Paired spreads (two minor, related works on one spread) keep both
  works whole with full metadata; the dominant prints larger, the second
  at about 0.7 of its own mapped size.

## 5. Crops

- **5.1** Cropping happens only for a genuine detail reading, after the
  whole painting has been shown, or on the cover (located on the closing
  page).
- **5.2** Every exact crop — detail photograph, plate cut, band slice,
  process frame — appears **once** in the book. `book.py` keeps a register
  keyed by file and crop box and refuses a duplicate at build time.
- **5.3** A place that returns does so as a different or a wider cut: the
  chapter on what comes back uses plate cuts that appear nowhere else, and
  a revisited detail is widened, not repeated.
- **5.4** A spine-crossing band is taken at the full width of its source
  and is used only where the centre of the image carries no face or focal
  figure. Full-page bleeds hold their subject with a stated focal point.

## 6. Families

Five spread families share the grid; none is a fixed template.

- **A · OPENING** — number, title, metadata, note and the three facets in
  one block on the verso; the plate on the recto. Variants: threshold
  (year numeral), integrated (docked study/version/detail), paired,
  monumental.
- **B · ARGUMENT** — one dominant cut against one to three counter-images.
  Secondaries lean toward the spine; the dominant's caption states
  location and what the hand did there; secondaries carry location only.
- **C · SEQUENCE** — time: the decisive stage large, the rest as a
  numbered strip, stagger or column, in order. The caption states how many
  stages exist and how many are shown. Borrowed sources are credited on
  the page.
- **D · PAUSE** — one sentence of the artist's at display size, tied to
  the image it describes, inside committed white. Each pause in the book
  is composed differently.
- **E · SURVEY** — contents, index, chapter contents, colophon: small
  images with strictly indexical function.

- **6.1** The same family never runs more than two spreads in a row
  (checked at build for B, C and D; openings vary by variant).
- **6.2** In a B or C spread the dominant holds at least half of the
  spread's printed image area (`audit.js` measures it; bands counted once).

## 7. Chronology

Newest first, 2026 → 2019. Year thresholds are numerals on the opening
spread of the first work of the year — no section pages. The 2023 spread
carries the one commission and states the gap in the painting years; its
emptiness is the content. Density falls as the book moves into the
archive: process-heavy 2026, tightening 2020, plate-led 2019.

## 8. The recurring chapter

Six figures, six behaviours on one grid: the onlooker disperses along the
foot of the spread; the chair isolates in emptiness; the crow ascends and
leaves off the top edge; the cage sits on drawn rules that never close;
the body packs into one butted mass across the gutter; the face confronts
at monumental scale. No cut in the chapter appears elsewhere in the book,
and each spread names the works it draws on.

## 9. Typography

Two families, four levels, chosen for paper rather than for the screen:

| | | |
|---|---|---|
| caption | Inter | 7.6 pt, uppercase, 1.46 |
| body | Newsreader | 10.8 pt, 1.40 |
| display | Inter bold | 15–108 pt |
| pause | Newsreader italic | 20 / 27 / 44 pt |

Grey text is #6e6e6e — dark enough to survive offset. Rules are 0.35 pt
and no finer. Italic marks one voice only: the artist's own sentences.
Micro captions sit within 4 mm of their image. Artwork-led pages carry no header rules and no
running labels — only a small folio at the outer foot, with year and place
on the verso. Titles keep the artist's spelling, punctuation and
capitalisation exactly.

## 10. Two files

- **Screen edition** — `Yigit-Ozen-Paintings-since-2019.pdf`, trim size,
  RGB, bookmarked. Cut at 203 ppi where the source allows, never upscaled:
  the median picture resolves at 203 ppi, a tenth at 153 or under, and
  a quarter at 240 or over. It was cut at 137 ppi in the first build,
  which was enough to read on a screen but threw away pixels the
  photographs actually held, so a picture enlarged in the editor — or
  printed from that file — showed less than the archive could give.
- **Print master** — `Yigit-Ozen-Paintings-Print-Master.pdf`, 246 × 326 mm:
  the 240 × 320 trim with a real 3 mm bleed on every edge, images cut at
  300 ppi where the source allows and never upscaled.

Colour is left as the photography was taken: no global grade, no CMYK
conversion, because no printer profile has been supplied. Conversion and
soft-proofing belong to the printer's profile, not to this repository.

## 11. Audit

`node audit.js` reports on the rendered file: distorted images, non-bleed
overflow, image overlaps (butted masses exempt), text over images, text
over text, text outside the margins, blank pages, the forbidden middle,
weak dominants, the count of the clue gesture, and bleeding pages per 32.
`node audit.js --print` adds effective resolution on the bleed master.
All must return zero findings. `book.py` additionally enforces spread
parity, the crop register, plate contexts, family runs and a page count of
126–146.

Fifty-eight images in the print master fall under 240 ppi. Every one is a
cut taken from a plate photograph, and the photograph is the limit: the
files are 2 000–2 500 px and a cut of a fifth of the width carries only
what it carries. They are not upscaled and not sharpened. Re-shooting the
plates at higher resolution is the only real fix; where a master exists —
work 02 — it is used.
