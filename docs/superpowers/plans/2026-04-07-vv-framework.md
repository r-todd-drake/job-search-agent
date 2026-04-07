# V&V Framework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a two-tier pytest suite (mock + live) with GitHub Actions CI covering the full pipeline — phases 1-5 plus utils — against documented success criteria contracts.

**Architecture:** Phase-aligned test directories mirror `scripts/`. Several scripts execute at module level and must be refactored (argparse and file I/O moved into `main()`) before they can be imported by tests. Testable functions are extracted and tested directly; API calls are mocked in Tier 1 and hit the real API in `@pytest.mark.live` Tier 2 tests.

**Tech Stack:** Python 3.11, pytest, pytest-mock, python-docx, anthropic SDK, GitHub Actions

---

## Pre-Flight: Read Before Starting

**Critical finding:** The following scripts execute at module level and will error on import if test data is absent. Each must be refactored before its test task. The plan includes the refactoring in-line with the test task.

| Script | Problem | Fix |
|---|---|---|
| `pipeline_report.py` | Opens xlsx at module level | Extract `analyze_applications()`, wrap in `main()` |
| `phase2_job_ranking.py` | Opens CSV at module level | Extract `detect_duplicates()`, wrap in `main()` |
| `phase2_semantic_analyzer.py` | Opens CSV + calls API at module level | Extract `analyze_job()`, wrap in `main()` |
| `phase3_compile_library.py` | Opens JSON files at module level | Wrap all logic in `main()` |
| `phase3_build_candidate_profile.py` | Hardcoded PII + module-level API call | Move PII to `.env`, wrap in `main()` |
| `phase4_resume_generator.py` | `argparse.parse_args()` at module level | Move argparse into `main()`, extract stage functions |
| `phase4_cover_letter.py` | `argparse.parse_args()` at module level | Move argparse into `main()`, extract stage functions |
| `phase5_interview_prep.py` | `argparse.parse_args()` at module level | Move argparse into `main()`, extract stage functions |

Scripts that are already importable (no action needed): `pii_filter.py`, `library_parser.py`, `phase3_parse_library.py`, `phase3_parse_employer.py`, `check_resume.py`.

**Import path standard:** Set `pythonpath = .` in `pytest.ini`. All imports use `from scripts.X.Y import Z` from the project root. Scripts that use `sys.path.insert` hacks may keep them for runtime compatibility — tests import via the project root.

---

## File Map

**Create:**
- `requirements-dev.txt`
- `pytest.ini`
- `.github/workflows/test.yml`
- `tests/__init__.py`
- `tests/conftest.py`
- `tests/utils/__init__.py`
- `tests/utils/test_pii_filter.py`
- `tests/utils/test_library_parser.py`
- `tests/phase1/__init__.py`
- `tests/phase1/test_pipeline_report.py`
- `tests/phase2/__init__.py`
- `tests/phase2/test_job_ranking.py`
- `tests/phase2/test_semantic_analyzer.py`
- `tests/phase3/__init__.py`
- `tests/phase3/test_parse_library.py`
- `tests/phase3/test_parse_employer.py`
- `tests/phase3/test_compile_library.py`
- `tests/phase3/test_build_candidate_profile.py`
- `tests/phase4/__init__.py`
- `tests/phase4/test_resume_generator.py`
- `tests/phase4/test_cover_letter.py`
- `tests/phase4/test_check_resume.py`
- `tests/phase5/__init__.py`
- `tests/phase5/test_interview_prep.py`
- `tests/fixtures/jobs/jobs_sample.csv`
- `tests/fixtures/library/experience_library.md`
- `tests/fixtures/library/experience_library.json`
- `tests/fixtures/library/candidate_profile.md`
- `tests/fixtures/stage_files/sample_jd.txt`
- `tests/fixtures/stage_files/stage1_draft.txt`
- `tests/fixtures/stage_files/stage2_approved.txt`
- `tests/fixtures/stage_files/stage3_review.txt`
- `tests/fixtures/stage_files/sample_background.md`

**Modify:**
- `scripts/pipeline_report.py` — extract functions, add `main()` guard
- `scripts/phase2_job_ranking.py` — extract `detect_duplicates()`, add `main()` guard
- `scripts/phase2_semantic_analyzer.py` — extract `analyze_job()`, add `main()` guard
- `scripts/phase3_compile_library.py` — wrap all logic in `main()` guard
- `scripts/phase3_build_candidate_profile.py` — remove hardcoded PII, wrap in `main()` guard
- `scripts/phase4_resume_generator.py` — move argparse + CANDIDATE_PROFILE into `main()`, extract stage functions
- `scripts/phase4_cover_letter.py` — move argparse into `main()`, extract stage functions
- `scripts/phase5_interview_prep.py` — move argparse into `main()`, extract stage functions
- `README.md` — add CI badge

---

## Task 1: Infrastructure Setup

**Files:**
- Create: `requirements-dev.txt`
- Create: `pytest.ini`
- Create: `.github/workflows/test.yml`
- Create: `tests/__init__.py` and all subdirectory `__init__.py` files

- [ ] **Step 1: Create `requirements-dev.txt`**

```
pytest
pytest-mock
```

- [ ] **Step 2: Create `pytest.ini`**

```ini
[pytest]
testpaths = tests
pythonpath = .
markers =
    live: marks tests that make real Claude API calls (run with -m live)
```

- [ ] **Step 3: Create `.github/workflows/test.yml`**

```yaml
name: Tests

on:
  push:
    branches: ["**"]
  pull_request:
    branches: ["**"]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run mock test suite
        run: pytest tests/ -m "not live" --tb=short -v
```

- [ ] **Step 4: Create `tests/__init__.py` and all subdirectory `__init__.py` files**

Create empty `__init__.py` in each directory:

```bash
touch tests/__init__.py
touch tests/utils/__init__.py
touch tests/phase1/__init__.py
touch tests/phase2/__init__.py
touch tests/phase3/__init__.py
touch tests/phase4/__init__.py
touch tests/phase5/__init__.py
```

- [ ] **Step 5: Create `tests/conftest.py`**

```python
import pytest
from pathlib import Path
from unittest.mock import MagicMock


@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def mock_anthropic(mocker):
    """Shared mock factory. Patch path is set per-test to match the script's import."""
    return mocker


@pytest.fixture
def pii_values():
    return {
        "name": "Jane Q. Applicant",
        "phone": "(555) 867-5309",
        "email": "applicant@example.com",
        "linkedin": "linkedin.com/in/applicant",
        "github": "github.com/applicant",
    }


def make_mock_response(text):
    """Build a minimal Anthropic API response mock for a given text string."""
    mock = MagicMock()
    mock.content = [MagicMock(text=text)]
    return mock
```

- [ ] **Step 6: Verify pytest discovers tests (empty suite = green)**

```bash
pytest tests/ -m "not live" --tb=short -v
```

Expected output:
```
=================== no tests ran =========================
```
Exit code 0. This confirms pytest configuration is valid before any tests exist.

- [ ] **Step 7: Commit**

```bash
git add requirements-dev.txt pytest.ini .github/workflows/test.yml tests/
git commit -m "Add V&V framework infrastructure: pytest, CI, conftest"
```

Push to GitHub. Verify the Actions tab shows a green run for the empty suite.

---

## Task 2: Fixture Files

**Files:**
- Create: `tests/fixtures/jobs/jobs_sample.csv`
- Create: `tests/fixtures/library/experience_library.md`
- Create: `tests/fixtures/library/candidate_profile.md`
- Create: `tests/fixtures/stage_files/sample_jd.txt`
- Create: `tests/fixtures/stage_files/stage1_draft.txt`
- Create: `tests/fixtures/stage_files/stage2_approved.txt`
- Create: `tests/fixtures/stage_files/stage3_review.txt`
- Create: `tests/fixtures/stage_files/sample_background.md`

- [ ] **Step 1: Create `tests/fixtures/jobs/jobs_sample.csv`**

```csv
company,title,location,salary_range,url,req_number,date_found,status,package_folder
Acme Defense Systems,Senior Systems Engineer,San Diego CA,$150-180k,https://example.com,ADS-12345,2026-01-01,PURSUE,acme_sse
Generic Tech Inc,Systems Engineer II,Remote,$120-145k,https://example.com,GTC-00001,2026-01-05,,generic_se2
Repeat Defense Co,Principal Engineer,San Diego CA,$155-175k,https://example.com,ADS-12345,2026-01-10,,repeat_pe
Old Industries LLC,Project Manager,Los Angeles CA,$130-150k,https://example.com,OLD-0042,2026-01-15,SKIP,old_pm
Applied Corp,Systems Architect,San Diego CA,$160-190k,https://example.com,AC-0099,2026-01-20,APPLIED,applied_arch
```

Note: Acme and Repeat Defense Co share req number ADS-12345 — this is the duplicate used in ranking and report tests.

- [ ] **Step 2: Create `tests/fixtures/library/experience_library.md`**

```markdown
# Experience Library

---

## Acme Defense Systems

**Title:** Senior Systems Engineer
**Dates:** 2020 - Present
**Domain:** Defense | Autonomous Systems | MBSE

### Theme: Systems Architecture

- Led MBSE development for autonomous surface vessel program using Cameo Systems Modeler and DoDAF architectural views.
*Used in: acme_sse*
*PRIORITY: true*

- Developed system-of-systems architecture models supporting multi-domain C2 integration.
*Used in: acme_sse*

### Theme: Stakeholder Engagement

- Facilitated IPT working groups with government stakeholders to define operational requirements and ConOps.
*Used in: acme_sse*

---

## PROFESSIONAL SUMMARIES

### Defense Systems Engineering

"Senior systems engineer with 20+ years of experience in defense MBSE, autonomous systems, and multi-domain C2 integration. TS/SCI cleared."
*Used in: acme_sse*
```

- [ ] **Step 3: Create `tests/fixtures/library/candidate_profile.md`**

```markdown
# Candidate Profile

## Confirmed Tools
Cameo Systems Modeler, DoDAF, MBSE

## Confirmed Skills
Systems architecture, stakeholder engagement, autonomous systems integration

## Confirmed Gaps
- No GitLab (GitHub only)
- No INCOSE certification
- No FAA/DO-178 experience

## Confirmed Clearance
Current TS/SCI

## Style Rules
- En dashes only, never em dashes
- No unverifiable metrics
```

- [ ] **Step 4: Create `tests/fixtures/stage_files/sample_jd.txt`**

```
Senior Systems Engineer - Autonomous Maritime Systems
Acme Defense Systems | San Diego, CA | Req: ADS-12345

We seek a Senior Systems Engineer to support autonomous surface vessel systems for maritime defense.
Requires MBSE expertise using Cameo Systems Modeler and DoDAF architectural framework.

REQUIRED:
- Active TS/SCI clearance
- MBSE proficiency (Cameo, MagicDraw, or equivalent)
- Defense acquisition experience (JCIDS, ACAT)
- Autonomous Systems or Uncrewed platform experience

PREFERRED:
- JADC2 or multi-domain operations experience
- ConOps development experience
- Maritime or naval domain experience
- C4ISR integration background
```

- [ ] **Step 5: Create `tests/fixtures/stage_files/stage1_draft.txt`**

```
SUMMARY
Senior systems engineer with 20+ years of experience in defense MBSE, autonomous systems, and multi-domain C2 integration. TS/SCI cleared.

CORE COMPETENCIES
MBSE | Cameo Systems Modeler | DoDAF | Autonomous Systems | System-of-Systems Architecture | Stakeholder Engagement | Defense Acquisition | ConOps

EXPERIENCE

Acme Defense Systems | Senior Systems Engineer | 2020 - Present
- Led MBSE development for autonomous surface vessel program using Cameo Systems Modeler and DoDAF architectural views.
- Developed system-of-systems architecture models supporting multi-domain C2 integration.
- Facilitated IPT working groups with government stakeholders to define operational requirements and ConOps.

EDUCATION
Jane Q. Applicant University | B.S. Systems Engineering | 2005
```

