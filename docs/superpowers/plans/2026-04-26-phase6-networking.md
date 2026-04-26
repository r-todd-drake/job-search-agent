# Phase 6 — Networking and Outreach Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `scripts/phase6_networking.py` — a contact-centric outreach script that reads `contact_pipeline.xlsx`, generates warmth-calibrated LinkedIn and email messages across four relationship stages via the Claude API, and writes stage advances back to the xlsx on interactive confirm.

**Architecture:** Stage handler functions (`_build_stage1_prompt` through `_build_stage4_prompt`) plus a `_warmth_context()` helper (modeled on `_infer_tone()` in `phase5_thankyou.py`) feed into a pure `generate_message()` function that owns the Claude API call. The CLI layer handles all I/O: xlsx reads, output printing, the y/n confirm, and xlsx write-back. This boundary makes `generate_message()` importable and testable without file I/O.

**Tech Stack:** Python 3, `openpyxl` (xlsx read/write), `anthropic` SDK, `python-dotenv`, `argparse`. Follows existing Phase 4/5 script patterns throughout.

**Design spec:** `docs/superpowers/specs/2026-04-26-phase6-networking-design.md`
**Feature spec:** `docs/features/phase6_networking_support/phase6_networking_support.md`

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `scripts/config.py` | Modify | Add `CONTACTS_TRACKER_PATH` constant |
| `scripts/phase6_networking.py` | Create | Main script — all logic |
| `tests/phase6/__init__.py` | Create | Package init |
| `tests/phase6/test_phase6_networking.py` | Create | Tier 1 mock tests |
| `tests/phase6/test_phase6_networking_live.py` | Create | Tier 2 live API tests |
| `tests/fixtures/contact_fixture.py` | Create | Four Jane Q. Applicant variants |
| `example_data/tracker/contact_pipeline_example.xlsx` | Create | Fictional example tracker for onboarding |
| `.gitignore` | Verify | `data/tracker/contact_pipeline.xlsx` must be covered |

---

## Task 1: Scaffold — config constant, package init, fixture file, script skeleton

**Files:**
- Modify: `scripts/config.py`
- Create: `tests/phase6/__init__.py`
- Create: `tests/fixtures/contact_fixture.py`
- Create: `scripts/phase6_networking.py` (skeleton only)

- [ ] **Step 1: Add CONTACTS_TRACKER_PATH to config.py**

Open `scripts/config.py` and append:

```python
CONTACTS_TRACKER_PATH = "data/tracker/contact_pipeline.xlsx"
```

- [ ] **Step 2: Create tests/phase6/__init__.py**

```python
# tests/phase6/__init__.py
```

- [ ] **Step 3: Write tests/fixtures/contact_fixture.py**

```python
# tests/fixtures/contact_fixture.py
"""
Fictional fixture contacts for Phase 6 tests.
Jane Q. Applicant at Acme Defense Systems — four warmth variants.
"""

BASE = {
    "contact_name": "Jane Q. Applicant",
    "company": "Acme Defense Systems",
    "title": "Systems Engineering Director",
    "linkedin_url": "https://linkedin.com/in/janequapplicant",
    "source": "LinkedIn search",
    "first_contact": None,
    "response_date": None,
    "stage": 1,
    "status": "Active",
    "role_activated": None,
    "referral_bonus": None,
    "notes": "",
}

COLD = {**BASE, "warmth": "Cold", "notes": ""}

ACQUAINTANCE = {
    **BASE,
    "warmth": "Acquaintance",
    "notes": "Met at AUSA Annual Meeting 2024, discussed LTAMDS program sustainment",
}

FORMER_COLLEAGUE = {
    **BASE,
    "warmth": "Former Colleague",
    "notes": "Worked together at Raytheon, Advanced Concepts group, 2019–2022",
}

STRONG = {
    **BASE,
    "warmth": "Strong",
    "notes": "Close colleague from Raytheon; collaborated on multiple capture efforts",
}

ALL_VARIANTS = [COLD, ACQUAINTANCE, FORMER_COLLEAGUE, STRONG]
```

- [ ] **Step 4: Create scripts/phase6_networking.py skeleton**

```python
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
```

- [ ] **Step 5: Syntax check**

```bash
python -m py_compile scripts/phase6_networking.py
```

Expected: no output (clean).

- [ ] **Step 6: Commit**

```bash
git add scripts/config.py tests/phase6/__init__.py tests/fixtures/contact_fixture.py scripts/phase6_networking.py
git commit -m "feat(phase6): scaffold — config constant, fixture, script skeleton"
```

---

## Task 2: xlsx loading and contact lookup

**Files:**
- Modify: `scripts/phase6_networking.py`
- Modify: `tests/phase6/test_phase6_networking.py` (create this file)

The script reads `contact_pipeline.xlsx` via `openpyxl`. Contact lookup is case-insensitive partial match against `contact_name`; errors on ambiguous or not found.

- [ ] **Step 1: Write failing tests for load_contacts() and find_contact()**

Create `tests/phase6/test_phase6_networking.py`:

```python
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
    path = _make_xlsx(tmp_path)  # all four share same name — ambiguous
    contacts = pn.load_contacts(path)
    with pytest.raises(ValueError, match="ambiguous"):
        pn.find_contact(contacts, "Jane")


def test_find_contact_not_found_raises(tmp_path):
    path = _make_xlsx(tmp_path)
    contacts = pn.load_contacts(path)
    with pytest.raises(ValueError, match="not found"):
        pn.find_contact(contacts, "Nonexistent Person")
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest tests/phase6/test_phase6_networking.py -v -k "load_contacts or find_contact"
```

