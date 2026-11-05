#!/usr/bin/env python3
"""Encode already-approved action frames as a transparent looping GIF."""

import argparse
import re
from pathlib import Path

from PIL import Image
from image_utils import visible_bytes


def natural_key(path):
    return [int(part) if part.isdigit() else part.lower()
            for part in re.split(r'(\d+)', path.name)]


def build(frames_dir, output, size=240, duration=120, durations=None, caption=None):
    files = sorted(Path(frames_dir).glob('*.png'), key=natural_key)
    if len(files) < 2:
        raise ValueError('At least two PNG action frames are required')
    if size <= 0 or duration < 20:
        raise ValueError('Size must be positive; frame duration must be at least 20ms')
    if durations is None:
        durations = [duration] * len(files)
    if len(durations) != len(files) or any(ms < 20 or ms % 10 for ms in durations):
        raise ValueError('Supply one duration per frame, each >=20ms and a multiple of 10ms')
    if Path(output).suffix.lower() != '.gif':
        raise ValueError('Output must have a .gif extension')
    originals = []
    for file in files:
        with Image.open(file) as im:
            originals.append(im.convert('RGBA'))
    base_size = originals[0].size
    if any(im.size != base_size for im in originals):
        raise ValueError('Frames must share one source canvas; normalize their anchors first')
    if len({visible_bytes(im) for im in originals}) < 2:
        raise ValueError('Frames contain no actual visual changes')
    scale = min(size / base_size[0], size / base_size[1])
    target_size = (max(1, round(base_size[0] * scale)), max(1, round(base_size[1] * scale)))
    offset = ((size - target_size[0]) // 2, (size - target_size[1]) // 2)
    overlay = None
    if caption:
        with Image.open(caption) as im:
            overlay = im.convert('RGBA')
        if overlay.size != (size, size):
            raise ValueError('Caption must be a transparent PNG on the exact output canvas')
    frames = []
    for original in originals:
        canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        canvas.alpha_composite(original.resize(target_size, Image.Resampling.LANCZOS), offset)
        if overlay is not None:
            canvas.alpha_composite(overlay)
        frames.append(canvas)
    # Build one palette for the entire animation. Reserve slot 255 for transparency.
    contact = Image.new('RGB', (size, size * len(frames)), 'white')
    for i, frame in enumerate(frames):
        rgb = Image.new('RGB', frame.size, 'white')
        rgb.paste(frame, mask=frame.getchannel('A'))
        contact.paste(rgb, (0, i * size))
    colors = contact.quantize(colors=255, method=Image.Quantize.MEDIANCUT).getpalette()[:765]
    colors.extend([0] * (765 - len(colors)))
    color_palette = Image.new('P', (1, 1))
    color_palette.putpalette(colors + [0, 0, 0])
    black_fallback = min(range(255), key=lambda i: sum(v * v for v in colors[i*3:i*3+3]))
    encoded = []
    for frame in frames:
        indexed = frame.convert('RGB').quantize(palette=color_palette, dither=Image.Dither.NONE)
        pixels, alpha = bytearray(indexed.tobytes()), frame.getchannel('A').tobytes()
        for i, a in enumerate(alpha):
            if a < 128:
                pixels[i] = 255
            elif pixels[i] == 255:
                pixels[i] = black_fallback
        fixed = Image.frombytes('P', (size, size), bytes(pixels))
        fixed.putpalette(colors + [0, 0, 0])
        encoded.append(fixed)
    # Freeze the caption rectangle, including its transparent padding, across frames.
    # The supplied caption must occupy a region reserved from the moving artwork.
    if overlay is not None and overlay.getbbox():
        box = overlay.getbbox()
        static_caption = encoded[0].crop(box)
        for frame in encoded[1:]:
            frame.paste(static_caption, box)
    if len({frame.tobytes() for frame in encoded}) < 2:
        raise ValueError('No visible motion remains after GIF quantization or caption composition')
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    encoded[0].save(output, save_all=True, append_images=encoded[1:],
                    duration=durations, loop=0, transparency=255, disposal=2, optimize=False)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frames', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--size', type=int, default=240)
    parser.add_argument('--duration', type=int, default=120)
    parser.add_argument('--durations', help='Comma-separated per-frame milliseconds, in file order')
    parser.add_argument('--caption', type=Path, help='Fixed caption on a transparent output-size canvas')
    args = parser.parse_args()
    try:
        times = [int(x) for x in args.durations.split(',')] if args.durations else None
        result = build(args.frames, args.output, args.size, args.duration, times, args.caption)
    except (ValueError, OSError) as exc:
        parser.exit(1, f'{exc}\n')
    print(result)


if __name__ == '__main__':
    main()
