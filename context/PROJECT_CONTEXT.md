<!-- assembled by build_docs.py -- edit docs/templates/ and docs/fragments/ not this file -->
# AI Job Search Agent — Project Context
Last updated: 04 May 2026

## About This File
Lean index file for quick orientation. Load supporting context files as needed.
Do not bulk-load all context files into every session — load only what is relevant.

## What This Project Is
A multi-phase AI-powered job search automation system built as both a practical tool for managing an active senior defense SE job search and a portfolio project demonstrating Python development, API integration, and AI agent design.

Candidate: [CANDIDATE] — Senior Systems Engineer, San Diego CA, Current TS/SCI.

## Project Split — Development vs Implementation

<!-- fragment: project_split -->
This project is split into two distinct workflows:

**Development** — building and improving the pipeline tools.
Performed using Claude Code in VS Code, working directly against local files.
Reference: `context/DECISIONS_LOG.md` for coding conventions and architecture.

**Implementation** — applying the tools to an active job search.
Performed using Claude web chat for resume tailoring, interview prep,
story workshopping, and pipeline management.
Reference: `context/PIPELINE_STATUS.md` and `context/CANDIDATE_BACKGROUND.md`.


## Current Phase Status

<!-- fragment: current_phase_status -->
| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Pipeline report script and tracker schema | ✅ Complete |
| 2 | Job ranking and semantic fit analysis | ✅ Complete |
| 3 | Experience knowledge base — structured JSON library with shared parsing module | ✅ Complete |
| 4 | Automated resume + cover letter generation — tailored .docx per application | ✅ Complete |
| 5 | Interview preparation — stage-aware prep packages (recruiter / hiring manager / team panel) | ✅ Complete |
| 6 | Networking and outreach support — warmth-calibrated LinkedIn and email outreach messages across four contact stages | ✅ Complete |
| 7 | Search agent — automated role discovery | ⏳ Planned |


## V&V Framework (added 07 Apr 2026)
A two-tier pytest suite now covers the full pipeline. This is the baseline for all future script changes.

- **Tier 1 (mock):** `pytest tests/ -m "not live" -v` — runs in CI on every push, no API key needed
- **Tier 2 (live):** `pytest -m live -v` — run before promoting a phase or after API changes
- **CI:** GitHub Actions at `.github/workflows/test.yml` — green badge on README
- **483 mock tests** across utils, phases 1–6. All passing as of 04 May 2026.
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

