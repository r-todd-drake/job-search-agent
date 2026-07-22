# tests/utils/test_writing_rules.py

import pytest


@pytest.fixture(autouse=True)
def reset_writing_rules():
    """Reset the module-level cache before each test."""
    import scripts.utils.writing_rules as wr
    wr._rules = None
    yield
    wr._rules = None


def test_load_returns_file_content(tmp_path, monkeypatch):
    rules_file = tmp_path / "writing_rules.md"
    rules_file.write_text("1. Keep it short.\n")

    import scripts.utils.writing_rules as wr
    monkeypatch.setattr(wr, "_WRITING_RULES_PATH", rules_file)

    result = wr.load()
    assert result == "1. Keep it short.\n"


def test_load_caches_after_first_call(tmp_path, monkeypatch):
    rules_file = tmp_path / "writing_rules.md"
    rules_file.write_text("1. Keep it short.\n")

    import scripts.utils.writing_rules as wr
    monkeypatch.setattr(wr, "_WRITING_RULES_PATH", rules_file)

    result1 = wr.load()
    rules_file.unlink()
    result2 = wr.load()

    assert result1 is result2


def test_load_raises_when_file_missing(tmp_path, monkeypatch):
    import scripts.utils.writing_rules as wr
    monkeypatch.setattr(wr, "_WRITING_RULES_PATH", tmp_path / "missing.md")

    with pytest.raises(FileNotFoundError) as exc:
        wr.load()
    assert "writing_rules.md" in str(exc.value)
