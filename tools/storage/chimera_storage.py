"""Safe file-image reference backend for Chimera II RAID/compression tests.

This operates only on explicitly supplied regular image files, never raw host
block devices. It is not a kernel block driver or production RAID implementation.
"""
from __future__ import annotations
import struct
import zlib
from pathlib import Path

_MAGIC = b"CHZ1"
_HEADER = struct.Struct(">4sBII")  # magic, codec (0=raw, 1=zlib), raw length, crc32


def pack_block(data: bytes, *, compress: bool = True) -> bytes:
    """Pack one independently verifiable block with bounded metadata."""
    raw = bytes(data)
    encoded = zlib.compress(raw) if compress else raw
    codec = 1 if compress and len(encoded) < len(raw) else 0
    payload = encoded if codec else raw
    return _HEADER.pack(_MAGIC, codec, len(raw), zlib.crc32(raw)) + payload


def unpack_block(frame: bytes, *, max_output: int = 16 * 1024 * 1024) -> bytes:
    """Decode a framed block, rejecting oversized, malformed or corrupt data."""
    if len(frame) < _HEADER.size:
        raise ValueError("compressed block header is truncated")
    magic, codec, raw_len, checksum = _HEADER.unpack(frame[:_HEADER.size])
    payload = frame[_HEADER.size:]
    if magic != _MAGIC or codec not in (0, 1):
        raise ValueError("unsupported compressed block header")
    if raw_len > max_output:
        raise ValueError("decompressed block exceeds configured output limit")
    if codec == 0:
        raw = payload
    else:
        dec = zlib.decompressobj()
        try:
            raw = dec.decompress(payload, max_output + 1)
            if len(raw) > max_output or dec.unconsumed_tail:
                raise ValueError("decompressed block exceeds configured output limit")
            raw += dec.flush(max_output + 1 - len(raw))
        except zlib.error as exc:
            raise ValueError("compressed block is corrupt") from exc
        if not dec.eof or dec.unused_data:
            raise ValueError("compressed block stream is incomplete or has trailing data")
    if len(raw) != raw_len:
        raise ValueError("decompressed length does not match block header")
    if zlib.crc32(raw) != checksum:
        raise ValueError("compressed block checksum mismatch")
    return raw


class ImageRaid:
    """Minimal RAID0/RAID1 reference over pre-created regular image files.

    All members must be equal-sized and sector-aligned. This helper does not
    create/format images, assemble real disks, journal metadata, rebuild failed
    members or provide crash consistency. Caller owns image creation and sizing.
    """
    def __init__(self, members: list[str | Path], *, level: int, sector_size: int = 512):
        if level not in (0, 1):
            raise ValueError("reference backend supports RAID0 and RAID1 only")
        if len(members) < (2 if level == 0 else 2):
            raise ValueError("at least two image members are required")
        if sector_size <= 0:
            raise ValueError("sector size must be positive")
        self.paths = [Path(p) for p in members]
        self.level, self.sector_size = level, sector_size
        self._files = [p.open("r+b") for p in self.paths]
        sizes = [p.stat().st_size for p in self.paths]
        if len(set(sizes)) != 1 or sizes[0] % sector_size:
            self.close()
            raise ValueError("RAID image members must have equal sector-aligned sizes")
        self.member_sectors = sizes[0] // sector_size
        self.sectors = self.member_sectors * len(self._files) if level == 0 else self.member_sectors

    def close(self):
        for f in getattr(self, "_files", []):
            if not f.closed:
                f.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _check(self, lba: int, count: int):
        if not isinstance(lba, int) or not isinstance(count, int) or lba < 0 or count < 1 or lba + count > self.sectors:
            raise ValueError("logical block range is out of bounds")

    def read(self, lba: int, count: int = 1) -> bytes:
        self._check(lba, count)
        out = bytearray()
        for logical in range(lba, lba + count):
            if self.level == 0:
                member, local = logical % len(self._files), logical // len(self._files)
                f = self._files[member]
                f.seek(local * self.sector_size)
                chunk = f.read(self.sector_size)
            else:
                chunk = b""
                for f in self._files:
                    f.seek(logical * self.sector_size)
                    chunk = f.read(self.sector_size)
                    if len(chunk) == self.sector_size:
                        break
            if len(chunk) != self.sector_size:
                raise OSError("short read from RAID image member")
            out.extend(chunk)
        return bytes(out)

    def write(self, lba: int, data: bytes):
        if len(data) == 0 or len(data) % self.sector_size:
            raise ValueError("write length must be a non-zero whole number of sectors")
        count = len(data) // self.sector_size
        self._check(lba, count)
        for offset in range(count):
            logical = lba + offset
            chunk = data[offset * self.sector_size:(offset + 1) * self.sector_size]
            if self.level == 0:
                member, local = logical % len(self._files), logical // len(self._files)
                targets = [(self._files[member], local)]
            else:
                targets = [(f, logical) for f in self._files]
            for f, local in targets:
                f.seek(local * self.sector_size)
                written = f.write(chunk)
                if written != self.sector_size:
                    raise OSError("short write to RAID image member")
                f.flush()
