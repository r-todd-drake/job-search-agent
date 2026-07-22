# tests/phase4/test_cover_letter.py

import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from docx import Document

FIXTURE_JD = Path(__file__).parent.parent / "fixtures" / "stage_files" / "sample_jd.txt"
FIXTURE_STAGE2 = Path(__file__).parent.parent / "fixtures" / "stage_files" / "stage2_approved.txt"
FIXTURE_BACKGROUND = Path(__file__).parent.parent / "fixtures" / "stage_files" / "sample_background.md"

MOCK_CL_RESPONSE = """Dear Hiring Manager,

I am writing to express my interest in the Senior Systems Engineer position at Acme Defense Systems.

My experience with MBSE and Cameo Systems Modeler directly aligns with your requirements. I have led
development of DoDAF architectural views for autonomous maritime systems.

I look forward to discussing how my background supports your mission.

Sincerely,
[CANDIDATE]
"""


def make_mock_client(response_text):
    client = MagicMock()
    client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=response_text)]
    )
    return client


def make_sequential_mock_client(response_texts):
    """Mock client whose messages.create() returns each text in order, one per call."""
    client = MagicMock()
    client.messages.create.side_effect = [
        MagicMock(content=[MagicMock(text=t)]) for t in response_texts
    ]
    return client


def test_run_cl_stage1_creates_draft_file():
    from scripts.phase4_cover_letter import run_cl_stage1
    client = make_sequential_mock_client([
        "Hiring Manager",
        MOCK_CL_RESPONSE,
        MOCK_CL_RESPONSE,
        f"## SECTION 1\n{MOCK_CL_RESPONSE}\n\n## SECTION 2\n{MOCK_CL_RESPONSE}",
    ])
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")
    resume_text = FIXTURE_STAGE2.read_text(encoding="utf-8")
    background_text = FIXTURE_BACKGROUND.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "cl_stage1_draft.txt"
        run_cl_stage1(client, jd_text, resume_text, background_text, str(output_path))
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert len(content) > 50


def test_run_cl_stage1_no_pii_in_payload(pii_values, monkeypatch):
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

    from scripts.phase4_cover_letter import run_cl_stage1
    client = make_sequential_mock_client([
        "Hiring Manager",
        MOCK_CL_RESPONSE,
        MOCK_CL_RESPONSE,
        f"## SECTION 1\n{MOCK_CL_RESPONSE}\n\n## SECTION 2\n{MOCK_CL_RESPONSE}",
    ])
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")
    resume_text = (
        f"Name: {pii_values['name']} | Phone: {pii_values['phone']}\n"
        + FIXTURE_STAGE2.read_text(encoding="utf-8")
    )
    background_text = FIXTURE_BACKGROUND.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "cl_stage1_draft.txt"
        run_cl_stage1(client, jd_text, resume_text, background_text, str(output_path))

    full_payload = str(client.messages.create.call_args_list)
    for pii_value in pii_values.values():
        assert pii_value not in full_payload, f"PII found in payload: {pii_value}"


def test_run_cl_stage1_output_has_content():
    from scripts.phase4_cover_letter import run_cl_stage1
    client = make_sequential_mock_client([
        "Hiring Manager",
        MOCK_CL_RESPONSE,
        MOCK_CL_RESPONSE,
        f"## SECTION 1\n{MOCK_CL_RESPONSE}\n\n## SECTION 2\n{MOCK_CL_RESPONSE}",
    ])
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")
    resume_text = FIXTURE_STAGE2.read_text(encoding="utf-8")
    background_text = FIXTURE_BACKGROUND.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "cl_stage1_draft.txt"
        run_cl_stage1(client, jd_text, resume_text, background_text, str(output_path))
        content = output_path.read_text(encoding="utf-8")
        assert "Dear" in content or "Hiring" in content or len(content) > 50


def test_revise_cover_letter_returns_parsed_sections():
    from scripts.phase4_cover_letter import revise_cover_letter
    revision_response = (
        "## SECTION 1\nRevised traditional letter body.\n\n"
        "## SECTION 2\nRevised application paragraph body."
    )
    client = make_mock_client(revision_response)

    revised1, revised2 = revise_cover_letter(client, "Draft section 1.", "Draft section 2.")

    assert revised1 == "Revised traditional letter body."
    assert revised2 == "Revised application paragraph body."


def test_revise_cover_letter_raises_on_missing_markers():
    from scripts.phase4_cover_letter import revise_cover_letter
    client = make_mock_client("No section markers in this response.")

    with pytest.raises(ValueError):
        revise_cover_letter(client, "Draft section 1.", "Draft section 2.")


def test_run_cl_stage1_writes_revised_not_draft_text():
    from scripts.phase4_cover_letter import run_cl_stage1
    client = make_sequential_mock_client([
        "Hiring Manager",
        "Draft traditional letter text.",
        "Draft application paragraph text.",
        "## SECTION 1\nRevised traditional letter text.\n\n"
        "## SECTION 2\nRevised application paragraph text.",
    ])
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")
    resume_text = FIXTURE_STAGE2.read_text(encoding="utf-8")
    background_text = FIXTURE_BACKGROUND.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "cl_stage1_draft.txt"
        run_cl_stage1(client, jd_text, resume_text, background_text, str(output_path))
        content = output_path.read_text(encoding="utf-8")

    assert "Revised traditional letter text." in content
    assert "Revised application paragraph text." in content
    assert "Draft traditional letter text." not in content
    assert "Draft application paragraph text." not in content


def test_run_cl_stage4_creates_readable_docx():
    from scripts.phase4_cover_letter import run_cl_stage4
    cl_text = MOCK_CL_RESPONSE

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_cover_letter.docx"
        run_cl_stage4(cl_text, str(output_path))
        assert output_path.exists()
        doc = Document(str(output_path))
        assert len(doc.paragraphs) > 0


def test_no_module_level_execution_on_import():
    import scripts.phase4_cover_letter  # noqa: F401


@pytest.mark.live
def test_run_cl_stage1_live():
    """Tier 2: real API call."""
    import os
    from anthropic import Anthropic
    from scripts.phase4_cover_letter import run_cl_stage1

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")
    resume_text = FIXTURE_STAGE2.read_text(encoding="utf-8")
    background_text = FIXTURE_BACKGROUND.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "cl_stage1_draft.txt"
        run_cl_stage1(client, jd_text, resume_text, background_text, str(output_path))
        content = output_path.read_text(encoding="utf-8")
        assert "Acme" in content or len(content) > 200
