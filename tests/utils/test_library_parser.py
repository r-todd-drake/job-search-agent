# tests/utils/test_library_parser.py

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from scripts.utils.library_parser import parse_library, employer_to_filename, get_keywords


FIXTURE_MD = Path(__file__).parent.parent / "fixtures" / "library" / "experience_library.md"


def test_parse_library_returns_employers_and_summaries():
    employers, summaries = parse_library(str(FIXTURE_MD))
    assert len(employers) >= 1
    assert len(summaries) >= 1


def test_parse_library_employer_has_required_fields():
    employers, _ = parse_library(str(FIXTURE_MD))
    for name, data in employers.items():
        assert "name" in data
        assert "title" in data
        assert "dates" in data
        assert "bullets" in data
        assert isinstance(data["bullets"], list)


def test_parse_library_bullet_count_matches_source():
    employers, _ = parse_library(str(FIXTURE_MD))
    acme = employers.get("Acme Defense Systems")
    assert acme is not None
    assert len(acme["bullets"]) == 3


def test_parse_library_priority_bullet_flagged():
    employers, _ = parse_library(str(FIXTURE_MD))
    acme = employers.get("Acme Defense Systems")
    priority_bullets = [b for b in acme["bullets"] if b["priority"]]
    assert len(priority_bullets) == 1
    assert "Cameo Systems Modeler" in priority_bullets[0]["text"]


def test_parse_library_bullet_ids_assigned():
    employers, _ = parse_library(str(FIXTURE_MD))
    for name, data in employers.items():
        for bullet in data["bullets"]:
            assert bullet["id"] != ""


def test_employer_to_filename_produces_safe_string():
    result = employer_to_filename("Acme Defense Systems")
    assert result.endswith(".json")
    assert " " not in result
    assert result == result.lower()


def test_parse_library_malformed_section_raises_not_silently_skips():
    """A markdown file with a broken employer section should not silently drop bullets."""
    import tempfile
    malformed_md = """# Experience Library

## Acme Defense Systems

**Title:** Senior Systems Engineer
**Dates:** 2020 - Present

### Theme: Systems Architecture

- Valid bullet one.

- Valid bullet two.
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(malformed_md)
        tmp_path = f.name

    employers, _ = parse_library(tmp_path)
    acme = employers.get("Acme Defense Systems")
    assert acme is not None
    assert len(acme["bullets"]) == 2, (
        "Parser should capture all bullets present -- silent drops are not acceptable"
    )


# ==============================================
# get_keywords -- PII safety
# ==============================================

def test_get_keywords_strips_pii_from_api_payload(pii_values, monkeypatch):
    """
    Verifies get_keywords strips PII from bullet text before the API call --
    bullets come straight from the experience library and are not pre-stripped
    by any caller.
    """
    monkeypatch.setenv("CANDIDATE_NAME", pii_values["name"])
    monkeypatch.setenv("CANDIDATE_EMAIL", pii_values["email"])

    client = MagicMock()
    client.messages.create.return_value = MagicMock(
        content=[MagicMock(text='["systems engineering"]')]
    )

    bullet = (
        f"Led integration effort with {pii_values['name']} "
        f"(reachable at {pii_values['email']})."
    )
    keywords = get_keywords(client, bullet)

    assert keywords == ["systems engineering"]
    full_payload = str(client.messages.create.call_args)
    assert pii_values["name"] not in full_payload, "PII from bullet text reached API payload"
    assert pii_values["email"] not in full_payload, "PII from bullet text reached API payload"