### find_duplicate_bullets utility (04 May 2026)
`scripts/utils/find_duplicate_bullets.py` — standalone utility for experience library quality maintenance:
- Scans `experience_library.json` for same or near-duplicate bullets across all employers using rapidfuzz `token_sort_ratio`
- Union-find clustering handles transitive matches (A ~ B ~ C → one cluster even if A and C don't directly match)
- Default threshold: 85%. Override with `--threshold`. Custom library path via `--library`.
- Writes grouped cluster report to `outputs/duplicate_bullet_report_YYYYMMDD_HHMM.txt`
- Pure function `find_duplicate_clusters(bullets, threshold)` is fully injectable for testability
- 14 Tier 1 mock tests covering edge cases, cross-employer matching, same-employer matching, transitive clustering, and report formatting

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
<!-- fragment: project_structure -->
```
Job_search_agent/
├── .github/workflows/test.yml            # GitHub Actions CI — mock suite on every push
├── context/                              # Context data store
│   ├── PROJECT_CONTEXT.md                # Lean index — load this first
│   ├── DECISIONS_LOG.md                  # Coding conventions + architecture decisions
│   ├── PARKING_LOT.md                    # Outstanding work items and priorities
│   └── candidate/                        # Personal data — gitignored
│       ├── candidate_config.yaml         # Structured career data (local only)
│       ├── candidate_config.example.yaml # Blank template (tracked)
│       ├── CANDIDATE_BACKGROUND.md       # Career background (local only)
│       └── PIPELINE_STATUS.md            # Active applications (local only)
├── data/
│   ├── jobs.csv                          # Pipeline — status + req number tracking
│   ├── job_packages/[role]/              # JD, stage files, interview prep (active)
│   │   └── inactive/[role]/              # Rejected / ghosted / withdrawn roles
│   ├── debriefs/[role]/                  # Post-interview debrief JSON (local only)
│   ├── interview_library.json           # Persistent story/gap/question library (local only)
│   └── experience_library/              # Library source, JSON, candidate profile
├── docs/
│   ├── features/                         # Requirements artifacts per capability
│   │   ├── README.md                     # Feature folder process and conventions
│   │   ├── user_story_template.md        # Template for new proposals
│   │   └── completed/                    # Built and tested features
│   ├── fragments/                        # Canonical shared content — edit these, not assembled docs
│   │   ├── audit_report.md               # Document audit findings (AC-1)
│   │   ├── current_phase_status.md       # Canonical phase table
│   │   ├── key_commands.md               # Canonical quick reference commands
│   │   ├── project_split.md              # Canonical dev vs implementation description
│   │   └── project_structure.md          # Canonical directory tree (this file)
│   ├── superpowers/
│   │   ├── specs/                        # Design specs (how to build it)
│   │   └── plans/                        # Implementation plans (how to execute)
│   ├── templates/                        # Document assembly templates ({{include:}} markers)
│   │   ├── README.md                     # Template for README.md
│   │   └── PROJECT_CONTEXT.md            # Template for context/PROJECT_CONTEXT.md
│   └── capabilities.md                   # Script-to-phase traceability (in progress)
├── example_data/
|   ├── job_packages/[role]/              # Example JD, stage files
|   ├── outputs/                          # Example generated reports, pipeline_reports, ranking_reports, semantic_analysis_reports
|   ├── tracker/job_pipeline_example.xlsx # Example job pipeline tracker
|   │    ├── README.txt                   # Tracker workbook README
|   │    └── contact_pipeline_example.xlsx # Example contact tracker (fictional data)
|   └── jobs.csv                          # Example Pipeline - status + req number tracking
├── outputs                               # Generated reports, pipeline_reports, ranking_reports, semantic_analysis_reports
├── resumes/                              # Generated resumes (local only)
├── templates/                            # Script input templates (tracked — YAML, plain-text)
│   └── interview_debrief_template.yaml   # Debrief YAML template for --init mode
├── templates_local/                      # Binary/personal templates (local only)
│   └── resume_template.docx              # Resume template (local only)
├── scripts/
│   ├── init_job_package.py               # Initialize new job package folder, job_description.txt, and jobs.csv row
│   ├── pipeline_report.py                # Pipeline metrics + duplicate req detection
│   ├── phase2_job_ranking.py             # Keyword scoring + req number tracking
│   ├── phase2_semantic_analyzer.py       # Claude API semantic fit analysis
│   ├── phase3_parse_library.py           # Full library parse (thin wrapper)
│   ├── phase3_parse_employer.py          # Single-employer re-parse
│   ├── phase3_build_candidate_profile.py
│   ├── phase3_compile_library.py
│   ├── phase4_resume_generator.py        # Four-stage resume generation
│   ├── phase4_cover_letter.py            # Staged cover letter generator
│   ├── phase5_interview_prep.py          # Stage-aware interview prep (recruiter/HM/team panel)
│   ├── phase5_debrief.py                  # Post-interview debrief capture (--init/--convert/--interactive)
│   ├── phase5_thankyou.py                # Post-interview thank-you letter generation (one per interviewer)
│   ├── phase5_workshop_capture.py        # Parses workshopped prep .docx into interview_library.json
│   ├── phase5_debrief_utils.py           # Shared utility — load filed debrief JSON
│   ├── interview_library_parser.py       # Shared module — read/write interview_library.json
│   ├── phase6_networking.py              # Warmth-calibrated outreach message generator; reads/writes contact_pipeline.xlsx
│   ├── check_resume.py                   # Two-layer resume quality check (string matching + API)
│   ├── check_cover_letter.py             # Two-layer cover letter quality check
│   └── utils/
│       ├── build_docs.py                 # Assemble README + PROJECT_CONTEXT from fragments
│       ├── candidate_config.py           # Candidate career data loader (load, get_hardcoded_rules, build_known_facts)
│       ├── find_duplicate_bullets.py     # Scan experience_library.json for duplicate bullets; writes cluster report to outputs/
│       ├── library_parser.py             # Shared parsing logic (no side effects)
│       ├── normalize_library.py          # One-time cleanup — merge tranche-suffixed employer sections
│       └── pii_filter.py                 # PII stripping — safe for GitHub
├── tests/                                # Two-tier pytest suite (mock + live)
│   ├── conftest.py                       # Shared fixtures and fictional test identity
│   ├── fixtures/                         # Fictional test data (Jane Q. Applicant / Acme)
│   ├── utils/                            # pii_filter, library_parser, build_docs tests
│   └── phase1/ … phase6/                 # Per-phase test files mirroring scripts/
├── CLAUDE.md                             # Claude Code conventions and safety rules
├── pytest.ini                            # Test config: pythonpath, live marker
├── requirements.txt                      # Runtime dependencies
├── requirements-dev.txt                  # Test dependencies (pytest, pytest-mock)
├── .env                                  # API keys and PII — never committed
├── .env.example                          # Environment variable template
├── .gitignore
└── README.md
```


## Quick Reference — Key Commands
<!-- fragment: key_commands -->
```
# Tests (run after any script change)
pytest tests/ -m "not live" -v          # Tier 1 mock suite — all must pass
pytest -m live -v                        # Tier 2 live API (before promoting a phase)

# Job package initialization
python -m scripts.init_job_package --role [role] --req [req#]

# Pipeline
python -m scripts.pipeline_report
python -m scripts.phase2_job_ranking
python -m scripts.phase2_semantic_analyzer

# Resume generation
python -m scripts.phase4_resume_generator --stage 1 --role [role]
python -m scripts.phase4_resume_generator --stage 3 --role [role]
python -m scripts.phase4_resume_generator --stage 4 --role [role]
python -m scripts.check_resume --role [role]

# Cover letter
python -m scripts.phase4_cover_letter --stage 1 --role [role]
python -m scripts.phase4_cover_letter --stage 4 --role [role]

# Interview prep
python -m scripts.phase5_interview_prep --role [role]

# Library maintenance
python -m scripts.phase3_parse_library
python -m scripts.phase3_parse_employer "[employer name]"
python -m scripts.phase3_build_candidate_profile
python -m scripts.phase3_compile_library

# Networking outreach
python -m scripts.phase6_networking --list
python -m scripts.phase6_networking --contact "[name]" --stage [1-4]
python -m scripts.phase6_networking --contact "[name]" --stage 2 --role [role]

# Library maintenance — duplicate bullet detection
python -m scripts.utils.find_duplicate_bullets                    # scan at default threshold (85%)
python -m scripts.utils.find_duplicate_bullets --threshold 90     # stricter threshold

# Document assembly (run after editing any fragment or template)
python scripts/utils/build_docs.py                   # rebuild all
python scripts/utils/build_docs.py --doc README.md   # rebuild one
```