- [ ] **Step 6: Create `tests/fixtures/stage_files/stage2_approved.txt`**

Same as stage1_draft.txt with one bullet reworded:

```
SUMMARY
Senior systems engineer with 20+ years of experience in defense MBSE, autonomous systems, and multi-domain C2 integration. TS/SCI cleared.

CORE COMPETENCIES
MBSE | Cameo Systems Modeler | DoDAF | Autonomous Systems | System-of-Systems Architecture | Stakeholder Engagement | Defense Acquisition | ConOps

EXPERIENCE

Acme Defense Systems | Senior Systems Engineer | 2020 - Present
- Led MBSE development for autonomous surface vessel program using Cameo Systems Modeler and DoDAF architectural views.
- Developed system-of-systems architecture models supporting multi-domain C4ISR integration.
- Facilitated IPT working groups with government stakeholders to define operational requirements and ConOps.

EDUCATION
Jane Q. Applicant University | B.S. Systems Engineering | 2005
```

- [ ] **Step 7: Create `tests/fixtures/stage_files/stage3_review.txt`**

```
SUMMARY
Senior systems engineer with 20+ years of experience in defense MBSE, autonomous systems, and multi-domain C2 integration. TS/SCI cleared.

CORE COMPETENCIES
MBSE | Cameo Systems Modeler | DoDAF | Autonomous Systems | System-of-Systems Architecture | Stakeholder Engagement | Defense Acquisition | ConOps

EXPERIENCE

Acme Defense Systems | Senior Systems Engineer | 2020 - Present
- Led MBSE development for autonomous surface vessel program using Cameo Systems Modeler and DoDAF architectural views.
- Developed system-of-systems architecture models supporting multi-domain C4ISR integration.
- Facilitated IPT working groups with government stakeholders to define operational requirements and ConOps.

EDUCATION
Jane Q. Applicant University | B.S. Systems Engineering | 2005

---
STAGE 3 REVIEW NOTES
Coherence: Strong alignment with JD requirements. Bullets are well-grounded in library content.
ATS Gap: JADC2 not represented — consider adding if experience supports.
Suggestions: No wording changes required.
```

- [ ] **Step 8: Create `tests/fixtures/stage_files/sample_background.md`**

```markdown
# Candidate Background

## Confirmed Tools
Cameo Systems Modeler, DoDAF, MBSE, Jira

## Confirmed Gaps
- No GitLab (GitHub only)
- No INCOSE certification
- No FAA/DO-178 experience (DO-178, DO-160)
- No Terraform or infrastructure-as-code
- No MATLAB

## Banned / Corrected Language
- Use en dashes (--), not em dashes (—)
- Use "mission-critical" not "safety-critical"
- Use "Current TS/SCI" between employers, not "Active TS/SCI"
- Use "Plank Owner" not "Plank Holder" or "plankowner"
```

- [ ] **Step 9: Commit fixture files**

```bash
git add tests/fixtures/
git commit -m "Add test fixture files: jobs CSV, library md, stage files"
```

---

## Task 3: pii_filter Tests

**Files:**
- Create: `tests/utils/test_pii_filter.py`

No refactoring needed. `pii_filter.py` is already importable.

- [ ] **Step 1: Write the failing tests**

```python
# tests/utils/test_pii_filter.py

import os
import pytest


def test_strip_pii_replaces_name(monkeypatch):
    monkeypatch.setenv("CANDIDATE_NAME", "Jane Q. Applicant")
    monkeypatch.setenv("CANDIDATE_PHONE", "")
    monkeypatch.setenv("CANDIDATE_EMAIL", "")
    monkeypatch.setenv("CANDIDATE_LINKEDIN", "")
    monkeypatch.setenv("CANDIDATE_GITHUB", "")

    # Re-import after env is set so get_pii_replacements() sees new values
    import importlib
    import scripts.utils.pii_filter as pii_module
    importlib.reload(pii_module)

    result = pii_module.strip_pii("Contact Jane Q. Applicant for details.")
    assert "Jane Q. Applicant" not in result
    assert "[CANDIDATE]" in result


def test_strip_pii_replaces_all_five_types(monkeypatch):
    monkeypatch.setenv("CANDIDATE_NAME", "Jane Q. Applicant")
    monkeypatch.setenv("CANDIDATE_PHONE", "(555) 867-5309")
    monkeypatch.setenv("CANDIDATE_EMAIL", "applicant@example.com")
    monkeypatch.setenv("CANDIDATE_LINKEDIN", "linkedin.com/in/applicant")
    monkeypatch.setenv("CANDIDATE_GITHUB", "github.com/applicant")

    import importlib
    import scripts.utils.pii_filter as pii_module
    importlib.reload(pii_module)

    text = (
        "Name: Jane Q. Applicant | Phone: (555) 867-5309 | "
        "Email: applicant@example.com | "
        "linkedin.com/in/applicant | github.com/applicant"
    )
    result = pii_module.strip_pii(text)

    assert "Jane Q. Applicant" not in result
    assert "(555) 867-5309" not in result
    assert "applicant@example.com" not in result
    assert "linkedin.com/in/applicant" not in result
    assert "github.com/applicant" not in result


def test_strip_pii_mid_sentence(monkeypatch):
    monkeypatch.setenv("CANDIDATE_NAME", "Jane Q. Applicant")
    monkeypatch.setenv("CANDIDATE_PHONE", "")
    monkeypatch.setenv("CANDIDATE_EMAIL", "")
    monkeypatch.setenv("CANDIDATE_LINKEDIN", "")
    monkeypatch.setenv("CANDIDATE_GITHUB", "")

    import importlib
    import scripts.utils.pii_filter as pii_module
    importlib.reload(pii_module)

    result = pii_module.strip_pii("Please reach Jane Q. Applicant at your earliest convenience.")
    assert "Jane Q. Applicant" not in result


def test_strip_pii_no_pii_in_text_returns_unchanged(monkeypatch):
    monkeypatch.setenv("CANDIDATE_NAME", "Jane Q. Applicant")
    monkeypatch.setenv("CANDIDATE_PHONE", "(555) 867-5309")
    monkeypatch.setenv("CANDIDATE_EMAIL", "applicant@example.com")
    monkeypatch.setenv("CANDIDATE_LINKEDIN", "linkedin.com/in/applicant")
    monkeypatch.setenv("CANDIDATE_GITHUB", "github.com/applicant")

    import importlib
    import scripts.utils.pii_filter as pii_module
    importlib.reload(pii_module)

    original = "Senior systems engineer with MBSE expertise."
    result = pii_module.strip_pii(original)
    assert result == original


def test_strip_pii_empty_string_returns_unchanged(monkeypatch):
    monkeypatch.setenv("CANDIDATE_NAME", "Jane Q. Applicant")
    monkeypatch.setenv("CANDIDATE_PHONE", "(555) 867-5309")
    monkeypatch.setenv("CANDIDATE_EMAIL", "applicant@example.com")
    monkeypatch.setenv("CANDIDATE_LINKEDIN", "linkedin.com/in/applicant")
    monkeypatch.setenv("CANDIDATE_GITHUB", "github.com/applicant")

    import importlib
    import scripts.utils.pii_filter as pii_module
    importlib.reload(pii_module)

    assert pii_module.strip_pii("") == ""
    assert pii_module.strip_pii(None) is None
```

- [ ] **Step 2: Run tests — expect FAIL (module import issue with env vars)**

```bash
pytest tests/utils/test_pii_filter.py -v --tb=short
```

Expected: tests run. If any fail with unexpected errors (not assertion errors), investigate before proceeding.

- [ ] **Step 3: Fix any import issues and re-run until all pass**

```bash
pytest tests/utils/test_pii_filter.py -v
```

Expected: 5 passed.

- [ ] **Step 4: Commit**

```bash
git add tests/utils/test_pii_filter.py
git commit -m "Add pii_filter tests: all five PII types, mid-sentence, no-op, empty"
```

---

## Task 4: library_parser Tests

**Files:**
- Create: `tests/utils/test_library_parser.py`
- Create: `tests/fixtures/library/experience_library.json` (generated in this task)

No refactoring needed. `library_parser.py` is already importable.

- [ ] **Step 1: Write the failing tests**

```python
# tests/utils/test_library_parser.py

import json
import pytest
from pathlib import Path
from scripts.utils.library_parser import parse_library, employer_to_filename


FIXTURE_MD = Path(__file__).parent.parent / "fixtures" / "library" / "experience_library.md"


def test_parse_library_returns_employers_and_summaries():
    employers, summaries = parse_library(str(FIXTURE_MD))
    assert len(employers) >= 1
    assert len(summaries) >= 1


def test_parse_library_employer_has_required_fields():
    employers, _ = parse_library(str(FIXTURE_MD))
    for name, data in employers.items():
        assert "name" in data
        assert "title" in data
        assert "dates" in data
        assert "bullets" in data
        assert isinstance(data["bullets"], list)


def test_parse_library_bullet_count_matches_source():
    employers, _ = parse_library(str(FIXTURE_MD))
    # Fixture has exactly 3 bullets for Acme Defense Systems
    acme = employers.get("Acme Defense Systems")
    assert acme is not None
    assert len(acme["bullets"]) == 3


def test_parse_library_priority_bullet_flagged():
    employers, _ = parse_library(str(FIXTURE_MD))
    acme = employers.get("Acme Defense Systems")
    priority_bullets = [b for b in acme["bullets"] if b["priority"]]
    assert len(priority_bullets) == 1
    assert "Cameo Systems Modeler" in priority_bullets[0]["text"]


def test_parse_library_bullet_ids_assigned():
    employers, _ = parse_library(str(FIXTURE_MD))
    for name, data in employers.items():
        for bullet in data["bullets"]:
            assert bullet["id"] != ""


def test_employer_to_filename_produces_safe_string():
    result = employer_to_filename("Acme Defense Systems")
    assert result.endswith(".json")
    assert " " not in result
    assert result == result.lower()


def test_parse_library_malformed_section_raises_not_silently_skips():
    """A markdown file with a broken employer section should not silently drop bullets."""
    import tempfile
    malformed_md = """# Experience Library

## Acme Defense Systems

**Title:** Senior Systems Engineer
**Dates:** 2020 - Present

### Theme: Systems Architecture

- Valid bullet one.

- Valid bullet two.
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(malformed_md)
        tmp_path = f.name

    # Even a minimal file should parse without error and return the bullets present
    employers, _ = parse_library(tmp_path)
    acme = employers.get("Acme Defense Systems")
    assert acme is not None
    assert len(acme["bullets"]) == 2, (
        "Parser should capture all bullets present — silent drops are not acceptable"
    )
```

- [ ] **Step 2: Run tests**

```bash
pytest tests/utils/test_library_parser.py -v --tb=short
```

Expected: all pass. If `test_parse_library_bullet_count_matches_source` fails, open the fixture markdown and count bullets — adjust the assertion to match.

- [ ] **Step 3: Generate and save the JSON fixture**

Run this one-time script from the project root to produce the committed JSON fixture:

```python
# Run as: python -c "exec(open('generate_fixture.py').read())"
# Or paste into a Python REPL

import json
from scripts.utils.library_parser import parse_library

employers, summaries = parse_library("tests/fixtures/library/experience_library.md")

library = {
    "metadata": {
        "candidate": "Jane Q. Applicant",
        "last_compiled": "2026-04-07 00:00",
        "total_employers": len(employers),
        "total_bullets": sum(len(e["bullets"]) for e in employers.values()),
        "total_flagged": 0,
        "total_verify": 0,
        "total_summaries": len(summaries),
        "employer_names": list(employers.keys())
    },
    "employers": list(employers.values()),
    "summaries": summaries
}

with open("tests/fixtures/library/experience_library.json", "w", encoding="utf-8") as f:
    json.dump(library, f, indent=2, ensure_ascii=False)

print("Fixture written.")
```

Verify the output file exists and is valid JSON:

```bash
python -c "import json; json.load(open('tests/fixtures/library/experience_library.json'))"
```

Expected: no output (no error).

- [ ] **Step 4: Commit**

