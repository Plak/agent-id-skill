#!/usr/bin/env python3
"""Utilities for handling secret material with restrictive permissions."""

import os
import tempfile


def secure_zero(buf: bytearray) -> None:
    """Best-effort in-place zeroing for mutable secret buffers."""
    for index in range(len(buf)):
        buf[index] = 0


def to_secure_buffer(data: bytes | str) -> bytearray:
    """Copy bytes or text into a mutable buffer that can be zeroed later."""
    raw = data.encode() if isinstance(data, str) else bytes(data)
    return bytearray(raw)


def atomic_write(path: str, content: bytes | str, mode: int = 0o600) -> None:
    """Atomically write secret content to a file with the requested permissions."""
    data = content.encode() if isinstance(content, str) else content
    directory = os.path.dirname(path) or "."
    dir_fd = os.open(directory, os.O_RDONLY)
    fd = None
    temp_path = None
    try:
        fd, temp_path = tempfile.mkstemp(prefix=".tmp-", dir=directory)
        os.fchmod(fd, mode)
        total_written = 0
        while total_written < len(data):
            written = os.write(fd, data[total_written:])
            if written == 0:
                raise OSError(f"Short write while writing secret file: {path}")
            total_written += written
        os.fsync(fd)
        os.replace(temp_path, path)
        os.fsync(dir_fd)
    except Exception:
        if fd is not None:
            os.close(fd)
            fd = None
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise
    finally:
        if fd is not None:
            os.close(fd)
        os.close(dir_fd)


def write_secret_file(path: str, content: str | bytes, mode: int = 0o600) -> None:
    """Write secret content to a file with restrictive permissions."""
    atomic_write(path, content, mode=mode)
