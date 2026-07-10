import json
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch


# --- fixtures ---

def _make_debrief(role="test_role", stage="hiring_manager", date="2026-04-10",
                  panel_label=None, interviewers=None, advancement="maybe",
                  stories=None, gaps=None, salary=None, what_i_said=None):
    return {
        "metadata": {
            "role": role, "stage": stage, "interview_date": date,
            "panel_label": panel_label,
            "interviewers": interviewers or [{"name": "Jane Smith", "title": "CE", "notes": ""}],
        },
        "advancement_read": {"assessment": advancement, "notes": ""},
        "stories_used": stories or [],
        "gaps_surfaced": gaps or [],
        "salary_exchange": salary or {},
        "what_i_said": what_i_said,
        "open_notes": None,
    }


def _write_debriefs(tmpdir, role, debriefs):
    role_dir = os.path.join(tmpdir, role)
    os.makedirs(role_dir, exist_ok=True)
    paths = []
    for i, d in enumerate(debriefs):
        p = os.path.join(role_dir, f"debrief_{i}.json")
        with open(p, "w") as f:
            json.dump(d, f)
        paths.append(p)
    return paths


# --- load_debriefs ---

def test_load_debriefs_absent_dir_returns_empty():
    from scripts.phase5_debrief_utils import load_debriefs
    with patch("scripts.phase5_debrief_utils.DEBRIEFS_DIR", "/nonexistent/path/xyz"):
        result = load_debriefs("any_role")
    assert result == []


def test_load_debriefs_returns_sorted_by_date():
    from scripts.phase5_debrief_utils import load_debriefs
    d1 = _make_debrief(date="2026-04-15")
    d2 = _make_debrief(date="2026-04-10")
    with tempfile.TemporaryDirectory() as tmp:
        _write_debriefs(tmp, "my_role", [d1, d2])
        with patch("scripts.phase5_debrief_utils.DEBRIEFS_DIR", tmp):
            result = load_debriefs("my_role")
    assert len(result) == 2
    assert result[0]["metadata"]["interview_date"] == "2026-04-10"
    assert result[1]["metadata"]["interview_date"] == "2026-04-15"


def test_load_debriefs_skips_invalid_json():
    from scripts.phase5_debrief_utils import load_debriefs
    with tempfile.TemporaryDirectory() as tmp:
        role_dir = os.path.join(tmp, "my_role")
        os.makedirs(role_dir)
        with open(os.path.join(role_dir, "bad.json"), "w") as f:
            f.write("not json {{{")
        with open(os.path.join(role_dir, "good.json"), "w") as f:
            json.dump(_make_debrief(), f)
        with patch("scripts.phase5_debrief_utils.DEBRIEFS_DIR", tmp):
            result = load_debriefs("my_role")
    assert len(result) == 1


# --- load_all_debriefs ---

def test_load_all_debriefs_absent_dir_returns_empty():
    from scripts.phase5_debrief_utils import load_all_debriefs
    with patch("scripts.phase5_debrief_utils.DEBRIEFS_DIR", "/nonexistent/xyz"):
        result = load_all_debriefs()
    assert result == []


def test_load_all_debriefs_combines_roles():
    from scripts.phase5_debrief_utils import load_all_debriefs
    with tempfile.TemporaryDirectory() as tmp:
        _write_debriefs(tmp, "role_a", [_make_debrief(role="role_a")])
        _write_debriefs(tmp, "role_b", [_make_debrief(role="role_b")])
        with patch("scripts.phase5_debrief_utils.DEBRIEFS_DIR", tmp):
            result = load_all_debriefs()
    assert len(result) == 2


# --- get_story_performance_signal ---

def test_story_signal_none_when_no_library_id():
    from scripts.phase5_debrief_utils import get_story_performance_signal
    assert get_story_performance_signal(None, []) is None
    assert get_story_performance_signal("", []) is None


def test_story_signal_none_when_no_match():
    from scripts.phase5_debrief_utils import get_story_performance_signal
    d = _make_debrief(stories=[{"library_id": "other_id", "landed": "yes", "tags": []}])
    assert get_story_performance_signal("story_001", [d]) is None


