# tests/utils/test_domain_config.py

import pytest
from pathlib import Path


@pytest.fixture(autouse=True)
def reset_domain_config():
    """Reset the module-level cache before each test."""
    import scripts.utils.domain_config as dc
    dc._config = None
    yield
    dc._config = None


def test_load_returns_dict_with_domain_label(tmp_path, monkeypatch):
    config_file = tmp_path / "domain_config.yaml"
    config_file.write_text("domain_label: \"software engineering\"\n")

    import scripts.utils.domain_config as dc
    monkeypatch.setattr(dc, "_DOMAIN_CONFIG_PATH", config_file)

    result = dc.load()
    assert result["domain_label"] == "software engineering"


def test_load_caches_after_first_call(tmp_path, monkeypatch):
    config_file = tmp_path / "domain_config.yaml"
    config_file.write_text("domain_label: \"marketing\"\n")

    import scripts.utils.domain_config as dc
    monkeypatch.setattr(dc, "_DOMAIN_CONFIG_PATH", config_file)

    result1 = dc.load()
    # Delete the file -- second call must use cache, not re-read disk
    config_file.unlink()
    result2 = dc.load()

    assert result1 is result2


def test_load_raises_when_file_missing(tmp_path, monkeypatch):
    import scripts.utils.domain_config as dc
    monkeypatch.setattr(dc, "_DOMAIN_CONFIG_PATH", tmp_path / "missing.yaml")

    with pytest.raises(FileNotFoundError) as exc:
        dc.load()
    assert "domain_config.yaml" in str(exc.value)
    assert "domain_config.example.yaml" in str(exc.value)


def test_get_label_returns_string(tmp_path, monkeypatch):
    config_file = tmp_path / "domain_config.yaml"
    config_file.write_text("domain_label: \"defense and aerospace systems engineering\"\n")

    import scripts.utils.domain_config as dc
    monkeypatch.setattr(dc, "_DOMAIN_CONFIG_PATH", config_file)

    assert dc.get_label() == "defense and aerospace systems engineering"


def test_patch_config_directly(monkeypatch):
    """Pattern used by tests in other modules: patch _config to avoid filesystem."""
    import scripts.utils.domain_config as dc
    monkeypatch.setattr(dc, "_config", {"domain_label": "test domain"})

    assert dc.get_label() == "test domain"
