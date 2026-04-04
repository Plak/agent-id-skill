#!/usr/bin/env python3
"""Utilities for writing secret material with restrictive permissions."""

import os


def write_secret_file(path: str, content: str | bytes, mode: int = 0o600) -> None:
    """Write secret content to a file with the requested permissions."""
    data = content.encode() if isinstance(content, str) else content
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    try:
        os.fchmod(fd, mode)
        total_written = 0
        while total_written < len(data):
            written = os.write(fd, data[total_written:])
            if written == 0:
                raise OSError(f"Short write while writing secret file: {path}")
            total_written += written
    finally:
        os.close(fd)
