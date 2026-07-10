# tests/phase3/conftest.py
import pytest
import scripts.utils.candidate_config as _cc
from tests.phase4.conftest import _TEST_CONFIG


@pytest.fixture(autouse=True)
def patch_candidate_config(monkeypatch):
    monkeypatch.setattr(_cc, "_config", _TEST_CONFIG)
