# check_cover_letter.py Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `scripts/check_cover_letter.py` — a two-layer cover letter quality checker that mirrors `check_resume.py` and writes findings to `cl_stage3_review.txt`.

**Architecture:** Layer 1 runs fast string matching (hardcoded rules + dynamic gap terms from CANDIDATE_BACKGROUND.md). Layer 2 makes a single API call focused on implied gap fulfillment, banned language, and generic opener phrases. All output is captured to `cl_stage3_review.txt`; exit code 1 on any findings.

**Tech Stack:** Python 3.11+, anthropic SDK, python-dotenv, pytest, unittest.mock

---

## File Map

| Action | Path |
|--------|------|
| Create | `scripts/check_cover_letter.py` |
| Create | `tests/fixtures/stage_files/cl_stage2_approved.txt` |
| Create | `tests/phase4/test_check_cover_letter.py` |

---

## Task 1: Create cover letter test fixture

**Files:**
- Create: `tests/fixtures/stage_files/cl_stage2_approved.txt`

- [ ] **Step 1: Create the fixture file**

Write exactly this content to `tests/fixtures/stage_files/cl_stage2_approved.txt`:

```
April 8, 2026

Hiring Team
Anduril Industries
Costa Mesa, CA

Dear Hiring Manager,

With 20 years of defense systems engineering experience and a Current TS/SCI clearance,
I offer a strong match for the Systems Engineer, Open Architecture role. As the functional
MBSE Pillar Lead for Project Overmatch – the CNO's second-highest priority program – I
translated operational vision into an implemented enterprise MBSE architecture from
program inception.

My work at KForce/NGLD-M centered on requirements harmonization, V/V matrix development,
and user story decomposition for a mission-critical Navy communications program. I
identified suspected duplicate requirements, confirmed findings through independent
research, and presented results to the Chief Engineer at periodic review boards.

At Shield AI, I served as Lead Systems Engineer for the V-BAT autonomous UAS on the
Army FTUAS program, coordinating across hardware and software teams to maintain system
architecture integrity through rapid development cycles.

I welcome the opportunity to discuss how my background in mission-critical systems and
open architecture aligns with Anduril's goals.

Sincerely,

[Candidate Name]
```

Note: No em dashes, no CompTIA, no Active TS/SCI, no Plank Holder variants, no
safety-critical, no gap term references, no generic opener. This is the clean baseline.

---

## Task 2: Write Layer 1 tests — verify they fail

**Files:**
- Create: `tests/phase4/test_check_cover_letter.py`

- [ ] **Step 1: Create test file with Layer 1 tests**

Write `tests/phase4/test_check_cover_letter.py`:

