# tests/phase5/conftest.py
# Autouse fixture: patches candidate_config and domain_config with test data for all phase5 tests.
# Prevents FileNotFoundError in generate_prep() which calls candidate_config.load()
# to derive clearance_level for extract_salary(), and domain_config.get_label().

import pytest
import scripts.utils.candidate_config as _cc
import scripts.utils.domain_config as _dc


_TEST_CONFIG = {
    "clearance": {"level": "TS/SCI", "status": "Current", "granted": "2022"},
}


@pytest.fixture(autouse=True)
def patch_candidate_config(monkeypatch):
    monkeypatch.setattr(_cc, "_config", _TEST_CONFIG)
    monkeypatch.setattr(_dc, "_config", {"domain_label": "software engineering"})
