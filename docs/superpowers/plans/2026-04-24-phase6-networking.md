# Phase 6 — Networking Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `scripts/phase6_networking.py` — a standalone script that generates personalized LinkedIn outreach guidance and message templates for a specific job application.

**Architecture:** Single script following the Phase 5 pattern: argparse CLI, `--role` loads the job package, Anthropic API for section generation, output to `networking_outreach.txt` + `networking_outreach.docx` in the job package folder. Five pure prompt-builder functions (one per section) make each section independently testable. A `generate_networking()` function with an injectable client drives all API calls and file writes. A `main_with_args()` function separates arg parsing from `main()` for testability.

**Tech Stack:** Python 3.11, anthropic SDK, python-docx, dotenv, `scripts/utils/pii_filter.py`, `scripts/config.py`

---

### Task 1: Test infrastructure + script scaffold

**Files:**
- Create: `tests/phase6/__init__.py`
- Create: `tests/phase6/test_phase6_networking.py`
- Create: `scripts/phase6_networking.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/phase6/__init__.py` as an empty file.

Create `tests/phase6/test_phase6_networking.py`:

```python
import pytest
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scripts.phase6_networking as pn


# ==============================================
# HELPERS
# ==============================================

def _mock_client(texts=None):
    """Return a mock Anthropic client.
    texts: list of response strings, one per API call (in order).
    Defaults to 5 identical placeholder responses.
    """
    if texts is None:
        texts = ["Section content."] * 5
    client = MagicMock()
    responses = []
    for t in texts:
        r = MagicMock()
        r.content = [MagicMock(text=t)]
        responses.append(r)
    client.messages.create.side_effect = responses
    return client


def _setup_job_package(tmp_path, role="TestRole"):
    pkg_dir = tmp_path / "job_packages" / role
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "job_description.txt").write_text(
        "Defense Systems Engineer. MBSE required.", encoding="utf-8"
    )
    return pkg_dir


def _make_role_data(jd_text="JD content.", candidate_profile="Candidate background."):
    return {
        "jd_text": jd_text,
        "candidate_profile": candidate_profile,
        "role_name": "TestRole",
    }


# ==============================================
# SCAFFOLD
# ==============================================

def test_script_importable():
    assert pn is not None


def test_output_txt_constant():
    assert pn.OUTPUT_TXT == "networking_outreach.txt"


def test_output_docx_constant():
    assert pn.OUTPUT_DOCX == "networking_outreach.docx"
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/phase6/test_phase6_networking.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.phase6_networking'`

- [ ] **Step 3: Create the script skeleton**

Create `scripts/phase6_networking.py`:

```python
# ==============================================
# phase6_networking.py
# Generates LinkedIn outreach guidance and message
# templates for a specific job application.
#
# Sections:
#   1: LinkedIn search strategy (who to find)
#   2: Connection request message (300 char limit)
#   3: Follow-up message after connecting
#   4: Cold outreach / InMail template
#   5: Informational interview request
#
# Usage:
#   python -m scripts.phase6_networking --role Acme_SE_Systems
# ==============================================

import os
import sys
import re
import argparse
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv
from docx import Document
from docx.shared import Pt, Inches

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.utils.pii_filter import strip_pii
from scripts.config import (
    JOBS_PACKAGES_DIR,
    CANDIDATE_PROFILE_PATH,
    MODEL_SONNET as MODEL,
)

load_dotenv()

OUTPUT_TXT = "networking_outreach.txt"
OUTPUT_DOCX = "networking_outreach.docx"

# ==============================================
# SYSTEM PROMPT
# ==============================================

SYSTEM_PROMPT = """You are an expert career coach and professional communications strategist
specializing in the defense and aerospace industry. You help senior engineers build
authentic professional networks.

You always:
- Write from the candidate's authentic professional perspective
- Ground messages in the candidate's specific background and the role context
- Keep messages direct, professional, and non-transactional
- Use en dashes, never em dashes

You never:
- Write generic, template-sounding messages
- Overstate the candidate's interest or urgency
- Suggest the candidate misrepresent their background or intentions"""


def main_with_args(args_list=None):
    parser = argparse.ArgumentParser(description="Phase 6 Networking Outreach Generator")
    parser.add_argument("--role", type=str, required=True,
                        help="Role package folder name (e.g. Acme_SE_Systems)")
    args = parser.parse_args(args_list)
    print(f"Phase 6 -- stub. Role: {args.role}")


def main():
    main_with_args()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/phase6/test_phase6_networking.py -v
```
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/phase6_networking.py tests/phase6/__init__.py tests/phase6/test_phase6_networking.py
git commit -m "feat: add phase6_networking scaffold with test infrastructure"
```

---

### Task 2: Section 1 — LinkedIn search strategy prompt builder

**Files:**
- Modify: `scripts/phase6_networking.py` — add `_build_section1_prompt()`
- Modify: `tests/phase6/test_phase6_networking.py` — add Section 1 tests

- [ ] **Step 1: Write the failing tests**

Append to `tests/phase6/test_phase6_networking.py`:

```python
# ==============================================
# _build_section1_prompt
# ==============================================

