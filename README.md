# AI Job Search Agent

A multi-phase AI-powered job search automation system built as both a 
practical tool for managing an active job search and a portfolio project 
demonstrating real-world Python development, API integration, and AI agent design.

---

## Project Overview

Most job seekers optimize their resume wording.
This system optimizes the entire process.

Instead of manually searching, scoring, and tailoring applications one at a time,
this agent pipeline handles discovery, ranking, resume generation, and networking
intelligence — producing a daily shortlist of high-fit roles with tailored 
application packages ready to go.

---

## Project Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Pipeline report script and tracker schema | ✅ Complete |
| 2 | Job ranking and semantic fit analysis — keyword scoring + Claude API | ✅ Complete |
| 3 | Experience knowledge base — structured JSON from resume library | ✅ Complete |
| 4 | Automated resume generation — tailored .docx output per application | 🔧 Prototype |
| 5 | Networking and intelligence agents — recruiter ID, company briefs, interview prep | ⏳ Planned |

---

## Daily Workflow

```
1. Add new roles to jobs.csv (blank status)
2. Run phase2_job_ranking.py
   → Scores all roles, reports only NEW/PURSUE/CONSIDER
   → Assign PURSUE / CONSIDER / SKIP to each new role
3. Run phase2_semantic_analyzer.py
   → API analysis on PURSUE and CONSIDER roles only
   → Review combined table, finalize decisions
4. Run phase4_resume_generator.py for top PURSUE roles
   → Four-stage async workflow with human review
5. Submit application, update status to APPLIED
6. Move APPLIED entries to job_pipeline.xlsx tracker
```

---

## Job Status Values

| Status | Meaning |
|--------|---------|
| *(blank)* | New — not yet reviewed |
| PURSUE | Apply next |
| CONSIDER | On deck, needs more thought |
| SKIP | Decided against |
| APPLIED | Submitted — move to tracker |

---

## Phase 4 — Resume Generation Workflow

Phase 4 uses a four-stage asynchronous workflow that keeps the human in the loop
at every critical decision point:

```
Stage 1 (automated)  →  stage1_draft.txt
                         Keyword + semantic bullet selection
                         Core competencies generated from JD
                         Summary selected from library

Stage 2 (manual)     →  stage2_approved.txt
                         Review draft, swap bullets, adjust wording
                         Save approved content before Stage 3

Stage 3 (automated)  →  stage3_review.txt
                         Semantic coherence check
                         Wording suggestions grounded in confirmed background
                         ATS keyword gap analysis

Stage 4 (automated)  →  [Company]_[Role]_Resume.docx
                         Template-based .docx generation
                         Auto quality check via check_resume.py
```

---

## Tech Stack

- **Python 3.x** — core scripting and automation
- **Anthropic Claude API** — LLM backbone for analysis, tailoring, and generation
- **openpyxl** — reading and writing the application tracker (.xlsx)
- **python-docx** — generating tailored resume files (.docx)
- **VS Code** — development environment
- **Git / GitHub** — version control and portfolio publishing

---

## Setup

