# AI Job Search Agent — Project Context
Last updated: 21 Apr 2026

## About This File
Lean index file for quick orientation. Load supporting context files as needed.
Do not bulk-load all context files into every session — load only what is relevant.

## What This Project Is
A multi-phase AI-powered job search automation system built as both a practical tool for managing an active senior defense SE job search and a portfolio project demonstrating Python development, API integration, and AI agent design.

Candidate: [CANDIDATE] — Senior Systems Engineer, San Diego CA, Current TS/SCI.

## Project Split — Development vs Implementation

{{include: project_split}}

## Current Phase Status

{{include: current_phase_status}}

## V&V Framework (added 07 Apr 2026)
A two-tier pytest suite now covers the full pipeline. This is the baseline for all future script changes.

- **Tier 1 (mock):** `pytest tests/ -m "not live" -v` — runs in CI on every push, no API key needed
- **Tier 2 (live):** `pytest -m live -v` — run before promoting a phase or after API changes
- **CI:** GitHub Actions at `.github/workflows/test.yml` — green badge on README
- **359 mock tests** across utils, phases 1–5. All passing on master as of 21 Apr 2026.
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

## Non-Negotiable Rules (always in scope)
- En dashes only — never em dashes (em dashes signal AI-generated content)
- Stage files are source of truth — never edit .docx directly
- Never git add . — always stage files explicitly
- Never fabricate or infer experience — ask if unclear
- PII stripped from all API calls via pii_filter.py
- Run `pytest tests/ -m "not live"` after any script change — all must pass before committing
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
{{include: project_structure}}

## Quick Reference — Key Commands
{{include: key_commands}}
