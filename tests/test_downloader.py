import hashlib

import pytest

from gh_latest.downloader import DownloadError, download_file, format_size


def test_download_skip_and_checksum(tmp_path):
    source = tmp_path / "source.bin"
    source.write_bytes(b"hello world")
    url = source.as_uri()
    sha = hashlib.sha256(b"hello world").hexdigest()
    dest = tmp_path / "out" / "file.bin"

    assert download_file(url, str(dest), 11, sha, show_progress=False) == "downloaded"
    assert dest.read_bytes() == b"hello world"
    assert download_file(url, str(dest), 11, sha, show_progress=False) == "skipped"


def test_checksum_mismatch_discards_file(tmp_path):
    source = tmp_path / "source.bin"
    source.write_bytes(b"hello world")
    dest = tmp_path / "bad.bin"

    with pytest.raises(DownloadError):
        download_file(source.as_uri(), str(dest), expected_sha256="0" * 64, show_progress=False)
    assert not dest.exists()
    assert not (tmp_path / "bad.bin.part").exists()


def test_format_size():
    assert format_size(None) == "unknown size"
    assert format_size(512) == "512 B"
    assert format_size(2048) == "2.0 KB"
    assert format_size(5 * 1024 * 1024) == "5.0 MB"
    assert format_size(3 * 1024**3) == "3.0 GB"
