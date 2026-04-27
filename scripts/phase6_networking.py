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
        raise ValueError(f"Contact '{name}' is ambiguous – matched: {found}. Use a more specific name.")
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


# ==============================================
# CANDIDATE CONTEXT
# ==============================================

def _build_candidate_context(candidate: dict) -> str:
    """Extract networking-relevant candidate context from candidate_config dict.

    Name and location come from env vars (CANDIDATE_NAME, CANDIDATE_LOCATION) —
    this matches the existing pattern in candidate_config.build_known_facts().
    Structured fields (clearance, military, skills) come from the YAML dict.
    """
    lines = [
        f"Name: {os.getenv('CANDIDATE_NAME', '[CANDIDATE]')}",
        f"Location: {os.getenv('CANDIDATE_LOCATION', '[LOCATION]')}",
    ]
    cl = candidate.get("clearance", {})
    if cl:
        lines.append(f"Clearance: {cl.get('status') or ''} {cl.get('level') or ''}".strip())
    for svc in (candidate.get("military") or {}).get("service") or []:
        branch = svc.get("branch", "")
        dates = svc.get("dates", "")
        if branch:
            lines.append(f"Military: {branch} {dates}".strip())
    prog = candidate.get("confirmed_skills", {}).get("programming", "")
    if prog:
        lines.append(f"Technical skills: {prog}")
    return "\n".join(lines)


# ==============================================
# WARMTH HELPER
# ==============================================

def _warmth_context(warmth: str) -> str:
    """Return placeholder instruction for Claude based on warmth tier."""
    w = warmth.lower()
    if "acquaintance" in w:
        return (
            "Include the placeholder [HOW YOU KNOW THIS PERSON] exactly where you would "
            "reference the shared connection. Do not invent or guess the shared context. "
            "Keep surrounding text to approximately 180 characters to leave room for the fill."
        )
    if "former colleague" in w:
        return (
            "Include the placeholder [WHERE YOU WORKED TOGETHER] exactly where you would "
            "reference the shared employer or project. Do not invent or guess the shared context. "
            "Keep surrounding text to approximately 180 characters to leave room for the fill."
        )
    return ""


# ==============================================
# PROMPT BUILDERS
# ==============================================

def _build_stage1_prompt(contact: dict, candidate: dict) -> str:
    warmth_instruction = _warmth_context(contact.get("warmth", ""))
    char_limit = "180 characters for the surrounding text" if warmth_instruction else "300 characters total"

    parts = [
        f"Write a LinkedIn connection request from {os.getenv('CANDIDATE_NAME', '[CANDIDATE]')} "
        f"to {contact['contact_name']}, a {contact.get('title', 'professional')} at {contact.get('company', 'their company')}.",
        "",
        "Candidate background:",
        _build_candidate_context(candidate),
        "",
        f"Warmth level: {contact.get('warmth', 'Cold')}",
        f"Notes on the relationship: {contact.get('notes') or 'No prior contact.'}",
        "",
        "Connection request requirements:",
        f"- HARD LIMIT: {char_limit}",
        "- Specific and genuine – no 'I came across your profile' openers",
        "- No role ask – relationship-building only",
        "- Write the connection request text only – no labels, no preamble",
    ]

    if warmth_instruction:
        parts.append(f"- {warmth_instruction}")

    parts.extend([
        "",
        "Then write a follow-up message for if the candidate is already connected with "
        f"{contact['contact_name']}. The follow-up should be 2-3 sentences – concise and warm.",
        "Separate the two outputs with exactly this delimiter on its own line: ---FOLLOW-UP---",
        "Format: [connection request text]\\n---FOLLOW-UP---\\n[follow-up message text]",
    ])

    return "\n".join(parts)


def _build_stage2_prompt(contact: dict, candidate: dict, jd_text: str) -> str:
    warmth = contact.get("warmth", "Cold")
    warmth_instruction = _warmth_context(warmth)
    referral_bonus = contact.get("referral_bonus")

    directness = {
        "cold": "professional and neutral – you have no prior relationship",
        "acquaintance": "warm but measured – you have a limited prior connection",
        "former colleague": "collegial and direct – you have a real working history together",
        "strong": "direct and personal – this is a close professional contact",
    }.get(warmth.lower(), "professional and warm")

    parts = [
        f"Write a LinkedIn message or email from {os.getenv('CANDIDATE_NAME', '[CANDIDATE]')} "
        f"to {contact['contact_name']}, a {contact.get('title', 'professional')} at {contact.get('company', 'their company')}, "
        f"asking for a referral for a specific role.",
        "",
        "Candidate background:",
        _build_candidate_context(candidate),
        "",
        f"Warmth level: {warmth}",
        f"Tone: {directness}",
        f"Notes on the relationship: {contact.get('notes') or 'No prior contact.'}",
        "",
        "Role being applied for (summary – do not paste verbatim):",
        jd_text[:800],
        "",
        "Message requirements:",
        "- Reference the specific role title and company; do not paste JD content verbatim",
        "- Make the ask clear but not pressuring",
        "- Keep to 3-4 short paragraphs",
        "- No hollow openers",
    ]

    if warmth_instruction:
        parts.append(f"- {warmth_instruction}")

    if referral_bonus:
        parts.extend([
            f"- The referral bonus for this role is {referral_bonus}. Mention this as mutual upside "
            "– frame it as a benefit to both parties, not as transactional pressure.",
        ])

    parts.extend([
        "",
        "First, on a single line, write a one-sentence role-fit rationale the candidate can use "
        "to calibrate whether this message is accurate before sending.",
        "Separate it from the message with exactly this delimiter on its own line: ---ROLE-FIT---",
        "Format: [one-line rationale]\\n---ROLE-FIT---\\n[message text]",
    ])

    return "\n".join(parts)
