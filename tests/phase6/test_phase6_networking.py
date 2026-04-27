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