```python
# tests/phase4/test_check_cover_letter.py
#
# Tests for scripts/check_cover_letter.py
# Covers Layer 1 (string matching), Layer 2 (API assessment), and PII safety.
#
# Run mock tests only:
#   pytest tests/phase4/test_check_cover_letter.py -m "not live" -v
# Run live test (requires ANTHROPIC_API_KEY):
#   pytest tests/phase4/test_check_cover_letter.py -m live -v

import importlib
import pytest
from pathlib import Path
from unittest.mock import MagicMock

FIXTURE_BACKGROUND = Path(__file__).parent.parent / "fixtures" / "stage_files" / "sample_background.md"
FIXTURE_CL_STAGE2 = Path(__file__).parent.parent / "fixtures" / "stage_files" / "cl_stage2_approved.txt"

MOCK_L2_RESPONSE = "[]"  # No violations -- valid empty JSON array


def make_mock_client(response_text):
    client = MagicMock()
    client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=response_text)]
    )
    return client


# ==============================================
# extract_section
# ==============================================

def test_extract_section_returns_content_between_headings():
    from scripts.check_cover_letter import extract_section
    text = "## Confirmed Gaps\nNo GitLab\n## Other Section\nOther content"
    result = extract_section(text, "## Confirmed Gaps")
    assert "No GitLab" in result
    assert "Other content" not in result


def test_extract_section_returns_empty_for_missing_heading():
    from scripts.check_cover_letter import extract_section
    text = "## Some Section\nContent here"
    result = extract_section(text, "## Nonexistent Heading")
    assert result == ""


# ==============================================
# extract_gap_terms
# ==============================================

def test_extract_gap_terms_returns_set():
    from scripts.check_cover_letter import extract_gap_terms
    background = FIXTURE_BACKGROUND.read_text(encoding="utf-8")
    terms = extract_gap_terms(background)
    assert isinstance(terms, set)


def test_extract_gap_terms_finds_acronyms():
    from scripts.check_cover_letter import extract_gap_terms
    background = FIXTURE_BACKGROUND.read_text(encoding="utf-8")
    terms = extract_gap_terms(background)
    assert "MATLAB" in terms or len(terms) > 0


# ==============================================
# run_layer1
# ==============================================

def test_run_layer1_detects_em_dash():
    from scripts.check_cover_letter import run_layer1
    cl_lines = ["Senior systems engineer \u2014 available immediately."]
    findings = run_layer1(cl_lines, gap_terms=set())
    rules = [f["rule"] for f in findings]
    assert "Em dash" in rules


def test_run_layer1_detects_safety_critical():
    from scripts.check_cover_letter import run_layer1
    cl_lines = ["Experience with safety-critical systems integration."]
    findings = run_layer1(cl_lines, gap_terms=set())
    rules = [f["rule"] for f in findings]
    assert "safety-critical" in rules


def test_run_layer1_detects_active_ts_sci():
    from scripts.check_cover_letter import run_layer1
    cl_lines = ["I hold an Active TS/SCI clearance."]
    findings = run_layer1(cl_lines, gap_terms=set())
    rules = [f["rule"] for f in findings]
    assert "Active TS/SCI" in rules


def test_run_layer1_detects_plank_holder():
    from scripts.check_cover_letter import run_layer1
    cl_lines = ["Served as Plank Holder for Project Overmatch."]
    findings = run_layer1(cl_lines, gap_terms=set())
    rules = [f["rule"] for f in findings]
    assert "Plank Holder (capitalized)" in rules


def test_run_layer1_detects_gap_term():
    from scripts.check_cover_letter import run_layer1
    cl_lines = ["Proficient with MATLAB for simulation and analysis."]
    findings = run_layer1(cl_lines, gap_terms={"MATLAB"})
    rules = [f["rule"] for f in findings]
    assert any("MATLAB" in r for r in rules)


def test_run_layer1_finding_has_required_keys():
    from scripts.check_cover_letter import run_layer1
    cl_lines = ["Used safety-critical approach throughout the program."]
    findings = run_layer1(cl_lines, gap_terms=set())
    assert len(findings) >= 1
    f = findings[0]
    for key in ("layer", "rule", "line", "flagged_text", "fix"):
        assert key in f
    assert f["layer"] == 1


def test_run_layer1_no_false_positives_on_clean_cover_letter():
    from scripts.check_cover_letter import run_layer1
    cl_lines = FIXTURE_CL_STAGE2.read_text(encoding="utf-8").splitlines()
    findings = run_layer1(cl_lines, gap_terms=set())
    rules = [f["rule"] for f in findings]
    assert "Em dash" not in rules
    assert "safety-critical" not in rules
    assert "Active TS/SCI" not in rules
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/phase4/test_check_cover_letter.py -m "not live" -v
```

Expected: All tests FAIL with `ModuleNotFoundError: No module named 'scripts.check_cover_letter'`

---

## Task 3: Implement script skeleton through Layer 1

**Files:**
- Create: `scripts/check_cover_letter.py` (constants, Layer 1 functions only)

- [ ] **Step 1: Create `scripts/check_cover_letter.py` with Layer 1 implementation**

