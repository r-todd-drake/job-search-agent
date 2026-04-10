# tests/phase5/test_interview_prep.py

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from docx import Document

FIXTURE_JD = Path(__file__).parent.parent / "fixtures" / "stage_files" / "sample_jd.txt"
FIXTURE_STAGE2 = Path(__file__).parent.parent / "fixtures" / "stage_files" / "stage2_approved.txt"
FIXTURE_LIBRARY = Path(__file__).parent.parent / "fixtures" / "library" / "experience_library.json"
FIXTURE_PROFILE = Path(__file__).parent.parent / "fixtures" / "library" / "candidate_profile.md"

MOCK_PREP_RESPONSE = """## SECTION 1: COMPANY & ROLE BRIEF
Acme Defense Systems is a defense contractor focused on autonomous maritime systems.
Role: Senior Systems Engineer supporting MBSE and DoDAF development.
Salary guidance: $150,000 - $180,000.

## SECTION 1.5: INTRODUCE YOURSELF
I am a senior systems engineer with 20 years of defense SE experience.
I specialize in MBSE and DoDAF architectural development.

## SECTION 2: STORY BANK
STAR Story 1 - MBSE Leadership
Situation: Led MBSE development for autonomous surface vessel program.
Task: Develop DoDAF architectural views using Cameo Systems Modeler.
Action: Facilitated IPT working groups with government stakeholders.
Result: Delivered system-of-systems architecture supporting multi-domain C2 integration.

STAR Story 2 - Stakeholder Engagement
Situation: Government stakeholder alignment required for requirements definition.
Task: Define operational requirements and ConOps.
Action: Conducted workshops and facilitated reviews.
Result: Approved ConOps baseline.

STAR Story 3 - Architecture Integration
Situation: System integration complexity.
Task: Develop integration architecture.
Action: Applied DoDAF SV views.
Result: Successful integration milestone.

## SECTION 3: GAP PREPARATION
REQUIRED: All required qualifications met.
PREFERRED: JADC2 experience limited -- acknowledge and reframe.

## SECTION 4: QUESTIONS TO ASK
1. What is the acquisition phase for this program?
2. How is MBSE integrated into the program baseline?
"""


def make_mock_client(response_text):
    client = MagicMock()
    client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=response_text)]
    )
    return client


def make_role_data():
    return {
        "jd_text": FIXTURE_JD.read_text(encoding="utf-8"),
        "stage_text": FIXTURE_STAGE2.read_text(encoding="utf-8"),
        "library": json.loads(FIXTURE_LIBRARY.read_text(encoding="utf-8")),
        "candidate_profile": FIXTURE_PROFILE.read_text(encoding="utf-8"),
        "role_name": "acme_sse",
    }


def test_generate_prep_creates_both_output_files():
    from scripts.phase5_interview_prep import generate_prep

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = make_role_data()

    with tempfile.TemporaryDirectory() as tmpdir:
        txt_path = Path(tmpdir) / "interview_prep_hiring_manager.txt"
        docx_path = Path(tmpdir) / "interview_prep_hiring_manager.docx"
        generate_prep(client, role_data, "hiring_manager", str(txt_path), str(docx_path))
        assert txt_path.exists()
        assert docx_path.exists()


def test_generate_prep_txt_has_required_sections():
    from scripts.phase5_interview_prep import generate_prep

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = make_role_data()

    with tempfile.TemporaryDirectory() as tmpdir:
        txt_path = Path(tmpdir) / "interview_prep_hiring_manager.txt"
        docx_path = Path(tmpdir) / "interview_prep_hiring_manager.docx"
        generate_prep(client, role_data, "hiring_manager", str(txt_path), str(docx_path))
        content = txt_path.read_text(encoding="utf-8")

    assert "COMPANY" in content or "BRIEF" in content
    assert "STORY" in content or "STAR" in content
    assert "GAP" in content
    assert "QUESTION" in content