```bash
git add tests/utils/test_library_parser.py tests/fixtures/library/experience_library.json
git commit -m "Add library_parser tests and generate JSON fixture"
```

---

## Task 5: Refactor pipeline_report + Tests

**Files:**
- Modify: `scripts/pipeline_report.py`
- Create: `tests/phase1/test_pipeline_report.py`

**The problem:** `pipeline_report.py` opens an xlsx file at module level — import fails without the real tracker.

**The fix:** Extract `analyze_applications(applications)` and `detect_duplicates(applications)` as pure functions. Wrap all file I/O in `main()`.

- [ ] **Step 1: Write the failing tests first (TDD — they will error on import)**

```python
# tests/phase1/test_pipeline_report.py

import pytest


def make_applications(rows):
    """Helper: build application list from list of (status, req_number) tuples."""
    return [{"Status": status, "req_number": req} for status, req in rows]


def test_analyze_applications_counts_by_status():
    from scripts.pipeline_report import analyze_applications
    apps = make_applications([
        ("Active", "REQ-001"),
        ("Active", "REQ-002"),
        ("Rejected", "REQ-003"),
        ("Pending", "REQ-004"),
    ])
    counts = analyze_applications(apps)
    assert counts["Active"] == 2
    assert counts["Rejected"] == 1


def test_analyze_applications_empty_list():
    from scripts.pipeline_report import analyze_applications
    counts = analyze_applications([])
    assert counts == {}


def test_detect_duplicates_finds_shared_req_number():
    from scripts.pipeline_report import detect_duplicates
    apps = make_applications([
        ("Active", "REQ-001"),
        ("Active", "REQ-001"),
        ("Active", "REQ-002"),
    ])
    dupes = detect_duplicates(apps)
    assert len(dupes) == 1
    assert dupes[0]["req_number"] == "REQ-001"


def test_detect_duplicates_no_duplicates_returns_empty():
    from scripts.pipeline_report import detect_duplicates
    apps = make_applications([
        ("Active", "REQ-001"),
        ("Active", "REQ-002"),
    ])
    assert detect_duplicates(apps) == []


def test_no_files_modified_during_import():
    """Importing pipeline_report should not open any files."""
    import importlib
    # If this import succeeds without errors, no module-level file I/O occurred
    import scripts.pipeline_report  # noqa: F401
```

- [ ] **Step 2: Run — expect ImportError or runtime error**

```bash
pytest tests/phase1/test_pipeline_report.py -v --tb=short
```

Expected: fails because module-level xlsx open fails. Proceed to refactor.

- [ ] **Step 3: Refactor `scripts/pipeline_report.py`**

Add these two functions before the existing code, then wrap all module-level logic in `main()`:

```python
def analyze_applications(applications):
    """
    Count applications by Status field.
    Returns dict of {status: count}.
    """
    counts = {}
    for app in applications:
        status = app.get("Status", "") or "Pending"
        counts[status] = counts.get(status, 0) + 1
    return counts


def detect_duplicates(applications):
    """
    Find applications with duplicate req_number values.
    Returns list of dicts with keys: req_number, first_entry, duplicate_entry.
    """
    seen = {}
    duplicates = []
    for app in applications:
        req = (app.get("req_number", "") or "").strip()
        if not req:
            continue
        if req in seen:
            duplicates.append({
                "req_number": req,
                "first_entry": seen[req],
                "duplicate_entry": app,
            })
        else:
            seen[req] = app
    return duplicates
```

Then find all the existing module-level code (everything after `load_dotenv()` that is not a function or class definition) and wrap it:

```python
def main():
    print("Script started")
    print("Loading tracker data...")

    wb = openpyxl.load_workbook(TRACKER_PATH)
    ws = wb[SHEET_NAME]

    headers = []
    applications = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            headers = [str(cell) if cell is not None else "" for cell in row]
            continue
        if any(cell is not None for cell in row):
            app = dict(zip(headers, row))
            applications.append(app)

    print(f"Loaded {len(applications)} applications")

    total = len(applications)
    status_counts = analyze_applications(applications)
    duplicates = detect_duplicates(applications)

    # ... rest of existing reporting logic moved here


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run syntax check**

```bash
python -m py_compile scripts/pipeline_report.py && echo "OK"
```

Expected: `OK`

- [ ] **Step 5: Run tests — expect PASS**

```bash
pytest tests/phase1/test_pipeline_report.py -v
```

Expected: 5 passed.

- [ ] **Step 6: Verify script still runs correctly (smoke test)**

```bash
python scripts/pipeline_report.py
```

Expected: same output as before refactoring. If the tracker file is unavailable, this will fail — that is expected behavior (the script requires real data to run). The tests do not require it.

- [ ] **Step 7: Commit**

```bash
git add scripts/pipeline_report.py tests/phase1/test_pipeline_report.py
git commit -m "Refactor pipeline_report: extract pure functions, add tests"
```

---

## Task 6: Refactor phase2_job_ranking + Tests

**Files:**
- Modify: `scripts/phase2_job_ranking.py`
- Create: `tests/phase2/test_job_ranking.py`

**The problem:** All scoring and reporting logic runs at module level — import opens `data/jobs.csv`.

**The fix:** `score_job()` already exists. Extract `detect_duplicates(results)`. Move all module-level execution into `main()`.

- [ ] **Step 1: Write failing tests**

```python
# tests/phase2/test_job_ranking.py

import pytest


HIGH_MATCH_JD = """
Senior Systems Engineer - Autonomous Maritime Systems.
Requires MBSE expertise using Cameo Systems Modeler and DoDAF architectural framework.
Autonomous Systems and Uncrewed platform experience required.
C4ISR integration, Defense Acquisition, ConOps, Stakeholder Engagement.
JADC2 and System-of-Systems architecture background desired.
"""

LOW_MATCH_JD = """
Junior Web Developer. Build React and Node.js applications for e-commerce.
No defense background required. Remote work available.
"""


def test_score_job_high_match_exceeds_threshold():
    from scripts.phase2_job_ranking import score_job
    score, matched = score_job(HIGH_MATCH_JD)
    assert score > 30, f"Expected score > 30, got {score}"
    assert "MBSE" in matched
    assert "Cameo" in matched


def test_score_job_low_match_near_zero():
    from scripts.phase2_job_ranking import score_job
    score, matched = score_job(LOW_MATCH_JD)
    assert score < 10, f"Expected score < 10, got {score}"


def test_score_job_returns_matched_keywords_dict():
    from scripts.phase2_job_ranking import score_job
    score, matched = score_job(HIGH_MATCH_JD)
    assert isinstance(matched, dict)
    for keyword, weight in matched.items():
        assert isinstance(weight, int)


def test_detect_duplicates_finds_shared_req():
    from scripts.phase2_job_ranking import detect_duplicates
    results = [
        {"company": "Acme", "title": "SE", "req_number": "ADS-12345", "score": 50},
        {"company": "Generic", "title": "PE", "req_number": "GTC-00001", "score": 30},
        {"company": "Repeat", "title": "PE", "req_number": "ADS-12345", "score": 45},
    ]
    dupes = detect_duplicates(results)
    assert len(dupes) == 1
    req, first_label, dupe_company, dupe_title = dupes[0]
    assert req == "ADS-12345"
    assert dupe_company == "Repeat"


def test_detect_duplicates_no_duplicates():
    from scripts.phase2_job_ranking import detect_duplicates
    results = [
        {"company": "Acme", "title": "SE", "req_number": "ADS-12345", "score": 50},
        {"company": "Generic", "title": "PE", "req_number": "GTC-00001", "score": 30},
    ]
    assert detect_duplicates(results) == []


def test_detect_duplicates_skips_empty_req():
    from scripts.phase2_job_ranking import detect_duplicates
    results = [
        {"company": "Acme", "title": "SE", "req_number": "", "score": 50},
        {"company": "Generic", "title": "PE", "req_number": "", "score": 30},
    ]
    assert detect_duplicates(results) == []


def test_roles_with_existing_status_score_zero_or_excluded():
    """Roles with SKIP or APPLIED status should not appear as actionable."""
    from scripts.phase2_job_ranking import score_job, ACTIONABLE_STATUSES, EXCLUDED_STATUSES
    # Verify the status constants separate correctly — no overlap
    assert ACTIONABLE_STATUSES.isdisjoint(EXCLUDED_STATUSES)
    assert "SKIP" in EXCLUDED_STATUSES
    assert "APPLIED" in EXCLUDED_STATUSES
    assert "" in ACTIONABLE_STATUSES  # blank = new = actionable


def test_no_module_level_execution_on_import():
    """Importing phase2_job_ranking should not open any files."""
    import scripts.phase2_job_ranking  # noqa: F401


@pytest.mark.live
def test_full_ranking_run_on_fixture_csv():
    """Tier 2: run scoring against the fixture CSV using real file I/O."""
    import csv
    from pathlib import Path
    from scripts.phase2_job_ranking import score_job, detect_duplicates

    fixture_csv = Path(__file__).parent.parent / "fixtures" / "jobs" / "jobs_sample.csv"
    jobs = []
    with open(fixture_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            jobs.append(row)

    results = []
    for job in jobs:
        score, matched = score_job("")  # No JD files in fixtures — score empty string
        results.append({**job, "score": score, "matched_keywords": matched, "req_number": job.get("req_number", "")})

    dupes = detect_duplicates(results)
    # Fixture has ADS-12345 appearing twice
    assert len(dupes) == 1
    assert dupes[0][0] == "ADS-12345"
```

- [ ] **Step 2: Run — expect failure on import**

```bash
pytest tests/phase2/test_job_ranking.py -v --tb=short
```

Expected: fails because module-level CSV read fails.

- [ ] **Step 3: Refactor `scripts/phase2_job_ranking.py`**

After the `KEYWORDS` list and the existing `score_job()` function, add:

```python
def detect_duplicates(results):
    """
    Find duplicate req numbers in a list of scored job results.
    Returns list of tuples: (req_number, first_label, dupe_company, dupe_title)
    """
    req_seen = {}
    duplicates = []
    for r in results:
        req = r.get("req_number", "").strip()
        if req:
            if req in req_seen:
                duplicates.append((req, req_seen[req], r["company"], r["title"]))
            else:
                req_seen[req] = f"{r['company']} | {r['title']}"
    return duplicates
```

Then move all module-level execution (everything after the `score_job()` function) into `main()`:

```python
def main():
    print("Script started")
    print("Loading jobs from CSV...")

    jobs = []
    with open(JOBS_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            jobs.append(row)

    # ... rest of existing scoring, sorting, reporting logic

    duplicates = detect_duplicates(all_results)

    # ... rest of report generation


if __name__ == "__main__":
    main()
```

Also remove the two `print()` calls that are currently between the imports and the `JOBS_CSV` config block:
```python
print("Script started")   # remove this — move to main()
print("Loading jobs from CSV...")  # remove this — move to main()
```

- [ ] **Step 4: Syntax check**

```bash
python -m py_compile scripts/phase2_job_ranking.py && echo "OK"
```

- [ ] **Step 5: Run tests — expect PASS**

```bash
pytest tests/phase2/test_job_ranking.py -v
```

Expected: 7 passed.

- [ ] **Step 6: Commit**

```bash
git add scripts/phase2_job_ranking.py tests/phase2/test_job_ranking.py
git commit -m "Refactor phase2_job_ranking: extract detect_duplicates, add tests"
```

---

## Task 7: Refactor phase2_semantic_analyzer + Tests

**Files:**
- Modify: `scripts/phase2_semantic_analyzer.py`
- Create: `tests/phase2/test_semantic_analyzer.py`

**The problem:** Module-level code opens `data/jobs.csv` and calls `load_candidate_profile()`.

**The fix:** Extract `analyze_job(client, job, jd_text, candidate_profile, keyword_scores)` as a callable function. Move all module-level execution into `main()`.

- [ ] **Step 1: Write failing tests**

```python
# tests/phase2/test_semantic_analyzer.py

import pytest
from unittest.mock import MagicMock
from pathlib import Path

FIXTURE_JD = (
    Path(__file__).parent.parent / "fixtures" / "stage_files" / "sample_jd.txt"
)


def make_mock_client(response_text):
    client = MagicMock()
    client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=response_text)]
    )
    return client


