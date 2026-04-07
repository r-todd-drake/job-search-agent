# V&V Framework Design
# Job Search Agent — Verification & Validation

Date: 2026-04-07
Status: Approved — pending implementation plan

---

## Purpose

This document defines the verification and validation (V&V) framework for the Job Search Agent
pipeline. It establishes how each script is tested, what a passing test looks like at each tier,
and how test results are surfaced via GitHub Actions CI.

The goal is a pipeline that is:
- **Trustworthy:** scripts catch their own errors and never silently produce bad output
- **Verifiable:** a pytest suite with documented pass/fail criteria confirms pipeline health after any change
- **Portfolio-ready:** CI badge, clean test structure, and explicit contracts readable by any senior developer

The core pipeline logic is proven in production (Phase 4 resume output is generating interviews).
This framework builds the right structure around that logic — it does not replace it.

---

## Section 1 — Architecture & Test Tier Model

The framework uses two tiers that serve distinct purposes.

### Tier 1 — Mock (automated, runs on every push)

Tests that validate logic, structure, contracts, and behavior without making real API calls.
Claude API responses are replaced with realistic fixtures. Runs in GitHub Actions CI automatically.
No API key required. Completes in under 60 seconds. This is the foundation of day-to-day confidence.

### Tier 2 — Live (on-demand, developer-run)

Tests that hit the real Claude API with fictional input data. Validate that the full end-to-end
call succeeds, the response is parseable, and the output meets quality thresholds. Marked
`@pytest.mark.live`. Run with `pytest -m live` before promoting a prototype to active use or
after significant changes to any API-calling script.

### What Each Tier Proves

| Question | Tier 1 (Mock) | Tier 2 (Live) |
|---|---|---|
| Does the logic handle edge cases? | Yes | — |
| Is PII stripped before API calls? | Yes | Yes |
| Does output match the expected schema? | Yes | Yes |
| Does the script survive a bad API response? | Yes | — |
| Does the LLM produce usable output? | — | Yes |
| Does the .docx open without corruption? | Yes | Yes |
| Is generated content grounded (not hallucinated)? | — | Yes |

GitHub Actions runs Tier 1 only. A green CI badge means pipeline structure and logic are sound.
A Tier 2 run before any phase goes live confirms end-to-end behavior.

---

## Section 2 — Directory Structure & Naming Conventions

The test directory mirrors `scripts/` so the relationship between a script and its tests is
always unambiguous.

```
tests/
├── conftest.py                        # shared fixtures, pytest marks, mock factory
├── fixtures/                          # fictional test data — committed to git
│   ├── jobs/
│   │   └── jobs_sample.csv            # fictional roles, known statuses, duplicate req numbers
│   ├── library/
│   │   ├── experience_library.md      # fictional experience entries
│   │   ├── experience_library.json    # pre-parsed output for downstream tests
│   │   └── candidate_profile.md      # fictional candidate profile
│   └── stage_files/
│       ├── sample_jd.txt              # fictional job description
│       ├── stage1_draft.txt           # fictional stage 1 output
│       ├── stage2_approved.txt        # fictional stage 2 output
│       ├── stage3_review.txt          # fictional stage 3 output
│       └── sample_resume.docx         # minimal valid .docx for check_resume tests
├── utils/
│   ├── test_pii_filter.py
│   └── test_library_parser.py
├── phase1/
│   └── test_pipeline_report.py
├── phase2/
│   ├── test_job_ranking.py
│   └── test_semantic_analyzer.py
├── phase3/
│   ├── test_parse_library.py
│   ├── test_parse_employer.py
│   ├── test_build_candidate_profile.py
│   └── test_compile_library.py
├── phase4/
│   ├── test_resume_generator.py
│   ├── test_cover_letter.py
│   └── test_check_resume.py
└── phase5/
    └── test_interview_prep.py
```

### Naming Conventions

- Test files: `test_<script_name>.py` — one file per script
- Test functions: `test_<what_it_does>` — describes behavior, not implementation
  - Good: `test_duplicate_req_numbers_flagged`
  - Avoid: `test_line_47`
