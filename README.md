# Painting details, Yiğit Özen

Full-resolution detail scans of paintings by Yiğit Özen, one folder per
work. These are the archival files: 2126 × 1417 or 2657 × 1772 pixels, 7
to 11 MB apiece, 38 in all.

| Work | Folder | Details |
|---|---|---|
| Virgil on Virtual Cage (final_final-finalV9), 2026 | `virgilonvirtualcage/` | 10 |
| gary grills cooper, 2026 | `garygrillscooper/` | 9 |
| s(t)lop, 2026 | `stlop/` | 8 |
| articulo attack on mandarin, 2026 | `articuloattackonmandarin/` | 7 |
| walls of perception, 2026 | `wallsofperception/` | 4 |

## How the site uses them

[yigitozen.xyz](https://yigitozen.xyz) does not serve these files. A page
that asked a visitor for an 11 MB PNG per detail would not load, which is
what used to happen. The site carries its own derivatives, made from these
originals and committed alongside it:

- `img/detail/<name>.jpg` at 1600px, for the strip of thumbnails and the
  detail viewer
- `img/full/detail/<name>.jpg` at 2000px, for the lightbox and its zoom
- a 24px copy inline in the catalogue, shown blurred while the real image
  arrives

So every one of these 38 details is on the site and can be looked at
closely. This repository is where the files they were made from live.

## Regenerating the derivatives

The site's build reads these scans by path. After adding or replacing a
file here, re-run the asset step in the site repository
([decentralize-dfw/yigit](https://github.com/decentralize-dfw/yigit)) so
the derivatives and the blurred placeholders are made again, then rebuild
the pages.

Naming is `<work>_detail_<n>.png`, numbered from 1. The site reads the
count and the proportion from the files themselves, so a new detail only
needs to be dropped into the right folder with the next number.
