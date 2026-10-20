"""Server-side Streamlit interactions; no browser rendering or external feed claims."""
from pathlib import Path

import pytest

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
APP = Path(__file__).resolve().parents[1] / "app.py"


def test_synthetic_dashboard_and_risk_button():
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception
    assert any("SYNTHETIC" in item.value for item in at.warning)
    assert len(at.metric) >= 5
    at.button(key="run_validation").click().run()
    assert not at.exception
    assert not any("Risk validation unavailable" in item.value for item in at.warning)
    assert any("observations" in item.value.columns for item in at.dataframe)


def test_csv_without_upload_has_empty_state():
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    source = next(item for item in at.selectbox if item.label == "Data source")
    source.set_value("CSV uploaded adjusted closes").run()
    assert not at.exception
    assert any("Upload your own" in item.value for item in at.info)
    assert not at.metric