Expected: ImportError or AttributeError — `load_contacts` not defined yet.

- [ ] **Step 3: Implement load_contacts() and find_contact() in phase6_networking.py**

Add after the SYSTEM_PROMPT block:

```python
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
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
python -m pytest tests/phase6/test_phase6_networking.py -v -k "load_contacts or find_contact"
```

Expected: 6 tests PASS.

- [ ] **Step 5: Syntax check**

```bash
python -m py_compile scripts/phase6_networking.py
```

- [ ] **Step 6: Commit**

```bash
git add scripts/phase6_networking.py tests/phase6/test_phase6_networking.py
git commit -m "feat(phase6): xlsx loading and contact lookup"
```

---

## Task 3: xlsx write-back and --list output

**Files:**
- Modify: `scripts/phase6_networking.py`
- Modify: `tests/phase6/test_phase6_networking.py`

Write-back rules per stage (see design spec DA-3). `list_contacts()` prints a sorted table.

- [ ] **Step 1: Write failing tests for update_contact() and list_contacts()**

Append to `tests/phase6/test_phase6_networking.py`:

```python
# ==============================================
# update_contact
# ==============================================

def test_update_contact_stage1_advances_stage_and_sets_first_contact(tmp_path):
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
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest tests/phase6/test_phase6_networking.py -v -k "update_contact or list_contacts"
```

Expected: AttributeError — functions not defined yet.

- [ ] **Step 3: Implement update_contact() and list_contacts()**

Append to `scripts/phase6_networking.py` after `find_contact()`:

```python
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
                col_idx = headers.index(field)
                row[col_idx].value = value
            break
    wb.save(path)


def list_contacts(contacts: list) -> None:
    """Print all contacts as a table sorted by stage ascending."""
    sorted_contacts = sorted(contacts, key=lambda c: (c.get("stage") or 0))
    col_widths = {"contact_name": 25, "company": 22, "stage": 6, "status": 12, "role_activated": 22}
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
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
python -m pytest tests/phase6/test_phase6_networking.py -v -k "update_contact or list_contacts"
```

Expected: 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/phase6_networking.py tests/phase6/test_phase6_networking.py
git commit -m "feat(phase6): xlsx write-back and --list output"
```

---

## Task 4: _warmth_context() helper and Stage 1 prompt builder

**Files:**
- Modify: `scripts/phase6_networking.py`
- Modify: `tests/phase6/test_phase6_networking.py`

`_warmth_context()` returns placeholder instructions for Claude. `_build_stage1_prompt()` generates both the connection request and follow-up, separated by `---FOLLOW-UP---` so the CLI can parse and display them separately.

- [ ] **Step 1: Write failing tests**

Append to `tests/phase6/test_phase6_networking.py`:

```python
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
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest tests/phase6/test_phase6_networking.py -v -k "warmth_context or stage1_prompt"
```

Expected: AttributeError — functions not defined.

- [ ] **Step 3: Implement _warmth_context() and _build_stage1_prompt()**

Append to `scripts/phase6_networking.py`:

```python
# ==============================================
# CANDIDATE CONTEXT
# ==============================================

def _build_candidate_context(candidate: dict) -> str:
    """Extract networking-relevant candidate context from candidate_config dict."""
    lines = [
        f"Name: {os.getenv('CANDIDATE_NAME', '[CANDIDATE]')}",
        f"Location: {os.getenv('CANDIDATE_LOCATION', '[LOCATION]')}",
    ]
    cl = candidate.get("clearance", {})
    if cl:
        lines.append(f"Clearance: {cl.get('status', '')} {cl.get('level', '')}")
    for svc in candidate.get("military", {}).get("service", []):
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
        "- Specific and genuine — no 'I came across your profile' openers",
        "- No role ask — relationship-building only",
        "- Write the connection request text only — no labels, no preamble",
    ]

    if warmth_instruction:
        parts.append(f"- {warmth_instruction}")

    parts.extend([
        "",
        "Then write a follow-up message for if the candidate is already connected with "
        f"{contact['contact_name']}. The follow-up should be 2-3 sentences — concise and warm.",
        "Separate the two outputs with exactly this delimiter on its own line: ---FOLLOW-UP---",
        "Format: [connection request text]\\n---FOLLOW-UP---\\n[follow-up message text]",
    ])

    return "\n".join(parts)
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
python -m pytest tests/phase6/test_phase6_networking.py -v -k "warmth_context or stage1_prompt"
```

Expected: 11 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/phase6_networking.py tests/phase6/test_phase6_networking.py
git commit -m "feat(phase6): _warmth_context helper and Stage 1 prompt builder"
```

---

## Task 5: Stage 2 prompt builder

**Files:**
- Modify: `scripts/phase6_networking.py`
- Modify: `tests/phase6/test_phase6_networking.py`

Stage 2 requires `jd_text`. Includes referral bonus angle only when the `referral_bonus` field is populated. Output includes a one-line role-fit rationale separated by `---ROLE-FIT---`.

- [ ] **Step 1: Write failing tests**

Append to `tests/phase6/test_phase6_networking.py`:

