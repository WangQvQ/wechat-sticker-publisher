"""Pixel helpers shared by GIF encoding and read-only inspection."""


def visible_bytes(image):
    """Normalize fully transparent RGB; hidden color is not visible motion."""
    pixels = bytearray(image.convert('RGBA').tobytes())
    for offset in range(0, len(pixels), 4):
        if pixels[offset + 3] == 0:
            pixels[offset:offset + 3] = b'\x00\x00\x00'
    return bytes(pixels)
