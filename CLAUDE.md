# CLAUDE.md — Job Search Agent Project

## Project Overview
AI-powered job search automation system. Python scripts for job ranking, resume generation, and interview prep.

## CRITICAL SAFETY RULES — READ BEFORE EVERY ACTION

### Never read, access, or touch these files/folders:
- .env — contains API keys and PII

### Read-only (understand structure, never modify):
- data/ — contains personal career data, resumes, job packages
- resumes/ — contains tailored resume documents
- outputs/ — contains generated reports
- context/candidate/candidate_config.example.yaml — blank template (tracked, read-only)

**Important:** .gitignore does NOT prevent Claude's tools (Glob, Read) from accessing these paths. Do not browse these directories unprompted or include them in exploratory searches.

### Gitignored (personal data, never commit):
- context/candidate/candidate_config.yaml — personal career data (gitignored)
- context/candidate/CANDIDATE_BACKGROUND.md — moved from context/ root (gitignored)
- context/candidate/PIPELINE_STATUS.md — moved from context/ root (gitignored)

### Safe to read and edit:
- scripts/*.py — all Python automation scripts
- scripts/utils/*.py — utility scripts
- scripts/utils/candidate_config.py — candidate data loader
- context/*.md — candidate background, decisions log, project context
- README.md
- requirements.txt
- CLAUDE.md

### Git safety:
- If the user asks how to push changes to GitHub or asks for git commands, do NOT suggest `git add .` — always tell them to stage specific files by name.
- Claude Code may use `git add .` internally, but only after running `git status` and verifying that no forbidden files (`.env`, `data/`, `resumes/`, `outputs/`) are staged, and that `.gitignore` is correctly named with a dot prefix. Background: a prior incident where `.gitignore` was misnamed caused personal data and API keys to be pushed to GitHub via `git add . && git commit && git push`.
- Never commit `.env`, `data/`, `resumes/`, or `outputs/`
- Always run `git status` before committing
- Verify `.gitignore` has the dot prefix before any git operations

## Codeburn Optimizations
- Before editing any file, read it first. Before modifying a function, grep for all callers. Research before you edit.
- Before touching a Phase 4/5 script, read the relevant schema and data flow docs

## Code Style
- Python scripts — en dashes in strings, not em dashes
- No hardcoded PII — all personal data via .env variables
- All API calls must use strip_pii() from scripts/utils/pii_filter.py
- Follow existing script patterns for consistency

## Project Structure
See README.md for full structure.
See context/SCRIPT_INDEX.md for a quick-reference table of every script — purpose, key flags, and shared module relationships. Read this before navigating multi-script tasks.
See context/SCHEMA_REFERENCE.md for the JSON schemas of the three key data files: debrief JSON, interview_library.json, and experience_library.json. Read this before modifying any Phase 4 or Phase 5 script that reads or writes these files.
See context/DATA_FLOW.md for a script-by-script table of what each production script reads and writes at runtime. Read this before tracing data through the pipeline.
See context/STAGE_FILES.md for the full file lifecycle inside data/job_packages/[role]/ and data/debriefs/[role]/. Read this before working with staged resume, cover letter, interview prep, or debrief files.

### Key scripts:
- scripts/pipeline_report.py
- scripts/phase2_job_ranking.py
- scripts/phase2_semantic_analyzer.py
- scripts/phase3_*.py
- scripts/phase4_resume_generator.py
- scripts/phase4_cover_letter.py
- scripts/check_resume.py
- scripts/check_cover_letter.py
- scripts/phase5_interview_prep.py
- scripts/phase5_debrief.py
- scripts/phase5_thankyou.py
- scripts/phase5_workshop_capture.py

## When asked to modify scripts:
1. Read the existing script first
2. Make targeted changes only
3. Run syntax check after editing
4. Never modify data files directly

## When asked to develop a capability:
1. Read the prompt and any provided files before responding.
2. Use Plan mode to discuss the proposed solution, including architecture and how to verify and test the solution, before writing any code.
Do not begin development until there is high confidence the approach meets the stated requirement. Ask clarifying questions to close any gaps.
3. Run a syntax check after development is complete.

## Script Templates
- `templates/` is the canonical home for all script input templates (tracked — plain-text and YAML only, no PII, no binaries).
- `templates_local/` holds binary and personal templates (gitignored — e.g. `resume_template.docx`).

## Naming Conventions
- Use underscores for all file and folder names. Never use hyphens or spaces.