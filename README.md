# AI Job Search Agent

A multi-phase AI-powered job search automation system built as both a 
practical tool for managing an active job search and a portfolio project 
demonstrating real-world Python development, API integration, and AI agent design.

---

## Project Overview

Most job seekers optimize their resume wording.
This system optimizes the entire process.

Instead of manually searching, scoring, and tailoring applications one at a time,
this agent pipeline handles discovery, ranking, resume generation, interview prep,
and networking intelligence — producing tailored application packages and
interview prep materials for every role in the pipeline.

---

## Project Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Pipeline report script and tracker schema | ✅ Complete |
| 2 | Job ranking and semantic fit analysis — keyword scoring + Claude API | ✅ Complete |
| 3 | Experience knowledge base — structured JSON from resume library | ✅ Complete |
| 4 | Automated resume generation — tailored .docx output per application | 🔧 Prototype |
| 5 | Interview preparation — company brief, story bank, gap prep, salary analysis | 🔧 Prototype |
| 6 | Networking and discovery agents | ⏳ Planned |

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
   → Four-stage async workflow with human review at each stage
5. Run phase5_interview_prep.py when interview is scheduled
   → Company brief, story bank, gap prep, questions to ask, salary guidance
6. Submit application, update status to APPLIED
7. Move APPLIED entries to job_pipeline.xlsx tracker
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

```
Stage 1 (automated)  →  stage1_draft.txt
                         Keyword + semantic bullet selection
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

---

## Phase 5 — Interview Prep

Single command generates a complete prep package:

```bash
python scripts/phase5_interview_prep.py --role [role_folder]
```

Output saved to `data/job_packages/[role]/interview_prep.txt` containing:
- Company and role brief with salary range analysis
- Salary expectations guidance with anchor and floor
- Role fit assessment and key themes to lead with
- Five STAR-format interview stories mapped to JD requirements
- Gap preparation with honest, confident talking points
- Eight questions to ask organized by category

---

## Tech Stack

- **Python 3.x** — core scripting and automation
- **Anthropic Claude API** — LLM backbone for analysis, tailoring, and generation
- **openpyxl** — reading and writing the application tracker (.xlsx)
- **python-docx** — generating tailored resume files (.docx)
- **VS Code** — development environment
- **Git / GitHub** — version control and portfolio publishing

---

## Security & Privacy

PII (name, phone, email, LinkedIn, GitHub) is stripped from all API calls
before any data leaves the local machine. The `pii_filter.py` utility loads
PII values from `.env` at runtime — no personal data is hardcoded anywhere
in the published code.

All personal data files (experience library, resumes, job packages, tracker)
are excluded from version control via `.gitignore`.

---

## Setup

### 1. Install Python
Download from [python.org](https://www.python.org/downloads/) — version 3.10 or higher.

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
Copy `.env.example` to `.env` and add your values:
```
ANTHROPIC_API_KEY=your_key_here
CANDIDATE_NAME=Your Full Name
CANDIDATE_PHONE=(xxx) xxx-xxxx
CANDIDATE_EMAIL=your@email.com
CANDIDATE_LINKEDIN=linkedin.com/in/yourprofile
CANDIDATE_GITHUB=github.com/yourusername
```

### 4. Add your data
- Experience library: `data/experience_library/experience_library.md`
- Resume template: `templates/resume_template.docx`
- Application tracker: `data/tracker/job_pipeline.xlsx`

### 5. Build the experience library
```bash
python scripts/phase3_parse_library.py
python scripts/phase3_build_candidate_profile.py
python scripts/phase3_compile_library.py
```

### 6. Run scripts
```bash
# Pipeline report
python scripts/pipeline_report.py

# Score and rank jobs
python scripts/phase2_job_ranking.py

# Semantic fit analysis (PURSUE/CONSIDER only)
python scripts/phase2_semantic_analyzer.py

# Resume generation
python scripts/phase4_resume_generator.py --stage 1 --role [role_folder]
python scripts/phase4_resume_generator.py --stage 3 --role [role_folder]
python scripts/phase4_resume_generator.py --stage 4 --role [role_folder]

# Interview prep
python scripts/phase5_interview_prep.py --role [role_folder]

# Resume quality check
python scripts/check_resume.py resumes/tailored/[role]/[resume].docx
```

---

## Project Structure

```
Job_search_agent/
├── data/
│   ├── tracker/                  # Application tracking spreadsheet (local only)
│   ├── jobs.csv                  # Job pipeline with status tracking
│   ├── job_packages/             # Per-job folders:
│   │   └── [role]/               #   job_description.txt
│   │                             #   stage1_draft.txt → stage4_final.txt
│   │                             #   interview_prep.txt
│   └── experience_library/       # Experience knowledge base (local only)
│       ├── experience_library.md # Human-readable source — edit this
│       ├── experience_library.json
│       ├── candidate_profile.md  # Canonical profile — hallucination prevention
│       └── employers/            # Per-employer JSON files
├── resumes/tailored/             # Generated resumes (local only)
├── templates/
│   └── resume_template.docx      # Blank styled Word template (local only)
├── scripts/
│   ├── pipeline_report.py
│   ├── phase2_job_ranking.py
│   ├── phase2_semantic_analyzer.py
│   ├── phase3_parse_library.py
│   ├── phase3_build_candidate_profile.py
│   ├── phase3_compile_library.py
│   ├── phase4_resume_generator.py
│   ├── phase5_interview_prep.py
│   ├── check_resume.py
│   └── utils/
│       └── pii_filter.py         # PII stripping utility (no personal data)
├── example_data/                 # Fictional reference data
├── .env                          # API keys and PII — never committed
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Skills Demonstrated

- Python scripting and automation
- REST API integration (Anthropic Claude API)
- Prompt engineering for structured LLM outputs
- Hallucination prevention through library-derived candidate profiling
- PII protection with environment variable based filtering
- Agent design and multi-step workflow orchestration
- Asynchronous human-in-the-loop workflow design
- Status-based pipeline management and filtering
- Document generation with python-docx
- JSON data modeling and structured knowledge base design
- Secrets management and security-conscious development practices
- Git version control and GitHub portfolio publishing

---

## Author

R. Todd Drake — Portfolio project, actively developed.  
Built from scratch as a real-world introduction to Python, API development,
and AI agent design — applied directly to an active senior defense SE job search.

---

## License

This project is for personal and portfolio use.