```python
# ==============================================
# check_cover_letter.py
# API-based cover letter quality checker.
# Two-layer architecture:
#   Layer 1 – fast pre-flight string matching
#   Layer 2 – single API call for nuanced assessment (implied gap fulfillment)
#
# Reads cl_stage2_approved.txt (text stage file).
# Constraints loaded dynamically from CANDIDATE_BACKGROUND.md.
#
# Usage:
#   python -m scripts.check_cover_letter --role [role]
# Example:
#   python -m scripts.check_cover_letter --role BAH_LCI_MBSE
# ==============================================

import io
import os
import re
import sys
import json
import argparse

import anthropic
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.utils.pii_filter import strip_pii

load_dotenv()

# ==============================================
# CONSTANTS
# ==============================================

CANDIDATE_BACKGROUND_PATH = "context/CANDIDATE_BACKGROUND.md"
JOBS_PACKAGES_DIR = "data/job_packages"
MODEL = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = (
    "You are a cover letter quality reviewer for a defense and aerospace systems engineering candidate. "
    "You assess cover letters for accuracy, honesty, and alignment with confirmed experience. "
    "You flag overclaiming, implied gap fulfillment, and language violations. "
    "Return only valid JSON \u2013 no markdown fences, no preamble, no explanation."
)

# Hardcoded Layer 1 rules: (rule_name, pattern, fix, case_sensitive)
HARDCODED_RULES = [
    (
        "Em dash",
        "\u2014",
        "Replace \u2014 with \u2013 (en dash)",
        True,
    ),
    (
        "CompTIA Security+ reference",
        "CompTIA Security+",
        "Remove \u2013 certification is lapsed and must not appear on cover letter",
        False,
    ),
    (
        "Active TS/SCI",
        "Active TS/SCI",
        "Use 'Current TS/SCI' between employers \u2013 'Active' only when employed on a program",
        True,
    ),
    (
        "Plank Holder (capitalized)",
        "Plank Holder",
        "Use 'Plank Owner' (two words, capitalized)",
        True,
    ),
    (
        "plank holder (lowercase)",
        "plank holder",
        "Use 'Plank Owner' (two words, capitalized)",
        False,
    ),
    (
        "plankowner (one word)",
        "plankowner",
        "Use 'Plank Owner' (two words, capitalized)",
        False,
    ),
    (
        "safety-critical",
        "safety-critical",
        "Use 'mission-critical' instead",
        False,
    ),
]

GAP_STOP_WORDS = {
    'NO', 'OR', 'AND', 'THE', 'NOT', 'USE', 'VIA', 'ANY', 'ONLY', 'NEVER',
    'CLAIM', 'THESE', 'ETC', 'SE', 'DO', 'AS', 'AT', 'IN', 'OF', 'TO',
    'BE', 'BY', 'IF', 'IS', 'IT', 'AN', 'ON', 'UP',
    'AI',
}

GAP_TERM_MIN_LENGTH = 3


# ==============================================
# SECTION EXTRACTION
# ==============================================

def extract_section(text, heading):
    """Extract content between heading and next ## heading."""
    lines = text.splitlines()
    in_section = False
    result = []
    for line in lines:
        if line.startswith(heading):
            in_section = True
            continue
        if in_section and line.startswith('## '):
            break
        if in_section:
            result.append(line)
    return '\n'.join(result)


# ==============================================
# GAP TERM EXTRACTION
# ==============================================

def extract_gap_terms(background_text):
    """
    Dynamically extract tool/credential names from the Confirmed Gaps section
    of CANDIDATE_BACKGROUND.md. Returns a set of lowercase strings for matching.
    """
    gaps_section = extract_section(background_text, "## Confirmed Gaps")
    terms = set()

    for line in gaps_section.splitlines():
        if not line.strip().startswith('-'):
            continue

        paren_matches = re.findall(r'\(([^)]+)\)', line)
        for match in paren_matches:
            for part in match.split(','):
                part = part.strip().rstrip('.')
                part = re.sub(r'\s+etc\.?$', '', part).strip()
                if part and len(part) >= 2:
                    terms.add(part)

        acronyms = re.findall(
            r'\b(?:[A-Z]{2,}(?:[/-][A-Z0-9]+)*|DO-\d+|MIL-STD-\d+)\b', line
        )
        for term in acronyms:
            if term not in GAP_STOP_WORDS:
                terms.add(term)

        camel = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]*)+\b', line)
        for term in camel:
            if term not in GAP_STOP_WORDS:
                terms.add(term)

    cleaned = set()
    for t in terms:
        if len(t) >= GAP_TERM_MIN_LENGTH and t.upper() not in GAP_STOP_WORDS:
            cleaned.add(t)

    return cleaned


# ==============================================
# LAYER 1 – STRING MATCHING
# ==============================================

def run_layer1(cl_lines, gap_terms):
    """
    Run pre-flight string checks against cover letter lines.
    Returns list of finding dicts.
    """
    findings = []

    for rule_name, pattern, fix, case_sensitive in HARDCODED_RULES:
        for i, line in enumerate(cl_lines, start=1):
            if not line.strip():
                continue
            check_line = line if case_sensitive else line.lower()
            check_pattern = pattern if case_sensitive else pattern.lower()
            if check_pattern in check_line:
                snippet = line.strip()[:120] + ('...' if len(line.strip()) > 120 else '')
                findings.append({
                    "layer": 1,
                    "rule": rule_name,
                    "line": i,
                    "flagged_text": snippet,
                    "fix": fix,
                })
                break

    for term in sorted(gap_terms):
        for i, line in enumerate(cl_lines, start=1):
            if not line.strip():
                continue
            if line.strip().startswith('##'):
                continue
            try:
                pattern = r'\b' + re.escape(term) + r'\b'
                if re.search(pattern, line, re.IGNORECASE):
                    snippet = line.strip()[:120] + ('...' if len(line.strip()) > 120 else '')
                    findings.append({
                        "layer": 1,
                        "rule": f"Confirmed gap referenced: {term}",
                        "line": i,
                        "flagged_text": snippet,
                        "fix": f"Remove or rephrase \u2013 '{term}' is in the confirmed gaps list (no professional experience to claim)",
                    })
                    break
            except re.error:
                continue

    return findings
```