```python
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
    # Both should reference warmth in some way — they should differ
    assert prompt_strong != prompt_acq
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest tests/phase6/test_phase6_networking.py -v -k "stage2_prompt"
```

Expected: AttributeError — `_build_stage2_prompt` not defined.

- [ ] **Step 3: Implement _build_stage2_prompt()**

Append to `scripts/phase6_networking.py`:

```python
def _build_stage2_prompt(contact: dict, candidate: dict, jd_text: str) -> str:
    warmth = contact.get("warmth", "Cold")
    warmth_instruction = _warmth_context(warmth)
    referral_bonus = contact.get("referral_bonus")

    directness = {
        "cold": "professional and neutral — you have no prior relationship",
        "acquaintance": "warm but measured — you have a limited prior connection",
        "former colleague": "collegial and direct — you have a real working history together",
        "strong": "direct and personal — this is a close professional contact",
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
        "Role being applied for (summary — do not paste verbatim):",
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
            "— frame it as a benefit to both parties, not as transactional pressure.",
        ])

    parts.extend([
        "",
        "First, on a single line, write a one-sentence role-fit rationale the candidate can use "
        "to calibrate whether this message is accurate before sending.",
        "Separate it from the message with exactly this delimiter on its own line: ---ROLE-FIT---",
        "Format: [one-line rationale]\\n---ROLE-FIT---\\n[message text]",
    ])

    return "\n".join(parts)
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
python -m pytest tests/phase6/test_phase6_networking.py -v -k "stage2_prompt"
```

Expected: 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/phase6_networking.py tests/phase6/test_phase6_networking.py
git commit -m "feat(phase6): Stage 2 prompt builder"
```

---

## Task 6: Stage 3 and Stage 4 prompt builders

**Files:**
- Modify: `scripts/phase6_networking.py`
- Modify: `tests/phase6/test_phase6_networking.py`

Stage 3 is a brief follow-up acknowledging the prior message. Stage 4 closes the loop after role resolution.

- [ ] **Step 1: Write failing tests**

Append to `tests/phase6/test_phase6_networking.py`:

```python
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
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest tests/phase6/test_phase6_networking.py -v -k "stage3_prompt or stage4_prompt"
```

Expected: AttributeError — functions not defined.

- [ ] **Step 3: Implement _build_stage3_prompt() and _build_stage4_prompt()**

Append to `scripts/phase6_networking.py`:

```python
def _build_stage3_prompt(contact: dict, candidate: dict) -> str:
    warmth = contact.get("warmth", "Cold")
    weight = "light and low-pressure" if warmth.lower() == "cold" else "warm and direct"

    return "\n".join([
        f"Write a brief follow-up message from {os.getenv('CANDIDATE_NAME', '[CANDIDATE]')} "
        f"to {contact['contact_name']} at {contact.get('company', 'their company')}.",
        "",
        "Context: a prior outreach message was sent but has not received a response.",
        f"Warmth level: {warmth}",
        f"Notes: {contact.get('notes') or 'No prior contact.'}",
        "",
        "Requirements:",
        f"- Tone: {weight}",
        "- Acknowledge the prior message briefly — do not repeat the full pitch",
        "- 2-3 sentences maximum",
        "- Leave the door open — no pressure",
        "- No hollow openers",
    ])


def _build_stage4_prompt(contact: dict, candidate: dict) -> str:
    return "\n".join([
        f"Write a brief closing message from {os.getenv('CANDIDATE_NAME', '[CANDIDATE]')} "
        f"to {contact['contact_name']} at {contact.get('company', 'their company')} "
        "to close the loop on a role that has now resolved.",
        "",
        f"Warmth level: {contact.get('warmth', 'Cold')}",
        f"Notes: {contact.get('notes') or 'No prior contact.'}",
        "",
        "Requirements:",
        "- Share the outcome briefly (the candidate will fill in: offer accepted / withdrawn / not selected)",
        "- Thank the contact genuinely",
        "- Keep the relationship warm regardless of outcome",
        "- 2-3 sentences maximum",
        "- No hollow closers like 'I hope to stay in touch'",
    ])
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
python -m pytest tests/phase6/test_phase6_networking.py -v -k "stage3_prompt or stage4_prompt"
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/phase6_networking.py tests/phase6/test_phase6_networking.py
git commit -m "feat(phase6): Stage 3 and Stage 4 prompt builders"
```

---

## Task 7: generate_message() dispatcher and character enforcement

**Files:**
- Modify: `scripts/phase6_networking.py`
- Modify: `tests/phase6/test_phase6_networking.py`

`generate_message()` routes to the correct stage handler and makes the Claude API call. For Stage 1, `_enforce_char_limit()` checks the connection request against the tier target and re-prompts once if over.

- [ ] **Step 1: Write failing tests**

Append to `tests/phase6/test_phase6_networking.py`:

```python
# ==============================================
# generate_message
# ==============================================

def _mock_client(text="Generated message.\n---FOLLOW-UP---\nFollow-up message."):
    client = MagicMock()
    response = MagicMock()
    response.content = [MagicMock(text=text)]
    client.messages.create.return_value = response
    return client


def test_generate_message_stage1_calls_api(tmp_path):
    client = _mock_client()
    result = pn.generate_message(1, COLD, CANDIDATE_FIXTURE, client=client)
    assert client.messages.create.called
    assert isinstance(result, str)