- Live tests: decorated `@pytest.mark.live`, grouped at the bottom of each test file
- Fixtures: named for what they represent (`sample_jd`, `parsed_library`), not how they are built

### `conftest.py` Responsibilities

```python
import pytest
from pathlib import Path

# Shared mock factory — one place to update if the API client import path changes
@pytest.fixture
def mock_anthropic(mocker):
    return mocker.patch("anthropic.Anthropic")

# Shared fixture path root
@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"

# Shared PII values for injection/stripping tests
@pytest.fixture
def pii_values():
    return {
        "name": "Jane Q. Applicant",
        "phone": "(555) 867-5309",
        "email": "applicant@example.com",
        "linkedin": "linkedin.com/in/applicant",
        "github": "github.com/applicant",
    }
```

### `pytest.ini` (project root)

```ini
[pytest]
testpaths = tests
markers =
    live: marks tests that make real Claude API calls (run with -m live)
```

---

## Section 3 — Fictional Test Data Conventions

All fixtures use a single consistent fictional identity throughout the suite. Fixtures compose
cleanly because the same values appear everywhere.

| Field | Value |
|---|---|
| Company | Acme Defense Systems |
| Role | Senior Systems Engineer |
| Req number | ADS-12345 |
| Candidate name | Jane Q. Applicant |
| Phone | (555) 867-5309 |
| Email | applicant@example.com |
| LinkedIn | linkedin.com/in/applicant |
| GitHub | github.com/applicant |

Fixture files are committed to git. They must never contain:
- Real employer names or project names
- Real salary figures drawn from the active pipeline
- Any value that could narrow attribution to the candidate

Plausible defense-adjacent content is acceptable. Invented names and roles only.

---

## Section 4 — Success Criteria Contracts

Each script has a formal contract: what it promises given valid input, and what passing looks
like at each tier. Tests are written against these contracts, not against the implementation.

---

### Utils

#### `pii_filter.py`

**Contract:** Given any string, `strip_pii()` replaces all PII values (name, phone, email,
LinkedIn, GitHub) with placeholders. Output contains zero instances of any injected PII value.

| Criterion | Tier |
|---|---|
| Single PII value replaced | Mock |
| All five PII types replaced in one pass | Mock |
| PII embedded mid-sentence replaced | Mock |
| String with no PII returned unchanged | Mock |
| Empty string handled without error | Mock |

---

#### `library_parser.py`

**Contract:** Given valid experience_library.md, returns a list of employer objects conforming
to the JSON schema. No data is dropped, invented, or reordered.

| Criterion | Tier |
|---|---|
| All employer sections parsed | Mock |
| Required fields present on every entry (employer, dates, title, bullets) | Mock |
| Bullet count matches source markdown | Mock |
| Priority bullets flagged correctly | Mock |
| Malformed section raises a clear error, not a silent skip | Mock |

---

### Phase 1 — `pipeline_report.py`

**Contract:** Given jobs.csv, produces accurate pipeline metrics and flags duplicate req numbers.
Does not modify any file.

| Criterion | Tier |
|---|---|
| Role counts match known CSV distribution | Mock |
| Duplicate req numbers identified by name and number | Mock |
| No files modified after run | Mock |
| Empty CSV handled without error | Mock |

---

### Phase 2

#### `phase2_job_ranking.py`

**Contract:** Given jobs.csv, scores blank-status roles by keyword match, assigns
PURSUE/CONSIDER/SKIP, detects duplicate req numbers, and reports only new roles.

| Criterion | Tier |
|---|---|
| High-match role scores above PURSUE threshold | Mock |
| Low-match role scores below SKIP threshold | Mock |
| Roles with existing status not re-scored | Mock |
| Duplicate req numbers detected and flagged | Mock |
| Only new roles appear in output report | Mock |
| Full run completes on real jobs.csv | Live |

---

#### `phase2_semantic_analyzer.py`

**Contract:** Given PURSUE/CONSIDER roles and their JDs, calls Claude API with PII-stripped
payload and writes structured semantic fit analysis per role.

