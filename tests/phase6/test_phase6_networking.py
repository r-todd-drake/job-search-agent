import pytest
import sys
import os
from openpyxl import Workbook
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import scripts.phase6_networking as pn
from tests.fixtures.contact_fixture import COLD, ACQUAINTANCE, FORMER_COLLEAGUE, STRONG, ALL_VARIANTS

COLUMNS = [
    "contact_name", "company", "title", "linkedin_url", "warmth",
    "source", "first_contact", "response_date", "stage", "status",
    "role_activated", "referral_bonus", "notes",
]


def _make_xlsx(tmp_path, rows=None):
    """Write fixture rows to a temporary xlsx and return its path."""
    if rows is None:
        rows = ALL_VARIANTS
    path = tmp_path / "contact_pipeline.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.append(COLUMNS)
    for row in rows:
        ws.append([row.get(c) for c in COLUMNS])
    wb.save(path)
    return str(path)


# ==============================================
# load_contacts
# ==============================================

def test_load_contacts_returns_list_of_dicts(tmp_path):
    path = _make_xlsx(tmp_path)
    contacts = pn.load_contacts(path)
    assert isinstance(contacts, list)
    assert len(contacts) == 4
    assert contacts[0]["contact_name"] == "Jane Q. Applicant"
    assert contacts[0]["warmth"] == "Cold"


def test_load_contacts_all_columns_present(tmp_path):
    path = _make_xlsx(tmp_path)
    contacts = pn.load_contacts(path)
    for col in COLUMNS:
        assert col in contacts[0]


# ==============================================
# find_contact
# ==============================================

def test_find_contact_exact_match(tmp_path):
    path = _make_xlsx(tmp_path)
    contacts = pn.load_contacts(path)
    result = pn.find_contact(contacts, "Jane Q. Applicant")
    assert result["contact_name"] == "Jane Q. Applicant"


def test_find_contact_case_insensitive(tmp_path):
    path = _make_xlsx(tmp_path)
    contacts = pn.load_contacts(path)
    result = pn.find_contact(contacts, "jane q. applicant")
    assert result["contact_name"] == "Jane Q. Applicant"


def test_find_contact_partial_match(tmp_path):
    path = _make_xlsx(tmp_path, rows=[COLD])
    contacts = pn.load_contacts(path)
    result = pn.find_contact(contacts, "Jane")
    assert result["contact_name"] == "Jane Q. Applicant"


def test_find_contact_ambiguous_raises(tmp_path):
    rows = [
        {**COLD, "contact_name": "Jane Smith"},
        {**COLD, "contact_name": "Jane Doe"},
    ]
    path = _make_xlsx(tmp_path, rows=rows)
    contacts = pn.load_contacts(str(path))
    with pytest.raises(ValueError, match="ambiguous"):
        pn.find_contact(contacts, "Jane")


def test_find_contact_not_found_raises(tmp_path):
    path = _make_xlsx(tmp_path)
    contacts = pn.load_contacts(path)
    with pytest.raises(ValueError, match="not found"):
        pn.find_contact(contacts, "Nonexistent Person")


# ==============================================
# update_contact
# ==============================================

def test_update_contact_stage1_advances_stage_and_sets_first_contact(tmp_path):
    from datetime import date
    path = _make_xlsx(tmp_path, rows=[COLD])
    pn.update_contact(str(path), "Jane Q. Applicant", {"stage": 2, "first_contact": date(2026, 4, 26)})
    contacts = pn.load_contacts(str(path))
    assert contacts[0]["stage"] == 2
    assert contacts[0]["first_contact"] == date(2026, 4, 26)


def test_update_contact_stage2_sets_role_activated(tmp_path):
    path = _make_xlsx(tmp_path, rows=[COLD])
    pn.update_contact(str(path), "Jane Q. Applicant", {"stage": 3, "role_activated": "acme-systems-se"})
    contacts = pn.load_contacts(str(path))
    assert contacts[0]["stage"] == 3
    assert contacts[0]["role_activated"] == "acme-systems-se"


def test_update_contact_never_writes_response_date(tmp_path):
    from datetime import date
    path = _make_xlsx(tmp_path, rows=[COLD])
    pn.update_contact(str(path), "Jane Q. Applicant", {"stage": 2, "first_contact": date(2026, 4, 26)})
    contacts = pn.load_contacts(str(path))
    assert contacts[0]["response_date"] is None


def test_update_contact_stage4_sets_status_closed(tmp_path):
    path = _make_xlsx(tmp_path, rows=[COLD])
    pn.update_contact(str(path), "Jane Q. Applicant", {"status": "Closed"})
    contacts = pn.load_contacts(str(path))
    assert contacts[0]["status"] == "Closed"


# ==============================================
# list_contacts
# ==============================================

def test_list_contacts_sorted_by_stage(tmp_path, capsys):
    rows = [
        {**COLD, "contact_name": "Alpha", "stage": 3, "status": "Active", "role_activated": None},
        {**COLD, "contact_name": "Beta", "stage": 1, "status": "Active", "role_activated": None},
    ]
    path = _make_xlsx(tmp_path, rows=rows)
    contacts = pn.load_contacts(str(path))
    pn.list_contacts(contacts)
    captured = capsys.readouterr()
    lines = [l for l in captured.out.splitlines() if l.strip()]
    beta_pos = next(i for i, l in enumerate(lines) if "Beta" in l)
    alpha_pos = next(i for i, l in enumerate(lines) if "Alpha" in l)
    assert beta_pos < alpha_pos


