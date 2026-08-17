# Catalogue

`catalogue.html` is the source. `Yigit-Ozen-Paintings-2019-2026.pdf` is printed from it.

- A4 portrait, one work per page: image in the top half, caption below at a fixed position on every plate.
- Works run newest first. Cat. numbers and page numbers follow that order.
- Edit `catalogue.html` (structure and copy) or `catalogue.css` (layout), then reprint:

```
node print-pdf.js
```

Requires Playwright with Chromium. Plate images live in `images/`.