- [ ] **Step 2: Run Layer 1 tests to verify they pass**

```
pytest tests/phase4/test_check_cover_letter.py -m "not live" -v -k "layer1 or extract_section or extract_gap or run_layer1 or no_false_positive"
```

Expected: All Layer 1 tests PASS.

- [ ] **Step 3: Commit**

```
git add scripts/check_cover_letter.py tests/phase4/test_check_cover_letter.py tests/fixtures/stage_files/cl_stage2_approved.txt
git commit -m "Add check_cover_letter: Layer 1 string matching + tests"
```

---

## Task 4: Write Layer 2 tests — verify they fail

**Files:**
- Modify: `tests/phase4/test_check_cover_letter.py` (append Layer 2 tests)

- [ ] **Step 1: Append Layer 2 tests to the test file**

Add to the end of `tests/phase4/test_check_cover_letter.py`:

```python
# ==============================================
# run_layer2
# ==============================================

def test_run_layer2_parses_valid_json_response():
    from scripts.check_cover_letter import run_layer2
    mock_response = (
        '[{"violation_type": "Em dash", "line_reference": "line 1",'
        ' "flagged_text": "test \u2014 text", "suggested_fix": "Use en dash"}]'
    )
    client = make_mock_client(mock_response)
    findings = run_layer2(
        client,
        cl_text="test \u2014 text",
        gaps_section="",
        banned_section=""
    )
    assert len(findings) == 1
    assert findings[0]["rule"] == "Em dash"
    assert findings[0]["layer"] == 2


def test_run_layer2_returns_empty_list_for_no_violations():
    from scripts.check_cover_letter import run_layer2
    client = make_mock_client(MOCK_L2_RESPONSE)
    findings = run_layer2(client, cl_text="Clean cover letter text.", gaps_section="", banned_section="")
    assert findings == []


def test_run_layer2_handles_json_parse_failure_gracefully():
    from scripts.check_cover_letter import run_layer2
    client = make_mock_client("This is not JSON at all.")
    findings = run_layer2(client, cl_text="some text", gaps_section="", banned_section="")
    assert len(findings) == 1
    assert findings[0]["rule"] == "JSON parse failure"
    assert findings[0]["layer"] == 2


def test_run_layer2_finding_has_required_keys():
    from scripts.check_cover_letter import run_layer2
    mock_response = (
        '[{"violation_type": "Generic opener", "line_reference": "line 1",'
        ' "flagged_text": "I am excited to apply", "suggested_fix": "Lead with strongest credential"}]'
    )
    client = make_mock_client(mock_response)
    findings = run_layer2(client, cl_text="I am excited to apply for this role.", gaps_section="", banned_section="")
    assert len(findings) == 1
    f = findings[0]
    for key in ("layer", "rule", "line", "flagged_text", "fix"):
        assert key in f
    assert f["layer"] == 2
```