### 1. Install Python
Download from [python.org](https://www.python.org/downloads/) — version 3.10 or higher recommended.

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
Copy `.env.example` to `.env` and add your Anthropic API key:
```
ANTHROPIC_API_KEY=your_key_here
```
Get your API key at [console.anthropic.com](https://console.anthropic.com/)

### 4. Add your data
- Place your master resume in `resumes/master_resume.docx`
- Place your application tracker in `data/tracker/job_pipeline.xlsx`
- Add job descriptions to `data/job_packages/[role]/job_description.txt`
- Add your experience library to `data/experience_library/experience_library.md`
- Save a blank styled Word document as `templates/resume_template.docx`

### 5. Build the experience library
```bash
# Parse experience_library.md into structured JSON with keyword generation
python scripts/phase3_parse_library.py

# Build canonical candidate profile for hallucination prevention
python scripts/phase3_build_candidate_profile.py

# Compile employer files into single library JSON
python scripts/phase3_compile_library.py
```

### 6. Run scripts
```bash
# Generate pipeline report from tracker
python scripts/pipeline_report.py

# Score and rank jobs — shows only NEW/PURSUE/CONSIDER roles
python scripts/phase2_job_ranking.py

# Run semantic fit analysis — PURSUE and CONSIDER roles only
python scripts/phase2_semantic_analyzer.py

# Generate tailored resume — Stage 1 (bullet selection + competencies)
python scripts/phase4_resume_generator.py --stage 1 --role [role_folder]

# Generate tailored resume — Stage 3 (semantic review)
python scripts/phase4_resume_generator.py --stage 3 --role [role_folder]

# Generate tailored resume — Stage 4 (document generation)
python scripts/phase4_resume_generator.py --stage 4 --role [role_folder]

# Validate a resume before submitting
python scripts/check_resume.py resumes/tailored/[role]/[resume].docx
```

---

## Project Structure

```
Job_search_agent/
├── data/
│   ├── tracker/                  # Application tracking spreadsheet (local only)
│   ├── jobs.csv                  # Job pipeline with status tracking
│   ├── job_packages/             # Per-job folders, each containing:
│   │   └── [role]/               #   job_description.txt  (local only)
│   │                             #   stage1_draft.txt     (auto-generated)
│   │                             #   stage2_approved.txt  (your review)
│   │                             #   stage3_review.txt    (auto-generated)
│   │                             #   stage4_final.txt     (final approved)
│   └── experience_library/       # Experience knowledge base (local only)
│       ├── experience_library.md # Human-readable source — edit this
│       ├── experience_library.json # Compiled library — Phase 4 input
│       ├── candidate_profile.md  # Canonical candidate profile — hallucination prevention
│       ├── employers/            # Per-employer JSON files
│       └── archive/              # Previous versions and session notes
├── example_data/                 # Fictional example data for reference
├── resumes/
│   ├── master_resume.docx        # Base resume (local only)
│   └── tailored/                 # Tailored resumes (local only)
│       └── [role]/
│           └── [Company]_[Role]_Resume.docx
├── templates/
│   └── resume_template.docx      # Blank styled Word document (local only)
├── prompts/                      # Reusable LLM prompt templates
├── scripts/
│   ├── pipeline_report.py        # Phase 1 — pipeline metrics from tracker
│   ├── phase2_job_ranking.py     # Phase 2 — keyword scoring, status filtering
│   ├── phase2_semantic_analyzer.py # Phase 2 — Claude API semantic fit analysis
│   ├── phase3_parse_library.py   # Phase 3 — parse experience library to JSON
│   ├── phase3_build_candidate_profile.py # Phase 3 — build canonical candidate profile
│   ├── phase3_compile_library.py # Phase 3 — compile employer files to single JSON
│   ├── phase4_resume_generator.py # Phase 4 — four-stage resume generator
│   ├── check_resume.py           # Pre-submission resume quality validator
│   └── utils/                    # Diagnostic and maintenance utilities (local only)
├── outputs/                      # Reports and generated content (local only)
├── .env                          # API keys — never committed (local only)
├── .gitignore
├── requirements.txt
└── README.md
```

> **Privacy note:** All folders marked "local only" are excluded from version 
> control via `.gitignore`. Only code, prompts, templates, and example data 
> are published to GitHub. Personal data, resumes, API keys, and experience
> library content never leave your local machine.

---

## Resume Tailoring

Phase 4 generates tailored resume packages for each role using:

1. `data/job_packages/[role]/job_description.txt` — the job posting
2. `data/experience_library/experience_library.json` — compiled experience library
3. `data/experience_library/candidate_profile.md` — canonical candidate profile
4. `templates/resume_template.docx` — blank styled Word template

---

## Quality Control

`scripts/check_resume.py` validates any `.docx` resume file against a set of
known rules before submission — catching em dashes, banned metrics, inaccurate
terminology, and clearance language issues automatically.

```bash
python scripts/check_resume.py resumes/tailored/[role]/[resume].docx
```

Returns PASS, REVIEW, or FAIL with specific line-level findings.

---

## Skills Demonstrated

- Python scripting and file I/O
- REST API integration (Anthropic Claude API)
- Prompt engineering for structured LLM outputs
- Hallucination prevention through library-derived candidate profiling
- Agent design and multi-step workflow orchestration
- Asynchronous human-in-the-loop workflow design
- Status-based pipeline management and filtering
- Data processing with openpyxl
- Document generation with python-docx
- JSON data modeling and structured knowledge base design
- Environment variable management and secrets handling
- Git version control and GitHub portfolio publishing

---

## Author

R. Todd Drake — Portfolio project, actively developed.  
Built from scratch as a real-world introduction to Python, API development, 
and AI agent design.

---

## License

This project is for personal and portfolio use.