| Criterion | Tier |
|---|---|
| No PII values present in API call payload | Mock |
| Output structure matches expected schema | Mock |
| Script handles API error response without crashing | Mock |
| Real API call succeeds and response is parsed | Live |
| Output written to expected file path | Live |

---

### Phase 3

#### `phase3_parse_library.py` *(thin wrapper — core logic covered by `library_parser.py` tests)*

**Contract:** Orchestrates full library parse and writes JSON output file.

| Criterion | Tier |
|---|---|
| JSON output file created at expected path | Mock |
| Output is valid JSON conforming to schema | Mock |

---

#### `phase3_parse_employer.py`

**Contract:** Re-parses a single named employer and updates only that entry in the JSON store.
All other employer entries are unchanged.

| Criterion | Tier |
|---|---|
| Target employer entry updated | Mock |
| All other employer entry values unchanged (JSON reformatting is acceptable) | Mock |
| Unknown employer name raises clear error | Mock |

---

#### `phase3_build_candidate_profile.py`

**Contract:** Given experience_library.json, produces candidate_profile.md containing skills,
tools, and certifications. All content traceable to input — nothing invented.

| Criterion | Tier |
|---|---|
| Output file created with required sections | Mock |
| Every item in output present in input JSON | Mock |
| Lapsed certifications flagged, not omitted | Mock |

---

#### `phase3_compile_library.py`

**Contract:** Given experience_library.json, compiles a unified library structure ready for
Phase 4 consumption.

| Criterion | Tier |
|---|---|
| All employers represented in output | Mock |
| Priority bullets correctly flagged | Mock |
| Output structure valid for Phase 4 consumption | Mock |

---

### Phase 4

#### `phase4_resume_generator.py`

**Stage 1 Contract:** Given JD and compiled library, selects and ranks bullets, writes
stage1_draft.txt. Priority bullets always included. No PII in API payload.

| Criterion | Tier |
|---|---|
| All required sections present (summary, competencies, experience, education) | Mock |
| Priority bullets present in output | Mock |
| No PII in API payload | Mock |
| Output is valid UTF-8 text file | Mock |
| Full Stage 1 run produces coherent draft | Live |

**Stage 2:** Human review gate — no automated test by design. Documented here as a required
manual step in the workflow. Automation cannot substitute for candidate judgment at this stage.

**Stage 3 Contract:** Given stage2_approved.txt and library, produces semantic coherence check
with ATS gap analysis and suggestions grounded in library content.

| Criterion | Tier |
|---|---|
| Output contains required sections (coherence, ATS gaps, suggestions) | Mock |
| No PII in API payload | Mock |
| Full Stage 3 run produces actionable feedback | Live |

**Stage 4 Contract:** Given stage3_review.txt, generates a .docx using the resume template.
Output is readable, non-corrupt, and within expected length.

| Criterion | Tier |
|---|---|
| .docx file created at expected path | Mock |
| File readable by python-docx without error | Mock |
| Word count within expected range (not empty, not truncated — range calibrated on first successful live run) | Mock |
| Expected sections present in document body | Mock |
| Full Stage 4 .docx passes visual inspection | Live |

---

#### `phase4_cover_letter.py`

**Contract:** Staged generation aligned with resume content. Stage 1 produces a draft; Stage 4
produces a .docx matching resume visual style.

| Criterion | Tier |
|---|---|
| Stage 1 output contains opening, body, closing | Mock |
| No PII in API payload | Mock |
| Stage 4 .docx created and readable | Mock |
| Content references JD-specific elements | Live |
| Visual style consistent with resume template | Live |

---

#### `check_resume.py`

**Contract:** Two-layer quality check. Layer 1 (string matching) detects known violation
patterns. Layer 2 (API) returns structured quality assessment. No false negatives on known
violations.

| Criterion | Tier |
|---|---|
| Layer 1 detects all injected violations in fixture .docx | Mock |
| Layer 1 produces no false positives on clean fixture | Mock |
| Layer 2 API payload contains no PII | Mock |
| Layer 2 response parsed into structured feedback | Mock |
| Full check on real resume returns actionable output | Live |