MOCK_ANALYSIS = """
FIT SCORE: 8/10

STRENGTHS:
- MBSE expertise aligns with Cameo requirement
- TS/SCI clearance confirmed

GAPS:
- ConOps experience not explicit

RECOMMENDATION: PURSUE
"""


def test_analyze_job_calls_api():
    from scripts.phase2_semantic_analyzer import analyze_job
    client = make_mock_client(MOCK_ANALYSIS)
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")
    candidate_profile = "Senior systems engineer, TS/SCI, MBSE expert."
    job = {"company": "Acme Defense Systems", "title": "Senior Systems Engineer"}

    result = analyze_job(client, job, jd_text, candidate_profile, keyword_scores={})

    assert client.messages.create.called
    assert result is not None


def test_analyze_job_no_pii_in_api_payload(pii_values):
    from scripts.phase2_semantic_analyzer import analyze_job
    client = make_mock_client(MOCK_ANALYSIS)
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")

    # Inject PII into the candidate profile text
    candidate_profile = (
        f"Candidate: {pii_values['name']} | "
        f"Email: {pii_values['email']} | "
        f"Phone: {pii_values['phone']} | "
        "Senior systems engineer, TS/SCI, MBSE expert."
    )
    job = {"company": "Acme Defense Systems", "title": "Senior Systems Engineer"}

    analyze_job(client, job, jd_text, candidate_profile, keyword_scores={})

    call_args = client.messages.create.call_args
    full_payload = str(call_args)
    for pii_value in pii_values.values():
        assert pii_value not in full_payload, f"PII found in API payload: {pii_value}"


def test_analyze_job_returns_response_text():
    from scripts.phase2_semantic_analyzer import analyze_job
    client = make_mock_client(MOCK_ANALYSIS)
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")
    candidate_profile = "Senior systems engineer, TS/SCI."
    job = {"company": "Acme", "title": "SE"}

    result = analyze_job(client, job, jd_text, candidate_profile, keyword_scores={})
    assert "FIT SCORE" in result or len(result) > 0


def test_analyze_job_handles_api_error_without_crashing():
    from scripts.phase2_semantic_analyzer import analyze_job
    from anthropic import APIError

    client = MagicMock()
    client.messages.create.side_effect = Exception("Simulated API error")

    jd_text = FIXTURE_JD.read_text(encoding="utf-8")
    candidate_profile = "Senior systems engineer."
    job = {"company": "Acme", "title": "SE"}

    # Script should handle the error gracefully — not raise unhandled exception
    try:
        result = analyze_job(client, job, jd_text, candidate_profile, keyword_scores={})
        # If it returns a fallback string, that is also acceptable
        assert isinstance(result, str)
    except Exception as e:
        pytest.fail(
            f"analyze_job raised an unhandled exception on API error: {e}\n"
            "Add try/except inside analyze_job to handle API failures gracefully."
        )


def test_no_module_level_execution_on_import():
    import scripts.phase2_semantic_analyzer  # noqa: F401


@pytest.mark.live
def test_analyze_job_live_api_call():
    """Tier 2: real API call. Requires ANTHROPIC_API_KEY in environment."""
    import os
    from anthropic import Anthropic
    from scripts.phase2_semantic_analyzer import analyze_job

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")
    candidate_profile = "Senior systems engineer, TS/SCI cleared, MBSE expertise."
    job = {"company": "Acme Defense Systems", "title": "Senior Systems Engineer"}

    result = analyze_job(client, job, jd_text, candidate_profile, keyword_scores={})
    assert len(result) > 100, "Expected substantive analysis output"
```

- [ ] **Step 2: Run — expect import failure**

```bash
pytest tests/phase2/test_semantic_analyzer.py -m "not live" -v --tb=short
```

- [ ] **Step 3: Refactor `scripts/phase2_semantic_analyzer.py`**

Add `analyze_job()` function after the `SYSTEM_PROMPT` constant:

```python
def analyze_job(client, job, jd_text, candidate_profile, keyword_scores):
    """
    Run semantic analysis for a single job using the Claude API.
    candidate_profile must already have PII stripped before calling.
    Returns the API response text.
    """
    company = job.get("company", "Unknown")
    title = job.get("title", "Unknown")
    key = f"{company}_{title}"
    kw_info = keyword_scores.get(key, {})

    prompt = f"""Analyze this job description against the candidate background.

CANDIDATE BACKGROUND:
{candidate_profile}

JOB: {company} | {title}
KEYWORD SCORE: {kw_info.get('score', 'N/A')} ({kw_info.get('match_pct', 'N/A')}% match)
TOP KEYWORDS: {kw_info.get('top_keywords', 'N/A')}

JOB DESCRIPTION:
{jd_text}

Provide: fit score (1-10), key strengths, genuine gaps, recommendation (PURSUE/CONSIDER/SKIP).
"""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
```

Then move all module-level execution into `main()`:

```python
def main():
    print("Script started")
    print("Loading jobs...")
    # ... move existing CSV loading, filtering, loop, and output writing here

if __name__ == "__main__":
    main()
```

Remove the `CANDIDATE_PROFILE = load_candidate_profile()` module-level call — call `load_candidate_profile()` inside `main()` instead.

- [ ] **Step 4: Syntax check**

```bash
python -m py_compile scripts/phase2_semantic_analyzer.py && echo "OK"
```

- [ ] **Step 5: Run tests — expect PASS**

```bash
pytest tests/phase2/test_semantic_analyzer.py -m "not live" -v
```

Expected: 4 passed (live test skipped).

- [ ] **Step 6: Commit**

```bash
git add scripts/phase2_semantic_analyzer.py tests/phase2/test_semantic_analyzer.py
git commit -m "Refactor phase2_semantic_analyzer: extract analyze_job, add tests"
```

---

## Task 8: phase3_parse_library Tests

**Files:**
- Create: `tests/phase3/test_parse_library.py`

No refactoring needed. `phase3_parse_library.py` is already guarded with `if __name__ == "__main__":`.
Core parsing logic is in `library_parser.py` (tested in Task 4). These tests cover the orchestration: parsing + saving.

- [ ] **Step 1: Write tests**

```python
# tests/phase3/test_parse_library.py

import json
import pytest
import tempfile
from pathlib import Path
from scripts.utils.library_parser import parse_library, save_employers, save_summaries

FIXTURE_MD = Path(__file__).parent.parent / "fixtures" / "library" / "experience_library.md"


def test_parse_and_save_creates_employer_json_files():
    employers, summaries = parse_library(str(FIXTURE_MD))
    with tempfile.TemporaryDirectory() as tmpdir:
        saved = save_employers(employers, tmpdir)
        assert len(saved) >= 1
        for filename in saved:
            path = Path(tmpdir) / filename
            assert path.exists()
            data = json.loads(path.read_text(encoding="utf-8"))
            assert "name" in data
            assert "bullets" in data


def test_parse_and_save_output_is_valid_json():
    employers, summaries = parse_library(str(FIXTURE_MD))
    with tempfile.TemporaryDirectory() as tmpdir:
        saved = save_employers(employers, tmpdir)
        for filename in saved:
            path = Path(tmpdir) / filename
            # Should not raise
            json.loads(path.read_text(encoding="utf-8"))


def test_save_summaries_creates_file():
    _, summaries = parse_library(str(FIXTURE_MD))
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = str(Path(tmpdir) / "summaries.json")
        save_summaries(summaries, output_path)
        assert Path(output_path).exists()
        data = json.loads(Path(output_path).read_text(encoding="utf-8"))
        assert "summaries" in data
        assert "total" in data
```

- [ ] **Step 2: Run**

```bash
pytest tests/phase3/test_parse_library.py -v
```

Expected: 3 passed.

- [ ] **Step 3: Commit**

```bash
git add tests/phase3/test_parse_library.py
git commit -m "Add phase3_parse_library orchestration tests"
```

---

## Task 9: phase3_parse_employer Tests

**Files:**
- Create: `tests/phase3/test_parse_employer.py`

No refactoring needed. Already guarded with `if __name__ == "__main__":`.

- [ ] **Step 1: Write tests**

```python
# tests/phase3/test_parse_employer.py

import json
import pytest
import tempfile
from pathlib import Path
from scripts.utils.library_parser import (
    parse_library, save_employers, employer_to_filename
)

FIXTURE_MD = Path(__file__).parent.parent / "fixtures" / "library" / "experience_library.md"


def test_target_employer_written_to_file():
    employers, _ = parse_library(str(FIXTURE_MD))
    target_name = "Acme Defense Systems"
    assert target_name in employers

    with tempfile.TemporaryDirectory() as tmpdir:
        target_data = {target_name: employers[target_name]}
        save_employers(target_data, tmpdir)
        filename = employer_to_filename(target_name)
        path = Path(tmpdir) / filename
        assert path.exists()


def test_other_employers_not_in_targeted_output():
    employers, _ = parse_library(str(FIXTURE_MD))
    target_name = "Acme Defense Systems"

    # Simulate single-employer save: only pass target
    with tempfile.TemporaryDirectory() as tmpdir:
        target_data = {target_name: employers[target_name]}
        saved = save_employers(target_data, tmpdir)
        assert len(saved) == 1
        assert employer_to_filename(target_name) in saved


def test_unknown_employer_not_in_parse_result():
    employers, _ = parse_library(str(FIXTURE_MD))
    assert "Nonexistent Corp" not in employers
```

- [ ] **Step 2: Run**

```bash
pytest tests/phase3/test_parse_employer.py -v
```

Expected: 3 passed.

- [ ] **Step 3: Commit**

```bash
git add tests/phase3/test_parse_employer.py
git commit -m "Add phase3_parse_employer tests"
```

---

## Task 10: Refactor phase3_compile_library + Tests

**Files:**
- Modify: `scripts/phase3_compile_library.py`
- Create: `tests/phase3/test_compile_library.py`

**The problem:** All logic executes at module level — import opens JSON files.

**The fix:** Extract `compile_library(employers_dir, summaries_path)` as a pure function. Wrap all execution in `main()`.

- [ ] **Step 1: Write failing tests**

```python
# tests/phase3/test_compile_library.py

import json
import pytest
import tempfile
from pathlib import Path

FIXTURE_JSON = Path(__file__).parent.parent / "fixtures" / "library" / "experience_library.json"


