# tests/phase5/test_gap_prompt_ground_truth.py
#
# Regression tests for the phase5 gap-prompt ground-truth defects (Jul 2026):
#   - the gap prompt truncated candidate_profile to its first 2,000 characters,
#     so the confirmed-skills guardrail referenced sections that never reached
#     the model (false "no people management" / "Cameo not confirmed" output)
#   - the CONFIRMED GAPS extraction searched for headers that do not exist in
#     candidate_profile.md and silently returned ""
#   - seed-tailoring instructions allowed the model to alter deliberately
#     worded qualifiers in vetted library text ("some" became "Several")
#
# Principle these tests encode: any prompt guardrail must have a test asserting
# that the content it references is actually present in the assembled prompt.

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

FIXTURE_JD = Path(__file__).parent.parent / "fixtures" / "stage_files" / "sample_jd.txt"
FIXTURE_STAGE2 = Path(__file__).parent.parent / "fixtures" / "stage_files" / "stage2_approved.txt"
FIXTURE_LIBRARY = Path(__file__).parent.parent / "fixtures" / "library" / "experience_library.json"

# Must match the protected-content clause added to the seed instructions in
# _build_section2_prompt and _build_gap_prompt.
PROTECTED_CLAUSE = "do not alter quantities, numbers, scope qualifiers"

MOCK_RESPONSE = "## SECTION\nMock content for all sections.\n"


def make_mock_client(response_text=MOCK_RESPONSE):
    client = MagicMock()
    client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=response_text)]
    )
    return client


