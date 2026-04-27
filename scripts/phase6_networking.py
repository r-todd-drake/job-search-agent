# ==============================================
# phase6_networking.py
# Generates warmth-calibrated LinkedIn and email
# outreach messages for professional networking.
#
# Reads contact data from contact_pipeline.xlsx.
# Writes stage advances back on interactive confirm.
# No automated sending — output is terminal only.
#
# Usage:
#   python -m scripts.phase6_networking \
#     --contact "Jane Smith" --stage 1
#   python -m scripts.phase6_networking \
#     --contact "Jane Smith" --stage 2 --role acme-systems-se
#   python -m scripts.phase6_networking --list
# ==============================================

import os
import sys
import argparse
from datetime import date
from anthropic import Anthropic
from dotenv import load_dotenv
import openpyxl

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.utils.pii_filter import strip_pii
from scripts.utils import candidate_config
from scripts.config import CONTACTS_TRACKER_PATH, MODEL_SONNET as MODEL

load_dotenv()

# ==============================================
# SYSTEM PROMPT
# ==============================================

SYSTEM_PROMPT = """You are an expert career coach writing professional networking messages \
for senior defense and systems engineering professionals. Your messages are specific, \
genuine, and appropriately brief.

You always:
- Use en dashes, never em dashes
- Write specific over generic
- Match the directness of the message to the warmth of the relationship
- Keep connection requests within their character limits

You never:
- Use hollow openers like "I came across your profile" or "Hope this message finds you well"
- Invent or guess shared history not explicitly provided
- Reference a specific role unless one is provided
- Use filler phrases or overly formal language"""

# ==============================================
# XLSX I/O
# ==============================================

COLUMNS = [
    "contact_name", "company", "title", "linkedin_url", "warmth",
    "source", "first_contact", "response_date", "stage", "status",
    "role_activated", "referral_bonus", "notes",
]


def load_contacts(path: str) -> list:
    """Load all contacts from xlsx. Returns list of dicts keyed by column name."""
    wb = openpyxl.load_workbook(path)
    ws = wb.active
    headers = [cell.value for cell in ws[1]]
    contacts = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if all(v is None for v in row):
            continue
        contacts.append(dict(zip(headers, row)))
    return contacts


def find_contact(contacts: list, name: str) -> dict:
    """Case-insensitive partial match on contact_name. Raises ValueError if ambiguous or not found."""
    name_lower = name.lower()
    matches = [c for c in contacts if name_lower in (c.get("contact_name") or "").lower()]
    if len(matches) == 0:
        raise ValueError(f"Contact '{name}' not found in contact_pipeline.xlsx.")
    if len(matches) > 1:
        found = ", ".join(c["contact_name"] for c in matches)
        raise ValueError(f"Contact '{name}' is ambiguous — matched: {found}. Use a more specific name.")
    return matches[0]


def update_contact(path: str, contact_name: str, updates: dict) -> None:
    """Write field updates back to the xlsx row matching contact_name."""
    wb = openpyxl.load_workbook(path)
    ws = wb.active
    headers = [cell.value for cell in ws[1]]
    for row in ws.iter_rows(min_row=2):
        if row[headers.index("contact_name")].value == contact_name:
            for field, value in updates.items():
                if field == "response_date":
                    continue  # never written by script
                if field not in headers:
                    raise ValueError(f"update_contact: field '{field}' not in xlsx headers")
                col_idx = headers.index(field)
                row[col_idx].value = value
            break
    wb.save(path)


def list_contacts(contacts: list) -> None:
    """Print all contacts as a table sorted by stage ascending."""
    sorted_contacts = sorted(contacts, key=lambda c: (c.get("stage") or 0))
    header = (
        f"{'NAME':<25}  {'COMPANY':<22}  {'STG':<6}  {'STATUS':<12}  {'ROLE':<22}"
    )
    print(header)
    print("-" * len(header))
    for c in sorted_contacts:
        print(
            f"{(c.get('contact_name') or ''):<25}  "
            f"{(c.get('company') or ''):<22}  "
            f"{str(c.get('stage') or ''):<6}  "
            f"{(c.get('status') or ''):<12}  "
            f"{(c.get('role_activated') or ''):<22}"
        )
