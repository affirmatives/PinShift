from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

from PIL import Image


ICON_ENTRIES = [
    ("icon_16x16.png", 16),
    ("icon_16x16@2x.png", 32),
    ("icon_32x32.png", 32),
    ("icon_32x32@2x.png", 64),
    ("icon_128x128.png", 128),
    ("icon_128x128@2x.png", 256),
    ("icon_256x256.png", 256),
    ("icon_256x256@2x.png", 512),
    ("icon_512x512.png", 512),
    ("icon_512x512@2x.png", 1024),
]

ICON_FILL_RATIO = 0.91


def color_distance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def remove_edge_background(image: Image.Image, tolerance: int = 80) -> Image.Image:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    pixels = rgba.load()
    samples = [
        pixels[0, 0],
        pixels[width - 1, 0],
        pixels[0, height - 1],
        pixels[width - 1, height - 1],
    ]
    bg = tuple(sum(channel) // len(samples) for channel in zip(*samples))

    visited: set[tuple[int, int]] = set()
    queue: deque[tuple[int, int]] = deque()
    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    while queue:
        x, y = queue.popleft()
        if (x, y) in visited or x < 0 or y < 0 or x >= width or y >= height:
            continue
        visited.add((x, y))
        if color_distance(pixels[x, y], bg) > tolerance:
            continue
        r, g, b, _ = pixels[x, y]
        pixels[x, y] = (r, g, b, 0)
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    return rgba


def square_crop(image: Image.Image) -> Image.Image:
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        return image

    left, top, right, bottom = bbox
    width = right - left
    height = bottom - top
    side = int(max(width, height) * 1.06)
    center_x = (left + right) // 2
    center_y = (top + bottom) // 2

    canvas = Image.new("RGBA", (side, side), (255, 255, 255, 0))
    paste_x = side // 2 - center_x
    paste_y = side // 2 - center_y
    canvas.alpha_composite(image, (paste_x, paste_y))
    return canvas


def write_iconset(source: Path, iconset: Path) -> None:
    iconset.mkdir(parents=True, exist_ok=True)
    image = square_crop(remove_edge_background(Image.open(source)))
    content_size = int(1024 * ICON_FILL_RATIO)
    content = image.resize((content_size, content_size), Image.Resampling.LANCZOS)
    master = Image.new("RGBA", (1024, 1024), (255, 255, 255, 0))
    offset = (1024 - content_size) // 2
    master.alpha_composite(content, (offset, offset))
    for filename, size in ICON_ENTRIES:
        resized = master.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(iconset / filename)


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: make_icon.py SOURCE_PNG OUTPUT_ICONSET", file=sys.stderr)
        return 2
    write_iconset(Path(sys.argv[1]), Path(sys.argv[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
