# tests/phase3/test_build_candidate_profile.py

import os
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

FIXTURE_JSON = Path(__file__).parent.parent / "fixtures" / "library" / "experience_library.json"

MOCK_PROFILE_RESPONSE = """
## Confirmed Tools
Cameo Systems Modeler, DoDAF, MBSE

## Confirmed Skills
Systems architecture, autonomous systems integration

## Confirmed Clearance
Current TS/SCI

## Confirmed Gaps
- No INCOSE certification
"""


def make_mock_client():
    client = MagicMock()
    client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=MOCK_PROFILE_RESPONSE)]
    )
    return client


def test_build_profile_creates_output_file(monkeypatch):
    monkeypatch.setenv("CANDIDATE_NAME", "Jane Q. Applicant")
    monkeypatch.setenv("CANDIDATE_PHONE", "(555) 867-5309")
    monkeypatch.setenv("CANDIDATE_EMAIL", "applicant@example.com")
    monkeypatch.setenv("CANDIDATE_LINKEDIN", "linkedin.com/in/applicant")
    monkeypatch.setenv("CANDIDATE_GITHUB", "github.com/applicant")
    monkeypatch.setenv("CANDIDATE_LOCATION", "Test City, CA")

    from scripts.phase3_build_candidate_profile import build_profile

    client = make_mock_client()
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "candidate_profile.md"
        build_profile(client, str(FIXTURE_JSON), str(output_path))
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert len(content) > 0


def test_build_profile_no_pii_in_api_payload(monkeypatch):
    monkeypatch.setenv("CANDIDATE_NAME", "Jane Q. Applicant")
    monkeypatch.setenv("CANDIDATE_PHONE", "(555) 867-5309")
    monkeypatch.setenv("CANDIDATE_EMAIL", "applicant@example.com")
    monkeypatch.setenv("CANDIDATE_LINKEDIN", "linkedin.com/in/applicant")
    monkeypatch.setenv("CANDIDATE_GITHUB", "github.com/applicant")
    monkeypatch.setenv("CANDIDATE_LOCATION", "Test City, CA")

    import importlib
    import scripts.utils.pii_filter as pii_module
    importlib.reload(pii_module)

    from scripts.phase3_build_candidate_profile import build_profile

    client = make_mock_client()
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "candidate_profile.md"
        build_profile(client, str(FIXTURE_JSON), str(output_path))

    call_args = client.messages.create.call_args
    full_payload = str(call_args)
    for pii in ["Jane Q. Applicant", "(555) 867-5309", "applicant@example.com"]:
        assert pii not in full_payload, f"PII found in payload: {pii}"


def test_no_module_level_execution_on_import(monkeypatch):
    monkeypatch.setenv("CANDIDATE_NAME", "Jane Q. Applicant")
    monkeypatch.setenv("CANDIDATE_PHONE", "(555) 867-5309")
    monkeypatch.setenv("CANDIDATE_EMAIL", "applicant@example.com")
    monkeypatch.setenv("CANDIDATE_LINKEDIN", "linkedin.com/in/applicant")
    monkeypatch.setenv("CANDIDATE_GITHUB", "github.com/applicant")
    monkeypatch.setenv("CANDIDATE_LOCATION", "Test City, CA")
    import scripts.phase3_build_candidate_profile  # noqa: F401