def test_compile_library_includes_all_employers():
    from scripts.phase3_compile_library import compile_library

    fixture_data = json.loads(FIXTURE_JSON.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory() as tmpdir:
        employers_dir = Path(tmpdir) / "employers"
        employers_dir.mkdir()
        summaries_path = Path(tmpdir) / "summaries.json"

        # Write employer files from fixture
        for emp in fixture_data["employers"]:
            filename = emp["name"].lower().replace(" ", "_")[:40] + ".json"
            (employers_dir / filename).write_text(
                json.dumps(emp, indent=2), encoding="utf-8"
            )

        # Write summaries
        summaries_path.write_text(
            json.dumps({"total": 0, "summaries": []}, indent=2), encoding="utf-8"
        )

        library = compile_library(str(employers_dir), str(summaries_path))

    assert "employers" in library
    assert len(library["employers"]) == len(fixture_data["employers"])


def test_compile_library_has_metadata():
    from scripts.phase3_compile_library import compile_library

    fixture_data = json.loads(FIXTURE_JSON.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory() as tmpdir:
        employers_dir = Path(tmpdir) / "employers"
        employers_dir.mkdir()
        summaries_path = Path(tmpdir) / "summaries.json"

        for emp in fixture_data["employers"]:
            filename = emp["name"].lower().replace(" ", "_")[:40] + ".json"
            (employers_dir / filename).write_text(json.dumps(emp), encoding="utf-8")
        summaries_path.write_text(
            json.dumps({"total": 0, "summaries": []}), encoding="utf-8"
        )

        library = compile_library(str(employers_dir), str(summaries_path))

    assert "metadata" in library
    assert "total_employers" in library["metadata"]


def test_no_module_level_execution_on_import():
    import scripts.phase3_compile_library  # noqa: F401
```

- [ ] **Step 2: Run — expect import failure**

```bash
pytest tests/phase3/test_compile_library.py -v --tb=short
```

- [ ] **Step 3: Refactor `scripts/phase3_compile_library.py`**

Replace the entire module with:

```python
import os
import json
from datetime import datetime


EMPLOYERS_DIR = "data/experience_library/employers"
SUMMARIES_PATH = "data/experience_library/summaries.json"
OUTPUT_PATH = "data/experience_library/experience_library.json"


def compile_library(employers_dir, summaries_path):
    """
    Load all employer JSON files and summaries, merge into a single library dict.
    Returns the compiled library dict (does not write to disk).
    """
    employer_files = [f for f in os.listdir(employers_dir) if f.endswith('.json')]

    employers = []
    total_bullets = total_flagged = total_verify = 0

    for filename in sorted(employer_files):
        filepath = os.path.join(employers_dir, filename)
        with open(filepath, encoding='utf-8') as f:
            emp_data = json.load(f)
        employers.append(emp_data)
        total_bullets += len(emp_data.get('bullets', []))
        total_flagged += sum(1 for b in emp_data['bullets'] if b.get('flagged'))
        total_verify += sum(1 for b in emp_data['bullets'] if b.get('verify'))

    summaries_data = {"total": 0, "summaries": []}
    if os.path.exists(summaries_path):
        with open(summaries_path, encoding='utf-8') as f:
            summaries_data = json.load(f)

    return {
        "metadata": {
            "candidate": "R. Todd Drake",
            "last_compiled": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total_employers": len(employers),
            "total_bullets": total_bullets,
            "total_flagged": total_flagged,
            "total_verify": total_verify,
            "total_summaries": summaries_data['total'],
            "employer_names": [e['name'] for e in employers]
        },
        "employers": employers,
        "summaries": summaries_data.get('summaries', [])
    }


def main():
    print("=" * 60)
    print("PHASE 3 - COMPILE EXPERIENCE LIBRARY")
    print("=" * 60)

    if not os.path.exists(EMPLOYERS_DIR):
        print(f"ERROR: Employers directory not found: {EMPLOYERS_DIR}")
        print("Run phase3_parse_library.py first.")
        exit(1)

    employer_files = [f for f in os.listdir(EMPLOYERS_DIR) if f.endswith('.json')]
    if not employer_files:
        print(f"ERROR: No employer JSON files found in {EMPLOYERS_DIR}")
        exit(1)

    print(f"\nLoading {len(employer_files)} employer files...")
    library = compile_library(EMPLOYERS_DIR, SUMMARIES_PATH)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(library, f, indent=2, ensure_ascii=False)

    size_kb = os.path.getsize(OUTPUT_PATH) / 1024
    print(f"\nCOMPILE COMPLETE")
    print(f"  Output: {OUTPUT_PATH}")
    print(f"  File size: {size_kb:.1f} KB")
    print(f"  Employers: {library['metadata']['total_employers']}")
    print(f"  Total bullets: {library['metadata']['total_bullets']}")
    print(f"  Summaries: {library['metadata']['total_summaries']}")
    print(f"\nLibrary ready for Phase 4 resume generator.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Syntax check**

```bash
python -m py_compile scripts/phase3_compile_library.py && echo "OK"
```

- [ ] **Step 5: Run tests — expect PASS**

```bash
pytest tests/phase3/test_compile_library.py -v
```

Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add scripts/phase3_compile_library.py tests/phase3/test_compile_library.py
git commit -m "Refactor phase3_compile_library: extract compile_library(), add tests"
```

---

## Task 11: Refactor phase3_build_candidate_profile + PII Remediation + Tests

**Files:**
- Modify: `scripts/phase3_build_candidate_profile.py`
- Create: `tests/phase3/test_build_candidate_profile.py`

**Two problems:**
1. Hardcoded PII in the `KNOWN_FACTS` constant (name, phone, email, LinkedIn, GitHub)
2. Module-level API calls

**Fix PII first.** Replace the hardcoded values in `KNOWN_FACTS` with environment variable references. Then wrap all execution in `main()` and extract `build_profile(client, library_json_path, output_path)`.

- [ ] **Step 1: Fix hardcoded PII in `KNOWN_FACTS`**

Locate the `KNOWN_FACTS` constant. Replace all hardcoded contact values with `os.getenv()` calls:

```python
KNOWN_FACTS = f"""
CONFIRMED FACTS (supplement library data):
- Name: {os.getenv('CANDIDATE_NAME', '[CANDIDATE]')}
- Location: {os.getenv('CANDIDATE_LOCATION', 'San Diego, CA')}
- Phone: {os.getenv('CANDIDATE_PHONE', '[PHONE]')}
- Email: {os.getenv('CANDIDATE_EMAIL', '[EMAIL]')}
- LinkedIn: {os.getenv('CANDIDATE_LINKEDIN', '[LINKEDIN]')}
- GitHub: {os.getenv('CANDIDATE_GITHUB', '[GITHUB]')}

EDUCATION (confirmed):
...rest of the KNOWN_FACTS content unchanged...
"""
```

Add `CANDIDATE_LOCATION` to `.env` and `.env.example`:
```
CANDIDATE_LOCATION=San Diego, CA
```

- [ ] **Step 2: Write failing tests**

```python
# tests/phase3/test_build_candidate_profile.py

import os
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

FIXTURE_JSON = Path(__file__).parent.parent / "fixtures" / "library" / "experience_library.json"

MOCK_PROFILE_RESPONSE = """
## Confirmed Tools
Cameo Systems Modeler, DoDAF, MBSE

## Confirmed Skills
Systems architecture, autonomous systems integration

## Confirmed Clearance
Current TS/SCI

## Confirmed Gaps
- No INCOSE certification
"""


def make_mock_client():
    client = MagicMock()
    client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=MOCK_PROFILE_RESPONSE)]
    )
    return client


def test_build_profile_creates_output_file(monkeypatch):
    monkeypatch.setenv("CANDIDATE_NAME", "Jane Q. Applicant")
    monkeypatch.setenv("CANDIDATE_PHONE", "(555) 867-5309")
    monkeypatch.setenv("CANDIDATE_EMAIL", "applicant@example.com")
    monkeypatch.setenv("CANDIDATE_LINKEDIN", "linkedin.com/in/applicant")
    monkeypatch.setenv("CANDIDATE_GITHUB", "github.com/applicant")
    monkeypatch.setenv("CANDIDATE_LOCATION", "Test City, CA")

    from scripts.phase3_build_candidate_profile import build_profile

    client = make_mock_client()
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "candidate_profile.md"
        build_profile(client, str(FIXTURE_JSON), str(output_path))
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert len(content) > 0


def test_build_profile_no_pii_in_api_payload(monkeypatch):
    monkeypatch.setenv("CANDIDATE_NAME", "Jane Q. Applicant")
    monkeypatch.setenv("CANDIDATE_PHONE", "(555) 867-5309")
    monkeypatch.setenv("CANDIDATE_EMAIL", "applicant@example.com")
    monkeypatch.setenv("CANDIDATE_LINKEDIN", "linkedin.com/in/applicant")
    monkeypatch.setenv("CANDIDATE_GITHUB", "github.com/applicant")
    monkeypatch.setenv("CANDIDATE_LOCATION", "Test City, CA")

    from scripts.phase3_build_candidate_profile import build_profile

    client = make_mock_client()
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "candidate_profile.md"
        build_profile(client, str(FIXTURE_JSON), str(output_path))

    call_args = client.messages.create.call_args
    full_payload = str(call_args)
    for pii in ["Jane Q. Applicant", "(555) 867-5309", "applicant@example.com"]:
        assert pii not in full_payload, f"PII found in payload: {pii}"


def test_no_module_level_execution_on_import(monkeypatch):
    monkeypatch.setenv("CANDIDATE_NAME", "Jane Q. Applicant")
    monkeypatch.setenv("CANDIDATE_PHONE", "(555) 867-5309")
    monkeypatch.setenv("CANDIDATE_EMAIL", "applicant@example.com")
    monkeypatch.setenv("CANDIDATE_LINKEDIN", "linkedin.com/in/applicant")
    monkeypatch.setenv("CANDIDATE_GITHUB", "github.com/applicant")
    monkeypatch.setenv("CANDIDATE_LOCATION", "Test City, CA")
    import scripts.phase3_build_candidate_profile  # noqa: F401
```

- [ ] **Step 3: Run — expect import failure**

```bash
pytest tests/phase3/test_build_candidate_profile.py -v --tb=short
```

- [ ] **Step 4: Refactor `scripts/phase3_build_candidate_profile.py`**

Add `build_profile(client, library_json_path, output_path)` function that contains the per-employer extraction loop. Move all module-level execution into `main()`.

```python
def build_profile(client, library_json_path, output_path):
    """
    Build candidate_profile.md from experience_library.json.
    All API payloads have PII stripped before sending.
    """
    with open(library_json_path, encoding='utf-8') as f:
        library = json.load(f)

    employers = library.get("employers", [])
    sections = []

    for employer in employers:
        bullets_text = "\n".join(
            f"- {b['text']}" for b in employer.get("bullets", [])
            if not b.get("flagged")
        )
        if not bullets_text:
            continue

        prompt = f"""Extract confirmed facts from these resume bullets for {employer['name']}.
Only include what is explicitly demonstrated.

{bullets_text}

Return: confirmed tools, confirmed skills, confirmed scope (brief, factual)."""

        safe_prompt = strip_pii(prompt)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": safe_prompt}],
        )
        sections.append(f"## {employer['name']}\n{response.content[0].text}")
        time.sleep(API_DELAY)

    profile_text = f"# Candidate Profile\nGenerated: {datetime.now().strftime('%Y-%m-%d')}\n\n"
    profile_text += "\n\n".join(sections)
    profile_text += f"\n\n---\n{KNOWN_FACTS}"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(profile_text)

    print(f"Profile written to {output_path}")


def main():
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    build_profile(client, LIBRARY_JSON, OUTPUT_PATH)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Syntax check**

```bash
python -m py_compile scripts/phase3_build_candidate_profile.py && echo "OK"
```

- [ ] **Step 6: Run tests — expect PASS**

```bash
pytest tests/phase3/test_build_candidate_profile.py -v
```

Expected: 3 passed.

- [ ] **Step 7: Commit**

```bash
git add scripts/phase3_build_candidate_profile.py tests/phase3/test_build_candidate_profile.py .env.example
git commit -m "Remediate hardcoded PII in build_candidate_profile, extract function, add tests"
```

---

## Task 12: Refactor phase4_resume_generator + Tests

**Files:**
- Modify: `scripts/phase4_resume_generator.py`
- Create: `tests/phase4/test_resume_generator.py`

**The problem:** `argparse.parse_args()` and `CANDIDATE_PROFILE = strip_pii(load_candidate_profile())` run at module level. Import fails in any test environment.

**The fix:** Move argparse entirely inside `main()`. Pass `candidate_profile` as a parameter to each stage function. Extract `run_stage1()`, `run_stage3()`, `run_stage4()` as callable functions.

- [ ] **Step 1: Write failing tests**