def test_story_signal_counts_correctly():
    from scripts.phase5_debrief_utils import get_story_performance_signal
    debriefs = [
        _make_debrief(stories=[{"library_id": "story_001", "landed": "yes", "tags": []}]),
        _make_debrief(stories=[{"library_id": "story_001", "landed": "yes", "tags": []}]),
        _make_debrief(stories=[{"library_id": "story_001", "landed": "partially", "tags": []}]),
    ]
    result = get_story_performance_signal("story_001", debriefs)
    assert "3 times" in result
    assert "yes x2" in result
    assert "partially x1" in result


# --- get_gap_performance_signal ---

def test_gap_signal_none_when_no_label():
    from scripts.phase5_debrief_utils import get_gap_performance_signal
    assert get_gap_performance_signal(None, []) is None
    assert get_gap_performance_signal("", []) is None


def test_gap_signal_case_insensitive_match():
    from scripts.phase5_debrief_utils import get_gap_performance_signal
    d = _make_debrief(gaps=[{"gap_label": "No SCIF Experience", "response_felt": "strong"}])
    result = get_gap_performance_signal("no scif experience", [d])
    assert result is not None
    assert "strong x1" in result


def test_gap_signal_counts_multiple():
    from scripts.phase5_debrief_utils import get_gap_performance_signal
    debriefs = [
        _make_debrief(gaps=[{"gap_label": "no scif", "response_felt": "adequate"}]),
        _make_debrief(gaps=[{"gap_label": "no scif", "response_felt": "adequate"}]),
        _make_debrief(gaps=[{"gap_label": "no scif", "response_felt": "weak"}]),
    ]
    result = get_gap_performance_signal("no scif", debriefs)
    assert "3 times" in result
    assert "adequate x2" in result
    assert "weak x1" in result


# --- load_salary_actuals ---

def test_salary_actuals_returns_none_when_no_debriefs():
    from scripts.phase5_debrief_utils import load_salary_actuals
    assert load_salary_actuals([]) is None


def test_salary_actuals_returns_none_when_no_salary_data():
    from scripts.phase5_debrief_utils import load_salary_actuals
    d = _make_debrief()  # empty salary_exchange
    assert load_salary_actuals([d]) is None


def test_salary_actuals_returns_most_recent():
    from scripts.phase5_debrief_utils import load_salary_actuals
    old = _make_debrief(date="2026-04-01",
                        salary={"range_given_min": 130000, "range_given_max": 160000})
    recent = _make_debrief(date="2026-04-15",
                           salary={"range_given_min": 145000, "range_given_max": 175000})
    result = load_salary_actuals([old, recent])
    assert result["range_given_min"] == 145000
    assert result["range_given_max"] == 175000


def test_salary_actuals_includes_stage_and_date():
    from scripts.phase5_debrief_utils import load_salary_actuals
    d = _make_debrief(date="2026-04-15", stage="hiring_manager",
                      salary={"range_given_min": 145000, "range_given_max": 175000})
    result = load_salary_actuals([d])
    assert result["interview_date"] == "2026-04-15"
    assert result["stage"] == "hiring_manager"


# --- build_continuity_section ---

def test_continuity_section_empty_when_no_debriefs():
    from scripts.phase5_debrief_utils import build_continuity_section
    assert build_continuity_section([]) == ""


def test_continuity_section_contains_stage_and_date():
    from scripts.phase5_debrief_utils import build_continuity_section
    d = _make_debrief(stage="hiring_manager", date="2026-04-15")
    result = build_continuity_section([d])
    assert "hiring_manager" in result
    assert "2026-04-15" in result
    assert "CONTINUITY SUMMARY" in result


def test_continuity_section_includes_panel_label():
    from scripts.phase5_debrief_utils import build_continuity_section
    d = _make_debrief(stage="team_panel", panel_label="se_team", date="2026-04-16")
    result = build_continuity_section([d])
    assert "se_team" in result


def test_continuity_section_shows_interviewers():
    from scripts.phase5_debrief_utils import build_continuity_section
    d = _make_debrief(interviewers=[
        {"name": "Alice", "title": "Chief Engineer", "notes": ""},
        {"name": "Bob", "title": "Systems Lead", "notes": ""},
    ])
    result = build_continuity_section([d])
    assert "Alice" in result
    assert "Bob" in result
    assert "Chief Engineer" in result


def test_continuity_section_no_what_i_said_placeholder():
    from scripts.phase5_debrief_utils import build_continuity_section
    d = _make_debrief(what_i_said=None)
    result = build_continuity_section([d])
    assert "no continuity data captured" in result


