# AI Job Search Agent — Project Context
Last updated: 19 Apr 2026

## About This File
Lean index file for quick orientation. Load supporting context files as needed.
Do not bulk-load all context files into every session — load only what is relevant.

## What This Project Is
A multi-phase AI-powered job search automation system built as both a practical tool for managing an active senior defense SE job search and a portfolio project demonstrating Python development, API integration, and AI agent design.

Candidate: [CANDIDATE] — Senior Systems Engineer, San Diego CA, Current TS/SCI.

## Project Split — Development vs Implementation

### Development (Claude Code in VS Code)
Building and improving the pipeline tools. Script editing, debugging, refactoring, architecture decisions, library maintenance, new phase development.
Reference: context/DECISIONS_LOG.md for coding conventions and architecture decisions.

### Implementation (Claude web chat)
Applying the tools to the active job search. Resume tailoring, interview prep, story workshopping, pipeline management, recruiter communications.
Reference: context/PIPELINE_STATUS.md and context/CANDIDATE_BACKGROUND.md.

## Current Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Pipeline report + tracker schema | Complete |
| 2 | Job ranking + semantic fit analysis | Complete |
| 3 | Experience library — structured JSON + shared parser | Complete |
| 4 | Resume generation + cover letter — tailored .docx per application | Competet |
| 5 | Interview prep — web search, story bank, gap analysis | Complete |
| 6 | Networking and outreach support | Planned |
| 7 | Search agent — automated role discovery | Planned |

## V&V Framework (added 07 Apr 2026)
A two-tier pytest suite now covers the full pipeline. This is the baseline for all future script changes.

- **Tier 1 (mock):** `pytest tests/ -m "not live" -v` — runs in CI on every push, no API key needed
- **Tier 2 (live):** `pytest -m live -v` — run before promoting a phase or after API changes
- **CI:** GitHub Actions at `.github/workflows/test.yml` — green badge on README
- **73 mock tests** across utils, phases 1–5. All passing on master as of 07 Apr 2026.
- **Test dependencies:** `requirements-dev.txt` (pytest, pytest-mock)
- **Fixture identity:** Jane Q. Applicant / Acme Defense Systems / ADS-12345

### Scripts refactored for testability (07 Apr 2026)
All 8 scripts below had module-level execution removed so they can be imported by tests:
- `pipeline_report.py` — extracted `analyze_applications()`, `detect_duplicates()`
- `phase2_job_ranking.py` — extracted `detect_duplicates()`, added `ACTIONABLE_STATUSES` / `EXCLUDED_STATUSES`
- `phase2_semantic_analyzer.py` — extracted `analyze_job()`
- `phase3_compile_library.py` — extracted `compile_library()`
- `phase3_build_candidate_profile.py` — **PII remediated** (KNOWN_FACTS hardcoded values → `os.getenv()`), extracted `build_profile()`; add `CANDIDATE_LOCATION` to `.env`
- `phase4_resume_generator.py` — extracted `run_stage1()`, `run_stage3()`, `run_stage4()`
- `phase4_cover_letter.py` — extracted `run_cl_stage1()`, `run_cl_stage4()`
- `phase5_interview_prep.py` — extracted `generate_prep()`

Already importable (no changes needed): `pii_filter.py`, `library_parser.py`, `phase3_parse_library.py`, `phase3_parse_employer.py`, `check_resume.py`.

### Known issue (documented, not yet fixed)
`library_parser.py` silently drops the last bullet in an employer section when immediately followed by `## PROFESSIONAL SUMMARIES`. Documented in `test_parse_library_bullet_count_matches_source`. Fix: flush the pending bullet before resetting `current_employer`.

## Non-Negotiable Rules (always in scope)
- En dashes only — never em dashes (em dashes signal AI-generated content)
- Stage files are source of truth — never edit .docx directly
- Never git add . — always stage files explicitly
- Never fabricate or infer experience — ask if unclear
- PII stripped from all API calls via pii_filter.py
- Run `pytest tests/ -m "not live"` after any script change — all 73 must pass before committing
- Python 3.11 compat required: no backslash escapes inside f-string `{}` expressions

## Supporting Context Files
Load these as needed for the session type:

| File | Load When |
|------|-----------|
| context/CANDIDATE_BACKGROUND.md | Resume tailoring, interview prep, story workshopping |
| context/PIPELINE_STATUS.md | Pipeline management, application decisions, recruiter comms |
| context/DECISIONS_LOG.md | Script development, architecture decisions, coding conventions |
| context/PARKING_LOT.md | Planning next development session, prioritizing work items |

## Project Structure (top level)
```
Job_search_agent/
├── .github/workflows/test.yml — CI: mock suite on every push
├── context/                  — context data store (this file + 4 supporting files)
├── data/                     — personal data, local only, never committed
├── resumes/tailored/         — generated resumes, local only
├── templates/                — resume template, local only
├── scripts/                  — all automation scripts
├── tests/                    — two-tier pytest suite
│   ├── conftest.py           — shared fixtures (pii_values, fixtures_dir, make_mock_response)
│   ├── fixtures/             — fictional test data (Jane Q. Applicant / Acme Defense Systems)
│   ├── utils/                — pii_filter and library_parser tests
│   └── phase1/ … phase5/    — per-phase test files mirroring scripts/
├── example_data/             — fictional reference data
├── CLAUDE.md                 — Claude Code conventions and safety rules
├── pytest.ini                — testpaths = tests, pythonpath = ., live marker
├── requirements.txt          — runtime dependencies
├── requirements-dev.txt      — test dependencies (pytest, pytest-mock)
├── .env                      — API keys and PII, never committed
├── .env.example              — environment variable template
├── .gitignore
└── README.md
```

## Quick Reference — Key Commands
```
# Tests (run after any script change)
pytest tests/ -m "not live" -v          # Tier 1 mock suite — all 73 must pass
pytest -m live -v                        # Tier 2 live API (before promoting a phase)

# Pipeline
python scripts/pipeline_report.py
python scripts/phase2_job_ranking.py
python scripts/phase2_semantic_analyzer.py

# Resume generation
python scripts/phase4_resume_generator.py --stage 1 --role [role]
python scripts/phase4_resume_generator.py --stage 3 --role [role]
python scripts/phase4_resume_generator.py --stage 4 --role [role]
python scripts/check_resume.py --role [role]

# Cover letter
python scripts/phase4_cover_letter.py --stage 1 --role [role]
python scripts/phase4_cover_letter.py --stage 4 --role [role]

# Interview prep
python scripts/phase5_interview_prep.py --role [role]

# Library maintenance
python scripts/phase3_parse_library.py
python scripts/phase3_parse_employer.py "[employer name]"
python scripts/phase3_build_candidate_profile.py
python scripts/phase3_compile_library.py
```
