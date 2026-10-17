"""Reference validation is blocked unless pinned archive provenance is present."""
import json
from pathlib import Path
import pytest
from atlas.reference_validation import check_reference
from atlas.real_study import ARCHIVE_COMMIT, GIT_BLOBS


def test_reference_validation_requires_real_download(tmp_path):
    sample = {'data_category': 'SYNTHETIC_TEST_FIXTURE', 'observations':2011,
              'pinned_repository_commit':ARCHIVE_COMMIT,'git_blob_sha1':GIT_BLOBS}
    with pytest.raises(ValueError,match='verified pinned downloader'):
        check_reference({},sample,tmp_path/'irrelevant.json')


def test_reference_metadata_is_non_synthetic_and_committed():
    path = Path(__file__).resolve().parents[1] / 'research/real_market_2018_2025/REFERENCE_RESULTS.json'
    x = json.loads(path.read_text())
    assert x['prices_are_synthetic'] is False
    assert x['git_commit'] == ARCHIVE_COMMIT
    assert x['git_blobs'] == GIT_BLOBS
    assert x['common_price_observations'] == 2011
    assert x['comparison_sessions'] == 752