- [ ] **Step 2: Run new tests to verify they fail**

```
pytest tests/phase4/test_check_cover_letter.py -m "not live" -v -k "layer2 or run_layer2"
```

Expected: All four Layer 2 tests FAIL with `ImportError: cannot import name 'run_layer2'`

---

## Task 5: Implement Layer 2

**Files:**
- Modify: `scripts/check_cover_letter.py` (append Layer 2 function)

- [ ] **Step 1: Append `run_layer2` to `scripts/check_cover_letter.py`**

```python
# ==============================================
# LAYER 2 – API ASSESSMENT
# ==============================================

def run_layer2(client, cl_text, gaps_section, banned_section):
    """
    Single API call for nuanced gap and claims assessment.
    Primary purpose: detect implied gap fulfillment – language that conveys experience
    in a confirmed gap area without naming the gap term directly.
    Returns list of finding dicts. Falls back to raw output on JSON parse failure.
    """
    prompt = f"""Review this cover letter text for violations against the confirmed gaps and banned language rules below.

CONFIRMED GAPS (candidate has no professional experience with these \u2013 do not claim or imply):
{gaps_section}

BANNED / CORRECTED LANGUAGE (specific terms and their correct replacements):
{banned_section}

COVER LETTER TEXT:
{cl_text}

Assess the cover letter for:
- IMPLIED GAP FULFILLMENT: Language that conveys experience, ownership, or authority in a confirmed
  gap area without naming the gap term directly. This is the primary concern \u2013 cover letter prose
  can imply gap fulfillment more subtly than resume bullets. Example: "hands-on experience deploying
  cloud infrastructure" implies AWS/Azure/GCP experience even if those terms do not appear.
- Claims that explicitly reference confirmed gap tools, credentials, or domains
- Use of banned terms or language that should be corrected
- GENERIC OPENER PHRASES: Flag sentences that open with "I am excited to apply", "I am writing to
  express", "I am writing to apply", "I am pleased to apply", or similar filler opener patterns
- Fabricated or unverifiable metrics, outcomes, or experience not grounded in confirmed background

IMPORTANT \u2013 EM DASH CLARIFICATION:
The em dash is the specific character \u2014 (U+2014). Only flag this character as a violation.
Hyphens (-) in compound words such as "end-to-end", "mission-critical", "real-time" are correct
usage and must NOT be flagged as em dash violations.

IMPORTANT \u2013 ONLY FLAG ACTUAL VIOLATIONS:
Only flag language that is actually wrong in the cover letter text. Do NOT flag language that already
conforms to the rules. Examples of correct language that must NOT be flagged:
- "mission-critical" \u2013 already the correct term, do not flag
- "Current TS/SCI" \u2013 already the correct form, do not flag
- "Plank Owner" \u2013 already the correct form, do not flag
Flag only what is actually present and actually wrong, not what demonstrates compliance.

Return ONLY a raw JSON array. No markdown fences. No explanation. No preamble.
If no violations found, return an empty array: []

Each finding must follow this exact structure:
{{
  "violation_type": "short label",
  "line_reference": "line N" or "N/A",
  "flagged_text": "exact quoted text from cover letter (keep short)",
  "suggested_fix": "specific correction"
}}"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()

    try:
        findings_raw = json.loads(raw)
        findings = []
        for f in findings_raw:
            findings.append({
                "layer": 2,
                "rule": f.get("violation_type", "Unknown"),
                "line": f.get("line_reference", "N/A"),
                "flagged_text": f.get("flagged_text", ""),
                "fix": f.get("suggested_fix", ""),
            })
        return findings
    except json.JSONDecodeError:
        print("\n  WARNING: Layer 2 response was not valid JSON. Raw output:")
        print("  " + raw[:500])
        return [{
            "layer": 2,
            "rule": "JSON parse failure",
            "line": "N/A",
            "flagged_text": raw[:200],
            "fix": "Review raw API output above manually",
        }]
```