def test_list_contacts_includes_required_columns(tmp_path, capsys):
    path = _make_xlsx(tmp_path, rows=[COLD])
    contacts = pn.load_contacts(str(path))
    pn.list_contacts(contacts)
    captured = capsys.readouterr()
    for col in ("contact_name", "company", "stage", "status"):
        assert col in captured.out.lower() or "Jane" in captured.out


# ==============================================
# _warmth_context
# ==============================================

def test_warmth_context_cold_returns_empty():
    assert pn._warmth_context("Cold") == ""


def test_warmth_context_strong_returns_empty():
    assert pn._warmth_context("Strong") == ""


def test_warmth_context_acquaintance_returns_placeholder_instruction():
    result = pn._warmth_context("Acquaintance")
    assert "[HOW YOU KNOW THIS PERSON]" in result


def test_warmth_context_former_colleague_returns_placeholder_instruction():
    result = pn._warmth_context("Former Colleague")
    assert "[WHERE YOU WORKED TOGETHER]" in result


# ==============================================
# _build_stage1_prompt
# ==============================================

CANDIDATE_FIXTURE = {
    "clearance": {"status": "Current", "level": "TS/SCI"},
    "military": {"service": [{"branch": "US Army", "dates": "2001-2009"}]},
    "confirmed_skills": {"programming": "Python, MATLAB"},
}


def test_stage1_prompt_cold_contains_300_char_limit():
    prompt = pn._build_stage1_prompt(COLD, CANDIDATE_FIXTURE)
    assert "300" in prompt


def test_stage1_prompt_acquaintance_contains_180_char_target():
    prompt = pn._build_stage1_prompt(ACQUAINTANCE, CANDIDATE_FIXTURE)
    assert "180" in prompt


def test_stage1_prompt_acquaintance_contains_how_you_know_placeholder():
    prompt = pn._build_stage1_prompt(ACQUAINTANCE, CANDIDATE_FIXTURE)
    assert "[HOW YOU KNOW THIS PERSON]" in prompt


def test_stage1_prompt_former_colleague_contains_where_worked_placeholder():
    prompt = pn._build_stage1_prompt(FORMER_COLLEAGUE, CANDIDATE_FIXTURE)
    assert "[WHERE YOU WORKED TOGETHER]" in prompt


def test_stage1_prompt_cold_no_placeholder():
    prompt = pn._build_stage1_prompt(COLD, CANDIDATE_FIXTURE)
    assert "[HOW YOU KNOW THIS PERSON]" not in prompt
    assert "[WHERE YOU WORKED TOGETHER]" not in prompt


def test_stage1_prompt_requests_follow_up_section():
    prompt = pn._build_stage1_prompt(COLD, CANDIDATE_FIXTURE)
    assert "---FOLLOW-UP---" in prompt


# ==============================================
# _build_stage2_prompt
# ==============================================

JD_FIXTURE = "Systems Engineering Director responsible for MBSE and digital engineering..."


def test_stage2_prompt_contains_role_fit_delimiter():
    contact = {**STRONG, "referral_bonus": None}
    prompt = pn._build_stage2_prompt(contact, CANDIDATE_FIXTURE, JD_FIXTURE)
    assert "---ROLE-FIT---" in prompt


def test_stage2_prompt_includes_referral_bonus_when_populated():
    contact = {**STRONG, "referral_bonus": "$5,000"}
    prompt = pn._build_stage2_prompt(contact, CANDIDATE_FIXTURE, JD_FIXTURE)
    assert "referral" in prompt.lower()
    assert "$5,000" in prompt


def test_stage2_prompt_omits_referral_angle_when_blank():
    contact = {**STRONG, "referral_bonus": None}
    prompt = pn._build_stage2_prompt(contact, CANDIDATE_FIXTURE, JD_FIXTURE)
    assert "referral bonus" not in prompt.lower()


def test_stage2_prompt_includes_jd_content():
    contact = {**STRONG, "referral_bonus": None}
    prompt = pn._build_stage2_prompt(contact, CANDIDATE_FIXTURE, JD_FIXTURE)
    assert "MBSE" in prompt


def test_stage2_prompt_includes_warmth_calibration():
    contact_strong = {**STRONG, "referral_bonus": None}
    contact_acquaintance = {**ACQUAINTANCE, "referral_bonus": None}
    prompt_strong = pn._build_stage2_prompt(contact_strong, CANDIDATE_FIXTURE, JD_FIXTURE)
    prompt_acq = pn._build_stage2_prompt(contact_acquaintance, CANDIDATE_FIXTURE, JD_FIXTURE)
    assert prompt_strong != prompt_acq


# ==============================================
# _build_stage3_prompt
# ==============================================

def test_stage3_prompt_contains_followup_instruction():
    prompt = pn._build_stage3_prompt(COLD, CANDIDATE_FIXTURE)
    assert "follow" in prompt.lower()


def test_stage3_prompt_cold_and_strong_differ():
    prompt_cold = pn._build_stage3_prompt(COLD, CANDIDATE_FIXTURE)
    prompt_strong = pn._build_stage3_prompt(STRONG, CANDIDATE_FIXTURE)
    assert prompt_cold != prompt_strong


# ==============================================
# _build_stage4_prompt
# ==============================================

def test_stage4_prompt_contains_close_instruction():
    prompt = pn._build_stage4_prompt(COLD, CANDIDATE_FIXTURE)
    assert "close" in prompt.lower() or "outcome" in prompt.lower() or "loop" in prompt.lower()


def test_stage4_prompt_instructs_keep_warm():
    prompt = pn._build_stage4_prompt(COLD, CANDIDATE_FIXTURE)
    assert "warm" in prompt.lower() or "relationship" in prompt.lower()