def test_continuity_section_shows_what_i_said():
    from scripts.phase5_debrief_utils import build_continuity_section
    d = _make_debrief(what_i_said="Said I prefer hybrid. Active TS/SCI.")
    result = build_continuity_section([d])
    assert "Said I prefer hybrid" in result


def test_continuity_section_multiple_debriefs_sorted():
    from scripts.phase5_debrief_utils import build_continuity_section
    d1 = _make_debrief(stage="recruiter", date="2026-04-01")
    d2 = _make_debrief(stage="hiring_manager", date="2026-04-15")
    result = build_continuity_section([d1, d2])
    assert result.index("recruiter") < result.index("hiring_manager")


# --- find_unmatched_debrief_content ---

def test_unmatched_empty_when_no_debriefs():
    from scripts.phase5_debrief_utils import find_unmatched_debrief_content
    stories, gaps = find_unmatched_debrief_content([])
    assert stories == []
    assert gaps == []


def test_unmatched_story_not_in_library():
    from scripts.phase5_debrief_utils import find_unmatched_debrief_content
    d = _make_debrief(stories=[{"library_id": "missing_id", "tags": ["mbse"], "landed": "yes"}])
    with patch("scripts.interview_library_parser._load_library",
               return_value={"stories": [], "gap_responses": [], "questions": []}):
        stories, gaps = find_unmatched_debrief_content([d])
    assert len(stories) == 1
    assert stories[0]["library_id"] == "missing_id"


def test_matched_story_not_in_unmatched():
    from scripts.phase5_debrief_utils import find_unmatched_debrief_content
    d = _make_debrief(stories=[{"library_id": "story_001", "tags": [], "landed": "yes"}])
    with patch("scripts.interview_library_parser._load_library",
               return_value={"stories": [{"id": "story_001"}], "gap_responses": [], "questions": []}):
        stories, _ = find_unmatched_debrief_content([d])
    assert stories == []


def test_unmatched_gap_not_in_library():
    from scripts.phase5_debrief_utils import find_unmatched_debrief_content
    d = _make_debrief(gaps=[{"gap_label": "no drone experience", "response_felt": "adequate"}])
    with patch("scripts.interview_library_parser._load_library",
               return_value={"stories": [], "gap_responses": [], "questions": []}):
        _, gaps = find_unmatched_debrief_content([d])
    assert "no drone experience" in gaps


def test_unmatched_deduplicates_across_debriefs():
    from scripts.phase5_debrief_utils import find_unmatched_debrief_content
    d1 = _make_debrief(stories=[{"library_id": "missing_id", "tags": [], "landed": "yes"}])
    d2 = _make_debrief(stories=[{"library_id": "missing_id", "tags": [], "landed": "yes"}])
    with patch("scripts.interview_library_parser._load_library",
               return_value={"stories": [], "gap_responses": [], "questions": []}):
        stories, _ = find_unmatched_debrief_content([d1, d2])
    assert len(stories) == 1


# --- has_debrief_for_stage ---

def test_has_debrief_for_stage_true():
    from scripts.phase5_debrief_utils import has_debrief_for_stage
    d = _make_debrief(stage="hiring_manager")
    assert has_debrief_for_stage([d], "hiring_manager") is True


def test_has_debrief_for_stage_false():
    from scripts.phase5_debrief_utils import has_debrief_for_stage
    d = _make_debrief(stage="recruiter")
    assert has_debrief_for_stage([d], "hiring_manager") is False


def test_has_debrief_for_stage_panel_label_match():
    from scripts.phase5_debrief_utils import has_debrief_for_stage
    d = _make_debrief(stage="team_panel", panel_label="se_team")
    assert has_debrief_for_stage([d], "team_panel", panel_label="se_team") is True


def test_has_debrief_for_stage_panel_label_no_match():
    from scripts.phase5_debrief_utils import has_debrief_for_stage
    d = _make_debrief(stage="team_panel", panel_label="se_team")
    assert has_debrief_for_stage([d], "team_panel", panel_label="biz_leaders") is False


def test_has_debrief_for_stage_empty_list():
    from scripts.phase5_debrief_utils import has_debrief_for_stage
    assert has_debrief_for_stage([], "hiring_manager") is False
