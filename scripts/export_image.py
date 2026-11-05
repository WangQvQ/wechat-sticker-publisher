#!/usr/bin/env python3
"""Resize generated artwork and honor an explicit upload byte budget."""

import argparse
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps


def export(source, output, width, height, max_bytes, fit='cover'):
    if min(width, height, max_bytes) <= 0:
        raise ValueError('Dimensions and byte budget must be positive')
    suffix = Path(output).suffix.lower()
    if suffix not in {'.png', '.jpg', '.jpeg'}:
        raise ValueError('Output must be PNG or JPEG')
    with Image.open(source) as im:
        im = ImageOps.exif_transpose(im).convert('RGBA')
    if fit == 'cover':
        im = ImageOps.fit(im, (width, height), method=Image.Resampling.LANCZOS)
    elif fit == 'contain':
        small = ImageOps.contain(im, (width, height), method=Image.Resampling.LANCZOS)
        im = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        im.alpha_composite(small, ((width-small.width)//2, (height-small.height)//2))
    else:
        raise ValueError('Fit must be cover or contain')
    buffer = BytesIO()
    if suffix == '.png':
        im.save(buffer, format='PNG', optimize=True)
        data = buffer.getvalue()
    else:
        rgb = Image.new('RGB', im.size, 'white')
        rgb.paste(im, mask=im.getchannel('A'))
        data = b''
        for quality in range(94, 39, -4):
            buffer = BytesIO()
            rgb.save(buffer, format='JPEG', quality=quality, optimize=True)
            data = buffer.getvalue()
            if len(data) <= max_bytes:
                break
    if len(data) > max_bytes:
        raise ValueError('Cannot meet byte budget in this format; simplify artwork or choose another permitted format')
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    return len(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--width', type=int, required=True)
    parser.add_argument('--height', type=int, required=True)
    parser.add_argument('--max-bytes', type=int, required=True)
    parser.add_argument('--fit', choices=['cover', 'contain'], default='cover')
    args = parser.parse_args()
    try:
        count = export(args.input, args.output, args.width, args.height, args.max_bytes, args.fit)
    except (ValueError, OSError) as exc:
        parser.exit(1, f'{exc}\n')
    print(f'{args.output}: {args.width}x{args.height}, {count} bytes')


if __name__ == '__main__':
    main()
