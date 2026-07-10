# Session Handoff — 2026-04-23

**For:** Claude web (claude.ai) — context to start the next conversation
**Project:** AI Job Search Agent — [docs/session_handoff_2026-04-23.md]

---

## What This Project Is

A multi-phase AI-powered job search automation system. Python scripts for job ranking, resume generation, cover letter generation, interview prep, and post-interview capture. Used for an active senior defense SE job search and as a portfolio project.

Two workflows:
- **Development** — Claude Code in VS Code, editing scripts and tests
- **Implementation** — Claude web, running scripts to support active applications

---

## Current State (as of end-of-day 2026-04-23)

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Pipeline report | Complete |
| 2 | Job ranking + semantic fit | Complete |
| 3 | Experience library (structured JSON) | Complete |
| 4 | Resume + cover letter generation (.docx) | Complete |
| 5 | Interview prep — stage-aware packages + debrief + thank-you + workshop capture | Complete |
| 6 | Networking + outreach support | Planned (next) |
| 7 | Search agent — automated role discovery | Planned |

**Test suite:** 384 mock tests passing, CI green on master. Two-tier: `pytest tests/ -m "not live" -v` (Tier 1, no API key) and `pytest -m live -v` (Tier 2, before promoting a phase).

---

## What Was Done in This Session

### Morning: Style fix (commit db6f3da)
- `scripts/phase3_parse_library.py` — updated next-step comment to use en dash per project convention.

### Evening: Codebase cleanup + housekeeping (commit 92b4036)

**Folder naming QC (parking lot item 12 — complete):**
- 8 `docs/` folders renamed from hyphens to underscores via `git mv` (e.g., `post-interview-debrief` → `post_interview_debrief`, `phase5-library-integration` → `phase5_library_integration`).
- 8 superpowers plan/spec/handoff documents updated for new internal cross-references.
- `docs/features/README.md` naming convention updated.

**Codebase cleanup (4 items — complete):**
1. `resumes/tailored/` path renamed to `resumes/` in `phase4_resume_generator.py` and `phase4_cover_letter.py` — the `tailored/` subdirectory never existed at runtime; this was a stale path.
2. Dead `RESUMES_TAILORED_DIR` constant removed from `phase5_interview_prep.py`.
3. `phase4_cover_letter.py` template path corrected from `templates/` to `templates_local/` — cover letter uses `resume_template.docx` which is gitignored and lives in `templates_local/`; `DATA_FLOW.md` updated to match.
4. 5 Phase 5 test files moved from `tests/` root to `tests/phase5/` via `git mv` (`test_phase5_debrief.py`, `test_phase5_debrief_utils.py`, `test_phase5_thankyou.py`, `test_phase5_workshop_capture.py`, `test_interview_library_parser.py`).

**Housekeeping (parking lot items 15, 16 — complete):**
- `generate_test_fixture.py` moved from `scripts/utils/` to `tests/utils/` — correctly classified as a dev utility, not a production module.
- Stale `docs/superpowers/plans/2026-04-13-post-interview-debrief-old.md` (~1,500 lines) archived to `docs/superpowers/plans/archive/`.

**New file — `scripts/config.py` (parking lot item 14, stub only):**
- Created as a shared constants stub with `JOBS_PACKAGES_DIR`, `EXPERIENCE_LIBRARY_JSON`, `CANDIDATE_PROFILE_PATH`, `RESUMES_DIR`, `RESUME_TEMPLATE`, `MODEL_SONNET`, `MODEL_HAIKU`.
- **Not yet wired** — callers still hardcode these values. Wiring all 9+ callers is item 14 in the parking lot.

**Docs rebuilt:**
- `README.md` and `context/PROJECT_CONTEXT.md` rebuilt via `build_docs.py` to reflect new layout.
- `PARKING_LOT.md` and `PARKING_LOT_DONE.md` updated.

---

## Active Parking Lot (prioritized)

| # | Item | Notes |
|---|------|-------|
| 4 | **Phase 6 — Networking support** | Highest priority. Fully scoped. Standalone script `phase6_networking.py --role [role]`. Five sections: LinkedIn search guidance, connection request (300 char), follow-up after connecting, cold outreach/InMail, informational interview request. User performs searches manually — script provides guidance. |
| 5 | Phase 4 Stage 4 — add Phase 6 next-step prompt | Deferred until Phase 6 stable. |
| 14 | Wire callers to `scripts/config.py` | Stub created. 9+ scripts still hardcode `JOBS_PACKAGES_DIR`, model strings, etc. Requires updating all callers after extracting constants. |
| 8 | Script identifier audit — GitHub exposure | Audit committed scripts for hardcoded role-specific strings or example values drawn from real applications. Remediate with generic placeholders. |
| 9 | `check_utils.py` shared module | Deferred — reevaluate if a third checker is added. |
| 11 | Phase 0 — Candidate Onboarding docs | Document structured prompts to capture existing experience into the working library. |
| 10 | Phase 7 — Search agent | Deferred — lower priority than Phase 6. |

---

## Key Conventions (always in scope)

- En dashes only — never em dashes (em dashes signal AI-generated content)
- No hardcoded PII — all personal data via `.env` variables
- Never `git add .` — always stage files explicitly
- Run `pytest tests/ -m "not live"` after any script change — all 384 must pass before committing
- Python 3.11 compat: no backslash escapes inside f-string `{}` expressions
- `scripts/utils/pii_filter.py` `strip_pii()` required on all API calls

---

## Key Context Files

| File | Purpose |
|------|---------|
| `context/PROJECT_CONTEXT.md` | Lean index — load first |
| `context/DECISIONS_LOG.md` | Coding conventions + architecture decisions |
| `context/PARKING_LOT.md` | Outstanding work items |
| `context/SCHEMA_REFERENCE.md` | JSON schemas for debrief, interview_library, experience_library |
| `context/DATA_FLOW.md` | What each script reads/writes at runtime |
| `context/SCRIPT_INDEX.md` | Quick-reference table of every script |
| `context/STAGE_FILES.md` | File lifecycle inside `data/job_packages/[role]/` |

---

## Suggested Next Conversation Opener

> "Here's the project context: [paste this file]. I'd like to start Phase 6 — Networking support. The spec is in `context/PARKING_LOT.md` item 4. Let's start with a plan."