def test_generate_message_invalid_stage_raises():
    with pytest.raises(ValueError, match="Invalid stage"):
        pn.generate_message(5, COLD, CANDIDATE_FIXTURE, client=_mock_client())


def test_generate_message_stage2_without_jd_raises():
    with pytest.raises(ValueError, match="jd_text"):
        pn.generate_message(2, STRONG, CANDIDATE_FIXTURE, client=_mock_client())


def test_generate_message_stage2_with_jd_calls_api():
    client = _mock_client("Role fit rationale here.\n---ROLE-FIT---\nReferral message.")
    result = pn.generate_message(2, STRONG, CANDIDATE_FIXTURE, jd_text=JD_FIXTURE, client=client)
    assert client.messages.create.called
    assert isinstance(result, str)


def test_generate_message_stage3_calls_api():
    client = _mock_client("Brief follow-up.")
    result = pn.generate_message(3, COLD, CANDIDATE_FIXTURE, client=client)
    assert client.messages.create.called


def test_generate_message_stage4_calls_api():
    client = _mock_client("Closing message.")
    result = pn.generate_message(4, COLD, CANDIDATE_FIXTURE, client=client)
    assert client.messages.create.called


# ==============================================
# Character limit enforcement (Stage 1)
# ==============================================

def test_char_limit_cold_strong_300(tmp_path):
    """Cold/Strong: connection request over 300 chars triggers retry."""
    long_cr = "x" * 310
    follow_up = "Follow-up text."
    first_response = f"{long_cr}\n---FOLLOW-UP---\n{follow_up}"
    good_cr = "x" * 290
    second_response = f"{good_cr}\n---FOLLOW-UP---\n{follow_up}"

    client = MagicMock()
    r1 = MagicMock()
    r1.content = [MagicMock(text=first_response)]
    r2 = MagicMock()
    r2.content = [MagicMock(text=second_response)]
    client.messages.create.side_effect = [r1, r2]

    result = pn.generate_message(1, COLD, CANDIDATE_FIXTURE, client=client)
    assert client.messages.create.call_count == 2
    assert good_cr in result


def test_char_limit_acquaintance_180(tmp_path):
    """Acquaintance: connection request over 180 chars triggers retry."""
    long_cr = "x" * 190
    follow_up = "Follow-up."
    first_response = f"{long_cr}\n---FOLLOW-UP---\n{follow_up}"
    good_cr = "x" * 170
    second_response = f"{good_cr}\n---FOLLOW-UP---\n{follow_up}"

    client = MagicMock()
    r1 = MagicMock()
    r1.content = [MagicMock(text=first_response)]
    r2 = MagicMock()
    r2.content = [MagicMock(text=second_response)]
    client.messages.create.side_effect = [r1, r2]

    result = pn.generate_message(1, ACQUAINTANCE, CANDIDATE_FIXTURE, client=client)
    assert client.messages.create.call_count == 2


def test_char_limit_within_budget_no_retry():
    """No retry when connection request is within budget."""
    cr = "x" * 250
    response_text = f"{cr}\n---FOLLOW-UP---\nFollow-up."
    client = _mock_client(response_text)
    pn.generate_message(1, COLD, CANDIDATE_FIXTURE, client=client)
    assert client.messages.create.call_count == 1


def test_placeholder_in_acquaintance_output():
    """Acquaintance output must contain the placeholder marker."""
    response_text = (
        "Hi [HOW YOU KNOW THIS PERSON], I wanted to reach out.\n"
        "---FOLLOW-UP---\n"
        "Great to be connected!"
    )
    client = _mock_client(response_text)
    result = pn.generate_message(1, ACQUAINTANCE, CANDIDATE_FIXTURE, client=client)
    assert "[HOW YOU KNOW THIS PERSON]" in result


def test_no_placeholder_in_cold_output():
    """Cold output must not contain any placeholder marker."""
    response_text = "Cold outreach message.\n---FOLLOW-UP---\nFollow-up."
    client = _mock_client(response_text)
    result = pn.generate_message(1, COLD, CANDIDATE_FIXTURE, client=client)
    assert "[HOW YOU KNOW THIS PERSON]" not in result
    assert "[WHERE YOU WORKED TOGETHER]" not in result
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest tests/phase6/test_phase6_networking.py -v -k "generate_message or char_limit or placeholder"
```

Expected: AttributeError — `generate_message` not defined.

- [ ] **Step 3: Implement _enforce_char_limit() and generate_message()**

Append to `scripts/phase6_networking.py`:

```python
# ==============================================
# CHARACTER LIMIT ENFORCEMENT
# ==============================================

def _enforce_char_limit(raw: str, warmth: str, client) -> str:
    """
    For Stage 1: parse connection request, check against tier limit,
    re-prompt Claude once if over. Returns final raw response string.
    """
    parts = raw.split("---FOLLOW-UP---")
    connection_request = parts[0].strip()
    follow_up = parts[1].strip() if len(parts) > 1 else ""

    w = warmth.lower()
    limit = 180 if "acquaintance" in w or "former colleague" in w else 300

    if len(connection_request) <= limit:
        return raw

    retry_prompt = (
        f"Your connection request was {len(connection_request)} characters, "
        f"which exceeds the {limit}-character limit. "
        f"Rewrite it to fit within {limit} characters — same structure, tighter language. "
        f"Then include the follow-up message again after '---FOLLOW-UP---'."
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": strip_pii(retry_prompt)}],
    )
    return response.content[0].text