- [ ] **Step 2: Run all non-live tests**

```
pytest tests/phase4/test_check_cover_letter.py -m "not live" -v
```

Expected: All tests PASS (Layer 1 + Layer 2).

- [ ] **Step 3: Commit**

```
git add scripts/check_cover_letter.py tests/phase4/test_check_cover_letter.py
git commit -m "Add check_cover_letter: Layer 2 API assessment + tests"
```

---

## Task 6: Write validate_inputs and pipeline tests — verify they fail

**Files:**
- Modify: `tests/phase4/test_check_cover_letter.py` (append)

- [ ] **Step 1: Append validate_inputs tests**

Add to the end of `tests/phase4/test_check_cover_letter.py`:

```python
# ==============================================
# validate_inputs
# ==============================================

def test_validate_inputs_exits_on_missing_stage2(tmp_path, monkeypatch):
    from scripts.check_cover_letter import validate_inputs
    monkeypatch.chdir(tmp_path)
    package_dir = tmp_path / "data" / "job_packages" / "Test_Role"
    package_dir.mkdir(parents=True)
    # cl_stage2_approved.txt does NOT exist
    stage2_path = str(package_dir / "cl_stage2_approved.txt")

    # CANDIDATE_BACKGROUND.md must exist for this test to isolate the stage2 error
    bg_dir = tmp_path / "context"
    bg_dir.mkdir()
    (bg_dir / "CANDIDATE_BACKGROUND.md").write_text("## Confirmed Gaps\n")

    import scripts.check_cover_letter as mod
    orig = mod.CANDIDATE_BACKGROUND_PATH
    mod.CANDIDATE_BACKGROUND_PATH = str(bg_dir / "CANDIDATE_BACKGROUND.md")

    try:
        with pytest.raises(SystemExit) as exc:
            validate_inputs(str(package_dir), stage2_path)
        assert exc.value.code == 1
    finally:
        mod.CANDIDATE_BACKGROUND_PATH = orig


def test_validate_inputs_exits_on_missing_background(tmp_path, monkeypatch):
    from scripts.check_cover_letter import validate_inputs
    monkeypatch.chdir(tmp_path)
    package_dir = tmp_path / "data" / "job_packages" / "Test_Role"
    package_dir.mkdir(parents=True)
    stage2_path = str(package_dir / "cl_stage2_approved.txt")
    (package_dir / "cl_stage2_approved.txt").write_text("Dear Hiring Manager,\n")

    import scripts.check_cover_letter as mod
    orig = mod.CANDIDATE_BACKGROUND_PATH
    # Point to a path that does not exist
    mod.CANDIDATE_BACKGROUND_PATH = str(tmp_path / "context" / "CANDIDATE_BACKGROUND.md")

    try:
        with pytest.raises(SystemExit) as exc:
            validate_inputs(str(package_dir), stage2_path)
        assert exc.value.code == 1
    finally:
        mod.CANDIDATE_BACKGROUND_PATH = orig
```

- [ ] **Step 2: Run new tests to verify they fail**

```
pytest tests/phase4/test_check_cover_letter.py -m "not live" -v -k "validate"
```

Expected: Both tests FAIL with `ImportError: cannot import name 'validate_inputs'`

---

## Task 7: Implement validate_inputs, print_findings, _run_checks, main

**Files:**
- Modify: `scripts/check_cover_letter.py` (append remaining functions)

- [ ] **Step 1: Append remaining functions to `scripts/check_cover_letter.py`**

