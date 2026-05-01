# AI Job Search Agent — Project Context
Last updated: 01 May 2026

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
- **469 mock tests** across utils, phases 1–6. All passing on master as of 01 May 2026.
- **Test dependencies:** `requirements-dev.txt` (pytest, pytest-mock)
- **Fixture identity:** Jane Q. Applicant / Acme Defense Systems / ADS-12345

### Scripts refactored for testability (07 Apr 2026)
All 8 scripts below had module-level execution removed so they can be imported by tests:
- `pipeline_report.py` — extracted `analyze_applications()`, `detect_duplicates()`
- `phase2_job_ranking.py` — extracted `detect_duplicates()`, added `ACTIONABLE_STATUSES` / `EXCLUDED_STATUSES`
- `phase2_semantic_analyzer.py` — extracted `analyze_job()`
- `phase3_compile_library.py` — extracted `compile_library()`
- `phase3_build_candidate_profile.py` — extracted `build_profile()`; PII fully migrated to `candidate_config.yaml` via 17a (KNOWN_FACTS, INTRO_MONOLOGUE, SHORT_TENURE_EXPLANATION → candidate_config loader)
- `phase4_resume_generator.py` — extracted `run_stage1()`, `run_stage3()`, `run_stage4()`
- `phase4_cover_letter.py` — extracted `run_cl_stage1()`, `run_cl_stage4()`
- `phase5_interview_prep.py` — extracted `generate_prep()`

Already importable (no changes needed): `pii_filter.py`, `library_parser.py`, `phase3_parse_library.py`, `phase3_parse_employer.py`, `check_resume.py`.

### phase3_compile_library + phase5_thankyou improvements (01 May 2026)
`scripts/phase3_compile_library.py` — employer ordering regression fix:
- `compile_library()` now sorts the `employers[]` array by `CHRONOLOGICAL_ORDER` from `candidate_config.yaml` instead of alphabetically by filename
- Accepts optional `chrono_order` parameter for testability (tests inject fixture names; production reads config)
- Skips employer files whose `name` field is not in `CHRONOLOGICAL_ORDER` — prevents stray files from appearing in compiled output
- Emits named warnings in both directions: file not in config, config entry not matched by any file

`scripts/phase4_resume_generator.py`:
- `build_stage1_draft()` now emits a named warning when an employer from the library is not in `CHRONOLOGICAL_ORDER` — surfaces name-mismatch issues at generation time

`scripts/phase5_thankyou.py` — salutation and closing block added to all generated letters:
- `_build_salutation(name)` — extracts first name; falls back to "Dear Hiring Manager," when name is null/empty
- `_build_closing(candidate_name)` — standard closing sentence (en dash), "Respectfully,", candidate name from `CANDIDATE_NAME` env var
- `generate_letters()` wraps Claude's body output: `salutation + body + closing` before writing `.txt` and `.docx`
- 15 new mock tests (35 total for phase5_thankyou): salutation, first-name extraction, null-name fallback, closing block, candidate name, en-dash enforcement

### Phase 6 — Networking and outreach support (27 Apr 2026)
`scripts/phase6_networking.py` — contact-centric outreach message generator:
- Reads/writes `data/tracker/contact_pipeline.xlsx` (gitignored)
- Four stages: connection request (Stage 1), referral ask (Stage 2), follow-up nudge (Stage 3), close the loop (Stage 4)
- Four warmth tiers: Cold, Acquaintance, Former Colleague, Strong — each with calibrated tone and placeholder markers
- Stage 1: 300-char connection request limit enforced with one API retry; Acquaintance/Former Colleague get character budget display for fill-in placeholders
- Stage 2: conditional referral bonus angle; role-fit rationale separator
- Interactive y/n confirm before writing stage advance back to xlsx
- `generate_message()` is pure/importable — injectable client for testing
- 52 Tier 1 mock tests; 6 Tier 2 live API tests

### Candidate data store — 17a (25 Apr 2026)
All personal constants migrated from 6 formerly-gitignored scripts to `context/candidate/candidate_config.yaml`:
- `scripts/utils/candidate_config.py` — new loader module (`load()`, `get_hardcoded_rules()`, `build_known_facts()`)
- `check_resume.py`, `check_cover_letter.py` — HARDCODED_RULES → `candidate_config.get_hardcoded_rules()`
- `phase4_resume_generator.py` — EMPLOYER_TIERS, CHRONOLOGICAL_ORDER, build_docx strings → candidate_config
- `phase2_semantic_analyzer.py` — hardcoded fallback profile → `candidate_config.build_known_facts()`
- `phase3_build_candidate_profile.py` — KNOWN_FACTS, INTRO_MONOLOGUE, SHORT_TENURE_EXPLANATION → candidate_config
- `phase2_job_ranking.py` — restored to tracking (no PII; KEYWORDS generalization deferred to 17b)
- All 6 scripts now git-tracked. 8 unit tests for loader. 392 mock tests passing.

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
| context/candidate/CANDIDATE_BACKGROUND.md | Resume tailoring, interview prep, story workshopping |
| context/candidate/PIPELINE_STATUS.md | Pipeline management, application decisions, recruiter comms |
| context/DECISIONS_LOG.md | Script development, architecture decisions, coding conventions |
| context/PARKING_LOT.md | Planning next development session, prioritizing work items |
| context/PARKING_LOT_DONE.md | Completed item history — load when reviewing what has been built |

## Project Structure (top level)
{{include: project_structure}}

## Quick Reference — Key Commands
{{include: key_commands}}
