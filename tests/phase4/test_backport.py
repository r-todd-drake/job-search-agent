# tests/phase4/test_backport.py

import pytest
from pathlib import Path

FIXTURE_STAGE4 = Path(__file__).parent.parent / "fixtures" / "stage_files" / "stage4_final_backport.txt"
FIXTURE_LIBRARY_MD = Path(__file__).parent.parent / "fixtures" / "library" / "experience_library.md"


def test_parse_stage_file_employer_count():
    from scripts.phase4_backport import parse_stage_file
    content = FIXTURE_STAGE4.read_text(encoding="utf-8")
    sections = parse_stage_file(content)
    assert len(sections) == 1
    assert sections[0]["employer"] == "Acme Defense Systems"


def test_parse_stage_file_bullet_count():
    from scripts.phase4_backport import parse_stage_file
    content = FIXTURE_STAGE4.read_text(encoding="utf-8")
    sections = parse_stage_file(content)
    bullets = sections[0]["bullets"]
    assert len(bullets) == 3


def test_parse_stage_file_theme_extracted():
    from scripts.phase4_backport import parse_stage_file
    content = FIXTURE_STAGE4.read_text(encoding="utf-8")
    sections = parse_stage_file(content)
    bullets = sections[0]["bullets"]
    assert bullets[0]["theme"] == "Systems Architecture"
    assert bullets[1]["theme"] == "Leadership"


def test_parse_stage_file_missing_theme_uses_unknown():
    from scripts.phase4_backport import parse_stage_file
    content = "## Employer A\n- A bullet with no theme annotation\n"
    sections = parse_stage_file(content)
    assert sections[0]["bullets"][0]["theme"] == "UNKNOWN -- assign before committing"


def test_parse_stage_file_skips_summary_and_competencies():
    from scripts.phase4_backport import parse_stage_file
    content = (
        "## PROFESSIONAL SUMMARY\n\nSome summary text.\n\n"
        "## CORE COMPETENCIES\n\n- MBSE | DoDAF\n\n"
        "## Real Employer\n- Real bullet\n  [Theme: Engineering]\n"
    )
    sections = parse_stage_file(content)
    assert len(sections) == 1
    assert sections[0]["employer"] == "Real Employer"
