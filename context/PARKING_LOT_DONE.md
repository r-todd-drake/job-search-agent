# Parking Lot Done
# Load for: planning next development session, understancing completed items
Last updated: 21 Apr 2026

## Completed (recent)
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
  Two-tier pytest suite, CI green badge, fixture identity: Jane Q. Applicant / Acme Defense Systems