# Script Index

Quick reference — what each script does, key flags, and what it reads/writes.
For full structure see README.md.

---

## Pipeline scripts

| Script | Purpose | Key flags |
|---|---|---|
| `pipeline_report.py` | Pipeline metrics summary from tracker .xlsx | — |
| `phase2_job_ranking.py` | Keyword score all roles; report NEW/PURSUE/CONSIDER | — |
| `phase2_semantic_analyzer.py` | Claude API semantic fit analysis on PURSUE/CONSIDER | — |

## Phase 3 — Experience library

| Script | Purpose | Key flags |
|---|---|---|
| `phase3_parse_library.py` | Full parse of experience_library.md → per-employer JSON | — |
| `phase3_parse_employer.py` | Re-parse a single employer (faster targeted edit) | `"Employer Name"` `--keywords` |
| `phase3_compile_library.py` | Merge per-employer JSON + summaries → experience_library.json | — |
| `phase3_build_candidate_profile.py` | Extract confirmed facts/skills/gaps → candidate_profile.md | — |

## Phase 4 — Resume and cover letter

| Script | Purpose | Key flags |
|---|---|---|
| `phase4_resume_generator.py` | Staged resume tailoring (Stages 1, 3, 4) | `--stage` `--role` |
| `phase4_backport.py` | Identify net-new/variant bullets from stage files; stage for library backport | `--role` `--dry-run` `--net-new-threshold` `--variant-floor` |
| `check_resume.py` | Two-layer quality check on stage2_approved.txt | `--role` |
| `phase4_cover_letter.py` | Staged cover letter generation (Stages 1, 4) | `--stage` `--role` |
| `check_cover_letter.py` | Two-layer quality check on cl_stage2_approved.txt | `--role` |

## Phase 5 — Interview

| Script | Purpose | Key flags |
|---|---|---|
| `phase5_interview_prep.py` | Stage-aware prep package (.txt + .docx) | `--role` `--interview_stage` `--dry_run` |
| `phase5_workshop_capture.py` | Parse workshopped prep .docx → interview_library.json | `--role` `--stage` |
| `phase5_debrief.py` | Post-interview debrief capture → JSON | `--role` `--stage` `--interactive` / `--init` / `--convert` |
| `phase5_thankyou.py` | Thank-you letters from debrief JSON (one per interviewer) | `--role` `--stage` `--panel_label` |

---

## Shared modules

| Module | Provides | Used by |
|---|---|---|
| `utils/library_parser.py` | `parse_library()` — parses experience_library.md with no side effects | phase3_parse_library, phase3_parse_employer |
| `utils/pii_filter.py` | `strip_pii()` — replaces PII values loaded from .env before any API call | all scripts making API calls |
| `interview_library_parser.py` | `init_library()`, load/save for interview_library.json (stories, gap_responses, questions) | phase5_workshop_capture |
| `phase5_debrief_utils.py` | `load_debriefs(role)` — loads all filed debrief JSON for a role | phase5_thankyou |

---

## One-time / utility scripts

| Script | Purpose |
|---|---|
| `utils/normalize_library.py` | Merge tranche-suffixed employer sections in experience_library.md |
| `utils/diagnose_*.py` | Development diagnostics — not part of the production workflow |