def test_generate_prep_star_stories_reference_resume_content():
    from scripts.phase5_interview_prep import generate_prep

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = make_role_data()

    with tempfile.TemporaryDirectory() as tmpdir:
        txt_path = Path(tmpdir) / "interview_prep_hiring_manager.txt"
        docx_path = Path(tmpdir) / "interview_prep_hiring_manager.docx"
        generate_prep(client, role_data, "hiring_manager", str(txt_path), str(docx_path))
        content = txt_path.read_text(encoding="utf-8")

    assert "Cameo Systems Modeler" in content or "MBSE" in content


def test_generate_prep_no_pii_in_api_payload(pii_values, monkeypatch):
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

    from scripts.phase5_interview_prep import generate_prep

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = make_role_data()
    role_data["stage_text"] = (
        f"Contact: {pii_values['name']} | {pii_values['email']}\n"
        + role_data["stage_text"]
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        txt_path = Path(tmpdir) / "interview_prep_hiring_manager.txt"
        docx_path = Path(tmpdir) / "interview_prep_hiring_manager.docx"
        generate_prep(client, role_data, "hiring_manager", str(txt_path), str(docx_path))

    call_args = client.messages.create.call_args
    full_payload = str(call_args)
    for pii_value in pii_values.values():
        assert pii_value not in full_payload, f"PII found in payload: {pii_value}"


def test_generate_prep_docx_readable():
    from scripts.phase5_interview_prep import generate_prep

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = make_role_data()

    with tempfile.TemporaryDirectory() as tmpdir:
        txt_path = Path(tmpdir) / "interview_prep_hiring_manager.txt"
        docx_path = Path(tmpdir) / "interview_prep_hiring_manager.docx"
        generate_prep(client, role_data, "hiring_manager", str(txt_path), str(docx_path))
        doc = Document(str(docx_path))
        assert len(doc.paragraphs) > 0


def test_no_module_level_execution_on_import():
    import scripts.phase5_interview_prep  # noqa: F401


def test_stage_profile_has_required_keys():
    from scripts.phase5_interview_prep import STAGE_PROFILES, VALID_STAGES

    required_keys = {
        "label", "description", "story_count", "story_depth",
        "gap_behavior", "salary_in_section1", "section1_focus", "questions_prompt",
    }
    assert set(VALID_STAGES) == {"recruiter", "hiring_manager", "team_panel"}
    for stage, profile in STAGE_PROFILES.items():
        missing = required_keys - profile.keys()
        assert not missing, f"Stage '{stage}' missing keys: {missing}"
    assert "peer_frame_prompt" in STAGE_PROFILES["team_panel"]
    assert STAGE_PROFILES["recruiter"]["gap_behavior"] == "omit"
    assert STAGE_PROFILES["hiring_manager"]["salary_in_section1"] is True
    assert STAGE_PROFILES["team_panel"]["story_depth"] == "full_technical"
    for stage, profile in STAGE_PROFILES.items():
        assert "{jd}" in profile["questions_prompt"], \
            f"Stage '{stage}' questions_prompt missing {{jd}} placeholder"
        assert "{profile_summary}" in profile["questions_prompt"], \
            f"Stage '{stage}' questions_prompt missing {{profile_summary}} placeholder"


@pytest.mark.live
def test_generate_prep_live():
    """Tier 2: real API call with web search."""
    import os
    from anthropic import Anthropic
    from scripts.phase5_interview_prep import generate_prep

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    role_data = make_role_data()
    role_data["role_name"] = "acme_sse_test"

    with tempfile.TemporaryDirectory() as tmpdir:
        txt_path = Path(tmpdir) / "interview_prep_hiring_manager.txt"
        docx_path = Path(tmpdir) / "interview_prep_hiring_manager.docx"
        generate_prep(client, role_data, "hiring_manager", str(txt_path), str(docx_path))
        content = txt_path.read_text(encoding="utf-8")

    assert len(content) > 500
    assert "STAR" in content or "Story" in content
    assert "GAP" in content or "Gap" in content