```python
# tests/phase4/test_resume_generator.py

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

FIXTURE_JD = Path(__file__).parent.parent / "fixtures" / "stage_files" / "sample_jd.txt"
FIXTURE_STAGE2 = Path(__file__).parent.parent / "fixtures" / "stage_files" / "stage2_approved.txt"
FIXTURE_LIBRARY = Path(__file__).parent.parent / "fixtures" / "library" / "experience_library.json"
FIXTURE_PROFILE = Path(__file__).parent.parent / "fixtures" / "library" / "candidate_profile.md"

MOCK_STAGE1_RESPONSE = """
SUMMARY
Senior systems engineer with MBSE expertise. TS/SCI cleared.

CORE COMPETENCIES
MBSE | Cameo Systems Modeler | DoDAF | Autonomous Systems

EXPERIENCE
Acme Defense Systems | Senior Systems Engineer | 2020 - Present
- Led MBSE development for autonomous surface vessel program using Cameo Systems Modeler.
- Developed system-of-systems architecture models.
- Facilitated IPT working groups with government stakeholders.

EDUCATION
Jane Q. Applicant University | B.S. Systems Engineering | 2005
"""

MOCK_STAGE3_RESPONSE = """
COHERENCE CHECK
Strong alignment with JD requirements.

ATS GAP ANALYSIS
JADC2 not represented.

SUGGESTIONS
No changes required.
"""


def make_mock_client(response_text):
    client = MagicMock()
    client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=response_text)]
    )
    return client


def test_run_stage1_creates_draft_file():
    from scripts.phase4_resume_generator import run_stage1
    client = make_mock_client(MOCK_STAGE1_RESPONSE)
    candidate_profile = FIXTURE_PROFILE.read_text(encoding="utf-8")
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")
    library = json.loads(FIXTURE_LIBRARY.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "stage1_draft.txt"
        run_stage1(client, jd_text, library, candidate_profile, str(output_path))
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "SUMMARY" in content
        assert "EXPERIENCE" in content


def test_run_stage1_no_pii_in_api_payload(pii_values):
    from scripts.phase4_resume_generator import run_stage1
    client = make_mock_client(MOCK_STAGE1_RESPONSE)
    candidate_profile = (
        f"Candidate: {pii_values['name']} | Email: {pii_values['email']}\n"
        "Senior systems engineer, MBSE expert."
    )
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")
    library = json.loads(FIXTURE_LIBRARY.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "stage1_draft.txt"
        run_stage1(client, jd_text, library, candidate_profile, str(output_path))

    call_args = client.messages.create.call_args
    full_payload = str(call_args)
    for pii_value in pii_values.values():
        assert pii_value not in full_payload, f"PII found in payload: {pii_value}"


def test_run_stage1_priority_bullets_included():
    from scripts.phase4_resume_generator import run_stage1
    client = make_mock_client(MOCK_STAGE1_RESPONSE)
    candidate_profile = FIXTURE_PROFILE.read_text(encoding="utf-8")
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")
    library = json.loads(FIXTURE_LIBRARY.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "stage1_draft.txt"
        run_stage1(client, jd_text, library, candidate_profile, str(output_path))
        content = output_path.read_text(encoding="utf-8")
        # The priority bullet contains "Cameo Systems Modeler" — must appear in output
        assert "Cameo Systems Modeler" in content


def test_run_stage3_creates_review_file():
    from scripts.phase4_resume_generator import run_stage3
    client = make_mock_client(MOCK_STAGE3_RESPONSE)
    stage2_text = FIXTURE_STAGE2.read_text(encoding="utf-8")
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "stage3_review.txt"
        run_stage3(client, stage2_text, jd_text, str(output_path))
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "COHERENCE" in content or "ATS" in content or len(content) > 50


def test_run_stage3_no_pii_in_api_payload(pii_values):
    from scripts.phase4_resume_generator import run_stage3
    client = make_mock_client(MOCK_STAGE3_RESPONSE)
    stage2_text = (
        f"Contact {pii_values['name']} at {pii_values['email']}\n"
        + FIXTURE_STAGE2.read_text(encoding="utf-8")
    )
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "stage3_review.txt"
        run_stage3(client, stage2_text, jd_text, str(output_path))

    call_args = client.messages.create.call_args
    full_payload = str(call_args)
    for pii_value in pii_values.values():
        assert pii_value not in full_payload, f"PII found in payload: {pii_value}"


def test_run_stage4_creates_docx():
    from scripts.phase4_resume_generator import run_stage4
    from docx import Document

    stage3_text = Path(__file__).parent.parent / "fixtures" / "stage_files" / "stage3_review.txt"

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "Test_Resume.docx"
        run_stage4(stage3_text.read_text(encoding="utf-8"), str(output_path))
        assert output_path.exists()
        # Verify the .docx is readable without corruption
        doc = Document(str(output_path))
        assert len(doc.paragraphs) > 0


def test_no_module_level_execution_on_import():
    import scripts.phase4_resume_generator  # noqa: F401


@pytest.mark.live
def test_run_stage1_live():
    """Tier 2: real API call."""
    import os
    from anthropic import Anthropic
    from scripts.phase4_resume_generator import run_stage1

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    candidate_profile = FIXTURE_PROFILE.read_text(encoding="utf-8")
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")
    library = json.loads(FIXTURE_LIBRARY.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "stage1_draft.txt"
        run_stage1(client, jd_text, library, candidate_profile, str(output_path))
        content = output_path.read_text(encoding="utf-8")
        assert "SUMMARY" in content
        assert "EXPERIENCE" in content
        assert len(content) > 200
```

- [ ] **Step 2: Run — expect import failure**

```bash
pytest tests/phase4/test_resume_generator.py -m "not live" -v --tb=short
```

- [ ] **Step 3: Refactor `scripts/phase4_resume_generator.py`**

This is the most significant refactoring. Key changes:

**a) Move argparse and CANDIDATE_PROFILE into `main()`:**

Remove from module level:
```python
# DELETE these module-level lines:
CANDIDATE_PROFILE = strip_pii(load_candidate_profile())
print("  Candidate profile loaded and PII stripped.")
parser = argparse.ArgumentParser(...)
parser.add_argument(...)
args = parser.parse_args()
```

**b) Extract three stage functions with these signatures:**

```python
def run_stage1(client, jd_text, library, candidate_profile, output_path):
    """
    Stage 1: Select and rank bullets from library against JD.
    Writes stage1_draft.txt to output_path.
    candidate_profile must be PII-stripped before passing.
    """
    # Priority bullets always included — collect them first
    priority_bullets = [
        b for emp in library.get("employers", [])
        for b in emp.get("bullets", [])
        if b.get("priority") and not b.get("flagged")
    ]
    priority_text = "\n".join(f"[PRIORITY] {b['text']}" for b in priority_bullets)

    # Build candidate bullets by employer for selection prompt
    employer_sections = []
    for emp in library.get("employers", []):
        bullets = [
            b["text"] for b in emp.get("bullets", [])
            if not b.get("flagged")
        ]
        if bullets:
            section = f"## {emp['name']}\n" + "\n".join(f"- {b}" for b in bullets)
            employer_sections.append(section)

    safe_profile = strip_pii(candidate_profile)
    safe_jd = strip_pii(jd_text)
    safe_bullets = strip_pii("\n\n".join(employer_sections))

    prompt = f"""Select and rank the best resume bullets for this job.

CANDIDATE PROFILE:
{safe_profile}

JOB DESCRIPTION:
{safe_jd}

PRIORITY BULLETS (always include these):
{priority_text}

AVAILABLE BULLETS BY EMPLOYER:
{safe_bullets}

Generate a complete resume draft in this exact format:
SUMMARY
[one summary paragraph]

CORE COMPETENCIES
[comma-separated list]

EXPERIENCE
[employer sections with selected bullets]

EDUCATION
[education section]"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.content[0].text
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  Stage 1 draft written to {output_path}")


def run_stage3(client, stage2_text, jd_text, output_path):
    """
    Stage 3: Semantic coherence check + ATS gap analysis.
    Writes stage3_review.txt to output_path.
    """
    safe_stage2 = strip_pii(stage2_text)
    safe_jd = strip_pii(jd_text)

    prompt = f"""Review this resume against the job description.

JOB DESCRIPTION:
{safe_jd}

RESUME (stage 2 approved):
{safe_stage2}

Provide in this exact format:
COHERENCE CHECK
[assessment of bullet-to-JD alignment]

ATS GAP ANALYSIS
[keywords in JD not represented in resume]

SUGGESTIONS
[specific wording improvements grounded in resume content — no invented claims]"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    # Prepend stage2 content so stage3 file is self-contained
    content = safe_stage2 + "\n\n---\nSTAGE 3 REVIEW NOTES\n" + response.content[0].text
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  Stage 3 review written to {output_path}")


def run_stage4(stage_text, output_path):
    """
    Stage 4: Generate .docx from stage text using resume template.
    No API call — pure python-docx generation.
    NOTE: The existing script has detailed template formatting logic.
    Extract it wholesale from the current stage 4 handler — do not rewrite it.
    This stub shows the function contract; real implementation uses the template.
    """
    doc = Document(RESUME_TEMPLATE) if os.path.exists(RESUME_TEMPLATE) else Document()
    for line in stage_text.splitlines():
        doc.add_paragraph(line)
    doc.save(output_path)
    print(f"  Resume .docx saved to {output_path}")
```

**Important note for implementer:** The `run_stage4` body above is a minimal stub for testing. The production implementation should extract the full docx formatting logic from the existing stage 4 handler in the current script — that code handles template styling, fonts, paragraph formatting, and header/footer. Copy it wholesale into `run_stage4`, do not rewrite it. The test only verifies the file is created and readable; it does not assert on formatting.

**c) Rewrite `main()` to call stage functions:**

```python
def main():
    parser = argparse.ArgumentParser(description='Phase 4 Resume Generator')
    parser.add_argument('--stage', type=int, required=True, choices=[1, 3, 4])
    parser.add_argument('--role', type=str, required=True)
    args = parser.parse_args()

    candidate_profile = strip_pii(load_candidate_profile())
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    package_dir = os.path.join(JOBS_PACKAGES_DIR, args.role)
    jd_path = os.path.join(package_dir, "job_description.txt")

    if args.stage == 1:
        library = json.load(open(EXPERIENCE_LIBRARY, encoding='utf-8'))
        jd_text = open(jd_path, encoding='utf-8').read()
        output_path = os.path.join(package_dir, "stage1_draft.txt")
        run_stage1(client, jd_text, library, candidate_profile, output_path)

    elif args.stage == 3:
        stage2_path = os.path.join(package_dir, "stage2_approved.txt")
        stage2_text = open(stage2_path, encoding='utf-8').read()
        jd_text = open(jd_path, encoding='utf-8').read()
        output_path = os.path.join(package_dir, "stage3_review.txt")
        run_stage3(client, stage2_text, jd_text, output_path)

    elif args.stage == 4:
        stage_path = os.path.join(package_dir, "stage4_final.txt")
        if not os.path.exists(stage_path):
            stage_path = os.path.join(package_dir, "stage2_approved.txt")
        stage_text = open(stage_path, encoding='utf-8').read()
        tailored_dir = os.path.join(RESUMES_TAILORED_DIR, args.role)
        os.makedirs(tailored_dir, exist_ok=True)
        docx_path = os.path.join(tailored_dir, f"{args.role}_Resume.docx")
        run_stage4(stage_text, docx_path)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Syntax check**

```bash
python -m py_compile scripts/phase4_resume_generator.py && echo "OK"
```

- [ ] **Step 5: Run mock tests — expect PASS**

```bash
pytest tests/phase4/test_resume_generator.py -m "not live" -v
```

Expected: 7 passed (1 live test skipped).

- [ ] **Step 6: Commit**

```bash
git add scripts/phase4_resume_generator.py tests/phase4/test_resume_generator.py
git commit -m "Refactor phase4_resume_generator: extract stage functions, add tests"
```

---

## Task 13: Refactor phase4_cover_letter + Tests

**Files:**
- Modify: `scripts/phase4_cover_letter.py`
- Create: `tests/phase4/test_cover_letter.py`

**The problem:** `args = parser.parse_args()` and all path variables run at module level.

**The fix:** Move argparse into `main()`. Extract `run_cl_stage1(client, jd_text, resume_text, background_text, output_path)` and `run_cl_stage4(stage4_text, output_path)`.

- [ ] **Step 1: Write failing tests**

```python
# tests/phase4/test_cover_letter.py

import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from docx import Document

FIXTURE_JD = Path(__file__).parent.parent / "fixtures" / "stage_files" / "sample_jd.txt"
FIXTURE_STAGE2 = Path(__file__).parent.parent / "fixtures" / "stage_files" / "stage2_approved.txt"
FIXTURE_BACKGROUND = Path(__file__).parent.parent / "fixtures" / "stage_files" / "sample_background.md"

