#!/usr/bin/env python3
"""news-image-20261125 entrypoint.

The entry is a single pre-rendered front page, ``entry.png`` beside
this file, summing up the world's news of Wednesday 25 November
2026. This program places a verified copy of it at
``$MAKEFUN_OUTPUT_DIR/entry.png`` (``/output/entry.png`` when the
variable is unset), so the grader sees exactly the bytes in this
repository. Standard library only, no network, no reading outside
this repository.

The copy is written through a temporary file and renamed into
place, then re-read and checked byte-for-byte against the source:
its length and its sha256 must match, or the program exits
non-zero. Run it with::

    python3 main.py
"""

import hashlib
import os
import sys

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 1_048_576
CHUNK = 1 << 16


def fingerprint(path):
    """sha256 of a file, streamed in chunks so nothing big is held."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(CHUNK)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


class EntryShipper:
    """Carries entry.png from this repository into the output dir."""

    def __init__(self, here):
        self.here = here
        self.source = os.path.join(here, "entry.png")

    def load_payload(self):
        """Read the image and refuse anything that is not a PNG."""
        with open(self.source, "rb") as handle:
            blob = handle.read()
        if blob[:8] != PNG_SIGNATURE:
            raise ValueError("entry.png does not start with PNG magic bytes")
        if len(blob) > MAX_BYTES:
            raise ValueError("entry.png is over the 1 MiB limit")
        return blob

    def place(self, blob, expected_hash):
        """Write the bytes atomically, then prove the copy matches."""
        target_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
        os.makedirs(target_dir, exist_ok=True)
        destination = os.path.join(target_dir, "entry.png")
        staging = destination + ".tmp"
        with open(staging, "wb") as handle:
            handle.write(blob)
        os.replace(staging, destination)
        written_hash = fingerprint(destination)
        if written_hash != expected_hash:
            raise ValueError(
                "written entry.png sha256 %s != source %s"
                % (written_hash, expected_hash)
            )
        if os.path.getsize(destination) != len(blob):
            raise ValueError("written entry.png size does not match source")
        return destination


def run():
    shipper = EntryShipper(os.path.dirname(os.path.abspath(__file__)))
    blob = shipper.load_payload()
    source_hash = fingerprint(shipper.source)
    destination = shipper.place(blob, source_hash)
    print("wrote %s (%d bytes, sha256 %s)"
          % (destination, len(blob), source_hash))
    return 0


if __name__ == "__main__":
    sys.exit(run())