# ==============================================
# GENERATE MESSAGE (importable pure function)
# ==============================================

def generate_message(stage: int, contact: dict, candidate: dict, jd_text: str = None, client=None) -> str:
    """
    Generate an outreach message for the given stage and contact.
    Pure function — no file I/O. Injectable client for testing.
    Raises ValueError for invalid stage or missing jd_text at Stage 2.
    """
    if client is None:
        client = Anthropic()

    if stage not in (1, 2, 3, 4):
        raise ValueError(f"Invalid stage: {stage}. Must be 1-4.")
    if stage == 2 and not jd_text:
        raise ValueError("jd_text is required for Stage 2 — pass --role to load the job description.")

    prompt_map = {
        1: lambda: _build_stage1_prompt(contact, candidate),
        2: lambda: _build_stage2_prompt(contact, candidate, jd_text),
        3: lambda: _build_stage3_prompt(contact, candidate),
        4: lambda: _build_stage4_prompt(contact, candidate),
    }

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": strip_pii(prompt_map[stage]())}],
    )
    raw = response.content[0].text

    if stage == 1:
        raw = _enforce_char_limit(raw, contact.get("warmth", "Cold"), client)

    return raw
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
python -m pytest tests/phase6/test_phase6_networking.py -v -k "generate_message or char_limit or placeholder"
```

Expected: 13 tests PASS.

- [ ] **Step 5: Run full test suite to check no regressions**

```bash
python -m pytest tests/ -v --ignore=tests/phase6/test_phase6_networking_live.py -q
```

Expected: 392+ tests pass, 0 failures.

- [ ] **Step 6: Commit**

```bash
git add scripts/phase6_networking.py tests/phase6/test_phase6_networking.py
git commit -m "feat(phase6): generate_message dispatcher and Stage 1 character enforcement"
```

---

## Task 8: CLI entry point — argparse, main(), stage mismatch, y/n confirm

**Files:**
- Modify: `scripts/phase6_networking.py`

The CLI layer owns all I/O. It reads the xlsx, loads context, calls `generate_message()`, formats and prints output, handles the y/n confirm, and writes back to xlsx.

- [ ] **Step 1: Write failing test for stage mismatch warning**

Append to `tests/phase6/test_phase6_networking.py`:

```python
# ==============================================
# Stage mismatch warning
# ==============================================

def test_stage_mismatch_prints_warning(tmp_path, capsys):
    """When --stage doesn't match xlsx stage, warn and proceed."""
    contact_at_stage1 = {**COLD, "stage": 1}
    # Simulate the warning logic directly (main() is harder to unit test)
    pn._warn_if_stage_mismatch(contact_at_stage1, requested_stage=3)
    captured = capsys.readouterr()
    assert "Warning" in captured.out
    assert "stage 1" in captured.out.lower() or "stage: 1" in captured.out.lower()


def test_stage_mismatch_no_warning_when_matching(tmp_path, capsys):
    contact_at_stage1 = {**COLD, "stage": 1}
    pn._warn_if_stage_mismatch(contact_at_stage1, requested_stage=1)
    captured = capsys.readouterr()
    assert "Warning" not in captured.out
```

- [ ] **Step 2: Run to confirm failure**

```bash
python -m pytest tests/phase6/test_phase6_networking.py -v -k "stage_mismatch"
```

- [ ] **Step 3: Implement _warn_if_stage_mismatch() and main()**

Append to `scripts/phase6_networking.py`:

```python
# ==============================================
# CLI HELPERS
# ==============================================

def _warn_if_stage_mismatch(contact: dict, requested_stage: int) -> None:
    """Print a warning if requested stage differs from contact's current xlsx stage."""
    xlsx_stage = contact.get("stage")
    if xlsx_stage is not None and int(xlsx_stage) != requested_stage:
        print(
            f"Warning: contact_pipeline.xlsx shows {contact['contact_name']} at stage {xlsx_stage}, "
            f"but --stage {requested_stage} was requested. Generating Stage {requested_stage} message anyway."
        )


def _format_stage1_output(raw: str, warmth: str) -> str:
    """Parse Stage 1 raw Claude output and format for display."""
    parts = raw.split("---FOLLOW-UP---")
    connection_request = parts[0].strip()
    follow_up = parts[1].strip() if len(parts) > 1 else ""

    w = warmth.lower()
    limit = 180 if "acquaintance" in w or "former colleague" in w else 300
    char_count = len(connection_request)

    if "acquaintance" in w or "former colleague" in w:
        char_line = f"[{char_count} chars generated | ~{limit - char_count} chars remaining for your fill]"
        if char_count > limit:
            char_line += f"  *** OVER {limit}-CHAR TARGET — trim before sending ***"
    else:
        char_line = f"[{char_count} / {limit} characters]"
        if char_count > limit:
            char_line += "  *** OVER LIMIT — trim before sending ***"

    output = f"--- Connection Request ---\n{connection_request}\n\n{char_line}"
    if follow_up:
        output += f"\n\n--- Follow-Up (if already connected) ---\n{follow_up}"
    return output


def _format_stage2_output(raw: str) -> str:
    """Parse Stage 2 raw Claude output and format for display."""
    parts = raw.split("---ROLE-FIT---")
    if len(parts) == 2:
        rationale = parts[0].strip()
        message = parts[1].strip()
        return f"Role fit: {rationale}\n\n{message}"
    return raw