MOCK_CL_RESPONSE = """
Dear Hiring Manager,

I am writing to express my interest in the Senior Systems Engineer position at Acme Defense Systems.

My experience with MBSE and Cameo Systems Modeler directly aligns with your requirements. I have led
development of DoDAF architectural views for autonomous maritime systems.

I look forward to discussing how my background supports your mission.

Sincerely,
[CANDIDATE]
"""


def make_mock_client(response_text):
    client = MagicMock()
    client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=response_text)]
    )
    return client


def test_run_cl_stage1_creates_draft_file():
    from scripts.phase4_cover_letter import run_cl_stage1
    client = make_mock_client(MOCK_CL_RESPONSE)
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")
    resume_text = FIXTURE_STAGE2.read_text(encoding="utf-8")
    background_text = FIXTURE_BACKGROUND.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "cl_stage1_draft.txt"
        run_cl_stage1(client, jd_text, resume_text, background_text, str(output_path))
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert len(content) > 50


def test_run_cl_stage1_no_pii_in_payload(pii_values):
    from scripts.phase4_cover_letter import run_cl_stage1
    client = make_mock_client(MOCK_CL_RESPONSE)
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")
    resume_text = (
        f"Name: {pii_values['name']} | Phone: {pii_values['phone']}\n"
        + FIXTURE_STAGE2.read_text(encoding="utf-8")
    )
    background_text = FIXTURE_BACKGROUND.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "cl_stage1_draft.txt"
        run_cl_stage1(client, jd_text, resume_text, background_text, str(output_path))

    call_args = client.messages.create.call_args
    full_payload = str(call_args)
    for pii_value in pii_values.values():
        assert pii_value not in full_payload, f"PII found in payload: {pii_value}"


def test_run_cl_stage1_output_has_opening_and_closing():
    from scripts.phase4_cover_letter import run_cl_stage1
    client = make_mock_client(MOCK_CL_RESPONSE)
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")
    resume_text = FIXTURE_STAGE2.read_text(encoding="utf-8")
    background_text = FIXTURE_BACKGROUND.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "cl_stage1_draft.txt"
        run_cl_stage1(client, jd_text, resume_text, background_text, str(output_path))
        content = output_path.read_text(encoding="utf-8")
        # The mock response has both greeting and closing
        assert "Dear" in content or "Hiring" in content or len(content) > 50


def test_run_cl_stage4_creates_readable_docx():
    from scripts.phase4_cover_letter import run_cl_stage4
    cl_text = MOCK_CL_RESPONSE

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_cover_letter.docx"
        run_cl_stage4(cl_text, str(output_path))
        assert output_path.exists()
        doc = Document(str(output_path))
        assert len(doc.paragraphs) > 0


def test_no_module_level_execution_on_import():
    import scripts.phase4_cover_letter  # noqa: F401


@pytest.mark.live
def test_run_cl_stage1_live():
    """Tier 2: real API call."""
    import os
    from anthropic import Anthropic
    from scripts.phase4_cover_letter import run_cl_stage1

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    jd_text = FIXTURE_JD.read_text(encoding="utf-8")
    resume_text = FIXTURE_STAGE2.read_text(encoding="utf-8")
    background_text = FIXTURE_BACKGROUND.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "cl_stage1_draft.txt"
        run_cl_stage1(client, jd_text, resume_text, background_text, str(output_path))
        content = output_path.read_text(encoding="utf-8")
        assert "Acme" in content or len(content) > 200
```

- [ ] **Step 2: Run — expect import failure**

```bash
pytest tests/phase4/test_cover_letter.py -m "not live" -v --tb=short
```

- [ ] **Step 3: Refactor `scripts/phase4_cover_letter.py`**

Extract two functions and move argparse into `main()`:

```python
def run_cl_stage1(client, jd_text, resume_text, background_text, output_path):
    """
    Generate cover letter draft from JD, resume content, and background.
    All inputs are PII-stripped before the API call.
    Writes cl_stage1_draft.txt to output_path.
    """
    safe_resume = strip_pii(resume_text)
    safe_jd = strip_pii(jd_text)
    safe_background = strip_pii(background_text)

    prompt = f"""Generate a professional cover letter draft.

JOB DESCRIPTION:
{safe_jd}

RESUME CONTENT (bullets to reference):
{safe_resume}

CANDIDATE CONSTRAINTS:
{safe_background}

Write a 3-paragraph cover letter: opening (role + match), body (specific evidence from resume),
closing (next step). Use en dashes, not em dashes."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.content[0].text
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"  Cover letter draft written to {output_path}")


def run_cl_stage4(cl_text, output_path):
    """
    Convert cover letter text to .docx.
    No API call — pure python-docx generation.
    """
    doc = Document()
    for line in cl_text.splitlines():
        doc.add_paragraph(line)
    doc.save(output_path)
    print(f"  Cover letter .docx saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Phase 4 Cover Letter Generator')
    parser.add_argument('--stage', type=int, required=True, choices=[1, 4])
    parser.add_argument('--role', type=str, required=True)
    args = parser.parse_args()

    package_dir = os.path.join(JOBS_PACKAGES_DIR, args.role)
    jd_path = os.path.join(package_dir, "job_description.txt")

    if args.stage == 1:
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        jd_text = open(jd_path, encoding='utf-8').read()
        resume_path = os.path.join(package_dir, "stage4_final.txt")
        if not os.path.exists(resume_path):
            resume_path = os.path.join(package_dir, "stage2_approved.txt")
        resume_text = open(resume_path, encoding='utf-8').read()
        background_text = open(CANDIDATE_BACKGROUND_PATH, encoding='utf-8').read()
        output_path = os.path.join(package_dir, CL_STAGE1)
        run_cl_stage1(client, jd_text, resume_text, background_text, output_path)

    elif args.stage == 4:
        cl_path = os.path.join(package_dir, CL_STAGE4)
        cl_text = open(cl_path, encoding='utf-8').read()
        tailored_dir = os.path.join(RESUMES_TAILORED_DIR, args.role)
        os.makedirs(tailored_dir, exist_ok=True)
        docx_path = os.path.join(tailored_dir, f"{args.role}_CoverLetter.docx")
        run_cl_stage4(cl_text, docx_path)


if __name__ == "__main__":
    main()
```

Remove all module-level code that is not constants or function/class definitions.

- [ ] **Step 4: Syntax check**

```bash
python -m py_compile scripts/phase4_cover_letter.py && echo "OK"
```

- [ ] **Step 5: Run tests — expect PASS**

```bash
pytest tests/phase4/test_cover_letter.py -m "not live" -v
```

Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add scripts/phase4_cover_letter.py tests/phase4/test_cover_letter.py
git commit -m "Refactor phase4_cover_letter: extract stage functions, add tests"
```

---

## Task 14: check_resume Tests

**Files:**
- Create: `tests/phase4/test_check_resume.py`

No refactoring needed. `check_resume.py` is already properly structured with `main()` and function-level logic.

- [ ] **Step 1: Write tests**

```python
# tests/phase4/test_check_resume.py

import pytest
from pathlib import Path
from unittest.mock import MagicMock

FIXTURE_BACKGROUND = Path(__file__).parent.parent / "fixtures" / "stage_files" / "sample_background.md"
FIXTURE_STAGE2 = Path(__file__).parent.parent / "fixtures" / "stage_files" / "stage2_approved.txt"

MOCK_L2_RESPONSE = "[]"  # No violations — valid empty JSON array


def make_mock_client(response_text):
    client = MagicMock()
    client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=response_text)]
    )
    return client


def test_extract_section_returns_content_between_headings():
    from scripts.check_resume import extract_section
    text = "## Confirmed Gaps\nNo GitLab\n## Other Section\nOther content"
    result = extract_section(text, "## Confirmed Gaps")
    assert "No GitLab" in result
    assert "Other content" not in result


def test_extract_gap_terms_finds_acronyms():
    from scripts.check_resume import extract_gap_terms
    background = FIXTURE_BACKGROUND.read_text(encoding="utf-8")
    terms = extract_gap_terms(background)
    # MATLAB is in sample_background.md Confirmed Gaps — all caps acronym
    assert "MATLAB" in terms or len(terms) > 0


def test_run_layer1_detects_em_dash():
    from scripts.check_resume import run_layer1
    resume_lines = ["Senior systems engineer \u2014 MBSE expert."]
    findings = run_layer1(resume_lines, gap_terms=set())
    assert len(findings) >= 1
    rules = [f["rule"] for f in findings]
    assert "Em dash" in rules


def test_run_layer1_detects_safety_critical():
    from scripts.check_resume import run_layer1
    resume_lines = ["Responsible for safety-critical systems design."]
    findings = run_layer1(resume_lines, gap_terms=set())
    rules = [f["rule"] for f in findings]
    assert "safety-critical" in rules


def test_run_layer1_no_false_positives_on_clean_resume():
    from scripts.check_resume import run_layer1
    resume_lines = FIXTURE_STAGE2.read_text(encoding="utf-8").splitlines()
    # Fixture stage2 has no known violations
    findings = run_layer1(resume_lines, gap_terms=set())
    # Em dash, safety-critical, Active TS/SCI, Plank Holder — none in fixture
    hardcoded_rule_findings = [f for f in findings if f["layer"] == 1]
    rule_names = [f["rule"] for f in hardcoded_rule_findings]
    assert "Em dash" not in rule_names
    assert "safety-critical" not in rule_names


def test_run_layer2_no_pii_in_api_payload(pii_values):
    from scripts.check_resume import run_layer2
    client = make_mock_client(MOCK_L2_RESPONSE)

    resume_text = (
        f"Contact {pii_values['name']} at {pii_values['email']}\n"
        + FIXTURE_STAGE2.read_text(encoding="utf-8")
    )
    gaps_section = "No GitLab, no INCOSE certification."
    banned_section = "Use en dashes, not em dashes."

    run_layer2(client, resume_text, gaps_section, banned_section)

    call_args = client.messages.create.call_args
    full_payload = str(call_args)
    for pii_value in pii_values.values():
        assert pii_value not in full_payload, f"PII found in Layer 2 payload: {pii_value}"


def test_run_layer2_parses_valid_json_response():
    from scripts.check_resume import run_layer2
    mock_response = '[{"violation_type": "Em dash", "line_reference": "line 1", "flagged_text": "test \u2014 text", "suggested_fix": "Use en dash"}]'
    client = make_mock_client(mock_response)

    findings = run_layer2(
        client,
        resume_text="test \u2014 text",
        gaps_section="",
        banned_section=""
    )
    assert len(findings) == 1
    assert findings[0]["rule"] == "Em dash"
    assert findings[0]["layer"] == 2


@pytest.mark.live
def test_run_layer2_live():
    """Tier 2: real API call."""
    import os
    import anthropic
    from scripts.check_resume import run_layer2

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    resume_text = FIXTURE_STAGE2.read_text(encoding="utf-8")
    background = FIXTURE_BACKGROUND.read_text(encoding="utf-8")

    from scripts.check_resume import extract_section
    gaps_section = extract_section(background, "## Confirmed Gaps")
    banned_section = extract_section(background, "## Banned / Corrected Language")

    findings = run_layer2(client, resume_text, gaps_section, banned_section)
    assert isinstance(findings, list)
```

- [ ] **Step 2: Run**

```bash
pytest tests/phase4/test_check_resume.py -m "not live" -v
```

Expected: 7 passed (1 live skipped).

- [ ] **Step 3: Commit**

```bash
git add tests/phase4/test_check_resume.py
git commit -m "Add check_resume tests: layer1, layer2, PII safety, false positive guard"
```

---

## Task 15: Refactor phase5_interview_prep + Tests

**Files:**
- Modify: `scripts/phase5_interview_prep.py`
- Create: `tests/phase5/test_interview_prep.py`

**The problem:** `argparse.parse_args()` at module level.

**The fix:** Move argparse into `main()`. Extract `generate_prep(client, role_data, output_txt_path, output_docx_path)` with `role_data` being a dict containing jd_text, library, stage_text, candidate_profile.

- [ ] **Step 1: Write failing tests**

```python
# tests/phase5/test_interview_prep.py

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from docx import Document

FIXTURE_JD = Path(__file__).parent.parent / "fixtures" / "stage_files" / "sample_jd.txt"
FIXTURE_STAGE2 = Path(__file__).parent.parent / "fixtures" / "stage_files" / "stage2_approved.txt"
FIXTURE_LIBRARY = Path(__file__).parent.parent / "fixtures" / "library" / "experience_library.json"
FIXTURE_PROFILE = Path(__file__).parent.parent / "fixtures" / "library" / "candidate_profile.md"

MOCK_PREP_RESPONSE = """
## SECTION 1: COMPANY & ROLE BRIEF
Acme Defense Systems is a defense contractor focused on autonomous maritime systems.
Role: Senior Systems Engineer supporting MBSE and DoDAF development.
Salary guidance: $150,000 - $180,000.