def test_section1_prompt_returns_string():
    result = pn._build_section1_prompt("JD content.", "Candidate profile.")
    assert isinstance(result, str)
    assert len(result) > 0


def test_section1_prompt_includes_jd():
    result = pn._build_section1_prompt("MBSE required.", "Candidate profile.")
    assert "MBSE required." in result


def test_section1_prompt_includes_linkedin():
    result = pn._build_section1_prompt("JD content.", "Candidate profile.")
    assert "LinkedIn" in result
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/phase6/test_phase6_networking.py -k "section1" -v
```
Expected: 3 FAIL — `AttributeError: module 'scripts.phase6_networking' has no attribute '_build_section1_prompt'`

- [ ] **Step 3: Implement `_build_section1_prompt()`**

Add to `scripts/phase6_networking.py` after the `SYSTEM_PROMPT` block:

```python
# ==============================================
# PROMPT BUILDERS
# ==============================================

def _build_section1_prompt(jd: str, candidate_profile: str) -> str:
    """Build Section 1: LinkedIn search strategy prompt."""
    return (
        f"You are helping a defense systems engineer identify the right people to contact "
        f"on LinkedIn for a specific role they are pursuing.\n\n"
        f"JOB DESCRIPTION:\n{jd[:2000]}\n\n"
        f"CANDIDATE BACKGROUND (PII removed):\n{candidate_profile[:1000]}\n\n"
        f"Generate a LinkedIn search strategy for this role. Structure your response with "
        f"ALL-CAPS section headers followed by a colon.\n\n"
        f"Include exactly these sections:\n\n"
        f"TARGET TITLES:\n"
        f"List 4-6 specific job titles to search for at this company -- the people who would "
        f"hire for this role or work alongside it (hiring manager titles, peer SE titles, "
        f"program manager titles). Use real title patterns from the JD language.\n\n"
        f"SEARCH QUERIES:\n"
        f"List 3-4 specific LinkedIn search strings using the company name + role keywords "
        f"from the JD. Format: one query per line, ready to paste into LinkedIn search.\n\n"
        f"FILTERS TO APPLY:\n"
        f"List 3-4 LinkedIn filter recommendations (location, connections degree, current "
        f"company, industry) specific to this role.\n\n"
        f"PRIORITY CONTACT ORDER:\n"
        f"List the 3 contact types to prioritize, from highest to lowest value, with one "
        f"sentence explaining why for each.\n\n"
        f"WHAT TO LOOK FOR:\n"
        f"2-3 sentences describing profile signals that indicate this person is a high-value "
        f"contact for this role -- program names, keywords, mutual connections, activity signals."
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/phase6/test_phase6_networking.py -k "section1" -v
```
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/phase6_networking.py tests/phase6/test_phase6_networking.py
git commit -m "feat: add phase6 section 1 LinkedIn search strategy prompt builder"
```

---

### Task 3: Section 2 — Connection request prompt builder

**Files:**
- Modify: `scripts/phase6_networking.py` — add `_build_section2_prompt()`
- Modify: `tests/phase6/test_phase6_networking.py` — add Section 2 tests

- [ ] **Step 1: Write the failing tests**

Append to `tests/phase6/test_phase6_networking.py`:

```python
# ==============================================
# _build_section2_prompt
# ==============================================

def test_section2_prompt_returns_string():
    result = pn._build_section2_prompt("JD content.", "Candidate profile.")
    assert isinstance(result, str)
    assert len(result) > 0


def test_section2_prompt_mentions_300_character_limit():
    result = pn._build_section2_prompt("JD content.", "Candidate profile.")
    assert "300" in result


def test_section2_prompt_mentions_connection_request():
    result = pn._build_section2_prompt("JD content.", "Candidate profile.")
    assert "connection request" in result.lower()


def test_section2_prompt_includes_jd():
    result = pn._build_section2_prompt("MBSE required for this role.", "Candidate profile.")
    assert "MBSE required for this role." in result
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/phase6/test_phase6_networking.py -k "section2" -v
```
Expected: 4 FAIL — `AttributeError`

- [ ] **Step 3: Implement `_build_section2_prompt()`**

Add to `scripts/phase6_networking.py` after `_build_section1_prompt`:

```python
def _build_section2_prompt(jd: str, candidate_profile: str) -> str:
    """Build Section 2: LinkedIn connection request message prompt.
    LinkedIn hard limit is 300 characters.
    """
    return (
        f"Write a LinkedIn connection request message for a defense systems engineer "
        f"pursuing the role described below.\n\n"
        f"JOB DESCRIPTION:\n{jd[:1500]}\n\n"
        f"CANDIDATE BACKGROUND (PII removed):\n{candidate_profile[:800]}\n\n"
        f"Requirements:\n"
        f"- Hard limit: 300 characters including spaces\n"
        f"- Do not use the recipient's name (we may not know it)\n"
        f"- Reference something specific from the role or company -- not generic\n"
        f"- Explain why you are reaching out in one clause\n"
        f"- End with a low-friction ask (connecting, not a call)\n"
        f"- Professional but not stiff -- peer-level tone\n\n"
        f"Format your response as:\n\n"
        f"CONNECTION REQUEST:\n"
        f"[message text only -- no labels or explanation inside the message itself]\n\n"
        f"CHARACTER COUNT: [exact count]\n\n"
        f"NOTE: [one sentence on what makes this message specific vs. generic]"
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/phase6/test_phase6_networking.py -k "section2" -v
```
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/phase6_networking.py tests/phase6/test_phase6_networking.py
git commit -m "feat: add phase6 section 2 connection request prompt builder (300-char limit)"
```

---

### Task 4: Sections 3, 4, 5 prompt builders

**Files:**
- Modify: `scripts/phase6_networking.py` — add `_build_section3_prompt()`, `_build_section4_prompt()`, `_build_section5_prompt()`
- Modify: `tests/phase6/test_phase6_networking.py` — add Section 3-5 tests

- [ ] **Step 1: Write the failing tests**

Append to `tests/phase6/test_phase6_networking.py`:

```python
# ==============================================
# _build_section3_prompt -- follow-up after connecting
# ==============================================

def test_section3_prompt_returns_string():
    result = pn._build_section3_prompt("JD content.", "Candidate profile.")
    assert isinstance(result, str)
    assert len(result) > 0


def test_section3_prompt_includes_jd():
    result = pn._build_section3_prompt("MBSE systems engineer.", "Candidate profile.")
    assert "MBSE systems engineer." in result


def test_section3_prompt_mentions_follow_up():
    result = pn._build_section3_prompt("JD content.", "Candidate profile.")
    assert "follow" in result.lower()


# ==============================================
# _build_section4_prompt -- cold outreach / InMail
# ==============================================

def test_section4_prompt_returns_string():
    result = pn._build_section4_prompt("JD content.", "Candidate profile.")
    assert isinstance(result, str)
    assert len(result) > 0


def test_section4_prompt_includes_jd():
    result = pn._build_section4_prompt("MBSE systems engineer.", "Candidate profile.")
    assert "MBSE systems engineer." in result


def test_section4_prompt_mentions_inmail():
    result = pn._build_section4_prompt("JD content.", "Candidate profile.")
    assert "InMail" in result or "inmail" in result.lower()


# ==============================================
# _build_section5_prompt -- informational interview request
# ==============================================

def test_section5_prompt_returns_string():
    result = pn._build_section5_prompt("JD content.", "Candidate profile.")
    assert isinstance(result, str)
    assert len(result) > 0


def test_section5_prompt_includes_jd():
    result = pn._build_section5_prompt("MBSE systems engineer.", "Candidate profile.")
    assert "MBSE systems engineer." in result


def test_section5_prompt_mentions_informational():
    result = pn._build_section5_prompt("JD content.", "Candidate profile.")
    assert "informational" in result.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/phase6/test_phase6_networking.py -k "section3 or section4 or section5" -v
```
Expected: 9 FAIL — `AttributeError`

- [ ] **Step 3: Implement sections 3-5 prompt builders**

Add to `scripts/phase6_networking.py` after `_build_section2_prompt`:

```python
def _build_section3_prompt(jd: str, candidate_profile: str) -> str:
    """Build Section 3: Follow-up message after a connection is accepted."""
    return (
        f"Write a LinkedIn follow-up message to send after a connection request is accepted. "
        f"The candidate is pursuing the role described below.\n\n"
        f"JOB DESCRIPTION:\n{jd[:1500]}\n\n"
        f"CANDIDATE BACKGROUND (PII removed):\n{candidate_profile[:800]}\n\n"
        f"Requirements:\n"
        f"- 2-3 short paragraphs, under 150 words total\n"
        f"- Open by referencing the shared connection context (defense SE, the company, "
        f"the domain -- whatever is most natural)\n"
        f"- Briefly describe the candidate's background in 1-2 sentences relevant to this role\n"
        f"- Close with a soft ask: a 15-minute call or any insights they can share -- "
        f"keep the ask low-friction and clearly optional\n"
        f"- Tone: collegial peer, not job seeker to gatekeeper\n\n"
        f"Format your response as:\n\n"
        f"FOLLOW-UP MESSAGE:\n"
        f"[message text]\n\n"
        f"NOTE: [one sentence on tone or personalization approach]"
    )


def _build_section4_prompt(jd: str, candidate_profile: str) -> str:
    """Build Section 4: Cold outreach / InMail template."""
    return (
        f"Write a LinkedIn InMail or cold outreach message for a defense systems engineer "
        f"reaching out to someone at the target company who has NOT yet connected with them.\n\n"
        f"JOB DESCRIPTION:\n{jd[:1500]}\n\n"
        f"CANDIDATE BACKGROUND (PII removed):\n{candidate_profile[:800]}\n\n"
        f"Requirements:\n"
        f"- Subject line (for InMail): concise, specific to the domain or role -- under 60 characters\n"
        f"- Body: 3-4 short paragraphs, under 200 words total\n"
        f"- Paragraph 1: establish relevance -- why you are reaching out to this person specifically\n"
        f"- Paragraph 2: brief candidate positioning -- 2 sentences on background aligned to the role\n"
        f"- Paragraph 3: soft ask -- a 20-minute call, virtual coffee, or any program insights "
        f"they can spare -- make it easy to say yes\n"
        f"- Paragraph 4 (optional): one sentence closing, no pressure\n"
        f"- Tone: direct and collegial -- senior peer reaching out, not applicant seeking help\n\n"
        f"Format your response as:\n\n"
        f"SUBJECT: [subject line]\n\n"
        f"INMAIL BODY:\n"
        f"[message text]\n\n"
        f"NOTE: [one sentence on what makes this non-generic]"
    )


def _build_section5_prompt(jd: str, candidate_profile: str) -> str:
    """Build Section 5: Informational interview request message."""
    return (
        f"Write an informational interview request message for a defense systems engineer "
        f"asking for a 20-minute conversation with someone at the target company.\n\n"
        f"JOB DESCRIPTION:\n{jd[:1500]}\n\n"
        f"CANDIDATE BACKGROUND (PII removed):\n{candidate_profile[:800]}\n\n"
        f"Requirements:\n"
        f"- 2-3 paragraphs, under 175 words total\n"
        f"- Be explicit that this is an informational request -- not a job application pitch\n"
        f"- Mention 1-2 specific things the candidate wants to learn about: the team, "
        f"the technical environment, the program culture -- not 'whether there are openings'\n"
        f"- Offer a specific time window (e.g., 'any 20 minutes in the next few weeks') -- "
        f"makes it easy to respond\n"
        f"- Close with appreciation for their time -- gracious but not obsequious\n"
        f"- Tone: curious and collegial -- not a cover letter, not a cold sales pitch\n\n"
        f"Format your response as:\n\n"
        f"INFORMATIONAL REQUEST:\n"
        f"[message text]\n\n"
        f"NOTE: [one sentence on the framing approach]"
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/phase6/test_phase6_networking.py -k "section3 or section4 or section5" -v
```
Expected: 9 PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/phase6_networking.py tests/phase6/test_phase6_networking.py
git commit -m "feat: add phase6 sections 3-5 prompt builders (follow-up, InMail, informational)"
```

---

### Task 5: Output assembly — `_compile_output()`

**Files:**
- Modify: `scripts/phase6_networking.py` — add `_compile_output()`
- Modify: `tests/phase6/test_phase6_networking.py` — add compile output tests

- [ ] **Step 1: Write the failing tests**

Append to `tests/phase6/test_phase6_networking.py`:

```python
# ==============================================
# _compile_output
# ==============================================

def test_compile_output_returns_string():
    result = pn._compile_output("TestRole", "s1", "s2", "s3", "s4", "s5")
    assert isinstance(result, str)


def test_compile_output_includes_role():
    result = pn._compile_output("AcmeSE", "s1", "s2", "s3", "s4", "s5")
    assert "AcmeSE" in result


def test_compile_output_includes_all_sections():
    result = pn._compile_output("TestRole", "alpha", "beta", "gamma", "delta", "epsilon")
    assert "alpha" in result
    assert "beta" in result
    assert "gamma" in result
    assert "delta" in result
    assert "epsilon" in result


def test_compile_output_has_section_headers():
    result = pn._compile_output("TestRole", "s1", "s2", "s3", "s4", "s5")
    assert "SECTION 1" in result
    assert "SECTION 2" in result
    assert "SECTION 3" in result
    assert "SECTION 4" in result
    assert "SECTION 5" in result
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/phase6/test_phase6_networking.py -k "compile_output" -v
```
Expected: 4 FAIL — `AttributeError`

- [ ] **Step 3: Implement `_compile_output()`**

Add to `scripts/phase6_networking.py` after the prompt builders, before `main_with_args`:

```python
# ==============================================
# OUTPUT ASSEMBLY
# ==============================================

def _compile_output(role: str, section1: str, section2: str, section3: str,
                    section4: str, section5: str) -> str:
    """Assemble all five sections into a formatted text output."""
    lines = [
        "=" * 60,
        "PHASE 6 – NETWORKING OUTREACH GUIDE",
        "=" * 60,
        f"Role: {role}",
        f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}",
        "Note: PII stripped from all API calls.",
        "=" * 60,
        "",
        "SECTION 1 – LINKEDIN SEARCH STRATEGY",
        "(Who to find and how to find them)",
        "-" * 60,
        section1,
        "",
        "=" * 60,
        "SECTION 2 – CONNECTION REQUEST",
        "(300-character limit – paste directly into LinkedIn)",
        "-" * 60,
        section2,
        "",
        "=" * 60,
        "SECTION 3 – FOLLOW-UP MESSAGE",
        "(Send after connection is accepted)",
        "-" * 60,
        section3,
        "",
        "=" * 60,
        "SECTION 4 – COLD OUTREACH / INMAIL",
        "(For direct outreach to non-connections)",
        "-" * 60,
        section4,
        "",
        "=" * 60,
        "SECTION 5 – INFORMATIONAL INTERVIEW REQUEST",
        "(Requesting a 20-minute conversation)",
        "-" * 60,
        section5,
        "",
        "=" * 60,
        "END OF NETWORKING OUTREACH GUIDE",
        f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}",
        "=" * 60,
    ]
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/phase6/test_phase6_networking.py -k "compile_output" -v
```
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/phase6_networking.py tests/phase6/test_phase6_networking.py
git commit -m "feat: add phase6 output assembly function"
```

---

### Task 6: Core generation function — `generate_networking()`

**Files:**
- Modify: `scripts/phase6_networking.py` — add `generate_networking_docx()` stub + `generate_networking()`
- Modify: `tests/phase6/test_phase6_networking.py` — add generation tests

- [ ] **Step 1: Write the failing tests**

Append to `tests/phase6/test_phase6_networking.py`:

```python
# ==============================================
# generate_networking
# ==============================================

def test_generate_networking_makes_5_api_calls(tmp_path):
    client = _mock_client()
    role_data = _make_role_data()
    txt_path = str(tmp_path / "networking_outreach.txt")
    docx_path = str(tmp_path / "networking_outreach.docx")

    pn.generate_networking(client, role_data, txt_path, docx_path)

    assert client.messages.create.call_count == 5


def test_generate_networking_writes_txt_file(tmp_path):
    client = _mock_client()
    role_data = _make_role_data()
    txt_path = str(tmp_path / "networking_outreach.txt")
    docx_path = str(tmp_path / "networking_outreach.docx")

    pn.generate_networking(client, role_data, txt_path, docx_path)

    assert os.path.exists(txt_path)


def test_generate_networking_writes_docx_file(tmp_path):
    client = _mock_client()
    role_data = _make_role_data()
    txt_path = str(tmp_path / "networking_outreach.txt")
    docx_path = str(tmp_path / "networking_outreach.docx")

    pn.generate_networking(client, role_data, txt_path, docx_path)

    assert os.path.exists(docx_path)


def test_generate_networking_all_sections_in_txt(tmp_path):
    client = _mock_client(texts=[
        "Section1 content.",
        "Section2 content.",
        "Section3 content.",
        "Section4 content.",
        "Section5 content.",
    ])
    role_data = _make_role_data()
    txt_path = str(tmp_path / "networking_outreach.txt")
    docx_path = str(tmp_path / "networking_outreach.docx")

    pn.generate_networking(client, role_data, txt_path, docx_path)

    with open(txt_path, encoding="utf-8") as f:
        content = f.read()
    assert "Section1 content." in content
    assert "Section2 content." in content
    assert "Section3 content." in content
    assert "Section4 content." in content
    assert "Section5 content." in content


def test_generate_networking_strips_pii(tmp_path, monkeypatch):
    stripped_calls = []
    original_strip = pn.strip_pii

    def tracking_strip(text):
        stripped_calls.append(text)
        return original_strip(text)

    monkeypatch.setattr(pn, "strip_pii", tracking_strip)
    client = _mock_client()
    role_data = _make_role_data(candidate_profile="Profile content here.")
    txt_path = str(tmp_path / "networking_outreach.txt")
    docx_path = str(tmp_path / "networking_outreach.docx")

    pn.generate_networking(client, role_data, txt_path, docx_path)

    assert len(stripped_calls) > 0
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/phase6/test_phase6_networking.py -k "generate_networking" -v
```
Expected: 5 FAIL — `AttributeError: module 'scripts.phase6_networking' has no attribute 'generate_networking'`

- [ ] **Step 3: Add `generate_networking_docx()` stub and implement `generate_networking()`**

Add to `scripts/phase6_networking.py` after `_compile_output`, before `main_with_args`:

```python
# ==============================================
# DOCX GENERATION (stub -- replaced in Task 7)
# ==============================================

def generate_networking_docx(output_path: str, role: str,
                              section1: str, section2: str, section3: str,
                              section4: str, section5: str) -> None:
    """Generate a formatted .docx networking outreach document."""
    doc = Document()
    doc.add_heading("Networking Outreach Guide", 0)
    doc.add_paragraph(f"Role: {role}")
    for i, section in enumerate([section1, section2, section3, section4, section5], 1):
        doc.add_heading(f"Section {i}", level=1)
        for line in section.split("\n"):
            if line.strip():
                doc.add_paragraph(line.strip())
    doc.save(output_path)


# ==============================================
# CORE GENERATION
# ==============================================

def generate_networking(client, role_data: dict, output_txt_path: str,
                        output_docx_path: str) -> None:
    """
    Generate networking outreach guide from role data.
    role_data keys: jd_text, candidate_profile, role_name.
    Writes both .txt and .docx output files.
    All PII stripped from API payloads.
    """
    jd = role_data["jd_text"]
    raw_profile = role_data.get("candidate_profile", "")
    role_name = role_data.get("role_name", "unknown")

    safe_profile = strip_pii(raw_profile)

    sections = [
        ("Section 1: LinkedIn Search Strategy", _build_section1_prompt(jd, safe_profile)),
        ("Section 2: Connection Request", _build_section2_prompt(jd, safe_profile)),
        ("Section 3: Follow-Up Message", _build_section3_prompt(jd, safe_profile)),
        ("Section 4: Cold Outreach / InMail", _build_section4_prompt(jd, safe_profile)),
        ("Section 5: Informational Interview Request", _build_section5_prompt(jd, safe_profile)),
    ]

    results = []
    for label, prompt in sections:
        print(f"  {label}...")
        response = client.messages.create(
            model=MODEL,
            max_tokens=800,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        results.append(response.content[0].text)

    section1, section2, section3, section4, section5 = results

    output_text = _compile_output(role_name, section1, section2, section3, section4, section5)

    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write(output_text)
    print(f"  Written to {output_txt_path}")

    try:
        generate_networking_docx(output_docx_path, role_name,
                                  section1, section2, section3, section4, section5)
        print(f"  .docx written to {output_docx_path}")
    except Exception as e:
        print(f"  WARNING: .docx generation failed: {str(e)}")
        doc = Document()
        for line in output_text.splitlines():
            doc.add_paragraph(line)
        doc.save(output_docx_path)
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/phase6/test_phase6_networking.py -k "generate_networking" -v
```
Expected: 5 PASS

- [ ] **Step 5: Run full suite to check for regressions**

```
pytest tests/ -m "not live" -v
```
Expected: all existing tests + 5 new tests PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/phase6_networking.py tests/phase6/test_phase6_networking.py
git commit -m "feat: implement generate_networking core function"
```

---

### Task 7: DOCX generation — full `generate_networking_docx()`

**Files:**
- Modify: `scripts/phase6_networking.py` — replace stub with full `generate_networking_docx()`
- Modify: `tests/phase6/test_phase6_networking.py` — add docx tests

- [ ] **Step 1: Write the failing tests**

Append to `tests/phase6/test_phase6_networking.py`:

```python
# ==============================================
# generate_networking_docx
# ==============================================

def test_generate_networking_docx_creates_file(tmp_path):
    output_path = str(tmp_path / "networking_outreach.docx")
    pn.generate_networking_docx(
        output_path, "TestRole",
        "Section 1 content.", "Section 2 content.", "Section 3 content.",
        "Section 4 content.", "Section 5 content."
    )
    assert os.path.exists(output_path)


def test_generate_networking_docx_is_valid_docx(tmp_path):
    from docx import Document as DocxDocument
    output_path = str(tmp_path / "networking_outreach.docx")
    pn.generate_networking_docx(
        output_path, "TestRole",
        "s1", "s2", "s3", "s4", "s5"
    )
    doc = DocxDocument(output_path)
    full_text = " ".join(p.text for p in doc.paragraphs)
    assert "TestRole" in full_text


def test_generate_networking_docx_contains_all_sections(tmp_path):
    from docx import Document as DocxDocument
    output_path = str(tmp_path / "networking_outreach.docx")
    pn.generate_networking_docx(
        output_path, "TestRole",
        "Alpha content.", "Beta content.", "Gamma content.",
        "Delta content.", "Epsilon content."
    )
    doc = DocxDocument(output_path)
    full_text = " ".join(p.text for p in doc.paragraphs)
    assert "Alpha content." in full_text
    assert "Beta content." in full_text
```

- [ ] **Step 2: Run tests to verify current state**

```
pytest tests/phase6/test_phase6_networking.py -k "docx" -v
```
If all 3 PASS with the stub: skip Step 3, commit as-is.
If any FAIL: proceed to Step 3.

- [ ] **Step 3: Replace stub with full `generate_networking_docx()` implementation**

Replace the stub `generate_networking_docx` in `scripts/phase6_networking.py` with:

```python
def generate_networking_docx(output_path: str, role: str,
                              section1: str, section2: str, section3: str,
                              section4: str, section5: str) -> None:
    """Generate a formatted .docx networking outreach guide."""
    doc = Document()

    sec = doc.sections[0]
    sec.left_margin = Inches(1.0)
    sec.right_margin = Inches(1.0)
    sec.top_margin = Inches(1.0)
    sec.bottom_margin = Inches(1.0)

    def add_section_heading(title, subtitle=""):
        p = doc.add_heading(title, level=1)
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        if subtitle:
            sub = doc.add_paragraph(subtitle)
            sub.paragraph_format.space_after = Pt(6)

    def add_content(text):
        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue
            if re.match(r'^[A-Z][A-Z\s\-–&/]+:', stripped) and len(stripped) < 80:
                p = doc.add_heading(stripped, level=2)
                p.paragraph_format.space_before = Pt(8)
                p.paragraph_format.space_after = Pt(2)
            elif stripped.startswith("- "):
                p = doc.add_paragraph(stripped[2:], style="List Bullet")
                p.paragraph_format.space_after = Pt(2)
            else:
                p = doc.add_paragraph(stripped)
                p.paragraph_format.space_after = Pt(4)

    title_p = doc.add_heading("Networking Outreach Guide", 0)
    title_p.paragraph_format.space_after = Pt(4)
    doc.add_paragraph(f"Role: {role}")
    doc.add_paragraph(f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}")
    doc.add_paragraph()

    add_section_heading("Section 1 – LinkedIn Search Strategy",
                        "Who to find and how to find them.")
    add_content(section1)

    add_section_heading("Section 2 – Connection Request",
                        "300-character limit – paste directly into LinkedIn.")
    add_content(section2)

    add_section_heading("Section 3 – Follow-Up Message",
                        "Send after connection is accepted.")
    add_content(section3)

    add_section_heading("Section 4 – Cold Outreach / InMail",
                        "For direct outreach to non-connections.")
    add_content(section4)

    add_section_heading("Section 5 – Informational Interview Request",
                        "Requesting a 20-minute conversation.")
    add_content(section5)

    doc.save(output_path)
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/phase6/test_phase6_networking.py -k "docx" -v
```
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/phase6_networking.py tests/phase6/test_phase6_networking.py
git commit -m "feat: implement full docx generation for phase6 networking guide"
```

---

### Task 8: `main()` — CLI wiring, file loading, validation

**Files:**
- Modify: `scripts/phase6_networking.py` — replace stub `main_with_args()` with full implementation
- Modify: `tests/phase6/test_phase6_networking.py` — add main() tests

- [ ] **Step 1: Write the failing tests**

Append to `tests/phase6/test_phase6_networking.py`:

```python
# ==============================================
# main_with_args() validation
# ==============================================

def test_main_exits_on_missing_package_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(pn, "JOBS_PACKAGES_DIR", str(tmp_path / "job_packages"))
    monkeypatch.setattr(pn, "CANDIDATE_PROFILE_PATH", str(tmp_path / "candidate_profile.md"))
    with pytest.raises(SystemExit) as exc:
        pn.main_with_args(["--role", "NonExistentRole"])
    assert exc.value.code != 0


def test_main_exits_on_missing_jd(tmp_path, monkeypatch):
    pkg_dir = tmp_path / "job_packages" / "TestRole"
    pkg_dir.mkdir(parents=True)
    # Package dir exists but no job_description.txt
    monkeypatch.setattr(pn, "JOBS_PACKAGES_DIR", str(tmp_path / "job_packages"))
    monkeypatch.setattr(pn, "CANDIDATE_PROFILE_PATH", str(tmp_path / "candidate_profile.md"))
    with pytest.raises(SystemExit) as exc:
        pn.main_with_args(["--role", "TestRole"])
    assert exc.value.code != 0


def test_main_exits_on_missing_candidate_profile(tmp_path, monkeypatch):
    pkg_dir = tmp_path / "job_packages" / "TestRole"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "job_description.txt").write_text("JD content.", encoding="utf-8")
    monkeypatch.setattr(pn, "JOBS_PACKAGES_DIR", str(tmp_path / "job_packages"))
    monkeypatch.setattr(pn, "CANDIDATE_PROFILE_PATH",
                        str(tmp_path / "nonexistent_profile.md"))
    with pytest.raises(SystemExit) as exc:
        pn.main_with_args(["--role", "TestRole"])
    assert exc.value.code != 0


def test_main_runs_and_produces_output_files(tmp_path, monkeypatch):
    pkg_dir = tmp_path / "job_packages" / "TestRole"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "job_description.txt").write_text("JD content.", encoding="utf-8")
    profile_path = tmp_path / "candidate_profile.md"
    profile_path.write_text("Candidate background.", encoding="utf-8")

    monkeypatch.setattr(pn, "JOBS_PACKAGES_DIR", str(tmp_path / "job_packages"))
    monkeypatch.setattr(pn, "CANDIDATE_PROFILE_PATH", str(profile_path))

    mock_api_client = _mock_client()
    monkeypatch.setattr(pn, "Anthropic", lambda **kwargs: mock_api_client)

    pn.main_with_args(["--role", "TestRole"])

    assert os.path.exists(str(pkg_dir / "networking_outreach.txt"))
    assert os.path.exists(str(pkg_dir / "networking_outreach.docx"))
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/phase6/test_phase6_networking.py -k "main" -v
```
Expected: tests that check `sys.exit` may PASS (stub calls `print` and returns), but `test_main_runs_and_produces_output_files` will FAIL — stub never writes files. That's acceptable — proceed to Step 3.

- [ ] **Step 3: Replace stub `main_with_args()` with full implementation**

Replace the stub `main_with_args` in `scripts/phase6_networking.py` with:

```python
# ==============================================
# MAIN
# ==============================================

def main_with_args(args_list=None):
    """Parse args and run -- separated from main() for testability."""
    parser = argparse.ArgumentParser(description="Phase 6 Networking Outreach Generator")
    parser.add_argument("--role", type=str, required=True,
                        help="Role package folder name (e.g. Acme_SE_Systems)")
    args = parser.parse_args(args_list)

    role = args.role
    package_dir = os.path.join(JOBS_PACKAGES_DIR, role)
    jd_path = os.path.join(package_dir, "job_description.txt")
    output_txt_path = os.path.join(package_dir, OUTPUT_TXT)
    output_docx_path = os.path.join(package_dir, OUTPUT_DOCX)

    print("=" * 60)
    print("PHASE 6 – NETWORKING OUTREACH GENERATOR")
    print("=" * 60)
    print(f"Role: {role}")
    print(f"Package: {package_dir}")

    errors = []
    if not os.path.exists(package_dir):
        errors.append(f"Job package folder not found: {package_dir}")
    if not os.path.exists(jd_path):
        errors.append(f"job_description.txt not found in {package_dir}")
    if not os.path.exists(CANDIDATE_PROFILE_PATH):
        errors.append(f"candidate_profile.md not found: {CANDIDATE_PROFILE_PATH}")

    if errors:
        print("\nERRORS – cannot proceed:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)

    if os.path.exists(output_txt_path):
        print(f"\nWARNING: {OUTPUT_TXT} already exists.")
        response = input("  Overwrite? (y/n): ").strip().lower()
        if response != "y":
            print("  Cancelled. Existing file preserved.")
            sys.exit(0)

    with open(jd_path, encoding="utf-8") as f:
        jd_text = f.read()

    with open(CANDIDATE_PROFILE_PATH, encoding="utf-8") as f:
        candidate_profile = f.read()

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    role_data = {
        "jd_text": jd_text,
        "candidate_profile": candidate_profile,
        "role_name": role,
    }

    print("\nGenerating networking outreach guide...")
    generate_networking(client, role_data, output_txt_path, output_docx_path)

    print(f"\n{'=' * 60}")
    print("PHASE 6 COMPLETE")
    print(f"{'=' * 60}")
    print(f"Output saved: {output_txt_path}")
    print(f"\nNext steps:")
    print(f"  1. Open {output_docx_path} in Word for formatted reading")
    print(f"  2. Run Section 1 searches on LinkedIn manually")
    print(f"  3. Personalize Section 2 connection request if recipient name is known")
    print(f"  4. Send Section 3 follow-up within 48 hours of connection acceptance")
    print(f"  5. Use Sections 4-5 for direct outreach when not yet connected")
    print(f"{'=' * 60}")


def main():
    main_with_args()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/phase6/test_phase6_networking.py -k "main" -v
```
Expected: 4 PASS

- [ ] **Step 5: Run full test suite to verify no regressions**

```
pytest tests/ -m "not live" -v
```
Expected: all 384 prior tests + ~35 new phase6 tests = all PASS. Note the count in the output.

- [ ] **Step 6: Run syntax check**

```
python -m py_compile scripts/phase6_networking.py && echo "OK"
```
Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git add scripts/phase6_networking.py tests/phase6/test_phase6_networking.py
git commit -m "feat: implement phase6_networking main() with CLI wiring and validation"
```

---

## Self-Review

### Spec coverage

| Spec requirement | Covered by |
|---|---|
| Standalone script `python -m scripts.phase6_networking --role [role]` | Task 8 — `main_with_args()` |
| Section 1: LinkedIn search guidance (queries, filters, who to look for) | Task 2 — `_build_section1_prompt()` |
| Section 2: Connection request (300-char limit) | Task 3 — `_build_section2_prompt()` |
| Section 3: Follow-up message after connecting | Task 4 — `_build_section3_prompt()` |
| Section 4: Cold outreach / InMail template | Task 4 — `_build_section4_prompt()` |
| Section 5: Informational interview request | Task 4 — `_build_section5_prompt()` |
| User performs searches manually — script provides guidance | Task 2 prompt design + Task 8 next-steps output |
| PII stripped from all API calls | Task 6 — `strip_pii(raw_profile)` called before all prompts |
| Output to `data/job_packages/[role]/` | Tasks 6 and 8 — path construction in `main_with_args()` |
| `.txt` + `.docx` output | Tasks 6 and 7 |

**Intentionally excluded:** Parking lot item 5 (add Phase 6 reference to Phase 4 Stage 4 next steps) — spec says deferred until Phase 6 is stable.

### Placeholder scan

No "TBD", "TODO", vague "add error handling", or "similar to Task N" patterns present. All code blocks show complete implementations.

### Type consistency

- `generate_networking(client, role_data, output_txt_path, output_docx_path)` — consistent across Task 6 definition and Task 8 call.
- `generate_networking_docx(output_path, role, section1, section2, section3, section4, section5)` — consistent across Task 6 stub, Task 7 full implementation, and Task 6 call inside `generate_networking()`.
- `_compile_output(role, section1, section2, section3, section4, section5)` — consistent across Task 5 definition and Task 6 call.
- All prompt builders: `_build_sectionN_prompt(jd, candidate_profile) -> str` — consistent signature across Tasks 2-4.
- `main_with_args(args_list=None)` — consistent between Task 1 stub, Task 8 replacement, and all test calls.