def _build_write_back(stage: int, role: str = None) -> dict:
    """Return the dict of fields to write back on confirm for a given stage."""
    today = date.today()
    if stage == 1:
        return {"stage": 2, "first_contact": today}
    if stage == 2:
        updates = {"stage": 3}
        if role:
            updates["role_activated"] = role
        return updates
    if stage == 3:
        return {"stage": 4}
    if stage == 4:
        return {"status": "Closed"}
    return {}


# ==============================================
# MAIN
# ==============================================

def main():
    parser = argparse.ArgumentParser(description="Phase 6 — Networking and Outreach Support")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--contact", type=str, help="Contact name (partial match)")
    group.add_argument("--list", action="store_true", help="List all contacts")
    parser.add_argument("--stage", type=int, choices=[1, 2, 3, 4], help="Message stage")
    parser.add_argument("--role", type=str, help="Job package role slug (required at Stage 2)")
    args = parser.parse_args()

    contacts = load_contacts(CONTACTS_TRACKER_PATH)

    if args.list:
        list_contacts(contacts)
        return

    if args.stage is None:
        parser.error("--stage is required when using --contact")

    contact = find_contact(contacts, args.contact)
    _warn_if_stage_mismatch(contact, args.stage)

    if args.stage == 2 and not args.role:
        print("Error: --role is required at Stage 2.")
        sys.exit(1)

    candidate = candidate_config.load()
    jd_text = None
    if args.stage == 2:
        jd_path = f"data/job_packages/{args.role}/job_description.txt"
        if not os.path.exists(jd_path):
            print(f"Error: job description not found at {jd_path}")
            sys.exit(1)
        with open(jd_path, encoding="utf-8") as f:
            jd_text = f.read()

    print(f"\n=== Stage {args.stage} | {contact['contact_name']} @ {contact.get('company', '')} | {contact.get('warmth', '')} ===\n")

    raw = generate_message(args.stage, contact, candidate, jd_text=jd_text)

    if args.stage == 1:
        print(_format_stage1_output(raw, contact.get("warmth", "Cold")))
    elif args.stage == 2:
        print(_format_stage2_output(raw))
    else:
        print(raw)

    answer = input("\nDid you send this? (y/n): ").strip().lower()
    if answer == "y":
        updates = _build_write_back(args.stage, role=args.role)
        update_contact(CONTACTS_TRACKER_PATH, contact["contact_name"], updates)
        print(f"Updated {contact['contact_name']} in contact_pipeline.xlsx.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run stage mismatch tests**

```bash
python -m pytest tests/phase6/test_phase6_networking.py -v -k "stage_mismatch"
```

Expected: 2 tests PASS.

- [ ] **Step 5: Write tests for _build_write_back() and _format_stage1_output()**

Append to `tests/phase6/test_phase6_networking.py`:

```python
# ==============================================
# _build_write_back
# ==============================================

def test_write_back_stage1_fields():
    updates = pn._build_write_back(1)
    assert updates["stage"] == 2
    assert "first_contact" in updates


def test_write_back_stage2_includes_role():
    updates = pn._build_write_back(2, role="acme-systems-se")
    assert updates["stage"] == 3
    assert updates["role_activated"] == "acme-systems-se"


def test_write_back_stage3_advances_stage():
    assert pn._build_write_back(3) == {"stage": 4}


def test_write_back_stage4_closes_status():
    assert pn._build_write_back(4) == {"status": "Closed"}


# ==============================================
# _format_stage1_output
# ==============================================

def test_format_stage1_output_cold_shows_300_budget():
    raw = "Short connection request.\n---FOLLOW-UP---\nFollow-up message."
    output = pn._format_stage1_output(raw, "Cold")
    assert "300" in output


def test_format_stage1_output_acquaintance_shows_remaining_budget():
    raw = "x" * 140 + "\n---FOLLOW-UP---\nFollow-up."
    output = pn._format_stage1_output(raw, "Acquaintance")
    assert "remaining" in output


def test_format_stage1_output_cold_over_limit_shows_warning():
    raw = "x" * 310 + "\n---FOLLOW-UP---\nFollow-up."
    output = pn._format_stage1_output(raw, "Cold")
    assert "OVER" in output
```

- [ ] **Step 6: Run write-back and format tests**

```bash
python -m pytest tests/phase6/test_phase6_networking.py -v -k "write_back or format_stage1"
```

Expected: 7 tests PASS.

- [ ] **Step 7: Syntax check**

```bash
python -m py_compile scripts/phase6_networking.py
```

- [ ] **Step 8: Commit**

```bash
git add scripts/phase6_networking.py tests/phase6/test_phase6_networking.py
git commit -m "feat(phase6): CLI entry point — argparse, main(), stage mismatch, y/n confirm"
```

---

## Task 9: Example xlsx and .gitignore verification

**Files:**
- Create: `example_data/tracker/contact_pipeline_example.xlsx`
- Verify: `.gitignore`

- [ ] **Step 1: Verify .gitignore covers contact_pipeline.xlsx**

```bash
git check-ignore -v data/tracker/contact_pipeline.xlsx
```

Expected: a `.gitignore` rule matches (e.g., `data/` or `data/tracker/`). If no output, the file is NOT gitignored — add the rule before continuing.

If no rule matches, add to `.gitignore`:
```
data/tracker/contact_pipeline.xlsx
```

Then: `git add .gitignore && git commit -m "chore: gitignore contact_pipeline.xlsx"`

- [ ] **Step 2: Create example xlsx with fictional data**

Run this one-time Python script in the project root:

```bash
python - <<'EOF'
import openpyxl
from openpyxl import Workbook
from datetime import date

COLUMNS = [
    "contact_name", "company", "title", "linkedin_url", "warmth",
    "source", "first_contact", "response_date", "stage", "status",
    "role_activated", "referral_bonus", "notes",
]

ROWS = [
    ["Jane Q. Applicant", "Acme Defense Systems", "Systems Engineering Director",
     "https://linkedin.com/in/janequapplicant", "Strong",
     "Former colleague", date(2026, 3, 1), date(2026, 3, 3), 2, "Active",
     "acme-defense-sr-se", "$5,000",
     "Worked together at Raytheon Advanced Concepts 2019-2022"],
    ["John A. Example", "TechSystems Corp", "VP Engineering",
     "https://linkedin.com/in/johnaexample", "Acquaintance",
     "AUSA Annual Meeting", None, None, 1, "Active",
     None, None,
     "Met at AUSA Annual Meeting 2024, discussed LTAMDS sustainment"],
    ["Mary B. Sample", "NavalTech Inc", "Chief Systems Engineer",
     "https://linkedin.com/in/marybsample", "Cold",
     "LinkedIn search", None, None, 1, "Active",
     None, None, ""],
    ["Robert C. Test", "Saronic Technologies", "Director, Program Management",
     "https://linkedin.com/in/robertctest", "Former Colleague",
     "Former colleague", date(2026, 2, 15), None, 3, "Active",
     "vehicle-systems-lead-saronic", None,
     "Worked together at General Dynamics C4 Systems, 2015-2018"],
]

wb = Workbook()
ws = wb.active
ws.title = "Contacts"
ws.append(COLUMNS)
for row in ROWS:
    ws.append(row)

wb.save("example_data/tracker/contact_pipeline_example.xlsx")
print("Created example_data/tracker/contact_pipeline_example.xlsx")
EOF
```

- [ ] **Step 3: Verify the file loads cleanly**

```bash
python -c "
import openpyxl
wb = openpyxl.load_workbook('example_data/tracker/contact_pipeline_example.xlsx')
ws = wb.active
print(f'Rows: {ws.max_row - 1} contacts, {ws.max_column} columns')
"
```

Expected: `Rows: 4 contacts, 13 columns`

- [ ] **Step 4: Commit**

```bash
git add example_data/tracker/contact_pipeline_example.xlsx
git commit -m "feat(phase6): add example contact tracker xlsx with fictional data"
```

---

## Task 10: Full Tier 1 test run and regression check

- [ ] **Step 1: Run all Tier 1 mock tests for Phase 6**

```bash
python -m pytest tests/phase6/test_phase6_networking.py -v
```

Expected: all tests PASS. Note the count.

- [ ] **Step 2: Run full existing test suite (regression)**

```bash
python -m pytest tests/ --ignore=tests/phase6/test_phase6_networking_live.py -q
```

Expected: 392+ tests PASS, 0 failures. If any existing test fails, investigate before continuing — do not proceed to Tier 2 tests with a failing regression.

- [ ] **Step 3: Final syntax check**

```bash
python -m py_compile scripts/phase6_networking.py
```

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "test(phase6): Tier 1 mock tests complete, regression clean"
```

---

## Task 11: Tier 2 live API tests

**Files:**
- Create: `tests/phase6/test_phase6_networking_live.py`

These tests call the real Claude API. They are separate from Tier 1 tests and not run in normal CI.

- [ ] **Step 1: Create Tier 2 test file**

```python
# tests/phase6/test_phase6_networking_live.py
"""
Tier 2 live API tests for phase6_networking.
Calls the real Claude API. Run manually — not in CI.

Run: pytest tests/phase6/test_phase6_networking_live.py -v -s
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import scripts.phase6_networking as pn
from tests.fixtures.contact_fixture import COLD, ACQUAINTANCE, FORMER_COLLEAGUE, STRONG

CANDIDATE_FIXTURE = {
    "clearance": {"status": "Current", "level": "TS/SCI"},
    "military": {"service": [{"branch": "US Army", "dates": "2001-2009"}]},
    "confirmed_skills": {"programming": "Python, MATLAB"},
}

JD_FIXTURE = (
    "Systems Engineering Director — Acme Defense Systems. "
    "Lead MBSE and digital engineering initiatives across the enterprise. "
    "TS/SCI required. 10+ years SE experience in defense."
)


@pytest.mark.parametrize("contact,label", [
    (COLD, "Cold"),
    (ACQUAINTANCE, "Acquaintance"),
    (FORMER_COLLEAGUE, "Former Colleague"),
    (STRONG, "Strong"),
])
def test_stage1_live_all_warmth_tiers(contact, label):
    result = pn.generate_message(1, contact, CANDIDATE_FIXTURE)
    print(f"\n--- Stage 1 / {label} ---\n{result}")
    assert isinstance(result, str)
    assert len(result) > 20
    if label in ("Acquaintance",):
        assert "[HOW YOU KNOW THIS PERSON]" in result
    if label in ("Former Colleague",):
        assert "[WHERE YOU WORKED TOGETHER]" in result


def test_stage2_live_strong_with_referral_bonus():
    contact = {**STRONG, "referral_bonus": "$5,000"}
    result = pn.generate_message(2, contact, CANDIDATE_FIXTURE, jd_text=JD_FIXTURE)
    print(f"\n--- Stage 2 / Strong + referral bonus ---\n{result}")
    assert isinstance(result, str)
    assert len(result) > 50


def test_stage2_live_acquaintance_no_referral_bonus():
    contact = {**ACQUAINTANCE, "referral_bonus": None}
    result = pn.generate_message(2, contact, CANDIDATE_FIXTURE, jd_text=JD_FIXTURE)
    print(f"\n--- Stage 2 / Acquaintance, no referral bonus ---\n{result}")
    assert "referral bonus" not in result.lower()
```

- [ ] **Step 2: Run Tier 2 tests**

```bash
python -m pytest tests/phase6/test_phase6_networking_live.py -v -s
```

Expected: 6 tests PASS. Review printed output for each warmth variant — verify placeholder markers appear where expected and messages are appropriate in tone and length.

- [ ] **Step 3: Commit**

```bash
git add tests/phase6/test_phase6_networking_live.py
git commit -m "test(phase6): Tier 2 live API tests"
```

---

## Task 12: Update SCRIPT_INDEX.md and DATA_FLOW.md

**Files:**
- Modify: `context/SCRIPT_INDEX.md`
- Modify: `context/DATA_FLOW.md`

- [ ] **Step 1: Add phase6_networking.py to SCRIPT_INDEX.md**

In `context/SCRIPT_INDEX.md`, add a new Phase 6 section after the Phase 5 table:

```markdown
## Phase 6 — Networking

| Script | Purpose | Key flags |
| --- | --- | --- |
| `phase6_networking.py` | Contact-centric outreach message generator; reads/writes `contact_pipeline.xlsx` | `--contact` `--stage` `--role` `--list` |
```

- [ ] **Step 2: Add phase6_networking.py to DATA_FLOW.md**

In `context/DATA_FLOW.md`, add a Phase 6 section:

```markdown
## Phase 6 — Networking

| Script | Reads | Writes |
| ------ | ----- | ------- |
| `phase6_networking.py` | `data/tracker/contact_pipeline.xlsx`, `context/candidate/candidate_config.yaml`, `data/job_packages/[role]/job_description.txt` (Stage 2 only) | `data/tracker/contact_pipeline.xlsx` (stage advance + date fields on y confirm) |
```

- [ ] **Step 3: Rebuild docs if build_docs.py is used**

```bash
python scripts/utils/build_docs.py
```

If this fails (fragments not updated), skip — the SCRIPT_INDEX and DATA_FLOW edits are sufficient.

- [ ] **Step 4: Commit**

```bash
git add context/SCRIPT_INDEX.md context/DATA_FLOW.md
git commit -m "docs(phase6): update SCRIPT_INDEX and DATA_FLOW for phase6_networking"
```

---

## Self-Review Checklist

Spec coverage check:

| Requirement | Task |
|---|---|
| AC-1: contact_pipeline.xlsx as sole store | Task 2 (load_contacts), Task 9 (example xlsx) |
| AC-2: --contact partial match, --stage, --role, --list | Task 2 (find_contact), Task 8 (main) |
| AC-2: stage mismatch warning | Task 8 (_warn_if_stage_mismatch) |
| AC-2: Stage 2 --role required error | Task 7 (generate_message), Task 8 (main) |
| AC-3: Stage 1 — connection request + follow-up, warmth-calibrated | Task 4 (_build_stage1_prompt) |
| AC-3: Stage 1 — 300-char hard limit enforced | Task 7 (_enforce_char_limit) |
| AC-3: Stage 2 — referral bonus angle conditional | Task 5 (_build_stage2_prompt) |
| AC-3: Stage 2 — role-fit rationale | Task 5 (_build_stage2_prompt) |
| AC-3: Stage 3 — follow-up, warmth-calibrated | Task 6 (_build_stage3_prompt) |
| AC-3: Stage 4 — close the loop | Task 6 (_build_stage4_prompt) |
| AC-4: Output format — labeled, char count, role-fit | Task 8 (_format_stage1_output, _format_stage2_output) |
| AC-4: Stage 1 placeholder char budget display | Task 8 (_format_stage1_output) |
| DA-2: y/n confirm before xlsx write-back | Task 8 (main) |
| DA-3: write-back rules per stage | Task 8 (_build_write_back) |
| DA-4: four distinct warmth tiers | Tasks 4, 5, 6 |
| DA-5: placeholder markers for Acquaintance/Former Colleague | Task 4 (_warmth_context) |
| DA-6: Stage 1 char budget split by warmth | Task 7 (_enforce_char_limit), Task 4 (_build_stage1_prompt) |
| AC-5: cross-pipeline integration | Out of scope — deferred |
| AC-6: generate_message() importable | Task 7 (function signature) |
| AC-6: Tier 1 mock tests | Tasks 2–8 |
| AC-6: Tier 2 live tests | Task 11 |
| AC-6: fixture content (4 variants with notes) | Task 1 (contact_fixture.py) |
| AC-6: 392 existing tests pass | Task 10 (regression check) |
