#!/usr/bin/env python3
"""news-image-20261117 entrypoint.

Copies the pre-rendered entry.png (Tuesday 17 November 2026 world news:
US strikes on Qeshm, Kerch Bridge hit again, Trump in Manila, the Iran
dirty-bomb report) to the output directory and checks the result fits the
competition limits: at most 1 MiB and at most 1024x1024.

Python 3.13, standard library only. Deterministic: the output is a byte
copy of the bundled image, so two runs write identical bytes.
"""

import hashlib
import os
import shutil
import struct
import sys

MAX_BYTES = 1024 * 1024
MAX_SIDE = 1024


def out_dir():
    """Output dir: --output <dir> / --output=<dir>, else
    $MAKEFUN_OUTPUT_DIR, else /output."""
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--output" and i + 1 < len(args):
            return args[i + 1]
        if arg.startswith("--output="):
            return arg[len("--output="):]
    return os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")


def jpeg_size(path):
    """Read (width, height) from a JPEG header, standard library only."""
    with open(path, "rb") as f:
        data = f.read(64 * 1024)
    if data[:2] != b"\xff\xd8":
        raise ValueError("not a JPEG file")
    pos = 2
    while pos + 9 < len(data):
        if data[pos] != 0xFF:
            raise ValueError("bad JPEG marker")
        marker = data[pos + 1]
        if marker in (0xD8, 0xD9, 0x01) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        seg_len = struct.unpack(">H", data[pos + 2:pos + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2):
            height, width = struct.unpack(">HH", data[pos + 5:pos + 9])
            return width, height
        pos += 2 + seg_len
    raise ValueError("no SOF marker found")


def sha256_of(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "entry.png")
    out = out_dir()
    os.makedirs(out, exist_ok=True)
    dst = os.path.join(out, "entry.png")
    shutil.copyfile(src, dst)

    size = os.path.getsize(dst)
    if size > MAX_BYTES:
        print(f"entry.png is {size} bytes, over the 1 MiB limit",
              file=sys.stderr)
        return 1
    width, height = jpeg_size(dst)
    if width > MAX_SIDE or height > MAX_SIDE:
        print(f"entry.png is {width}x{height}, over the 1024x1024 limit",
              file=sys.stderr)
        return 1
    if sha256_of(src) != sha256_of(dst):
        print("copy mismatch: output differs from the bundled image",
              file=sys.stderr)
        return 1
    print(f"wrote {dst} ({size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
