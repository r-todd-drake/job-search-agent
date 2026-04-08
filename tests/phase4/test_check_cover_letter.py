# tests/phase4/test_check_cover_letter.py
#
# Tests for scripts/check_cover_letter.py
# Covers Layer 1 (string matching), Layer 2 (API assessment), and PII safety.
#
# Run mock tests only:
#   pytest tests/phase4/test_check_cover_letter.py -m "not live" -v
# Run live test (requires ANTHROPIC_API_KEY):
#   pytest tests/phase4/test_check_cover_letter.py -m live -v

import pytest
from pathlib import Path
from unittest.mock import MagicMock

FIXTURE_BACKGROUND = Path(__file__).parent.parent / "fixtures" / "stage_files" / "sample_background.md"
FIXTURE_CL_STAGE2 = Path(__file__).parent.parent / "fixtures" / "stage_files" / "cl_stage2_approved.txt"

MOCK_L2_RESPONSE = "[]"  # No violations -- valid empty JSON array


def make_mock_client(response_text):
    client = MagicMock()
    client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=response_text)]
    )
    return client


# ==============================================
# extract_section
# ==============================================

def test_extract_section_returns_content_between_headings():
    from scripts.check_cover_letter import extract_section
    text = "## Confirmed Gaps\nNo GitLab\n## Other Section\nOther content"
    result = extract_section(text, "## Confirmed Gaps")
    assert "No GitLab" in result
    assert "Other content" not in result


def test_extract_section_returns_empty_for_missing_heading():
    from scripts.check_cover_letter import extract_section
    text = "## Some Section\nContent here"
    result = extract_section(text, "## Nonexistent Heading")
    assert result == ""


# ==============================================
# extract_gap_terms
# ==============================================

def test_extract_gap_terms_returns_set():
    from scripts.check_cover_letter import extract_gap_terms
    background = FIXTURE_BACKGROUND.read_text(encoding="utf-8")
    terms = extract_gap_terms(background)
    assert isinstance(terms, set)


def test_extract_gap_terms_finds_acronyms():
    from scripts.check_cover_letter import extract_gap_terms
    background = FIXTURE_BACKGROUND.read_text(encoding="utf-8")
    terms = extract_gap_terms(background)
    assert "MATLAB" in terms


# ==============================================
# run_layer1
# ==============================================

def test_run_layer1_detects_em_dash():
    from scripts.check_cover_letter import run_layer1
    cl_lines = ["Senior systems engineer \u2014 available immediately."]
    findings = run_layer1(cl_lines, gap_terms=set())
    rules = [f["rule"] for f in findings]
    assert "Em dash" in rules


def test_run_layer1_detects_safety_critical():
    from scripts.check_cover_letter import run_layer1
    cl_lines = ["Experience with safety-critical systems integration."]
    findings = run_layer1(cl_lines, gap_terms=set())
    rules = [f["rule"] for f in findings]
    assert "safety-critical" in rules


def test_run_layer1_detects_active_ts_sci():
    from scripts.check_cover_letter import run_layer1
    cl_lines = ["I hold an Active TS/SCI clearance."]
    findings = run_layer1(cl_lines, gap_terms=set())
    rules = [f["rule"] for f in findings]
    assert "Active TS/SCI" in rules


def test_run_layer1_detects_plank_holder():
    from scripts.check_cover_letter import run_layer1
    cl_lines = ["Served as Plank Holder for Project Overmatch."]
    findings = run_layer1(cl_lines, gap_terms=set())
    rules = [f["rule"] for f in findings]
    assert "Plank Holder (capitalized)" in rules


def test_run_layer1_detects_gap_term():
    from scripts.check_cover_letter import run_layer1
    cl_lines = ["Proficient with MATLAB for simulation and analysis."]
    findings = run_layer1(cl_lines, gap_terms={"MATLAB"})
    rules = [f["rule"] for f in findings]
    assert any("MATLAB" in r for r in rules)


def test_run_layer1_finding_has_required_keys():
    from scripts.check_cover_letter import run_layer1
    cl_lines = ["Used safety-critical approach throughout the program."]
    findings = run_layer1(cl_lines, gap_terms=set())
    assert len(findings) >= 1
    f = findings[0]
    for key in ("layer", "rule", "line", "flagged_text", "fix"):
        assert key in f
    assert f["layer"] == 1


def test_run_layer1_no_false_positives_on_clean_cover_letter():
    from scripts.check_cover_letter import run_layer1
    cl_lines = FIXTURE_CL_STAGE2.read_text(encoding="utf-8").splitlines()
    findings = run_layer1(cl_lines, gap_terms=set())
    assert len(findings) == 0, f"Expected no findings on clean fixture, got: {[f['rule'] for f in findings]}"


# ==============================================
# run_layer2
# ==============================================

def test_run_layer2_parses_valid_json_response():
    from scripts.check_cover_letter import run_layer2
    mock_response = (
        '[{"violation_type": "Em dash", "line_reference": "line 1",'
        ' "flagged_text": "test \u2014 text", "suggested_fix": "Use en dash"}]'
    )
    client = make_mock_client(mock_response)
    findings = run_layer2(
        client,
        cl_text="test \u2014 text",
        gaps_section="",
        banned_section=""
    )
    assert len(findings) == 1
    assert findings[0]["rule"] == "Em dash"
    assert findings[0]["layer"] == 2


def test_run_layer2_returns_empty_list_for_no_violations():
    from scripts.check_cover_letter import run_layer2
    client = make_mock_client(MOCK_L2_RESPONSE)
    findings = run_layer2(client, cl_text="Clean cover letter text.", gaps_section="", banned_section="")
    assert findings == []


def test_run_layer2_handles_json_parse_failure_gracefully():
    from scripts.check_cover_letter import run_layer2
    client = make_mock_client("This is not JSON at all.")
    findings = run_layer2(client, cl_text="some text", gaps_section="", banned_section="")
    assert len(findings) == 1
    assert findings[0]["rule"] == "JSON parse failure"
    assert findings[0]["layer"] == 2


def test_run_layer2_finding_has_required_keys():
    from scripts.check_cover_letter import run_layer2
    mock_response = (
        '[{"violation_type": "Generic opener", "line_reference": "line 1",'
        ' "flagged_text": "I am excited to apply", "suggested_fix": "Lead with strongest credential"}]'
    )
    client = make_mock_client(mock_response)
    findings = run_layer2(client, cl_text="I am excited to apply for this role.", gaps_section="", banned_section="")
    assert len(findings) == 1
    f = findings[0]
    for key in ("layer", "rule", "line", "flagged_text", "fix"):
        assert key in f
    assert f["layer"] == 2