```python
# ==============================================
# OUTPUT FORMATTING
# ==============================================

def print_findings(findings, layer_num, layer_label):
    """Print findings for one layer. Returns count."""
    layer_findings = [f for f in findings if f["layer"] == layer_num]
    if not layer_findings:
        print(f"  {layer_label}: No violations found.")
    else:
        for f in layer_findings:
            line_ref = f"Line {f['line']}" if str(f['line']).isdigit() else f['line']
            print(f"\n  [L{f['layer']} \u2013 {f['rule']}]")
            print(f"    {line_ref}: \"{f['flagged_text']}\"")
            print(f"    Fix: {f['fix']}")
    return len(layer_findings)


# ==============================================
# VALIDATION
# ==============================================

def validate_inputs(package_dir, stage2_path):
    errors = []
    if not os.path.exists(package_dir):
        errors.append(f"Package folder not found: {package_dir}")
    if not os.path.exists(stage2_path):
        errors.append(f"cl_stage2_approved.txt not found: {stage2_path}")
    if not os.path.exists(CANDIDATE_BACKGROUND_PATH):
        errors.append(f"CANDIDATE_BACKGROUND.md not found: {CANDIDATE_BACKGROUND_PATH}")
    if errors:
        print("============================================================")
        print("COVER LETTER QUALITY CHECK \u2013 INPUT ERROR")
        print("============================================================")
        for e in errors:
            print(f"  ERROR: {e}")
        sys.exit(1)


# ==============================================
# MAIN
# ==============================================

def main():
    parser = argparse.ArgumentParser(
        description="Cover letter quality checker \u2013 Layer 1 string matching + Layer 2 API assessment"
    )
    parser.add_argument("--role", required=True, help="Role folder name (e.g. BAH_LCI_MBSE)")
    args = parser.parse_args()

    ROLE = args.role
    PACKAGE_DIR = os.path.join(JOBS_PACKAGES_DIR, ROLE)
    STAGE2_PATH = os.path.join(PACKAGE_DIR, "cl_stage2_approved.txt")

    validate_inputs(PACKAGE_DIR, STAGE2_PATH)

    RESULTS_PATH = os.path.join(PACKAGE_DIR, "cl_stage3_review.txt")

    buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buffer

    try:
        _run_checks(ROLE, PACKAGE_DIR, STAGE2_PATH)
    finally:
        sys.stdout = old_stdout

    output = buffer.getvalue()
    with open(RESULTS_PATH, 'w', encoding='utf-8') as f:
        f.write(output)

    print(f"Results written to {RESULTS_PATH}")
    sys.exit(1 if "Status: FAIL" in output else 0)


def _run_checks(ROLE, PACKAGE_DIR, STAGE2_PATH):
    """Run both check layers. All output goes to stdout (captured by caller)."""
    print("============================================================")
    print("COVER LETTER QUALITY CHECK")
    print("============================================================")
    print(f"Role:   {ROLE}")
    print(f"Source: {STAGE2_PATH}")

    with open(STAGE2_PATH, 'r', encoding='utf-8') as f:
        cl_text = f.read()
    cl_lines = cl_text.splitlines()

    with open(CANDIDATE_BACKGROUND_PATH, 'r', encoding='utf-8') as f:
        background_text = f.read()

    # \u2500\u2500 LAYER 1 \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    print("\n--- LAYER 1: Pre-flight checks ---")
    print("Loading CANDIDATE_BACKGROUND.md...")
    gap_terms = extract_gap_terms(background_text)
    print(f"  Gap terms extracted: {len(gap_terms)} terms")
    print("Running string checks...")

    l1_findings = run_layer1(cl_lines, gap_terms)
    l1_count = print_findings(l1_findings, 1, "LAYER 1")

    # \u2500\u2500 LAYER 2 \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    print("\n--- LAYER 2: API assessment ---")
    print("Stripping PII...")
    safe_cl = strip_pii(cl_text)
    gaps_section = extract_section(background_text, "## Confirmed Gaps")
    banned_section = extract_section(background_text, "## Banned / Corrected Language")

    print("Calling API...")
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    l2_findings = run_layer2(client, safe_cl, gaps_section, banned_section)
    l2_count = print_findings(l2_findings, 2, "LAYER 2")

    # \u2500\u2500 SUMMARY \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    total = l1_count + l2_count
    print("\n============================================================")
    print("SUMMARY")
    print("============================================================")
    print(f"Layer 1: {l1_count} violation(s)")
    print(f"Layer 2: {l2_count} finding(s)")
    print(f"Total:   {total}")
    print()
    if total == 0:
        print("Status: PASS")
    else:
        print(f"Status: FAIL \u2013 {total} violation(s) found. Correct cl_stage2_approved.txt and rerun.")
    print("============================================================")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run full test suite (non-live)**

```
pytest tests/phase4/test_check_cover_letter.py -m "not live" -v
```

Expected: All tests PASS.

- [ ] **Step 3: Commit**

```
git add scripts/check_cover_letter.py tests/phase4/test_check_cover_letter.py
git commit -m "Add check_cover_letter: validate_inputs, _run_checks, main"
```

---

## Task 8: Write and verify PII safety test

**Files:**
- Modify: `tests/phase4/test_check_cover_letter.py` (append PII test)

- [ ] **Step 1: Append PII safety test**

Add to the end of `tests/phase4/test_check_cover_letter.py`:

```python
# ==============================================
# PII safety -- strip_pii called before API
# ==============================================

