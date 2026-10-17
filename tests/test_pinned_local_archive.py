"""Offline local archive path: tampering rejects; no price facts are fabricated."""
from pathlib import Path
import pytest
from atlas.real_study import read_pinned_market_data, blob_sha1, GIT_BLOBS, archive_url


def test_git_blob_sha_computation():
    assert blob_sha1(b"test content\n") == "d670460b4b4aece5915caf5c68d12f560a9fe3e4"


def test_pinned_archive_rejects_modified_local_csv(tmp_path):
    for name in ('spy','qqq','tlt'):
        (tmp_path / f'{name}.csv').write_text('Date,Close\n2018-01-02,100\n')
    with pytest.raises(ValueError, match='differ from expected pinned Git blob'):
        read_pinned_market_data(archive_dir=tmp_path)


def test_pinned_archive_requires_exact_files(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_pinned_market_data(archive_dir=tmp_path)


def test_pinned_archive_invalid_path(tmp_path):
    with pytest.raises(FileNotFoundError,match='directory not found'):
        read_pinned_market_data(archive_dir=tmp_path / 'missing')


def test_pin_is_stable():
    assert all(len(s) == 40 for s in GIT_BLOBS.values())
    assert archive_url('SPY').endswith('/market/us/spy.csv')
    with pytest.raises(ValueError):
        archive_url('FAKE')
