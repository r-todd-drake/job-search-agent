# Context Indexes: Data Flow Map and Stage File Reference

## User Story and Acceptance Criteria

### User Story

"As a developer working on the job search agent pipeline, I want a data flow map
and a stage file reference in the context/ folder so that I can understand what
each script reads and writes -- and how job package files are named and owned --
without opening individual scripts."

### Acceptance Criteria (AC)

#### DATA_FLOW.md (`context/DATA_FLOW.md`)

A single-table reference showing inputs and outputs for every production script.

- One row per script, ordered by pipeline sequence (Phase 2 → Phase 5)
- Columns: Script | Reads | Writes
- File paths use the canonical form (e.g. `data/job_packages/[role]/stage1_draft.txt`,
  not abbreviated or paraphrased)
- Shared module imports (pii_filter, library_parser, etc.) are NOT listed as "reads" --
  only data files the script opens at runtime
- Optional inputs are marked "(optional)" in the Reads column
- Scripts that write to the tracker (.xlsx) note that explicitly
- A "Shared modules" section below the table lists each utility module and the data
  files it reads or writes on behalf of callers
- Accurate as of the date written; includes a "Last verified" date at the top

#### STAGE_FILES.md (`context/STAGE_FILES.md`)

A reference for the full file lifecycle inside `data/job_packages/[role]/`.

- Lists every file that can appear in a role's job package folder
- For each file: filename pattern, who writes it (script or user), and what reads it next
- Covers both the resume pipeline (stage1_draft.txt → stage4_final.txt → .docx)
  and the cover letter pipeline (cl_stage1_draft.txt → cl_stage4_final.txt → .docx)
- Covers interview prep outputs (interview_prep_[stage].txt / .docx)
- Covers debrief-derived outputs (thankyou_[stage]_[interviewer].txt / .docx)
- Marks which files are user-edited (manual stage) vs. script-generated (automated)
- Marks which files are source-of-truth (edits made here) vs. derived (never edit directly)
- Notes the fallback behavior where it exists (e.g. stage4_final.txt falls back to
  stage2_approved.txt in the resume generator)
- A separate short section covers `data/debriefs/[role]/` filename patterns and
  the panel_label variant

#### CLAUDE.md pointer

- A line is added to the Project Structure section of CLAUDE.md pointing to both files,
  matching the style of the existing SCRIPT_INDEX.md pointer

### Out of Scope

- Automating the generation or validation of these files from script source
- Tracking data flow for one-time utility scripts (normalize_library.py, diagnose_*.py)
- Documenting the internal in-memory data structures passed between functions
- Any changes to production scripts
- Any changes to SCHEMA_REFERENCE.md (separate document, already written)

---

## Review Annotations

*This section is populated during the Chat spec review step. Do not fill in manually.*

Open items use `> ⚠ REVIEW:` and must be resolved before build starts.
Resolved items use `> ✅ RESOLVED:` and document what was decided.
