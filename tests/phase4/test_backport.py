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


def test_extract_library_bullets_count():
    from scripts.phase4_backport import extract_library_bullets
    bullets = extract_library_bullets(str(FIXTURE_LIBRARY_MD))
    # Generated fixture has 3 employers x up to 3 bullets each — assert at least 3
    assert len(bullets) >= 3


def test_extract_library_bullets_fields():
    from scripts.phase4_backport import extract_library_bullets
    bullets = extract_library_bullets(str(FIXTURE_LIBRARY_MD))
    b = bullets[0]
    assert isinstance(b["employer"], str) and b["employer"]
    assert isinstance(b["theme"], str) and b["theme"]
    assert isinstance(b["text"], str) and b["text"]
    assert isinstance(b["line_number"], int) and b["line_number"] > 0
    assert isinstance(b["sources"], list)
    # Generated fixture has real *Used in: tags — at least one bullet has sources
    assert any(bullet["sources"] for bullet in bullets)


def test_extract_library_bullets_excludes_summaries():
    from scripts.phase4_backport import extract_library_bullets
    bullets = extract_library_bullets(str(FIXTURE_LIBRARY_MD))
    # Summaries section should not produce bullet entries
    texts = [b["text"] for b in bullets]
    assert not any(t.startswith('"') for t in texts)  # summary text is quoted


def test_extract_library_bullets_sources_survive_note_lines():
    """*Used in:* must attach even when *NOTE:* or [CANONICAL] lines intervene."""
    import tempfile, os
    from scripts.phase4_backport import extract_library_bullets
    content = (
        "# Experience Library\n\n"
        "## Acme Corp\n\n"
        "**Title:** Engineer\n"
        "**Dates:** 2020-2025\n"
        "**Domain:** Defense\n\n"
        "### Theme: Leadership\n\n"
        "- Led a team of engineers to deliver key milestones.\n"
        "*NOTE: [CANONICAL -- use this version]*\n"
        "*PRIORITY: true*\n"
        "*Used in: Acme_Resume*\n"
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(content)
        tmp = f.name
    try:
        bullets = extract_library_bullets(tmp)
        assert len(bullets) == 1
        assert "Acme_Resume" in bullets[0]["sources"]
    finally:
        os.unlink(tmp)


LIBRARY_BULLETS_SAMPLE = [
    {
        "text": "Led MBSE development for autonomous surface vessel program using Cameo Systems Modeler and DoDAF architectural views.",
        "theme": "Systems Architecture",
        "employer": "Acme Defense Systems",
        "line_number": 13,
        "sources": ["acme_sse"],
    },
    {
        "text": "Developed system-of-systems architecture models supporting multi-domain C2 integration.",
        "theme": "Systems Architecture",
        "employer": "Acme Defense Systems",
        "line_number": 17,
        "sources": ["acme_sse"],
    },
]


def test_classify_bullet_present():
    from scripts.phase4_backport import classify_bullet
    result = classify_bullet(
        "Led MBSE development for autonomous surface vessel program using Cameo Systems Modeler and DoDAF architectural views.",
        LIBRARY_BULLETS_SAMPLE,
    )
    assert result["classification"] == "present"
    assert result["score"] >= 85


def test_classify_bullet_net_new():
    from scripts.phase4_backport import classify_bullet
    result = classify_bullet(
        "Architected system interface definitions for all GNC subsystems across the autonomous vehicle program.",
        LIBRARY_BULLETS_SAMPLE,
    )
    assert result["classification"] == "net_new"
    assert result["match"] is None


def test_classify_bullet_variant():
    from scripts.phase4_backport import classify_bullet
    result = classify_bullet(
        "Developed system-of-sys architecture models for multi-domain C2 integration with minor rewording.",
        LIBRARY_BULLETS_SAMPLE,
    )
    assert result["classification"] == "variant"
    assert result["score"] >= 60
    assert result["score"] < 85


def test_classify_bullet_custom_thresholds():
    from scripts.phase4_backport import classify_bullet
    result = classify_bullet(
        "Developed system-of-sys architecture models for multi-domain C2 integration with minor rewording.",
        LIBRARY_BULLETS_SAMPLE,
        net_new_threshold=70,
        variant_floor=50,
    )
    assert result["classification"] == "present"


def test_match_employer_found():
    from scripts.phase4_backport import match_employer
    result = match_employer("Acme Defense Systems", LIBRARY_BULLETS_SAMPLE)
    assert result == "Acme Defense Systems"


def test_match_employer_not_found():
    from scripts.phase4_backport import match_employer
    result = match_employer("Unknown Corp", LIBRARY_BULLETS_SAMPLE)
    assert result is None


def test_classify_bullet_cross_employer_isolation():
    """A bullet from Employer A must not be suppressed by a high-scoring match from Employer B.

    main() filters library_bullets to the matched employer before calling classify_bullet.
    This test verifies that employer-filtered classify_bullet correctly returns net_new
    even when the same bullet text would score >=85 against a different employer's bullets.
    """
    from scripts.phase4_backport import classify_bullet
    # Same bullet text as in LIBRARY_BULLETS_SAMPLE (Acme Defense Systems)
    bullet_text = "Led MBSE development for autonomous surface vessel program using Cameo Systems Modeler and DoDAF architectural views."
    # But we only pass Saronic bullets -- the Acme match is excluded by employer filtering
    saronic_bullets = [
        {
            "text": "Developed software-defined radio integration architecture for multi-domain mesh networks.",
            "theme": "Communications",
            "employer": "Saronic Technologies",
            "line_number": 55,
            "sources": ["saronic_se"],
        }
    ]
    result = classify_bullet(bullet_text, saronic_bullets)
    # Should be net_new against Saronic's library -- the Acme match is not present
    assert result["classification"] == "net_new"
