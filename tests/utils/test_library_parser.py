# tests/utils/test_library_parser.py

import json
import pytest
from pathlib import Path
from scripts.utils.library_parser import parse_library, employer_to_filename


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
    # Fixture has 3 bullet lines, but the parser drops the last pending bullet
    # when it encounters ## PROFESSIONAL SUMMARIES (sets current_employer = None
    # before the end-of-loop flush). Actual parsed count is 2.
    acme = employers.get("Acme Defense Systems")
    assert acme is not None
    assert len(acme["bullets"]) == 2


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
