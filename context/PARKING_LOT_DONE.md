
# Parking Lot Done

__Load for: planning next development session, understancing completed items__  
Last updated: 27 Apr 2026

## Completed (recent)

- Phase 6 — Networking and outreach support — COMPLETE (27 Apr 2026)
  `scripts/phase6_networking.py` — warmth-calibrated outreach message generator. Reads contact list from `data/tracker/contact_pipeline.xlsx` (gitignored). Four stages: Stage 1 = LinkedIn connection request (300-char hard limit, one API retry if over) + follow-up; Stage 2 = referral ask with conditional referral bonus angle and role-fit rationale; Stage 3 = follow-up nudge (warmth-calibrated tone); Stage 4 = close the loop. Four warmth tiers: Cold, Acquaintance, Former Colleague, Strong — Acquaintance and Former Colleague receive placeholder markers ([HOW YOU KNOW THIS PERSON] / [WHERE YOU WORKED TOGETHER]) for user fill-in. Interactive y/n confirm before writing stage advance back to xlsx. `generate_message()` is a pure importable function with injectable client for testing. 52 Tier 1 mock tests, 6 Tier 2 live API tests. `@pytest.mark.live` added so CI skips live tests. `SCRIPT_INDEX.md` and `DATA_FLOW.md` updated. Example tracker at `example_data/tracker/contact_pipeline_example.xlsx`. Parking lot item 4 closed; item 5 (Phase 4 Stage 4 next steps prompt) unblocked.

- Candidate data store — 17a — COMPLETE (25 Apr 2026)
  `context/candidate/` folder created and gitignored via single rule. `candidate_config.example.yaml` tracked as blank template. `scripts/utils/candidate_config.py` loader built with `load()`, `get_hardcoded_rules()`, `build_known_facts()`. All 6 formerly-gitignored scripts refactored to PII-free and restored to git tracking: `check_resume.py`, `check_cover_letter.py` (HARDCODED_RULES → loader), `phase4_resume_generator.py` (EMPLOYER_TIERS, CHRONOLOGICAL_ORDER, build_docx strings → loader), `phase2_semantic_analyzer.py` (hardcoded fallback profile → loader), `phase3_build_candidate_profile.py` (KNOWN_FACTS, INTRO_MONOLOGUE, SHORT_TENURE_EXPLANATION → loader), `phase2_job_ranking.py` (no PII — restored directly; KEYWORDS generalization deferred to 17b). `CANDIDATE_BACKGROUND.md` and `PIPELINE_STATUS.md` moved to `context/candidate/`. `.gitignore`, `CLAUDE.md`, `SCRIPT_INDEX`, `PROJECT_CONTEXT.md` all updated. 8 loader unit tests. 392 mock tests passing.

