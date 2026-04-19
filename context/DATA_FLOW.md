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
| `phase3_parse_library.py` | `data/experience_library/experience_library.md` | `data/experience_library/employers/[employer_slug].json`, `data/experience_library/summaries.json` |
| `phase3_parse_employer.py` | `data/experience_library/experience_library.md` | `data/experience_library/employers/[employer_slug].json` |
| `phase3_compile_library.py` | `data/experience_library/employers/*.json`, `data/experience_library/summaries.json` | `data/experience_library/experience_library.json` |
| `phase3_build_candidate_profile.py` | `data/experience_library/experience_library.json`, `data/experience_library/employers/*.json`, `data/experience_library/summaries.json` | `data/experience_library/candidate_profile.md` |

## Phase 4 — Resume and cover letter

| Script | Reads | Writes |
|--------|-------|--------|
| `phase4_resume_generator.py --stage 1` | `data/job_packages/[role]/job_description.txt`, `data/experience_library/experience_library.json`, `data/experience_library/candidate_profile.md` | `data/job_packages/[role]/stage1_draft.txt` |
| `phase4_resume_generator.py --stage 3` | `data/job_packages/[role]/stage2_approved.txt`, `data/job_packages/[role]/job_description.txt` | `data/job_packages/[role]/stage3_review.txt` |
| `phase4_resume_generator.py --stage 4` | `data/job_packages/[role]/stage4_final.txt` (optional, fallback: `stage2_approved.txt`), `templates_local/resume_template.docx` | `resumes/tailored/[role]/[role]_Resume.docx` |
| `check_resume.py` | `data/job_packages/[role]/stage2_approved.txt`, `context/CANDIDATE_BACKGROUND.md` | `data/job_packages/[role]/check_results.txt` |
| `phase4_cover_letter.py --stage 1` | `data/job_packages/[role]/job_description.txt`, `context/CANDIDATE_BACKGROUND.md` | `data/job_packages/[role]/cl_stage1_draft.txt` |
| `phase4_cover_letter.py --stage 4` | `data/job_packages/[role]/cl_stage4_final.txt`, `templates/resume_template.docx` | `resumes/tailored/[role]/[role]_CoverLetter.docx` |
| `check_cover_letter.py` | `data/job_packages/[role]/cl_stage2_approved.txt`, `context/CANDIDATE_BACKGROUND.md` | `data/job_packages/[role]/cl_stage3_review.txt` |

## Phase 5 — Interview

| Script | Reads | Writes |
|--------|-------|--------|
| `phase5_interview_prep.py` | `data/job_packages/[role]/job_description.txt`, `data/interview_library.json`, `data/experience_library/candidate_profile.md` | `data/job_packages/[role]/interview_prep_[stage].txt`, `data/job_packages/[role]/interview_prep_[stage].docx` |
| `phase5_workshop_capture.py` | `data/job_packages/[role]/interview_prep_[stage].docx` | `data/interview_library.json` (appends/updates) |
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
