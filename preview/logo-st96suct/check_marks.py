#!/usr/bin/env python3
"""Fail if any logo mark isn't line-work on a transparent background.

Checks every SVG/PNG in marks/, the traced homepage mark, and the homepage
noscript fallback (or the paths given as arguments). A mark fails if any
corner pixel is not transparent, or if its solid (opaque) pixels cover more
than MAX_SOLID of its content bounding box.

    pip install cairosvg pillow
    python3 check_marks.py [paths...]
"""
import io
import sys
from pathlib import Path

import cairosvg
from PIL import Image

HERE = Path(__file__).resolve().parent
SIZE = 256          # raster size (longest side) used for the checks
ALPHA_CLEAR = 8     # corner alpha at or below this counts as transparent
ALPHA_SOLID = 128   # alpha above this counts as solid
MAX_SOLID = 0.40


def load(path):
    if path.suffix.lower() == '.svg':
        png = cairosvg.svg2png(url=str(path), output_width=SIZE)
        im = Image.open(io.BytesIO(png))
    else:
        im = Image.open(path)
        im.thumbnail((SIZE, SIZE))
    return im.convert('RGBA')


def solid_coverage(alpha, w, h):
    """Share of the mark's content box that is solid. Measured over the box
    rather than per connected region, because a cut-out (e.g. a star whose
    points touch the edges of a filled square) splits the fill into pieces."""
    xs, ys, n = [], [], 0
    for i, a in enumerate(alpha):
        if a > ALPHA_CLEAR:
            xs.append(i % w)
            ys.append(i // w)
        if a > ALPHA_SOLID:
            n += 1
    if not xs:
        return 0.0
    box = (max(xs) - min(xs) + 1) * (max(ys) - min(ys) + 1)
    return n / box


def check(path):
    im = load(path)
    w, h = im.size
    alpha = list(im.getchannel('A').tobytes())
    problems = []
    corners = [alpha[0], alpha[w - 1], alpha[(h - 1) * w], alpha[h * w - 1]]
    if max(corners) > ALPHA_CLEAR:
        problems.append(f'corner alpha {corners}')
    solid = solid_coverage(alpha, w, h)
    if solid > MAX_SOLID:
        problems.append(f'solid {solid:.0%} of its box')
    return problems, solid


def main(argv):
    paths = [Path(p) for p in argv] or [
        *sorted((HERE / 'marks').glob('*.svg')),
        *sorted((HERE / 'marks').glob('*.png')),
        HERE / 'brek-mark-lines.svg',
        HERE.parent.parent / 'brek-mark.png',
    ]
    failed = 0
    for p in paths:
        problems, solid = check(p)
        status = 'FAIL' if problems else 'ok  '
        failed += bool(problems)
        print(f'{status} {p.name:34} solid {solid:5.1%} of box  {"; ".join(problems)}')
    print(f'\n{len(paths) - failed}/{len(paths)} marks pass')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