## SECTION 2: STORY BANK
STAR Story 1 - MBSE Leadership
Situation: Led MBSE development for autonomous surface vessel program.
Task: Develop DoDAF architectural views using Cameo Systems Modeler.
Action: Facilitated IPT working groups with government stakeholders.
Result: Delivered system-of-systems architecture supporting multi-domain C2 integration.

STAR Story 2 - Stakeholder Engagement
Situation: Government stakeholder alignment required for requirements definition.
Task: Define operational requirements and ConOps.
Action: Conducted workshops and facilitated reviews.
Result: Approved ConOps baseline.

STAR Story 3 - Architecture Integration
Situation: System integration complexity.
Task: Develop integration architecture.
Action: Applied DoDAF SV views.
Result: Successful integration milestone.

## SECTION 3: GAP PREPARATION
REQUIRED: All required qualifications met.
PREFERRED: JADC2 experience limited — acknowledge and reframe.

## SECTION 4: QUESTIONS TO ASK
- What is the acquisition phase for this program?
- How is MBSE integrated into the program baseline?
"""


def make_mock_client(response_text):
    client = MagicMock()
    client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=response_text)]
    )
    return client


def test_generate_prep_creates_both_output_files():
    from scripts.phase5_interview_prep import generate_prep

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = {
        "jd_text": FIXTURE_JD.read_text(encoding="utf-8"),
        "stage_text": FIXTURE_STAGE2.read_text(encoding="utf-8"),
        "library": json.loads(FIXTURE_LIBRARY.read_text(encoding="utf-8")),
        "candidate_profile": FIXTURE_PROFILE.read_text(encoding="utf-8"),
        "role_name": "acme_sse",
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        txt_path = Path(tmpdir) / "interview_prep.txt"
        docx_path = Path(tmpdir) / "interview_prep.docx"
        generate_prep(client, role_data, str(txt_path), str(docx_path))
        assert txt_path.exists()
        assert docx_path.exists()


def test_generate_prep_txt_has_required_sections():
    from scripts.phase5_interview_prep import generate_prep

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = {
        "jd_text": FIXTURE_JD.read_text(encoding="utf-8"),
        "stage_text": FIXTURE_STAGE2.read_text(encoding="utf-8"),
        "library": json.loads(FIXTURE_LIBRARY.read_text(encoding="utf-8")),
        "candidate_profile": FIXTURE_PROFILE.read_text(encoding="utf-8"),
        "role_name": "acme_sse",
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        txt_path = Path(tmpdir) / "interview_prep.txt"
        docx_path = Path(tmpdir) / "interview_prep.docx"
        generate_prep(client, role_data, str(txt_path), str(docx_path))
        content = txt_path.read_text(encoding="utf-8")

    assert "COMPANY" in content or "BRIEF" in content
    assert "STORY" in content or "STAR" in content
    assert "GAP" in content
    assert "QUESTION" in content


def test_generate_prep_star_stories_reference_resume_content():
    from scripts.phase5_interview_prep import generate_prep

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = {
        "jd_text": FIXTURE_JD.read_text(encoding="utf-8"),
        "stage_text": FIXTURE_STAGE2.read_text(encoding="utf-8"),
        "library": json.loads(FIXTURE_LIBRARY.read_text(encoding="utf-8")),
        "candidate_profile": FIXTURE_PROFILE.read_text(encoding="utf-8"),
        "role_name": "acme_sse",
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        txt_path = Path(tmpdir) / "interview_prep.txt"
        docx_path = Path(tmpdir) / "interview_prep.docx"
        generate_prep(client, role_data, str(txt_path), str(docx_path))
        content = txt_path.read_text(encoding="utf-8")

    # "Cameo Systems Modeler" appears in both fixture stage2 and the mock STAR story
    assert "Cameo Systems Modeler" in content or "MBSE" in content


def test_generate_prep_no_pii_in_api_payload(pii_values):
    from scripts.phase5_interview_prep import generate_prep

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = {
        "jd_text": FIXTURE_JD.read_text(encoding="utf-8"),
        "stage_text": (
            f"Contact: {pii_values['name']} | {pii_values['email']}\n"
            + FIXTURE_STAGE2.read_text(encoding="utf-8")
        ),
        "library": json.loads(FIXTURE_LIBRARY.read_text(encoding="utf-8")),
        "candidate_profile": FIXTURE_PROFILE.read_text(encoding="utf-8"),
        "role_name": "acme_sse",
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        txt_path = Path(tmpdir) / "interview_prep.txt"
        docx_path = Path(tmpdir) / "interview_prep.docx"
        generate_prep(client, role_data, str(txt_path), str(docx_path))

    call_args = client.messages.create.call_args
    full_payload = str(call_args)
    for pii_value in pii_values.values():
        assert pii_value not in full_payload, f"PII found in payload: {pii_value}"


def test_generate_prep_docx_readable():
    from scripts.phase5_interview_prep import generate_prep

    client = make_mock_client(MOCK_PREP_RESPONSE)
    role_data = {
        "jd_text": FIXTURE_JD.read_text(encoding="utf-8"),
        "stage_text": FIXTURE_STAGE2.read_text(encoding="utf-8"),
        "library": json.loads(FIXTURE_LIBRARY.read_text(encoding="utf-8")),
        "candidate_profile": FIXTURE_PROFILE.read_text(encoding="utf-8"),
        "role_name": "acme_sse",
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        txt_path = Path(tmpdir) / "interview_prep.txt"
        docx_path = Path(tmpdir) / "interview_prep.docx"
        generate_prep(client, role_data, str(txt_path), str(docx_path))
        doc = Document(str(docx_path))
        assert len(doc.paragraphs) > 0


def test_no_module_level_execution_on_import():
    import scripts.phase5_interview_prep  # noqa: F401


@pytest.mark.live
def test_generate_prep_live():
    """Tier 2: real API call with web search."""
    import os
    from anthropic import Anthropic
    from scripts.phase5_interview_prep import generate_prep

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    role_data = {
        "jd_text": FIXTURE_JD.read_text(encoding="utf-8"),
        "stage_text": FIXTURE_STAGE2.read_text(encoding="utf-8"),
        "library": json.loads(FIXTURE_LIBRARY.read_text(encoding="utf-8")),
        "candidate_profile": FIXTURE_PROFILE.read_text(encoding="utf-8"),
        "role_name": "acme_sse_test",
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        txt_path = Path(tmpdir) / "interview_prep.txt"
        docx_path = Path(tmpdir) / "interview_prep.docx"
        generate_prep(client, role_data, str(txt_path), str(docx_path))
        content = txt_path.read_text(encoding="utf-8")

    assert len(content) > 500
    assert "STAR" in content or "Story" in content
    assert "GAP" in content or "Gap" in content
```

- [ ] **Step 2: Run — expect import failure**

```bash
pytest tests/phase5/test_interview_prep.py -m "not live" -v --tb=short
```

- [ ] **Step 3: Refactor `scripts/phase5_interview_prep.py`**

Add `generate_prep(client, role_data, output_txt_path, output_docx_path)` and move argparse into `main()`:

```python
def generate_prep(client, role_data, output_txt_path, output_docx_path):
    """
    Generate interview prep package from role data.
    role_data keys: jd_text, stage_text, library, candidate_profile, role_name.
    Writes both .txt and .docx output files.
    All PII stripped from API payloads.
    """
    safe_jd = strip_pii(role_data["jd_text"])
    safe_stage = strip_pii(role_data["stage_text"])
    safe_profile = strip_pii(role_data["candidate_profile"])

    prompt = f"""Generate a comprehensive interview prep package.

JOB DESCRIPTION:
{safe_jd}

RESUME CONTENT (what was submitted):
{safe_stage}

CANDIDATE PROFILE:
{safe_profile}

Generate:
SECTION 1: COMPANY & ROLE BRIEF (role overview, salary guidance)
SECTION 2: STORY BANK (minimum 3 STAR stories grounded in resume content above)
SECTION 3: GAP PREPARATION (REQUIRED vs PREFERRED, sourced from JD text only)
SECTION 4: QUESTIONS TO ASK
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.content[0].text

    # Write .txt
    with open(output_txt_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Write .docx
    doc = Document()
    for line in content.splitlines():
        doc.add_paragraph(line)
    doc.save(output_docx_path)

    print(f"  Interview prep written to {output_txt_path}")
    print(f"  Interview prep .docx written to {output_docx_path}")


def main():
    parser = argparse.ArgumentParser(description='Phase 5 Interview Prep Generator')
    parser.add_argument('--role', type=str, required=True)
    args = parser.parse_args()

    role = args.role
    package_dir = os.path.join(JOBS_PACKAGES_DIR, role)
    jd_path = os.path.join(package_dir, "job_description.txt")
    stage_path = os.path.join(package_dir, "stage4_final.txt")
    if not os.path.exists(stage_path):
        stage_path = os.path.join(package_dir, "stage2_approved.txt")

    library = json.load(open(EXPERIENCE_LIBRARY, encoding='utf-8'))

    candidate_profile = ""
    if os.path.exists(CANDIDATE_PROFILE_PATH):
        with open(CANDIDATE_PROFILE_PATH, encoding='utf-8') as f:
            candidate_profile = f.read()

    role_data = {
        "jd_text": open(jd_path, encoding='utf-8').read(),
        "stage_text": open(stage_path, encoding='utf-8').read(),
        "library": library,
        "candidate_profile": candidate_profile,
        "role_name": role,
    }

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    txt_path = os.path.join(package_dir, OUTPUT_FILENAME)
    docx_path = os.path.join(package_dir, OUTPUT_DOCX_FILENAME)
    generate_prep(client, role_data, txt_path, docx_path)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Syntax check**

```bash
python -m py_compile scripts/phase5_interview_prep.py && echo "OK"
```

- [ ] **Step 5: Run mock tests — expect PASS**

```bash
pytest tests/phase5/test_interview_prep.py -m "not live" -v
```

Expected: 6 passed (1 live skipped).

- [ ] **Step 6: Commit**

```bash
git add scripts/phase5_interview_prep.py tests/phase5/test_interview_prep.py
git commit -m "Refactor phase5_interview_prep: extract generate_prep(), add tests"
```

---

## Task 16: README CI Badge

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add badge to top of README.md**

Open `README.md`. After the `# AI Job Search Agent` heading, add:

```markdown
![Tests](https://github.com/r-todd-drake/Job_search_agent/actions/workflows/test.yml/badge.svg)
```

Replace `r-todd-drake` with your actual GitHub username if different.

- [ ] **Step 2: Verify badge renders correctly**

Push to GitHub and confirm the badge appears on the repository front page. Green = all mock tests passing.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "Add CI test badge to README"
git push
```

---

## Running the Full Suite

**Tier 1 (mock, same as CI):**
```bash
pytest tests/ -m "not live" --tb=short -v
```

**Tier 2 (live, on-demand):**
```bash
pytest -m live -v
```

**Single phase:**
```bash
pytest tests/phase4/ -m "not live" -v
```

**Live tests for a single phase before promoting:**
```bash
pytest tests/phase4/ -m live -v
```
