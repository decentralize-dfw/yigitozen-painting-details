# Editorial specification

Binding rules for *Paintings since 2019*. Every rule is numeric and can be
checked; `audit.js` checks them on the rendered file. A page that fails is
rebuilt, not argued about.

## 1. Page

Trim 240 × 320 mm. Margins: head 18, foot 22, outer 16, inner 20, so the
measure is 204 mm on both sides of a spread and the two sides of a spread
are not the same page. Twelve columns, 4 mm gutters, 13.33 mm columns.
Baseline 5 mm. Four horizontal registers at 18, 83, 148 and 213 mm; the
**top** edge of every picture sits on one of them, the bottom edge is free.
Bleed 5 mm on all four edges.

## 2. Scale

Six steps and nothing between them.

| | columns | width |
|---|---|---|
| XS | 3 | 48 mm |
| S | 4 | 65 mm |
| M | 6 | 100 mm |
| L | 9 | 153 mm |
| XL | 12 | 204 mm |
| XXL | bleed | 250 × 330 mm |

- **2.1** Within a spread, largest and smallest differ by at least three steps.
- **2.2** The largest picture covers at least four times the area of the smallest.
- **2.3** One picture takes more than 55 % of the spread's printed area. It
  is the subject; the rest hang off it. In practice this means every detail
  spread carries a full-page plate or a strip.
- **2.4** Nothing under three columns. Small means XS, not "a bit small".

A step is also capped by resolution: 3.8 pixels per millimetre of printed
width, 5.2 for a full-page plate. Where a crop cannot reach the step the
page wants, its box is **widened** rather than its pixels stretched, and
the widening stops at the edge of the canvas so the wall behind the
painting never enters the frame.

## 3. Six archetypes, a closed set

- **A · PLATE** — one picture, XXL, bleeding on three edges, a strip at the
  foot carrying the work's number and title and then the caption. One per
  work at most. Full-page plates are cut by the sheet; each is also printed
  small and whole elsewhere in the same work.
- **B · JUMP** — two pictures, a large one and an XS, on one left edge, at
  least 26 mm apart, the white opening to the right.
- **C · STACK** — three to five pictures at exactly one width, left-aligned,
  4 mm apart, bottom edge ragged.
- **D · STRIP** — one band, 108 mm tall, crossing both pages of the spread
  and bleeding left and right. Cut from the full width of the source, so it
  carries the most pixels it can.
- **E · FIELD** — six to twelve XS cells in a tight 4 mm grid, a block with
  no white in it, anchored to the foot; the locations are keyed underneath
  in three columns.
- **F · WELD** — two pictures at one size, zero gutter, butted, bleeding
  both edges: read as one picture.

## 4. Sequence

- **4.1** The same archetype never appears in two consecutive spreads.
- **4.2** A work's detail series opens with A or D.
- **4.3** A series of more than one sheet ends on its smallest picture.
- **4.4** Four sheets or more run: open wide, thicken, single point, scatter.
- **4.5** At least six fully bleeding pages in every 32.

## 5. Repetition

- **5.1 Reprise** — in a series of three sheets or more, the opening crop is
  printed a second time, XS and whole, captioned *the same place, whole*.
- **5.2 Echo** — a crop that also carries a recurring figure is marked with
  a degree sign and printed again in the chapter on what comes back, at the
  step it was printed at here where the grid allows it.
- **5.3 Refrain** — in works 03, 15 and 27 the small picture moves to a
  fixed corner, so a fast riffle finds a pulse.

## 6. White

- **6.1** The white on a page is one block and touches at least two edges.
- **6.2** Never equal left and right, never equal top and bottom.
- **6.3** No top-left to bottom-right diagonal.
- **6.4** On a note page the text is one vertical block — title, dimensions,
  paragraph, the three notes — with no gap over 12 mm inside it. What is
  left over collects at the foot, not in the middle.

## 7. Captions

`LOCATION — WHAT THE HAND DID THERE`, at most 90 characters. The second
half is taken from that work's own note on colour, composition or hand, and
turns with each crop so one work's captions do not repeat. XS and S carry
the location alone: a field of nine is a list, not an essay.

## 8. Forbidden

1. A picture with white on all four sides, unless it is the only one on the page.
2. Two pictures within 15 % of each other's area, outside C, E and F.
3. The top-left to bottom-right diagonal.
4. Anything under three columns.
5. A page of exactly two similar pictures and nothing else.
6. A picture floating free of every column and register line.
7. The same archetype in two consecutive spreads.
8. A bleeding picture whose caption takes the running head's place and
   hides the work's title.

## 9. Allocation

Detail sheets are allotted by what the work is, not by what happened to be
photographed:

| | |
|---|---|
| surface over 0.7 m² | +1 |
| each recurring figure it carries | +1 |
| a process series exists | +1 |

0 → none · 1–2 → one sheet · 3–4 → two · 5 and over → three.
A work with detail photography takes at least one sheet, so nothing already
photographed is thrown away; a 2026 work with five crops or more takes four,
so the reprise has room. Where a work has no detail photography, its crops
are taken from its own plate at the places the recurring chapter marks.

## 10. Audit

`node audit.js` reports, on the rendered file: distorted pictures, pictures
outside the sheet that are not bleeding, overlaps, text past the margin,
blank pages, diagonals, the area ratio and the dominant share of every
detail spread, and the count of bleeding pages in every block of 32.
All of them must come back at zero or over the floor.