def test_no_pii_in_api_payload(pii_values, monkeypatch):
    """
    Verifies PII is stripped before the API call.
    Sets PII env vars, reloads pii_filter, strips text the same way _run_checks does,
    then confirms the API payload contains no PII values.
    """
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

    raw_cl = (
        f"Contact {pii_values['name']} at {pii_values['email']}\n"
        + FIXTURE_CL_STAGE2.read_text(encoding="utf-8")
    )
    safe_cl = pii_module.strip_pii(raw_cl)

    for pii_value in pii_values.values():
        assert pii_value not in safe_cl, f"PII not stripped before API call: {pii_value}"

    from scripts.check_cover_letter import run_layer2
    client = make_mock_client(MOCK_L2_RESPONSE)

    run_layer2(client, safe_cl, gaps_section="No GitLab.", banned_section="Use en dashes.")

    call_args = client.messages.create.call_args
    full_payload = str(call_args)
    for pii_value in pii_values.values():
        assert pii_value not in full_payload, f"PII found in Layer 2 API payload: {pii_value}"
```

- [ ] **Step 2: Run PII test**

```
pytest tests/phase4/test_check_cover_letter.py -m "not live" -v -k "pii"
```

Expected: PASS

- [ ] **Step 3: Run full non-live suite one final time**

```
pytest tests/phase4/test_check_cover_letter.py -m "not live" -v
```

Expected: All tests PASS, 0 failures.

- [ ] **Step 4: Commit**

```
git add tests/phase4/test_check_cover_letter.py
git commit -m "Add check_cover_letter: PII safety test"
```

---

## Task 9: (Optional) Live integration test

Requires `ANTHROPIC_API_KEY` set in environment. Skipped in CI by default.

**Files:**
- Modify: `tests/phase4/test_check_cover_letter.py` (append live test)

- [ ] **Step 1: Append live test**

Add to the end of `tests/phase4/test_check_cover_letter.py`:

```python
# ==============================================
# Live test (Tier 2 -- real API)
# ==============================================

@pytest.mark.live
def test_run_layer2_live():
    """Tier 2: real API call. Requires ANTHROPIC_API_KEY in environment."""
    import os
    import anthropic
    from scripts.check_cover_letter import run_layer2, extract_section

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    cl_text = FIXTURE_CL_STAGE2.read_text(encoding="utf-8")
    background = FIXTURE_BACKGROUND.read_text(encoding="utf-8")

    gaps_section = extract_section(background, "## Confirmed Gaps")
    banned_section = extract_section(background, "## Banned / Corrected Language")

    findings = run_layer2(client, cl_text, gaps_section, banned_section)
    assert isinstance(findings, list)
    for f in findings:
        assert "layer" in f
        assert "rule" in f
        assert f["layer"] == 2
```

- [ ] **Step 2: Run live test**

```
pytest tests/phase4/test_check_cover_letter.py -m live -v
```

Expected: PASS — clean fixture should produce no findings or a valid empty list.

- [ ] **Step 3: Commit**

```
git add tests/phase4/test_check_cover_letter.py
git commit -m "Add check_cover_letter: live API integration test"
```

---

## Verification

After all tasks are complete, run the full non-live suite and do a smoke-test invocation:

```
pytest tests/phase4/test_check_cover_letter.py -m "not live" -v
```

Smoke test (requires a role package with `cl_stage2_approved.txt`):

```
python -m scripts.check_cover_letter --role Anduril_SE_OA
```

Expected: `Results written to data/job_packages/Anduril_SE_OA/cl_stage3_review.txt`
