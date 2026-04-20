# Context Indexes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create `context/DATA_FLOW.md` and `context/STAGE_FILES.md` — two reference documents that map every production script's file I/O and the full lifecycle of files inside a job package folder.

**Architecture:** Pure documentation task — no code changes. Both files live in `context/` alongside `SCRIPT_INDEX.md` and `SCHEMA_REFERENCE.md`. Content is pre-researched below; each task writes the file directly then spot-checks it against the source scripts.

**Tech Stack:** Markdown only. No Python changes. No data files touched.

---

## Files

- Create: `context/DATA_FLOW.md`
- Create: `context/STAGE_FILES.md`
- Modify: `CLAUDE.md` (Project Structure section, lines 38–41)

---

## Task 1: Write `context/DATA_FLOW.md`

**Files:**
- Create: `context/DATA_FLOW.md`

- [ ] **Step 1: Write the file**

Write `context/DATA_FLOW.md` with exactly this content:

```markdown
# Data Flow Map

Last verified: 2026-04-19

Script-by-script reference for what each production script reads and writes at runtime.
Shared module imports are NOT listed as reads — see the Shared Modules section below.

---

## Pipeline scripts

| Script | Reads | Writes |
|--------|-------|--------|
| `pipeline_report.py` | `data/tracker/job_pipeline.xlsx` | `outputs/pipeline_report_YYYYMMDD_HHMM.txt` |
| `phase2_job_ranking.py` | `data/jobs.csv`, `data/job_packages/[role]/job_description.txt` | `outputs/ranked_jobs.csv`, `outputs/ranking_report_YYYYMMDD_HHMM.txt` |
| `phase2_semantic_analyzer.py` | `data/jobs.csv`, `data/job_packages/[role]/job_description.txt`, `data/experience_library/candidate_profile.md`, `outputs/ranked_jobs.csv` (optional) | `outputs/semantic_analysis_YYYYMMDD_HHMM.txt` |

## Phase 3 — Experience library

| Script | Reads | Writes |
|--------|-------|--------|
| `phase3_parse_library.py` | `data/experience_library/experience_library.md` | `data/experience_library/employers/[name].json`, `data/experience_library/summaries.json` |
| `phase3_parse_employer.py` | `data/experience_library/experience_library.md` | `data/experience_library/employers/[employer_slug].json` |
| `phase3_compile_library.py` | `data/experience_library/employers/*.json`, `data/experience_library/summaries.json` | `data/experience_library/experience_library.json` |
| `phase3_build_candidate_profile.py` | `data/experience_library/experience_library.json`, `data/experience_library/employers/*.json`, `data/experience_library/summaries.json` | `data/experience_library/candidate_profile.md` |

## Phase 4 — Resume and cover letter

| Script | Reads | Writes |
|--------|-------|--------|
| `phase4_resume_generator.py --stage 1` | `data/job_packages/[role]/job_description.txt`, `data/experience_library/experience_library.json`, `data/experience_library/candidate_profile.md` | `data/job_packages/[role]/stage1_draft.txt` |
| `phase4_resume_generator.py --stage 3` | `data/job_packages/[role]/stage2_approved.txt`, `data/job_packages/[role]/job_description.txt` | `data/job_packages/[role]/stage3_review.txt` |
| `phase4_resume_generator.py --stage 4` | `data/job_packages/[role]/stage4_final.txt` (fallback: `stage2_approved.txt`), `templates_local/resume_template.docx` | `resumes/tailored/[role]/[role]_Resume.docx` |
| `check_resume.py` | `data/job_packages/[role]/stage2_approved.txt`, `context/CANDIDATE_BACKGROUND.md` | `data/job_packages/[role]/check_results.txt` |
| `phase4_cover_letter.py --stage 1` | `data/job_packages/[role]/job_description.txt`, `context/CANDIDATE_BACKGROUND.md` | `data/job_packages/[role]/cl_stage1_draft.txt` |
| `phase4_cover_letter.py --stage 4` | `data/job_packages/[role]/cl_stage4_final.txt`, `templates/resume_template.docx` | `resumes/tailored/[role]/[role]_CoverLetter.docx` |
| `check_cover_letter.py` | `data/job_packages/[role]/cl_stage2_approved.txt`, `context/CANDIDATE_BACKGROUND.md` | `data/job_packages/[role]/cl_stage3_review.txt` |

## Phase 5 — Interview

| Script | Reads | Writes |
|--------|-------|--------|
| `phase5_interview_prep.py` | `data/job_packages/[role]/job_description.txt`, `data/interview_library.json`, `data/experience_library/candidate_profile.md` | `data/job_packages/[role]/interview_prep_[stage].txt`, `data/job_packages/[role]/interview_prep_[stage].docx` |
| `phase5_workshop_capture.py` | `data/job_packages/[role]/interview_prep_[stage].docx`, `data/interview_library_tags.json` | `data/interview_library.json` (appends/updates) |
| `phase5_debrief.py --init` | `templates/interview_debrief_template.yaml` | `data/debriefs/[role]/debrief_[stage]_draft.yaml` |
| `phase5_debrief.py --convert` | `data/debriefs/[role]/debrief_[stage]_draft.yaml` | `data/debriefs/[role]/debrief_[stage]_[interview-date]_filed-[produced-date].json` |
| `phase5_debrief.py --interactive` | (none) | `data/debriefs/[role]/debrief_[stage]_[interview-date]_filed-[produced-date].json` |
| `phase5_thankyou.py` | `data/debriefs/[role]/debrief_*.json`, `data/experience_library/candidate_profile.md`, `data/job_packages/[role]/job_description.txt`, `data/job_packages/[role]/stage4_final.txt` (optional, fallback: `stage2_approved.txt`) | `data/job_packages/[role]/thankyou_[stage]_[lastname]_[date].txt`, `data/job_packages/[role]/thankyou_[stage]_[lastname]_[date].docx` |

---

## Shared modules

| Module | Reads / writes on behalf of callers |
|--------|--------------------------------------|
| `utils/library_parser.py` | Reads `data/experience_library/experience_library.md` |
| `utils/pii_filter.py` | Reads `.env` (PII values to strip before API calls — not a data file) |
| `interview_library_parser.py` | Reads and writes `data/interview_library.json`; reads `data/interview_library_tags.json` |
| `phase5_debrief_utils.py` | Reads `data/debriefs/[role]/*.json` (all filed debriefs for a role) |
```

- [ ] **Step 2: Spot-check three rows against source scripts**

Open and verify these three constants match what was written:

1. `scripts/pipeline_report.py` — confirm `TRACKER_PATH = "data/tracker/job_pipeline.xlsx"` and `REPORT_PATH = "outputs"` with filename `pipeline_report_{timestamp}.txt`
2. `scripts/check_resume.py` — confirm `RESULTS_PATH = os.path.join(PACKAGE_DIR, "check_results.txt")`
3. `scripts/phase5_thankyou.py` — confirm output stem `thankyou_{stage}_{lastname}_{run_date}` and that it reads `job_description.txt` and the debrief JSON glob

If any path differs from what is written in DATA_FLOW.md, correct the file before continuing.

- [ ] **Step 3: Commit**

```bash
git add context/DATA_FLOW.md
git commit -m "docs: add DATA_FLOW.md — script-by-script input/output reference"
```

---

## Task 2: Write `context/STAGE_FILES.md`

**Files:**
- Create: `context/STAGE_FILES.md`

- [ ] **Step 1: Write the file**

Write `context/STAGE_FILES.md` with exactly this content:

```markdown
# Stage Files Reference

Last verified: 2026-04-19

Full file lifecycle inside `data/job_packages/[role]/` and `data/debriefs/[role]/`.

Legend:
- **Source-of-truth** — this is where edits are made; other files are derived from it
- **Derived** — generated by a script; never edit directly
- **User-edited** — created or edited manually, not by a script

---

## Resume pipeline — `data/job_packages/[role]/`

| File | Written by | Read next by | Source-of-truth or Derived |
|------|-----------|--------------|---------------------------|
| `job_description.txt` | User (manual — paste JD text here to start a package) | `phase2_job_ranking.py`, `phase2_semantic_analyzer.py`, `phase4_resume_generator.py --stage 1`, `phase4_cover_letter.py --stage 1`, `phase5_interview_prep.py`, `phase5_thankyou.py` | Source-of-truth — never edit after initial creation |
| `stage1_draft.txt` | `phase4_resume_generator.py --stage 1` | User reviews and saves as `stage2_approved.txt` | Derived — do not edit directly |
| `stage2_approved.txt` | User (manual edit from `stage1_draft.txt`) | `phase4_resume_generator.py --stage 3`, `check_resume.py`, `phase4_resume_generator.py --stage 4` (fallback), `phase5_thankyou.py` (fallback) | Source-of-truth — resume edits go here |
| `stage3_review.txt` | `phase4_resume_generator.py --stage 3` | User reviews; applies changes back to `stage2_approved.txt` or creates `stage4_final.txt` | Derived — do not edit directly |
| `stage4_final.txt` | User (manual — final polished version before docx generation) | `phase4_resume_generator.py --stage 4`, `phase5_thankyou.py` | Source-of-truth — edits made here for docx output |
| `check_results.txt` | `check_resume.py` (invoked by `phase4_resume_generator.py --stage 4`) | User reviews | Derived — do not edit directly |

**Fallback behavior:** `phase4_resume_generator.py --stage 4` reads `stage4_final.txt` if it exists; otherwise falls back to `stage2_approved.txt`. `phase5_thankyou.py` follows the same fallback.

---

## Cover letter pipeline — `data/job_packages/[role]/`

| File | Written by | Read next by | Source-of-truth or Derived |
|------|-----------|--------------|---------------------------|
| `cl_stage1_draft.txt` | `phase4_cover_letter.py --stage 1` | User reviews and saves as `cl_stage2_approved.txt` | Derived — do not edit directly |
| `cl_stage2_approved.txt` | User (manual edit from `cl_stage1_draft.txt`) | `check_cover_letter.py` | Source-of-truth — cover letter edits go here |
| `cl_stage3_review.txt` | `check_cover_letter.py` | User reviews; applies changes to `cl_stage2_approved.txt` or creates `cl_stage4_final.txt` | Derived — do not edit directly |
| `cl_stage4_final.txt` | User (manual — final polished version before docx generation) | `phase4_cover_letter.py --stage 4` | Source-of-truth — edits made here for docx output |

---

## Interview prep outputs — `data/job_packages/[role]/`

| File | Written by | Read next by | Source-of-truth or Derived |
|------|-----------|--------------|---------------------------|
| `interview_prep_[stage].txt` | `phase5_interview_prep.py` | User reviews | Derived — do not edit directly |
| `interview_prep_[stage].docx` | `phase5_interview_prep.py` | User workshops; `phase5_workshop_capture.py` reads for library capture | Derived initially — user edits the .docx during workshopping |

`[stage]` is one of: `recruiter_screen`, `hiring_manager`, `team_panel`.

---

## Thank-you letter outputs — `data/job_packages/[role]/`

| File | Written by | Read next by | Source-of-truth or Derived |
|------|-----------|--------------|---------------------------|
| `thankyou_[stage]_[lastname]_[date].txt` | `phase5_thankyou.py` | User reviews | Derived — do not edit directly |
| `thankyou_[stage]_[lastname]_[date].docx` | `phase5_thankyou.py` | User sends | Derived — do not edit directly |

With panel label: `thankyou_[stage]_[panel_label]_[lastname]_[date].txt/.docx`

`[date]` format: `YYYYMMDD`.

---

## Debrief files — `data/debriefs/[role]/`

| File | Written by | Read next by | Source-of-truth or Derived |
|------|-----------|--------------|---------------------------|
| `debrief_[stage]_draft.yaml` | `phase5_debrief.py --init` | User fills in; `phase5_debrief.py --convert` reads it | Source-of-truth for convert mode — edits made here |
| `debrief_[stage]_[interview-date]_filed-[produced-date].json` | `phase5_debrief.py --convert` or `--interactive` | `phase5_thankyou.py`, `phase5_debrief_utils.py` | Source-of-truth — never edit directly after filing |

With panel label: `debrief_[stage]_[panel_label]_[interview-date]_filed-[produced-date].json`

Date formats: `YYYY-MM-DD` for both `[interview-date]` and `[produced-date]`.

Valid `[stage]` values: `recruiter_screen`, `hiring_manager`, `panel`, `final`.
```

- [ ] **Step 2: Spot-check three entries against source scripts**

Verify these three entries match the source:

1. `scripts/check_cover_letter.py` — confirm `RESULTS_PATH = os.path.join(PACKAGE_DIR, "cl_stage3_review.txt")` (not a separate file — this IS cl_stage3_review.txt)
2. `scripts/phase5_debrief.py` — confirm `draft_path = os.path.join(role_dir, f"debrief_{stage}_draft.yaml")` and the JSON output filename pattern with `filed-` prefix
3. `scripts/phase5_thankyou.py` — confirm stem patterns `thankyou_{stage}_{panel_label}_{lastname}_{run_date}` and `thankyou_{stage}_{lastname}_{run_date}`

If any pattern differs from what is written in STAGE_FILES.md, correct the file before continuing.

- [ ] **Step 3: Commit**

```bash
git add context/STAGE_FILES.md
git commit -m "docs: add STAGE_FILES.md — job package file lifecycle reference"
```

---

## Task 3: Update `CLAUDE.md`

**Files:**
- Modify: `CLAUDE.md` (Project Structure section)

- [ ] **Step 1: Read current CLAUDE.md Project Structure section**

Read `CLAUDE.md` lines 38–42 to confirm the current text:

```
## Project Structure
See README.md for full structure.
See context/SCRIPT_INDEX.md for a quick-reference table of every script — purpose, key flags, and shared module relationships. Read this before navigating multi-script tasks.
See context/SCHEMA_REFERENCE.md for the JSON schemas of the three key data files: debrief JSON, interview_library.json, and experience_library.json. Read this before modifying any Phase 4 or Phase 5 script that reads or writes these files.
```

- [ ] **Step 2: Add two pointer lines after the SCHEMA_REFERENCE.md line**

Replace the Project Structure block so it reads:

```
## Project Structure
See README.md for full structure.
See context/SCRIPT_INDEX.md for a quick-reference table of every script — purpose, key flags, and shared module relationships. Read this before navigating multi-script tasks.
See context/SCHEMA_REFERENCE.md for the JSON schemas of the three key data files: debrief JSON, interview_library.json, and experience_library.json. Read this before modifying any Phase 4 or Phase 5 script that reads or writes these files.
See context/DATA_FLOW.md for a script-by-script table of what each production script reads and writes at runtime. Read this before tracing data through the pipeline.
See context/STAGE_FILES.md for the full file lifecycle inside data/job_packages/[role]/ and data/debriefs/[role]/. Read this before working with staged resume, cover letter, interview prep, or debrief files.
```

- [ ] **Step 3: Verify the edit looks correct**

Read `CLAUDE.md` lines 38–48 after the edit and confirm both new pointer lines appear with correct paths and no typos.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add DATA_FLOW.md and STAGE_FILES.md pointers to CLAUDE.md"
```

---

## Spec Coverage Check

| Spec requirement | Task that satisfies it |
|-----------------|------------------------|
| `context/DATA_FLOW.md` — one row per script, Phase 2 → Phase 5 | Task 1 |
| Columns: Script \| Reads \| Writes | Task 1 |
| Canonical file paths | Task 1 (all paths match source constants) |
| Shared module imports NOT in Reads column | Task 1 (shared modules section is separate) |
| Optional inputs marked "(optional)" | Task 1 (`outputs/ranked_jobs.csv (optional)`, `stage4_final.txt (optional...)`) |
| No tracker (.xlsx) writes from production scripts | Task 1 (pipeline_report reads .xlsx, does not write it) |
| Shared modules section lists utility modules and their data files | Task 1 |
| "Last verified" date | Task 1 |
| `context/STAGE_FILES.md` — every file in `data/job_packages/[role]/` | Task 2 |
| Both resume and cover letter pipelines | Task 2 |
| Interview prep outputs | Task 2 |
| Debrief-derived outputs (thankyou) | Task 2 |
| User-edited vs. script-generated distinction | Task 2 (Written by column) |
| Source-of-truth vs. derived distinction | Task 2 (last column) |
| Fallback behavior noted | Task 2 (explicit note under resume pipeline table) |
| `data/debriefs/[role]/` section with panel_label variant | Task 2 |
| CLAUDE.md pointer added | Task 3 |
