# tests/phase4/conftest.py
# Autouse fixture: patches candidate_config and domain_config with test data for all phase4 tests.
# Prevents import-time failures in refactored scripts that call candidate_config.load()
# or domain_config.get_label().

import pytest
import scripts.utils.candidate_config as _cc
import scripts.utils.domain_config as _dc


_TEST_CONFIG = {
    "style_rules": {
        "lapsed_certs_to_exclude": [
            {"name": "CompTIA Security+", "fix": "Remove — certification is lapsed"}
        ],
        "clearance_language": {
            "pattern_to_flag": "Active TS/SCI",
            "fix": "Use 'Current TS/SCI' between employers — 'Active' only when employed on a program",
            "between_employers": "Current TS/SCI",
            "on_program": "Active TS/SCI",
        },
        "terminology": [
            {"rule_name": "Plank Holder (capitalized)", "pattern": "Plank Holder",
             "replacement": "Plank Owner (two words, capitalized)", "case_sensitive": True},
            {"rule_name": "plank holder (lowercase)", "pattern": "plank holder",
             "replacement": "Plank Owner (two words, capitalized)", "case_sensitive": False},
            {"rule_name": "plankowner (one word)", "pattern": "plankowner",
             "replacement": "Plank Owner (two words, capitalized)", "case_sensitive": False},
            {"rule_name": "safety-critical", "pattern": "safety-critical",
             "replacement": "mission-critical", "case_sensitive": False},
        ],
        "dash_style": "en dash only",
        "metric_rule": "no unverifiable metrics",
    },
    "employers": [
        {"name": "APEX MARITIME SYSTEMS", "tier": 1},
        {"name": "TECHSTAFF INC. (Supporting NavalTech)", "tier": 1},
        {"name": "MERIDIAN AUTONOMY", "tier": 1},
        {"name": "Talon Dynamics", "tier": 1},
        {"name": "DEFENSECORP", "tier": 2},
        {"name": "L3 COMMUNICATIONS", "tier": 3},
        {"name": "U.S. ARMY", "tier": 3},
    ],
    "resume_defaults": {
        "role_title": "Senior Systems Engineer",
        "education_line": "State University — B.A. Test Degree | ROTC",
        "certifications_line": "Test Cert | Current TS/SCI",
    },
    "clearance": {"level": "TS/SCI", "status": "Current", "granted": "2022"},
    "confirmed_gaps": [],
    "intro_monologue": "Test intro monologue.",
    "short_tenure_explanation": "Test tenure explanation.",
}


@pytest.fixture(autouse=True)
def patch_candidate_config(monkeypatch):
    monkeypatch.setattr(_cc, "_config", _TEST_CONFIG)
    monkeypatch.setattr(_dc, "_config", {"domain_label": "software engineering"})
