# AI Job Search Agent

![Tests](https://github.com/r-todd-drake/job-search-agent/actions/workflows/test.yml/badge.svg)

A multi-phase AI-powered job search automation system built as both a practical tool for managing an active job search and a portfolio project demonstrating real-world Python development, API integration, and AI agent design.

---

## Project Overview

Most job seekers optimize their resume wording.
This system optimizes the entire process.

Instead of manually searching, scoring, and tailoring applications one at a time, this agent pipeline handles discovery, ranking, resume generation, and interview preparation — producing tailored application packages and interview prep materials for every role in the pipeline.

---

## Project Phases

{{include: current_phase_status}}

---

## Development vs Implementation

{{include: project_split}}

---

## Daily Workflow

```
01. Add new roles to jobs.csv (blank status, req number if available)
02. Run phase2_job_ranking.py
   → Scores all roles, reports only NEW/PURSUE/CONSIDER
   → Flags duplicate requisition numbers
   → Assign PURSUE / CONSIDER / SKIP to each new role
03. Run phase2_semantic_analyzer.py
   → Claude API analysis on PURSUE and CONSIDER roles only
04. Run phase4_resume_generator.py for top PURSUE roles
   → Four-stage async workflow with human review at each stage
   → Stage files are source of truth — never edit .docx directly
   → Run check_resume.py --role [role] after Stage 2 to catch violations
05. Run phase4_cover_letter.py --stage 1 --role [role]
   → Generates cover letter draft aligned with resume content
   → Run check_cover_letter.py --role [role] after editing Stage 2
   → Stage through to docx via --stage 4
06. Submit, update status to APPLIED, move to job_pipeline.xlsx
07. Run phase5_interview_prep.py when interview is scheduled
   → Specify --interview_stage (recruiter, hiring_manager, team_panel)
   → Generates stage-specific .txt and .docx prep package
   → Workshop stories in Claude web chat before interview
   → Run phase5_workshop_capture.py after workshopping to persist stories to interview_library.json
08. Run phase5_debrief.py after each interview
   → --interactive for guided capture with optional AI follow-up questions
   → --init / --convert for YAML-based offline workflow
   → Saves structured JSON to data/debriefs/[role]/
09. Run phase4_backport.py to improve experience library
   → Identifies net-new and variant resume bullets from submitted resumes to update the experience library
10. Run phase5_thankyou.py to generate thank-you letters
   → One .txt and .docx per interviewer, drawn from the filed debrief
   → Use --panel_label for panel interviews with multiple interviewers

```

---

## Job Status Values

| Status | Meaning |
|--------|---------|
| *(blank)* | New — not yet reviewed |
| PURSUE | Apply next |
| CONSIDER | On deck |
| SKIP | Decided against |
| APPLIED | Submitted — move to tracker |

---

## Phase 4 — Resume Generation

```
Stage 1 (automated)  →  stage1_draft.txt
                         Keyword + semantic bullet selection
                         Priority bullets always included (priority: true in library)
                         Core competencies generated from JD
                         Summary selected from library

Stage 2 (manual)     →  stage2_approved.txt
                         Review draft, swap bullets, adjust wording

Stage 3 (automated)  →  stage3_review.txt
                         Semantic coherence check
                         Wording suggestions grounded in confirmed background
                         ATS keyword gap analysis

Stage 4 (automated)  →  [Company]_[Role]_Resume.docx
                         Template-based .docx generation
                         Auto quality check via check_resume.py
```

## Phase 4 — Cover Letter Generation

```
Stage 1 (automated)  →  cl_stage1_draft.txt
                         Traditional cover letter (3–4 paragraphs)
                         Application paragraph (150–250 words, plain-text field)
                         Hiring manager name extracted from JD if present
                         Gap filtering from resume stage3_review.txt if available

Stage 2 (manual)     →  cl_stage2_approved.txt
                         Review draft, verify all claims against confirmed experience

Stage 3 (automated)  →  cl_stage3_review.txt
                         Two-layer quality check via check_cover_letter.py
                         Layer 1: string matching (em dash, lapsed cert, gap terms)
                         Layer 2: API assessment for implied gap fulfillment,
                                  banned language, generic opener phrases

Stage 4 (automated)  →  [Role]_CoverLetter.docx
                         Template-based .docx — page 1 letter, page 2 application paragraph
```

---

## Phase 5 — Interview Prep

Single command generates a stage-appropriate prep package:

```bash
python scripts/phase5_interview_prep.py --role [role_folder] --interview_stage [recruiter|hiring_manager|team_panel]
```

Valid stages: `recruiter`, `hiring_manager`, `team_panel`

If `--interview_stage` is omitted the script prompts interactively. Use `--dry_run` to
validate stage config without making API calls.

Outputs to `data/job_packages/[role]/`:
- `interview_prep_[stage].txt` — for VS Code review and story workshopping
- `interview_prep_[stage].docx` — formatted Word document for reading and printing

Running multiple stages for the same role produces separate files without collision.

**Package sections by stage:**

| Section | Recruiter | Hiring Manager | Team Panel |
|---------|-----------|----------------|------------|
| 1 — Company & Role Brief | Culture, process, recent news | Full brief + salary guidance | Condensed + technical environment |
| 1.5 — Introduce Yourself | Concise fit signal (2–3 sentences) | Program-context aware (3–4 sentences) | Technically grounded, peer register |
| 2 — Story Bank | 1–2 stories, headline only | 3–4 stories, full STAR + probe branch | 4–6 stories, full STAR + technical specificity |
| 3 — Gap Preparation | Omitted (short tenure block only) | Full four-element format | Full five-element format + Peer Frame |
| 4 — Questions to Ask | Process, culture, logistics | Program pain points, success criteria | Day-to-day tools, integration problems |

Stage label and description are written to the output file header so the register is
immediately clear when opening the package.

---

## Post-Interview Debrief

Captures structured debrief data immediately after each interview — advancement read,
stories used, gaps surfaced, salary exchange, and continuity notes.

```bash
# Guided questionnaire (recommended — AI follow-up questions per section)
python scripts/phase5_debrief.py --role [role] --stage [stage] --interactive

# YAML-based workflow (fill the draft, then convert)
python scripts/phase5_debrief.py --role [role] --stage [stage] --init
python scripts/phase5_debrief.py --role [role] --stage [stage] --convert
```

Valid stages: `recruiter_screen`, `hiring_manager`, `panel`, `final`

Output: `data/debriefs/[role]/debrief_[stage]_[interview-date]_filed-[produced-date].json`

**Captured fields:**

| Section | Fields |
|---------|--------|
| Metadata | company, interviewer name/title, date, format, stage |
| Advancement read | assessment (for_sure / maybe / doubt_it / definitely_not), notes |
| Stories used | tags, framing, landed (yes / partially / no), library_id (for future linking) |
| Gaps surfaced | gap label, response given, response felt (strong / adequate / weak) |
| Salary exchange | range given, candidate anchor/floor, notes |
| Continuity | what I said — claims and framings to stay consistent on |
| Open notes | anything else worth capturing |

`--interactive` mode calls the Claude API to generate one optional follow-up question
per section. All responses are PII-stripped before the API call.

---

## Post-Interview Thank-You Letters

Generates a personalized thank-you letter for each interviewer from a filed debrief JSON.

```bash
# Standard (single interviewer or named panel label)
python scripts/phase5_thankyou.py --role [role] --stage [stage]

# Panel with a specific label
python scripts/phase5_thankyou.py --role [role] --stage panel --panel_label [label]
```

Valid stages: `recruiter_screen`, `hiring_manager`, `panel`, `final`

Outputs to `data/job_packages/[role]/`:
- `thankyou_[stage]_[interviewer].txt`
- `thankyou_[stage]_[interviewer].docx`

One API call per letter. Reads interviewer name and exchange details from the debrief JSON.

---

## Interview Workshop Capture

Parses a workshopped interview prep `.docx` and writes durable story, gap, and question
content into a persistent interview library for reuse across roles.

```bash
python scripts/phase5_workshop_capture.py --role [role] --stage [stage]
```

Reads: `data/job_packages/[role]/interview_prep_[stage].docx`
Writes: `data/interview_library.json` (appends or updates existing entries)

Run this after story workshopping in Claude web chat to capture refined content before
it is lost.

---

## Tech Stack

- **Python 3.x** — core scripting and automation
- **Anthropic Claude API** — LLM backbone including web search tool
- **openpyxl** — application tracker (.xlsx)
- **python-docx** — resume and interview prep document generation
- **pytest / pytest-mock** — two-tier test suite (mock + live API)
- **GitHub Actions** — CI pipeline running mock suite on every push
- **VS Code** — development environment (View > Word Wrap for .txt files)
- **Git / GitHub** — version control and portfolio publishing
- **Claude Code** — AI-assisted development via CLI and VS Code extension

---

## Security & Privacy

PII is stripped from all API calls before any data leaves the local machine.
`pii_filter.py` loads PII values from `.env` at runtime — no personal data
is hardcoded in the published code.

All personal data (experience library, resumes, job packages, tracker, and
candidate background files) is excluded from version control via `.gitignore`.

Anthropic API: inputs are not used for model training under commercial terms.

---

## Claude Code (Optional)

This project includes a `CLAUDE.md` configuration file for use with
[Claude Code](https://claude.ai/code) in VS Code. It defines project
conventions and file access boundaries for AI-assisted script development.

Install the Claude Code extension from the VS Code marketplace to use it.
Claude Code is useful for making targeted script changes, debugging, and
refactoring — working directly against local files without manual uploads.
All personal data folders are excluded from Claude Code access via
instructions in `CLAUDE.md`.

Note: `.gitignore` controls what is committed to git but does NOT restrict
Claude Code's file system access. `CLAUDE.md` is the correct control for
that boundary.

---

## Setup

### 1. Install Python
Version 3.10 or higher from [python.org](https://python.org/downloads/)

### 2. Install dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # test dependencies (pytest, pytest-mock)
```

### 3. Configure environment
Copy `.env.example` to `.env`:
```
ANTHROPIC_API_KEY=your_key_here
CANDIDATE_NAME=Your Full Name
CANDIDATE_PHONE=(xxx) xxx-xxxx
CANDIDATE_EMAIL=your@email.com
CANDIDATE_LINKEDIN=linkedin.com/in/yourprofile
CANDIDATE_GITHUB=github.com/yourusername
CANDIDATE_LOCATION=City, ST
```

### 4. Add your data
- Experience library: `data/experience_library/experience_library.md`
- Resume template: `templates_local/resume_template.docx`
- Tracker: `data/tracker/job_pipeline.xlsx`

### 5. Build the experience library
```bash
# Full parse — all employers:
python scripts/phase3_parse_library.py

# Re-parse a single employer (faster for targeted edits):
python scripts/phase3_parse_employer.py "employer name"

python scripts/phase3_build_candidate_profile.py
python scripts/phase3_compile_library.py
```

### 6. Run tests
```bash
# Tier 1 — mock suite (same as CI, no API key required):
pytest tests/ -m "not live" -v

# Tier 2 — live API tests (requires ANTHROPIC_API_KEY):
pytest -m live -v
```

### 7. Run scripts
```bash
python scripts/pipeline_report.py
python scripts/phase2_job_ranking.py
python scripts/phase2_semantic_analyzer.py
python scripts/phase4_resume_generator.py --stage 1 --role [role]
python scripts/phase4_resume_generator.py --stage 3 --role [role]
python scripts/phase4_resume_generator.py --stage 4 --role [role]
python scripts/check_resume.py --role [role]
python scripts/phase4_cover_letter.py --stage 1 --role [role]
python -m scripts.check_cover_letter --role [role]
python scripts/phase4_cover_letter.py --stage 4 --role [role]
python scripts/phase5_interview_prep.py --role [role] --interview_stage [recruiter|hiring_manager|team_panel]
python scripts/phase5_debrief.py --role [role] --stage [recruiter_screen|hiring_manager|panel|final] --interactive
python scripts/phase5_debrief.py --role [role] --stage [recruiter_screen|hiring_manager|panel|final] --init
python scripts/phase5_debrief.py --role [role] --stage [recruiter_screen|hiring_manager|panel|final] --convert
python scripts/phase5_workshop_capture.py --role [role] --stage [recruiter|hiring_manager|team_panel]
python scripts/phase5_thankyou.py --role [role] --stage [recruiter_screen|hiring_manager|panel|final]
```

---

## Project Structure

{{include: project_structure}}

---

## Way Ahead

| Item | Description |
|------|-------------|
| Phase 5 updates | Reconcile duplicate salary guidance, fix fabricated MBSE gap redirect, remove lapsed Security+ language |
| candidate_profile.md rebuild | Rebuild from current library — flag lapsed certifications, add confirmed [CANDIDATE] experience |
| Phase 6 | Networking support — LinkedIn search guidance, connection request and follow-up message templates |
| Phase 7 | Search agent — automated role discovery from Google, USAJobs, ClearanceJobs |
| Pipeline report | Pull interview stage from job_pipeline.xlsx into pipeline_report.py output |


---

## Skills Demonstrated

- Python scripting and automation
- REST API integration (Anthropic Claude API including web search tool)
- Prompt engineering for structured LLM outputs
- Hallucination prevention through library-derived candidate profiling
- PII protection with environment variable based filtering
- Agent design and multi-step workflow orchestration
- Asynchronous human-in-the-loop workflow design
- Status-based pipeline management with duplicate detection
- Document generation with python-docx
- JSON data modeling and structured knowledge base design
- Modular shared-library design — parsing logic extracted to importable module
- Security-conscious development practices
- Two-tier pytest suite with mock and live API tiers
- CI/CD pipeline with GitHub Actions — green badge on every push
- AI-assisted development workflow with Claude Code
- Git version control and GitHub portfolio publishing

---

## Author

R. Todd Drake — Senior Systems Engineer, San Diego CA.
This project started as a structured problem: active defense SE job search, high application volume, and a need for tailored materials at scale without sacrificing quality or accuracy. I applied the same systems engineering discipline I use professionally — phased development, requirements traceability, V&V framework, human-in-the-loop workflow design — and used Claude Code and the Anthropic API to implement it. The result is a working pipeline that has measurably improved decision quality, resume tailoring, and interview preparation outcomes across an active job search.

---

## License

This project is for personal and portfolio use.
