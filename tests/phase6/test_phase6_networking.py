import pytest
import sys
import os
from datetime import date
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
    path = _make_xlsx(tmp_path, rows=[COLD])
    contacts = pn.load_contacts(path)
    result = pn.find_contact(contacts, "Jane Q. Applicant")
    assert result["contact_name"] == "Jane Q. Applicant"


def test_find_contact_case_insensitive(tmp_path):
    path = _make_xlsx(tmp_path, rows=[COLD])
    contacts = pn.load_contacts(path)
    result = pn.find_contact(contacts, "jane q. applicant")
    assert result["contact_name"] == "Jane Q. Applicant"


def test_find_contact_partial_match(tmp_path):
    path = _make_xlsx(tmp_path, rows=[COLD])
    contacts = pn.load_contacts(path)
    result = pn.find_contact(contacts, "Jane")
    assert result["contact_name"] == "Jane Q. Applicant"


def test_find_contact_ambiguous_raises(tmp_path):
    # Two different contacts whose names both contain the search term
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
    path = _make_xlsx(tmp_path, rows=[COLD])
    pn.update_contact(str(path), "Jane Q. Applicant", {"stage": 2, "first_contact": date(2026, 4, 26)})
    contacts = pn.load_contacts(str(path))
    assert contacts[0]["stage"] == 2
    # openpyxl loads dates as datetime objects, so compare date only
    assert contacts[0]["first_contact"].date() == date(2026, 4, 26)


def test_update_contact_stage2_sets_role_activated(tmp_path):
    path = _make_xlsx(tmp_path, rows=[COLD])
    pn.update_contact(str(path), "Jane Q. Applicant", {"stage": 3, "role_activated": "acme-systems-se"})
    contacts = pn.load_contacts(str(path))
    assert contacts[0]["stage"] == 3
    assert contacts[0]["role_activated"] == "acme-systems-se"


def test_update_contact_never_writes_response_date(tmp_path):
    path = _make_xlsx(tmp_path, rows=[COLD])
    pn.update_contact(str(path), "Jane Q. Applicant", {
        "stage": 2,
        "first_contact": date(2026, 4, 26),
        "response_date": date(2026, 4, 27),  # should be silently ignored
    })
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
    # Beta (stage 1) should appear before Alpha (stage 3)
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
