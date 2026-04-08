# tests/phase4/test_resume_generator.py

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

FIXTURE_JD = Path(__file__).parent.parent / "fixtures" / "stage_files" / "sample_jd.txt"
FIXTURE_STAGE2 = Path(__file__).parent.parent / "fixtures" / "stage_files" / "stage2_approved.txt"
FIXTURE_LIBRARY = Path(__file__).parent.parent / "fixtures" / "library" / "experience_library.json"
FIXTURE_PROFILE = Path(__file__).parent.parent / "fixtures" / "library" / "candidate_profile.md"

MOCK_STAGE1_RESPONSE = """
SUMMARY
Senior systems engineer with MBSE expertise. TS/SCI cleared.

CORE COMPETENCIES
MBSE | Cameo Systems Modeler | DoDAF | Autonomous Systems

EXPERIENCE
Acme Defense Systems | Senior Systems Engineer | 2020 - Present
- Led MBSE development for autonomous surface vessel program using Cameo Systems Modeler.
- Developed system-of-systems architecture models.
- Facilitated IPT working groups with government stakeholders.

EDUCATION
Jane Q. Applicant University | B.S. Systems Engineering | 2005
"""

MOCK_STAGE3_RESPONSE = """
COHERENCE CHECK
Strong alignment with JD requirements.

ATS GAP ANALYSIS
JADC2 not represented.

SUGGESTIONS
No changes required.
"""


def make_mock_client(response_text):
    client = MagicMock()
    client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=response_text)]
    )
    return client


def test_run_stage1_creates_draft_file():
    from scripts.phase4_resume_generator import run_stage1
    client = make_mock_client(MOCK_STAGE1_RESPONSE)
    candidate_profile = FIXTURE_PROFILE.read_text(encoding="utf-8")
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")
    library = json.loads(FIXTURE_LIBRARY.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "stage1_draft.txt"
        run_stage1(client, jd_text, library, candidate_profile, str(output_path))
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "SUMMARY" in content
        assert "EXPERIENCE" in content


def test_run_stage1_no_pii_in_api_payload(pii_values, monkeypatch):
    import importlib
    import scripts.utils.pii_filter as pii_module
    for key, val in [
        ("CANDIDATE_NAME", pii_values["name"]),
        ("CANDIDATE_PHONE", pii_values["phone"]),
        ("CANDIDATE_EMAIL", pii_values["email"]),
        ("CANDIDATE_LINKEDIN", pii_values["linkedin"]),
        ("CANDIDATE_GITHUB", pii_values["github"]),
    ]:
        monkeypatch.setenv(key, val)
    importlib.reload(pii_module)

    from scripts.phase4_resume_generator import run_stage1
    client = make_mock_client(MOCK_STAGE1_RESPONSE)
    candidate_profile = (
        f"Candidate: {pii_values['name']} | Email: {pii_values['email']}\n"
        "Senior systems engineer, MBSE expert."
    )
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")
    library = json.loads(FIXTURE_LIBRARY.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "stage1_draft.txt"
        run_stage1(client, jd_text, library, candidate_profile, str(output_path))

    call_args = client.messages.create.call_args
    full_payload = str(call_args)
    for pii_value in pii_values.values():
        assert pii_value not in full_payload, f"PII found in payload: {pii_value}"


def test_run_stage1_priority_bullets_in_prompt(monkeypatch):
    """Priority bullets must be included in the API prompt."""
    import importlib
    import scripts.utils.pii_filter as pii_module
    importlib.reload(pii_module)

    from scripts.phase4_resume_generator import run_stage1
    client = make_mock_client(MOCK_STAGE1_RESPONSE)
    candidate_profile = FIXTURE_PROFILE.read_text(encoding="utf-8")
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")
    library = json.loads(FIXTURE_LIBRARY.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "stage1_draft.txt"
        run_stage1(client, jd_text, library, candidate_profile, str(output_path))

    # The priority bullet text "Cameo Systems Modeler" must appear in the API call
    call_args = client.messages.create.call_args
    full_payload = str(call_args)
    assert "Cameo Systems Modeler" in full_payload


def test_run_stage3_creates_review_file():
    from scripts.phase4_resume_generator import run_stage3
    client = make_mock_client(MOCK_STAGE3_RESPONSE)
    stage2_text = FIXTURE_STAGE2.read_text(encoding="utf-8")
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "stage3_review.txt"
        run_stage3(client, stage2_text, jd_text, str(output_path))
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "COHERENCE" in content or "ATS" in content or len(content) > 50


def test_run_stage3_no_pii_in_api_payload(pii_values, monkeypatch):
    import importlib
    import scripts.utils.pii_filter as pii_module
    for key, val in [
        ("CANDIDATE_NAME", pii_values["name"]),
        ("CANDIDATE_PHONE", pii_values["phone"]),
        ("CANDIDATE_EMAIL", pii_values["email"]),
        ("CANDIDATE_LINKEDIN", pii_values["linkedin"]),
        ("CANDIDATE_GITHUB", pii_values["github"]),
    ]:
        monkeypatch.setenv(key, val)
    importlib.reload(pii_module)

    from scripts.phase4_resume_generator import run_stage3
    client = make_mock_client(MOCK_STAGE3_RESPONSE)
    stage2_text = (
        f"Contact {pii_values['name']} at {pii_values['email']}\n"
        + FIXTURE_STAGE2.read_text(encoding="utf-8")
    )
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "stage3_review.txt"
        run_stage3(client, stage2_text, jd_text, str(output_path))

    call_args = client.messages.create.call_args
    full_payload = str(call_args)
    for pii_value in pii_values.values():
        assert pii_value not in full_payload, f"PII found in payload: {pii_value}"


def test_run_stage4_creates_docx():
    from scripts.phase4_resume_generator import run_stage4
    from docx import Document

    stage_text = FIXTURE_STAGE2.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "Test_Resume.docx"
        run_stage4(stage_text, str(output_path))
        assert output_path.exists()
        doc = Document(str(output_path))
        assert len(doc.paragraphs) > 0


def test_no_module_level_execution_on_import():
    import scripts.phase4_resume_generator  # noqa: F401


@pytest.mark.live
def test_run_stage1_live():
    """Tier 2: real API call."""
    import os
    from anthropic import Anthropic
    from scripts.phase4_resume_generator import run_stage1

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    candidate_profile = FIXTURE_PROFILE.read_text(encoding="utf-8")
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")
    library = json.loads(FIXTURE_LIBRARY.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "stage1_draft.txt"
        run_stage1(client, jd_text, library, candidate_profile, str(output_path))
        content = output_path.read_text(encoding="utf-8")
        assert "SUMMARY" in content
        assert "EXPERIENCE" in content
        assert len(content) > 200
