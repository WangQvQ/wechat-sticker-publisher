#!/usr/bin/env python3
"""Read-only image/GIF inspection. Requires Pillow. No artwork generation."""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from image_utils import visible_bytes

try:
    from PIL import Image
except ImportError:
    sys.exit('Missing Pillow. Install it in your chosen Python environment: pip install Pillow')


def inspect(path, args):
    result = {'file': str(path), 'bytes': path.stat().st_size, 'errors': []}
    with Image.open(path) as im:
        result.update(format=im.format, width=im.width, height=im.height,
                      frames=getattr(im, 'n_frames', 1), loop=im.info.get('loop'))
        hashes, durations, bounds = set(), [], []
        transparent = False
        for index in range(result['frames']):
            im.seek(index)
            frame = im.convert('RGBA')
            hashes.add(hashlib.sha256(visible_bytes(frame)).hexdigest())
            durations.append(im.info.get('duration', 0))
            alpha = frame.getchannel('A')
            transparent |= alpha.getextrema()[0] == 0
            bounds.append(alpha.getbbox())
        result.update(distinct_frames=len(hashes), durations_ms=durations,
                      duration_ms=sum(durations), has_transparent_pixels=transparent,
                      frame_bounds=bounds)
    errors = result['errors']
    if args.width is not None and result['width'] != args.width:
        errors.append(f"Expected width {args.width}, got {result['width']}")
    if args.height is not None and result['height'] != args.height:
        errors.append(f"Expected height {args.height}, got {result['height']}")
    if args.max_bytes is not None and result['bytes'] > args.max_bytes:
        errors.append(f"Exceeds {args.max_bytes} bytes")
    if args.require_animation:
        if result['format'] != 'GIF':
            errors.append('Expected GIF format')
        if result['frames'] < 2 or result['distinct_frames'] < 2:
            errors.append('No actual multi-frame animation detected')
        if any(duration <= 0 for duration in result['durations_ms']):
            errors.append('Animation has zero or missing frame duration')
    if args.require_loop and result['loop'] != 0:
        errors.append('Expected infinite loop (GIF loop=0)')
    if args.require_transparency and not result['has_transparent_pixels']:
        errors.append('No fully transparent pixels detected')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='+', type=Path)
    parser.add_argument('--width', type=int)
    parser.add_argument('--height', type=int)
    parser.add_argument('--max-bytes', type=int, help='Exact bytes, e.g. 80000; use current platform limits')
    parser.add_argument('--expect-count', type=int)
    parser.add_argument('--require-animation', action='store_true')
    parser.add_argument('--require-loop', action='store_true')
    parser.add_argument('--require-transparency', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    files, errors = set(), []
    extensions = {'.png', '.jpg', '.jpeg', '.gif'}
    for item in args.paths:
        if item.is_dir():
            files.update(p for p in item.rglob('*') if p.is_file() and p.suffix.lower() in extensions)
        elif item.is_file():
            files.add(item)
        else:
            errors.append(f'Missing input: {item}')
    if not files:
        errors.append('No images found')
    if args.expect_count is not None and len(files) != args.expect_count:
        errors.append(f'Expected {args.expect_count} files, found {len(files)}')
    results = []
    for file in sorted(files):
        try:
            results.append(inspect(file, args))
        except Exception as exc:
            results.append({'file': str(file), 'errors': [f'Cannot decode: {type(exc).__name__}: {exc}']})
    valid = not errors and all(not item['errors'] for item in results)
    report = {'passed': valid, 'count': len(results), 'errors': errors,
              'visual_review_required': True,
              'scope': 'Technical file checks only; does not prove identity consistency, anchor stability, smooth motion, copyright or platform acceptance.',
              'images': results}
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + '\n', encoding='utf-8')
        print(json.dumps({'passed': valid, 'count': len(results), 'report': str(args.output)}, ensure_ascii=False))
    else:
        print(text)
    return 0 if valid else 1


if __name__ == '__main__':
    raise SystemExit(main())
