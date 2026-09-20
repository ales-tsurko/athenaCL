#!/usr/bin/env python3
"""Render athenaCL's `:: athcl` icon on an exact bitmap grid.

Python 3 standard library only. No font installation or image library needed.
Run: python3 render_icon.py
Optional: python3 render_icon.py --size 1024 --output /path/to/output
Previous version: python3 render_icon.py --text ':: ath'

The a/t/h bitmaps are copied without alteration from WORDMARK in
athenaCL/src/app/pixel.rs. The colon uses MACRO's square dots from
athenaCL/src/figure/font/glyphs.rs, shifted down one cell to align with
the lowercase body: dot bounds match the a/c top and shared baseline.
The original wordmark has no lowercase c/l: matching lowercase extensions
use the e's left contour for c and the h's stem / t's foot for l.
Colors come from DARK in athenaCL/src/app/theme.rs.
This script writes only to its output directory; it never edits the app.
"""

import argparse
import binascii
import json
from pathlib import Path
import struct
import zlib


BACKGROUND = (0x0B, 0x0B, 0x0A)
FOREGROUND = (0xEC, 0xEB, 0xE6)
GLYPHS = {
    ":": ("..", "..", "..", "##", "##", "..", "##", "##"),
    "a": (
        ".........",
        ".........",
        ".........",
        ".#######.",
        ".......##",
        ".########",
        "##.....##",
        ".########",
    ),
    "t": (
        ".......",
        "..##...",
        "..##...",
        "#######",
        "..##...",
        "..##...",
        "..##...",
        "...####",
    ),
    "h": (
        "##........",
        "##........",
        "##........",
        "##.######.",
        "###.....##",
        "##......##",
        "##......##",
        "##......##",
    ),
    "c": (
        "..........",
        "..........",
        "..........",
        ".########.",
        "##........",
        "##........",
        "##........",
        ".#########",
    ),
    "l": (
        "##...",
        "##...",
        "##...",
        "##...",
        "##...",
        "##...",
        "##...",
        ".####",
    ),
}


def bitmap(text=":: athcl"):
    """Two columns between glyphs; four between the prompt and the word."""
    parts = []
    for index, char in enumerate(text):
        if char == " ":
            parts.append(("....",) * 8)
        else:
            if index and text[index - 1] != " ":
                parts.append(("..",) * 8)
            parts.append(GLYPHS[char])
    return tuple("".join(part[y] for part in parts) for y in range(8))


def chunk(kind, payload):
    return (struct.pack(">I", len(payload)) + kind + payload
            + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF))


def render(size, output, text=":: athcl"):
    rows = bitmap(text)
    width, height = len(rows[0]), len(rows)
    if size < 64:
        raise ValueError("Use at least 64px to keep the original glyphs intact.")
    # ~72% canvas width, rounded down to a whole logical-pixel scale.
    cell = max(1, size * 72 // (100 * width))
    if width * cell > size:
        raise ValueError("The bitmap is wider than the canvas.")
    left, top = (size - width * cell) // 2, (size - height * cell) // 2
    rectangles = []
    for y, row in enumerate(rows):
        for x, value in enumerate(row):
            if value == "#":
                rectangles.append((left + x * cell, top + y * cell, cell, cell))

    pixels = bytearray(bytes(BACKGROUND) * size * size)
    for x, y, w, h in rectangles:
        scanline = bytes(FOREGROUND) * w
        for py in range(y, y + h):
            start = (py * size + x) * 3
            pixels[start:start + w * 3] = scanline

    # True RGB, opaque, exactly two colors. No resampling or antialiasing.
    scanlines = b"".join(b"\x00" + pixels[y * size * 3:(y + 1) * size * 3]
                         for y in range(size))
    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
           + chunk(b"sRGB", b"\x00")
           + chunk(b"IDAT", zlib.compress(scanlines, 9))
           + chunk(b"IEND", b""))
    label = "".join(char for char in text if char.isalnum())
    stem = f"athenacl-icon-{label}-{size}"
    (output / f"{stem}.png").write_bytes(png)

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}" shape-rendering="crispEdges">',
        f"  <title>athenaCL — {text}</title>",
        f'  <rect width="{size}" height="{size}" fill="#0b0b0a"/>',
        '  <g fill="#ecebe6">',
    ]
    svg.extend(f'    <rect x="{x}" y="{y}" width="{w}" height="{h}"/>'
               for x, y, w, h in rectangles)
    svg.extend(["  </g>", "</svg>"])
    (output / f"{stem}.svg").write_text("\n".join(svg) + "\n", encoding="utf-8")

    # Validate the actual raster, including every logical pixel cell.
    assert {bytes(pixels[i:i + 3]) for i in range(0, len(pixels), 3)} == {
        bytes(BACKGROUND), bytes(FOREGROUND)
    }
    for y, row in enumerate(rows):
        for x, value in enumerate(row):
            expected = bytes(FOREGROUND if value == "#" else BACKGROUND) * cell
            for py in range(top + y * cell, top + (y + 1) * cell):
                start = (py * size + left + x * cell) * 3
                assert pixels[start:start + cell * 3] == expected
    for x, y in ((0, 0), (size - 1, 0), (0, size - 1), (size - 1, size - 1)):
        start = (y * size + x) * 3
        assert pixels[start:start + 3] == bytes(BACKGROUND)
    assert abs(left - (size - left - width * cell)) <= 1
    assert abs(top - (size - top - height * cell)) <= 1
    return {"text": text, "size": size, "cell_size": cell, "bitmap": [width, height],
            "origin": [left, top], "colors": ["#0b0b0a", "#ecebe6"],
            "antialiasing": False, "alpha": False, "png": f"{stem}.png"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, default=1024)
    parser.add_argument("--text", default=":: athcl")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    if args.size < 64:
        parser.error("--size must be at least 64")
    if not args.text.strip() or any(char not in GLYPHS and char != " " for char in args.text):
        parser.error("--text must contain only spaces and these glyphs: : a t h c l")
    args.output.mkdir(parents=True, exist_ok=True)
    report = render(args.size, args.output, args.text)
    label = "".join(char for char in args.text if char.isalnum())
    (args.output / f"bitmap-{label}.txt").write_text("\n".join(bitmap(args.text)) + "\n", encoding="ascii")
    (args.output / f"verification-{label}-{args.size}.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