def _filler(n):
    """Deterministic filler text used to push sections past a character offset."""
    line = "Filler line used only to pad character offsets in this fixture.\n"
    return line * (n // len(line) + 1)


def make_fixture_profile():
    """Jane Q. Applicant profile with the confirmed-skills table row and the
    leadership section deliberately placed PAST character 2,000 -- mirroring the
    real profile layout that exposed the truncation defect."""
    profile = (
        "# Candidate Profile\n\n"
        "## IDENTITY & CONTACT\n"
        "Jane Q. Applicant -- Anytown, USA\n\n"
        "## CAREER SUMMARY\n"
        + _filler(2400)
        + "\n## CONFIRMED SKILLS BY CATEGORY\n\n"
        "### MBSE & Architecture Tools\n\n"
        "| Tool | Depth |\n"
        "|------|-------|\n"
        "| Cameo Systems Modeler (MagicDraw) | **Proficient** -- deployed "
        "enterprise SysML environments |\n"
        + _filler(1000)
        + "\n### Leadership & Stakeholder Management\n"
        "- Built and led an eight-person MBSE team -- hired, mentored, "
        "managed workload\n"
        "\n## INTRO MONOLOGUE\nHello, I am Jane.\n"
    )
    # Layout invariants the regression depends on
    assert profile.index("CONFIRMED SKILLS BY CATEGORY") > 2000
    assert profile.index("Leadership & Stakeholder Management") > 2000
    return profile


# ---- Fix 1: no profile truncation in the gap prompt ----

def test_gap_prompt_contains_profile_content_past_2000_chars():
    """The guardrail tells the model confirmed skills are not gaps -- so the
    confirmed-skills content must actually be present in the assembled prompt,
    wherever it sits in the profile."""
    from scripts.phase5_interview_prep import _build_gap_prompt, STAGE_PROFILES

    prompt = _build_gap_prompt(
        "JD text", "", make_fixture_profile(),
        STAGE_PROFILES["hiring_manager"], library_seeds=None,
    )
    assert "Cameo Systems Modeler (MagicDraw)" in prompt, (
        "Confirmed-skills table row past char 2,000 missing from gap prompt -- "
        "profile truncation has been reintroduced"
    )
    assert "Leadership & Stakeholder Management" in prompt, (
        "Leadership section past char 2,000 missing from gap prompt -- "
        "profile truncation has been reintroduced"
    )


def test_gap_prompt_gaps_section_not_truncated():
    from scripts.phase5_interview_prep import _build_gap_prompt, STAGE_PROFILES

    gaps = "GAP LIST START\n" + _filler(1600) + "FINAL GAP MARKER"
    prompt = _build_gap_prompt(
        "JD text", gaps, "profile",
        STAGE_PROFILES["hiring_manager"], library_seeds=None,
    )
    assert "FINAL GAP MARKER" in prompt, (
        "gaps_section content past char 1,500 missing from gap prompt"
    )


def test_generate_prep_gap_api_call_receives_full_profile(monkeypatch, tmp_path):
    """End-to-end guard: the truncation must not be reintroduced at the
    generate_prep call site either."""
    import scripts.interview_library_parser as ilp
    import scripts.phase5_debrief_utils as dbu
    from scripts.phase5_interview_prep import generate_prep

    monkeypatch.setattr(ilp, "load_tags", lambda: [])
    monkeypatch.setattr(ilp, "get_stories", lambda **kw: [])
    monkeypatch.setattr(ilp, "get_gap_responses", lambda **kw: [])
    monkeypatch.setattr(ilp, "get_questions", lambda **kw: [])
    monkeypatch.setattr(dbu, "load_all_debriefs", lambda: [])
    monkeypatch.setattr(dbu, "load_debriefs", lambda role: [])

    client = make_mock_client()
    role_data = {
        "jd_text": FIXTURE_JD.read_text(encoding="utf-8"),
        "stage_text": FIXTURE_STAGE2.read_text(encoding="utf-8"),
        "library": json.loads(FIXTURE_LIBRARY.read_text(encoding="utf-8")),
        "candidate_profile": make_fixture_profile(),
        "role_name": "jane_q_test",
    }
    generate_prep(client, role_data, "hiring_manager",
                  str(tmp_path / "p.txt"), str(tmp_path / "p.docx"))

    # hiring_manager call order: S1=0, S1.5=1 (fixture has INTRO MONOLOGUE),
    # S2=2, S3 (gap)=3, S4=4
    gap_prompt = client.messages.create.call_args_list[3].kwargs["messages"][0]["content"]
    assert "Cameo Systems Modeler (MagicDraw)" in gap_prompt
    assert "Leadership & Stakeholder Management" in gap_prompt


# ---- Fix 2: gaps-section extraction is optional but loud ----

def test_missing_gaps_section_emits_named_warning(capsys):
    from scripts.phase5_interview_prep import _extract_gaps_section

    result = _extract_gaps_section("## OTHER SECTION\nStuff.\n")
    captured = capsys.readouterr()
    assert result == ""
    assert "WARNING" in captured.out
    assert "CONFIRMED GAPS" in captured.out, (
        "Empty extraction must be announced by name, never returned silently"
    )


def test_gaps_section_extracted_when_present_any_header_case(capsys):
    from scripts.phase5_interview_prep import _extract_gaps_section

    text = (
        "## Confirmed Gaps\n- No GitLab (GitHub only)\n\n"
        "## Confirmed Clearance\nCurrent TS/SCI\n"
    )
    result = _extract_gaps_section(text)
    captured = capsys.readouterr()
    assert "No GitLab" in result
    assert "TS/SCI" not in result, "Extraction must stop at the next ## header"
    assert "WARNING" not in captured.out


# ---- Fix 3: protected-content clause for seeded library text ----

def test_section2_seed_instructions_protect_seeded_wording():
    from scripts.phase5_interview_prep import _build_section2_prompt, STAGE_PROFILES

    seeds = [{
        "id": "story_001", "employer": "Talon Dynamics", "title": "Lead SE",
        "dates": "2022-2024", "situation": "Led MBSE for some subsystems.",
        "task": "Build OV-1.", "action": "Facilitated IPT.",
        "result": "Delivered baseline.", "tags": ["mbse"], "if_probed": None,
    }]
    prompt = _build_section2_prompt("JD text", "story context", "profile",
                                    STAGE_PROFILES["hiring_manager"],
                                    library_seeds=seeds)
    assert PROTECTED_CLAUSE in prompt
    assert "some / several / all / most / a few" in prompt
    # Existing verbatim-Performance-line rule must be unchanged
    assert "reproduce it verbatim on the next line" in prompt


def test_section2_prompt_contains_profile_content_past_2500_chars():
    """Section 2's Role Fit Assessment asserts facts about the candidate, so the
    full profile must reach the assembled prompt -- the [:2500] slice produced a
    live self-contradiction (Role Fit denied leadership the gap analysis
    confirmed from the same profile)."""
    from scripts.phase5_interview_prep import _build_section2_prompt, STAGE_PROFILES

    profile_text = make_fixture_profile()
    assert profile_text.index("CONFIRMED SKILLS BY CATEGORY") > 2500
    assert profile_text.index("Leadership & Stakeholder Management") > 2500

    prompt = _build_section2_prompt("JD text", "story context", profile_text,
                                    STAGE_PROFILES["hiring_manager"],
                                    library_seeds=None)
    assert "Cameo Systems Modeler (MagicDraw)" in prompt, (
        "Confirmed-skills row past char 2,500 missing from section-2 prompt -- "
        "profile truncation has been reintroduced"
    )
    assert "Leadership & Stakeholder Management" in prompt, (
        "Leadership section past char 2,500 missing from section-2 prompt -- "
        "profile truncation has been reintroduced"
    )


# ---- output-side truncation: stop_reason and gap-count completeness ----

class _FakeResponse:
    def __init__(self, stop_reason):
        self.stop_reason = stop_reason


def test_max_tokens_stop_reason_fires_warning(capsys):
    from scripts.phase5_interview_prep import _warn_if_incomplete

    _warn_if_incomplete(_FakeResponse("max_tokens"), "Section 3 (gap preparation)")
    captured = capsys.readouterr()
    assert "WARNING" in captured.out
    assert "max_tokens" in captured.out
    assert "Section 3 (gap preparation)" in captured.out


def test_normal_stop_reason_no_warning(capsys):
    from scripts.phase5_interview_prep import _warn_if_incomplete

    _warn_if_incomplete(_FakeResponse("end_turn"), "Section 2 (story bank)")
    assert "WARNING" not in capsys.readouterr().out


def test_gap_completeness_warning_when_rendered_below_declared(capsys):
    from scripts.phase5_interview_prep import _check_gap_completeness

    text = (
        "I identified 5 gaps between the JD and the candidate profile.\n\n"
        "GAP 1 -- DRM Development [REQUIRED]:\n"
        "Gap: JD requires DRM development and the profile does not name"
    )
    _check_gap_completeness(text)
    captured = capsys.readouterr()
    assert "WARNING" in captured.out
    assert "5" in captured.out and "1" in captured.out
    assert "incomplete" in captured.out


def test_gap_completeness_no_warning_when_counts_match(capsys):
    from scripts.phase5_interview_prep import _check_gap_completeness

    text = (
        "I identified 2 gaps.\n\n"
        "GAP 1 -- Topic A [REQUIRED]:\nGap: a\n\n"
        "GAP 2 -- Topic B [PREFERRED]:\nGap: b\n"
    )
    _check_gap_completeness(text)
    assert "WARNING" not in capsys.readouterr().out


def test_gap_completeness_no_warning_without_declared_count(capsys):
    from scripts.phase5_interview_prep import _check_gap_completeness

    _check_gap_completeness("GAP 1 -- Topic [REQUIRED]:\nGap: a\n")
    assert "WARNING" not in capsys.readouterr().out


def test_gap_seed_instructions_protect_seeded_wording():
    from scripts.phase5_interview_prep import _build_gap_prompt, STAGE_PROFILES

    seeds = [{
        "id": "gap_001", "gap_label": "no SCIF experience",
        "severity": "REQUIRED", "honest_answer": "I have not worked in SCIF.",
        "bridge": "Worked TS cleared.", "redirect": "Adapt quickly.",
        "tags": ["clearance"],
    }]
    prompt = _build_gap_prompt("JD text", "gaps text", "profile",
                               STAGE_PROFILES["hiring_manager"],
                               library_seeds=seeds)
    assert PROTECTED_CLAUSE in prompt
    assert "reproduce it verbatim on the next line" in prompt
