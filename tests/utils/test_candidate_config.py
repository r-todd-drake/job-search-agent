# tests/utils/test_candidate_config.py
#
# Unit tests for scripts/utils/candidate_config.py
# These tests control _config directly — do NOT apply the autouse patch fixture here.
#
# Run: pytest tests/utils/test_candidate_config.py -v

import pytest
import yaml
import scripts.utils.candidate_config as cc


@pytest.fixture(autouse=True)
def reset_config_cache():
    """Reset the module cache before each test so tests are independent."""
    cc._config = None
    yield
    cc._config = None


def test_load_returns_dict_from_yaml(tmp_path):
    config_data = {
        "clearance": {"level": "TS/SCI", "status": "Current", "granted": "2022"},
        "style_rules": {"dash_style": "en dash only"},
    }
    config_file = tmp_path / "candidate_config.yaml"
    config_file.write_text(yaml.dump(config_data), encoding="utf-8")

    original_path = cc._CONFIG_PATH
    cc._CONFIG_PATH = str(config_file)
    try:
        result = cc.load()
        assert result["clearance"]["level"] == "TS/SCI"
    finally:
        cc._CONFIG_PATH = original_path


def test_load_caches_result(tmp_path):
    config_data = {"clearance": {"level": "TS/SCI"}}
    config_file = tmp_path / "candidate_config.yaml"
    config_file.write_text(yaml.dump(config_data), encoding="utf-8")

    original_path = cc._CONFIG_PATH
    cc._CONFIG_PATH = str(config_file)
    try:
        result1 = cc.load()
        result2 = cc.load()
        assert result1 is result2
    finally:
        cc._CONFIG_PATH = original_path


def test_load_raises_with_helpful_message_when_file_missing(tmp_path):
    original_path = cc._CONFIG_PATH
    cc._CONFIG_PATH = str(tmp_path / "nonexistent.yaml")
    try:
        with pytest.raises(FileNotFoundError) as exc_info:
            cc.load()
        assert "candidate_config.example.yaml" in str(exc_info.value)
    finally:
        cc._CONFIG_PATH = original_path


def test_get_hardcoded_rules_always_includes_em_dash():
    cc._config = {"style_rules": {}}
    rules = cc.get_hardcoded_rules()
    patterns = [r[1] for r in rules]
    assert "—" in patterns


def test_get_hardcoded_rules_includes_lapsed_cert():
    cc._config = {
        "style_rules": {
            "lapsed_certs_to_exclude": [
                {"name": "CompTIA Security+", "fix": "Remove — lapsed"}
            ],
            "clearance_language": {},
            "terminology": [],
        }
    }
    rules = cc.get_hardcoded_rules("resume")
    patterns = [r[1] for r in rules]
    assert "CompTIA Security+" in patterns


def test_get_hardcoded_rules_includes_clearance_pattern():
    cc._config = {
        "style_rules": {
            "lapsed_certs_to_exclude": [],
            "clearance_language": {
                "pattern_to_flag": "Active TS/SCI",
                "fix": "Use Current TS/SCI",
            },
            "terminology": [],
        }
    }
    rules = cc.get_hardcoded_rules()
    patterns = [r[1] for r in rules]
    assert "Active TS/SCI" in patterns


def test_get_hardcoded_rules_returns_four_tuples():
    cc._config = {
        "style_rules": {
            "lapsed_certs_to_exclude": [
                {"name": "Test Cert", "fix": "Remove it"}
            ],
            "clearance_language": {
                "pattern_to_flag": "Active TS/SCI",
                "fix": "Use Current",
            },
            "terminology": [
                {"rule_name": "test", "pattern": "foo", "replacement": "bar", "case_sensitive": False}
            ],
        }
    }
    rules = cc.get_hardcoded_rules()
    assert all(len(r) == 4 for r in rules)


def test_get_hardcoded_rules_passes_document_type_to_fix():
    cc._config = {
        "style_rules": {
            "lapsed_certs_to_exclude": [
                {"name": "Test Cert", "fix": "Remove — lapsed"}
            ],
            "clearance_language": {},
            "terminology": [],
        }
    }
    rules_resume = cc.get_hardcoded_rules("resume")
    rules_cl = cc.get_hardcoded_rules("cover letter")
    cert_fix_resume = next(r[2] for r in rules_resume if r[1] == "Test Cert")
    cert_fix_cl = next(r[2] for r in rules_cl if r[1] == "Test Cert")
    assert "resume" in cert_fix_resume
    assert "cover letter" in cert_fix_cl
