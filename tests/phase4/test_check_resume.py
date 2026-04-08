# tests/phase4/test_check_resume.py
#
# Tests for scripts/check_resume.py
# Covers Layer 1 (string matching), Layer 2 (API assessment), and PII safety.
#
# Run mock tests only:
#   pytest tests/phase4/test_check_resume.py -m "not live" -v
# Run live test (requires ANTHROPIC_API_KEY):
#   pytest tests/phase4/test_check_resume.py -m live -v

import importlib
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

FIXTURE_BACKGROUND = Path(__file__).parent.parent / "fixtures" / "stage_files" / "sample_background.md"
FIXTURE_STAGE2 = Path(__file__).parent.parent / "fixtures" / "stage_files" / "stage2_approved.txt"

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
    from scripts.check_resume import extract_section
    text = "## Confirmed Gaps\nNo GitLab\n## Other Section\nOther content"
    result = extract_section(text, "## Confirmed Gaps")
    assert "No GitLab" in result
    assert "Other content" not in result


def test_extract_section_returns_empty_for_missing_heading():
    from scripts.check_resume import extract_section
    text = "## Some Section\nContent here"
    result = extract_section(text, "## Nonexistent Heading")
    assert result == ""


# ==============================================
# extract_gap_terms
# ==============================================

def test_extract_gap_terms_finds_acronyms():
    from scripts.check_resume import extract_gap_terms
    background = FIXTURE_BACKGROUND.read_text(encoding="utf-8")
    terms = extract_gap_terms(background)
    # MATLAB is in sample_background.md Confirmed Gaps as an ALL-CAPS acronym
    assert "MATLAB" in terms or len(terms) > 0


def test_extract_gap_terms_returns_set():
    from scripts.check_resume import extract_gap_terms
    background = FIXTURE_BACKGROUND.read_text(encoding="utf-8")
    terms = extract_gap_terms(background)
    assert isinstance(terms, set)


# ==============================================
# run_layer1
# ==============================================

def test_run_layer1_detects_em_dash():
    from scripts.check_resume import run_layer1
    resume_lines = ["Senior systems engineer \u2014 MBSE expert."]
    findings = run_layer1(resume_lines, gap_terms=set())
    assert len(findings) >= 1
    rules = [f["rule"] for f in findings]
    assert "Em dash" in rules


def test_run_layer1_detects_safety_critical():
    from scripts.check_resume import run_layer1
    resume_lines = ["Responsible for safety-critical systems design."]
    findings = run_layer1(resume_lines, gap_terms=set())
    rules = [f["rule"] for f in findings]
    assert "safety-critical" in rules


def test_run_layer1_finding_has_required_keys():
    from scripts.check_resume import run_layer1
    resume_lines = ["Used safety-critical approach."]
    findings = run_layer1(resume_lines, gap_terms=set())
    assert len(findings) >= 1
    f = findings[0]
    assert "layer" in f
    assert "rule" in f
    assert "line" in f
    assert "flagged_text" in f
    assert "fix" in f
    assert f["layer"] == 1


def test_run_layer1_detects_gap_term():
    from scripts.check_resume import run_layer1
    resume_lines = ["Proficient with MATLAB for simulation work."]
    findings = run_layer1(resume_lines, gap_terms={"MATLAB"})
    rules = [f["rule"] for f in findings]
    assert any("MATLAB" in r for r in rules)


def test_run_layer1_no_false_positives_on_clean_resume():
    from scripts.check_resume import run_layer1
    resume_lines = FIXTURE_STAGE2.read_text(encoding="utf-8").splitlines()
    findings = run_layer1(resume_lines, gap_terms=set())
    rule_names = [f["rule"] for f in findings]
    assert "Em dash" not in rule_names
    assert "safety-critical" not in rule_names


# ==============================================
# run_layer2
# ==============================================