- Move generate_test_fixture.py to tests/utils/ (item #15) — COMPLETE (23 Apr 2026)
  `scripts/utils/generate_test_fixture.py` moved to `tests/utils/generate_test_fixture.py` via `git mv`. Path was already project-root-relative — no fix needed. Correctly classified as a dev utility, not a production module.
- Archive stale plan doc (item #16) — COMPLETE (23 Apr 2026)
  `docs/superpowers/plans/2026-04-13-post-interview-debrief-old.md` (~1,500 lines) moved to `docs/superpowers/plans/archive/` via `git mv`.
- Folder naming QC (item #12) — COMPLETE (23 Apr 2026)
  8 folders renamed via `git mv` (hyphens to underscores): `docs/features/completed/context_indexes`, `interview_prep_stage_awareness`, `phase5_library_integration`, `phase5_thankyou_letters`, `phase5_workflow_orchestration`, `phase5_workshop_capture`, `post_interview_debrief`, and `docs/web-skills/interview_prep`. `docs/features/README.md` naming convention updated. 8 superpowers plan docs updated for internal cross-references via sed. Zero hyphenated folder refs remain outside archive. `data/job_packages/` role folders were out of scope (gitignored personal data). pytest: 384 passed, 0 failures.
- Codebase cleanup — COMPLETE (23 Apr 2026)
  Four mechanical improvements from codebase audit: (1) `resumes/tailored/` path renamed to `resumes/` in `phase4_resume_generator.py` and `phase4_cover_letter.py`; (2) dead `RESUMES_TAILORED_DIR` constant removed from `phase5_interview_prep.py`; (3) `phase4_cover_letter.py` template path corrected from `templates/` to `templates_local/` (was a misconfiguration vs. resume generator); `DATA_FLOW.md` updated to match; (4) 5 Phase 5 test files moved from `tests/` root to `tests/phase5/` via `git mv` (`test_phase5_debrief.py`, `test_phase5_debrief_utils.py`, `test_phase5_thankyou.py`, `test_phase5_workshop_capture.py`, `test_interview_library_parser.py`). `build_docs.py` run after; README and PROJECT_CONTEXT rebuilt. pytest: 384 passed, 0 failures.
- Job Package Initializer — COMPLETE (21 Apr 2026)
  `scripts/init_job_package.py` — CLI: `python -m scripts.init_job_package --role [role] --req [req#]`. Creates job package folder and empty job_description.txt, appends jobs.csv row (blank status for Phase 2 review), opens file in editor. Full conflict detection: true duplicate (same req# + same role + active status), inactive reactivation (any non-active status), folder collision with interactive suffix prompt. 25 unit tests. PR #3.
- candidate_profile.md rebuild — COMPLETE (21 Apr 2026)
  Security+ flagged as (lapsed); HAIPE-enabled architectures added to KForce employer bullet and confirmed in Domain Knowledge. Profile regenerated 19 Apr 2026.
- Phase 5 HAIPE gap false positive — COMPLETE (21 Apr 2026)
  Resolved by candidate_profile.md rebuild above; HAIPE now confirmed in employer history and Domain Knowledge, preventing Phase 5 from flagging it as a gap.
- Single source of truth for assembled documents — COMPLETE (21 Apr 2026)
  Fragment-based assembly via build_docs.py. Canonical content in docs/fragments/, assembled into README.md and context/PROJECT_CONTEXT.md via docs/templates/. Pre-commit hook warns on direct edits to assembled files.
- Script usage instructions updated to python -m invocation — COMPLETE (21 Apr 2026)
  Header comments and runtime print statements updated across 12 scripts + README.md. Note: build_docs.py and generate_test_fixture.py were out of scope and retain old style.
- Phase 5 prompt fixes — salary duplicate and gap fabrication guardrails — COMPLETE (21 Apr 2026)
  Salary actuals exclusivity guardrail in `_build_section1_prompt`; confirmed-skills guardrail + redirect honesty rule in `_build_gap_prompt`. Commits: 1a2c073, aa46c76. 45 tests pass.
- Experience library update workflow (a script that identifies net-new and variant resume bullets from stage files, stages them for human review) (19 Apr 2026)
  `phase4_backport.py` (full backport script (no API calls, rapidfuzz fuzzy matching))
  `generate_test_fixture.py` (one time fixture generator)
- Updated Security+ status to (lapsed), was already removed from resume generator (19 Apr 2026)
- Added UCSD Systems Engineering certificate program to CANDIDATE_BACKGROUND, phase3_build_candidate_profile.py and experience library education section (19 Apr 2026)
- Interview follow-up capture and library -- COMPLETE (Apr 2026)
  `phase5_debrief.py` (--init/--convert/--interactive), `phase5_workshop_capture.py`, `phase5_thankyou.py`, library integration in `phase5_interview_prep.py`. Full workflow in `docs/phase5_workflow_orchestration_amended.md`.
- library_parser.py last-bullet drop bug — COMPLETE (18 Apr 2026)
  Flush guard added before `## PROFESSIONAL SUMMARIES` transition; test assertion corrected 2→3; 7/7 parser tests pass
- pytest baseline setup — COMPLETE (07 Apr 2026)
  73 mock tests across utils, phases 1–5; CI via GitHub Actions; all passing on master
- Phase 4 cover letter generator — COMPLETE (07 Apr 2026)
  phase4_cover_letter.py built, refactored for testability; in Quick Reference commands
- Overmatch bullet priority flag — COMPLETE (05 Apr 2026)
  Data tagged (*PRIORITY: true*), parser updated, confirmed working in Stage 1
- Phase 5 gap detection fix — COMPLETE
  Two-tier REQUIRED/PREFERRED, full JD used, no inference from industry norms
- Phase 5 web search — COMPLETE (v2)
- Phase 5 resume bullet pull from stage files — COMPLETE (v2)
- Phase 5 .docx output — COMPLETE
- req_number tracking in jobs.csv — COMPLETE
- Duplicate req number detection in pipeline and ranking scripts — COMPLETE
- Experience library cleanup — COMPLETE (05 Apr 2026)
  G2 OPS: 158 to 118 bullets | Summaries: 48 to 26
  Overmatch theme: cleaned to 2 canonical bullets + 2 supporting themes
- Phase 3 architecture refactor — COMPLETE
  Shared library_parser.py module, single-employer re-parse script
- Claude Code setup in VS Code — COMPLETE
  CLAUDE.md configured with access restrictions
- pii_filter.py — COMPLETE (on GitHub)
- check_resume.py — COMPLETE (two-layer: string matching + API assessment)
- check_cover_letter.py — COMPLETE
- V&V framework — COMPLETE (07 Apr 2026)
- Two-tier pytest suite, CI green badge, fixture identity: Jane Q. Applicant / Acme Defense Systems
  