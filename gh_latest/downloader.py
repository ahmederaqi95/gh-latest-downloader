"""File downloading with progress, atomic writes and SHA-256 verification."""

from __future__ import annotations

import hashlib
import os
import sys
import urllib.request
from typing import Optional

USER_AGENT = "gh-latest-downloader"
CHUNK_SIZE = 1 << 16


class DownloadError(Exception):
    """A download failed or the file did not pass verification."""


def format_size(num_bytes: Optional[int]) -> str:
    """Human readable size, e.g. ``12.3 MB``."""
    if num_bytes is None:
        return "unknown size"
    size = float(num_bytes)
    for unit in ("B", "KB", "MB"):
        if size < 1024:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def sha256_of_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_up_to_date(dest: str, size: Optional[int], sha256: Optional[str]) -> bool:
    if size is None or not os.path.isfile(dest) or os.path.getsize(dest) != size:
        return False
    return sha256 is None or sha256_of_file(dest).lower() == sha256.lower()


def download_file(
    url: str,
    dest: str,
    expected_size: Optional[int] = None,
    expected_sha256: Optional[str] = None,
    show_progress: Optional[bool] = None,
) -> str:
    """Download ``url`` to ``dest``.

    Returns ``"skipped"`` if an identical file already exists, otherwise
    ``"downloaded"``. Data is written to ``dest + ".part"`` first and moved into
    place only after the size / checksum checks pass.

    No credentials are sent: release assets of public repos do not need them, and
    the request is redirected to a different host.
    """
    if show_progress is None:
        show_progress = sys.stdout.isatty()
    if _is_up_to_date(dest, expected_size, expected_sha256):
        return "skipped"

    os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
    partial = dest + ".part"
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/octet-stream"}
    )
    digest = hashlib.sha256()
    try:
        with urllib.request.urlopen(request, timeout=60) as response, open(partial, "wb") as out:
            total = int(response.headers.get("Content-Length") or 0)
            done = 0
            while True:
                chunk = response.read(CHUNK_SIZE)
                if not chunk:
                    break
                out.write(chunk)
                digest.update(chunk)
                done += len(chunk)
                if show_progress and total:
                    print(
                        f"\r  {format_size(done)} / {format_size(total)} ({done * 100 // total}%)",
                        end="",
                        flush=True,
                    )
        if show_progress:
            print()
        if total and done != total:
            raise DownloadError(f"Incomplete download ({done} of {total} bytes).")
        if expected_sha256 and digest.hexdigest().lower() != expected_sha256.lower():
            raise DownloadError("SHA-256 checksum mismatch - file discarded.")
        os.replace(partial, dest)
    except BaseException:
        if os.path.exists(partial):
            os.remove(partial)
        raise
    return "downloaded"