def test_run_layer2_parses_valid_json_response():
    from scripts.check_resume import run_layer2
    mock_response = (
        '[{"violation_type": "Em dash", "line_reference": "line 1",'
        ' "flagged_text": "test \u2014 text", "suggested_fix": "Use en dash"}]'
    )
    client = make_mock_client(mock_response)

    findings = run_layer2(
        client,
        resume_text="test \u2014 text",
        gaps_section="",
        banned_section=""
    )
    assert len(findings) == 1
    assert findings[0]["rule"] == "Em dash"
    assert findings[0]["layer"] == 2


def test_run_layer2_returns_empty_list_for_no_violations():
    from scripts.check_resume import run_layer2
    client = make_mock_client(MOCK_L2_RESPONSE)
    findings = run_layer2(client, resume_text="Clean text.", gaps_section="", banned_section="")
    assert findings == []


def test_run_layer2_handles_json_parse_failure_gracefully():
    from scripts.check_resume import run_layer2
    client = make_mock_client("This is not JSON at all.")
    findings = run_layer2(client, resume_text="some text", gaps_section="", banned_section="")
    assert len(findings) == 1
    assert findings[0]["rule"] == "JSON parse failure"
    assert findings[0]["layer"] == 2


# ==============================================
# PII safety -- strip_pii called before API
# ==============================================

def test_no_pii_in_api_payload(pii_values, monkeypatch):
    """
    Verifies that PII is stripped before the API call by patching at the
    _run_checks level: set PII env vars, reload pii_filter and check_resume,
    then call run_layer2 with pre-stripped text (mirroring _run_checks behavior).
    """
    import scripts.utils.pii_filter as pii_module

    for key, val in [
        ("CANDIDATE_NAME", pii_values["name"]),
        ("CANDIDATE_PHONE", pii_values["phone"]),
        ("CANDIDATE_EMAIL", pii_values["email"]),
        ("CANDIDATE_LINKEDIN", pii_values["linkedin"]),
        ("CANDIDATE_GITHUB", pii_values["github"]),
    ]:
        monkeypatch.setenv(key, val)

    # Reload pii_filter so it picks up the monkeypatched env vars
    importlib.reload(pii_module)

    # Now strip PII the same way _run_checks does before calling run_layer2
    raw_resume = (
        f"Contact {pii_values['name']} at {pii_values['email']}\n"
        + FIXTURE_STAGE2.read_text(encoding="utf-8")
    )
    safe_resume = pii_module.strip_pii(raw_resume)

    # Verify strip_pii actually removed PII from the text that will go to API
    for pii_value in pii_values.values():
        assert pii_value not in safe_resume, f"PII not stripped before API call: {pii_value}"

    # Now call run_layer2 with the safe text and confirm payload is clean
    from scripts.check_resume import run_layer2
    client = make_mock_client(MOCK_L2_RESPONSE)

    run_layer2(client, safe_resume, gaps_section="No GitLab.", banned_section="Use en dashes.")

    call_args = client.messages.create.call_args
    full_payload = str(call_args)
    for pii_value in pii_values.values():
        assert pii_value not in full_payload, f"PII found in Layer 2 API payload: {pii_value}"


# ==============================================
# Live test (Tier 2 -- real API)
# ==============================================

@pytest.mark.live
def test_run_layer2_live():
    """Tier 2: real API call. Requires ANTHROPIC_API_KEY in environment."""
    import os
    import anthropic
    from scripts.check_resume import run_layer2, extract_section

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    resume_text = FIXTURE_STAGE2.read_text(encoding="utf-8")
    background = FIXTURE_BACKGROUND.read_text(encoding="utf-8")

    gaps_section = extract_section(background, "## Confirmed Gaps")
    banned_section = extract_section(background, "## Banned / Corrected Language")

    findings = run_layer2(client, resume_text, gaps_section, banned_section)
    assert isinstance(findings, list)
    # Each finding must have required keys if any are returned
    for f in findings:
        assert "layer" in f
        assert "rule" in f
        assert f["layer"] == 2
