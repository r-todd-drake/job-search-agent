# tests/phase2/test_semantic_analyzer.py

import pytest
from unittest.mock import MagicMock
from pathlib import Path

FIXTURE_JD = (
    Path(__file__).parent.parent / "fixtures" / "stage_files" / "sample_jd.txt"
)


def make_mock_client(response_text):
    client = MagicMock()
    client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=response_text)]
    )
    return client


MOCK_ANALYSIS = """
FIT SCORE: 8/10

STRENGTHS:
- MBSE expertise aligns with Cameo requirement
- TS/SCI clearance confirmed

GAPS:
- ConOps experience not explicit

RECOMMENDATION: PURSUE
"""


def test_analyze_job_calls_api():
    from scripts.phase2_semantic_analyzer import analyze_job
    client = make_mock_client(MOCK_ANALYSIS)
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")
    candidate_profile = "Senior systems engineer, TS/SCI, MBSE expert."
    job = {"company": "Acme Defense Systems", "title": "Senior Systems Engineer"}

    result = analyze_job(client, job, jd_text, candidate_profile, keyword_scores={})

    assert client.messages.create.called
    assert result is not None


def test_analyze_job_no_pii_in_api_payload(pii_values, monkeypatch):
    from scripts.phase2_semantic_analyzer import analyze_job
    client = make_mock_client(MOCK_ANALYSIS)
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")

    # Register the fixture PII values as env vars so strip_pii can find them
    monkeypatch.setenv("CANDIDATE_NAME", pii_values["name"])
    monkeypatch.setenv("CANDIDATE_EMAIL", pii_values["email"])
    monkeypatch.setenv("CANDIDATE_PHONE", pii_values["phone"])
    monkeypatch.setenv("CANDIDATE_LINKEDIN", pii_values["linkedin"])
    monkeypatch.setenv("CANDIDATE_GITHUB", pii_values["github"])

    candidate_profile = (
        f"Candidate: {pii_values['name']} | "
        f"Email: {pii_values['email']} | "
        f"Phone: {pii_values['phone']} | "
        "Senior systems engineer, TS/SCI, MBSE expert."
    )
    job = {"company": "Acme Defense Systems", "title": "Senior Systems Engineer"}

    analyze_job(client, job, jd_text, candidate_profile, keyword_scores={})

    call_args = client.messages.create.call_args
    full_payload = str(call_args)
    for pii_value in pii_values.values():
        assert pii_value not in full_payload, f"PII found in API payload: {pii_value}"


def test_analyze_job_returns_response_text():
    from scripts.phase2_semantic_analyzer import analyze_job
    client = make_mock_client(MOCK_ANALYSIS)
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")
    candidate_profile = "Senior systems engineer, TS/SCI."
    job = {"company": "Acme", "title": "SE"}

    result = analyze_job(client, job, jd_text, candidate_profile, keyword_scores={})
    assert "FIT SCORE" in result or len(result) > 0


def test_analyze_job_handles_api_error_without_crashing():
    from scripts.phase2_semantic_analyzer import analyze_job

    client = MagicMock()
    client.messages.create.side_effect = Exception("Simulated API error")

    jd_text = FIXTURE_JD.read_text(encoding="utf-8")
    candidate_profile = "Senior systems engineer."
    job = {"company": "Acme", "title": "SE"}

    try:
        result = analyze_job(client, job, jd_text, candidate_profile, keyword_scores={})
        assert isinstance(result, str)
    except Exception as e:
        pytest.fail(
            f"analyze_job raised an unhandled exception on API error: {e}\n"
            "Add try/except inside analyze_job to handle API failures gracefully."
        )


def test_no_module_level_execution_on_import():
    import scripts.phase2_semantic_analyzer  # noqa: F401


@pytest.mark.live
def test_analyze_job_live_api_call():
    """Tier 2: real API call. Requires ANTHROPIC_API_KEY in environment."""
    import os
    from anthropic import Anthropic
    from scripts.phase2_semantic_analyzer import analyze_job

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")
    candidate_profile = "Senior systems engineer, TS/SCI cleared, MBSE expertise."
    job = {"company": "Acme Defense Systems", "title": "Senior Systems Engineer"}

    result = analyze_job(client, job, jd_text, candidate_profile, keyword_scores={})
    assert len(result) > 100, "Expected substantive analysis output"
