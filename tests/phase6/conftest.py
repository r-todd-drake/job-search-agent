# tests/phase6/conftest.py
# Autouse fixture: patches domain_config with test data for all phase6 tests.
# Prevents FileNotFoundError when tests call functions that use domain_config.get_label().

import pytest
import scripts.utils.domain_config as _dc


@pytest.fixture(autouse=True)
def patch_domain_config(monkeypatch):
    monkeypatch.setattr(_dc, "_config", {"domain_label": "software engineering"})