---

### Phase 5 — `phase5_interview_prep.py`

**Contract:** Given a role folder containing JD and stage files, produces interview_prep.txt
and interview_prep.docx. All STAR stories traceable to submitted resume bullets. Gap analysis
sourced from full JD text, not inferred from industry norms.

| Criterion | Tier |
|---|---|
| Both output files created at expected paths | Mock |
| All required sections present: company brief, salary guidance, STAR stories (>=3), gap analysis (REQUIRED/PREFERRED split), questions to ask | Mock |
| STAR stories reference content present in stage file fixtures | Mock |
| Gap analysis sections sourced from JD text, not invented | Mock |
| No PII in API payload | Mock |
| .docx readable without error | Mock |
| Web search returns current company information | Live |
| Salary range populated with real data | Live |
| STAR stories are coherent: recognizable S/T/A/R structure, content traceable to submitted resume bullets | Live |

**Note on STAR story quality:** Coherence (recognizable structure, grounded content) is the
automated standard. Interview-readiness is a human judgment — story workshopping in Claude
web chat is the correct venue for that refinement, not automated testing.

---

## Section 5 — CI/CD Pipeline

### GitHub Actions Workflow

File: `.github/workflows/test.yml`

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

**`requirements-dev.txt`** — test dependencies kept separate from runtime:

```
pytest
pytest-mock
```

### README Badge

Add to the top of README.md after CI is live:

```markdown
![Tests](https://github.com/YOUR_USERNAME/Job_search_agent/actions/workflows/test.yml/badge.svg)
```

### Live Test Runbook

| Trigger | Scope | Command |
|---|---|---|
| Promoting a prototype phase to active use | Full phase | `pytest tests/phaseN/ -m live -v` |
| Changing any API-calling script | Affected phase only | `pytest tests/phaseN/ -m live -v` |
| Claude model or API version change | Full suite | `pytest -m live -v` |
| Routine commit, bug fix, refactor | None — CI handles it | — |

**Live test pass criteria** — a live test passes when:
1. The API call completes without error
2. The response is parsed successfully into the expected structure
3. Output files are written to expected paths
4. No PII appears in the API payload

Live tests do not assert on content quality. That is a human judgment. The live tier proves
the pipeline executes end-to-end correctly. Content review is a separate step.

---

## Section 6 — Implementation Priority Order

The parking lot (item 10) identified this sequence. This design confirms it is correct and
extends it to the full pipeline.

| Priority | Target | Rationale |
|---|---|---|
| 1 | CI configuration + `pytest.ini` | Green badge before any tests — establishes the pipeline |
| 2 | `utils/test_pii_filter.py` | Foundational safety — highest value, no dependencies |
| 3 | `utils/test_library_parser.py` | Foundational — enables Phase 3 fixture generation |
| 4 | `phase2/test_job_ranking.py` | No API dependency, duplicate detection already working |
| 5 | `phase1/test_pipeline_report.py` | No API dependency |
| 6 | `phase3/` (all four scripts) | Depends on library_parser fixtures being stable |
| 7 | `phase4/test_resume_generator.py` | Highest complexity, most stages |
| 8 | `phase4/test_cover_letter.py` | Depends on phase4 fixture patterns being established |
| 9 | `phase4/test_check_resume.py` | Depends on .docx fixtures from phase4 |
| 10 | `phase5/test_interview_prep.py` | Depends on stage file fixtures from phase4 |

---

## Boundaries and Explicit Non-Goals

- **Stage 2 human review** is not automated. It is a design feature, not a gap.
- **Interview-readiness** of STAR stories is not a test criterion. Coherence is.
- **Content quality assessment** (is this a good resume?) is a human judgment. The suite
  validates structure, schema, grounding, and safety — not quality.
- **Live tests are never run in CI.** API cost and response variability make them unsuitable
  for automated gating. They are a developer tool, not a CI gate.
