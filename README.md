# AI Job Search Agent

A multi-phase AI-powered job search automation system built as both a 
practical tool for managing an active job search and a portfolio project 
demonstrating real-world Python development, API integration, and AI agent design.

---

## Project Overview

Most job seekers optimize their resume wording.
This system optimizes the entire process.

Instead of manually searching, scoring, and tailoring applications one at a time,
this agent pipeline handles discovery, ranking, resume generation, and interview
preparation — producing tailored application packages and interview prep materials
for every role in the pipeline.

---

## Project Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Pipeline report script and tracker schema | ✅ Complete |
| 2 | Job ranking and semantic fit analysis | ✅ Complete |
| 3 | Experience knowledge base — structured JSON library | ✅ Complete |
| 4 | Automated resume generation — tailored .docx per application | 🔧 Prototype |
| 5 | Interview preparation — web-informed brief, story bank, gap prep | 🔧 Prototype |
| 6 | Networking and discovery agents | ⏳ Planned |

---

## Daily Workflow

```
1. Add new roles to jobs.csv (blank status, req number if available)
2. Run phase2_job_ranking.py
   → Scores all roles, reports only NEW/PURSUE/CONSIDER
   → Flags duplicate requisition numbers
   → Assign PURSUE / CONSIDER / SKIP to each new role
3. Run phase2_semantic_analyzer.py
   → Claude API analysis on PURSUE and CONSIDER roles only
4. Run phase4_resume_generator.py for top PURSUE roles
   → Four-stage async workflow with human review at each stage
   → Stage files are source of truth — never edit .docx directly
5. Run phase5_interview_prep.py when interview is scheduled
   → Generates .txt and .docx prep package
   → Workshop stories in chat before interview
6. Submit, update status to APPLIED, move to tracker
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

Outputs to `data/job_packages/[role]/`:
- `interview_prep.txt` — for VS Code review and story workshopping
- `interview_prep.docx` — formatted Word document for reading and printing

Package contains:
- Company & role brief with current web-searched information
- Salary expectations guidance with anchor and floor
- Employer-attributed STAR stories grounded in submitted resume bullets
- Gap preparation with honest/bridge/redirect structure
- Thoughtful questions to ask organized by category

---

## Tech Stack

- **Python 3.x** — core scripting and automation
- **Anthropic Claude API** — LLM backbone including web search tool
- **openpyxl** — application tracker (.xlsx)
- **python-docx** — resume and interview prep document generation
- **VS Code** — development environment (View > Word Wrap for .txt files)
- **Git / GitHub** — version control and portfolio publishing
- **Claude Code** — AI-assisted development via VS Code extension (optional)

---

## Security & Privacy

PII is stripped from all API calls before any data leaves the local machine.
`pii_filter.py` loads PII values from `.env` at runtime — no personal data
is hardcoded in the published code.

All personal data (experience library, resumes, job packages, tracker) is
excluded from version control via `.gitignore`.

Anthropic API: inputs are not used for model training under commercial terms.

---

## Claude Code (Optional)

This project includes a `CLAUDE.md` configuration file for use with
[Claude Code](https://claude.ai/code) in VS Code. It defines project
conventions and file access boundaries for AI-assisted script development.

Install the Claude Code extension from the VS Code marketplace to use it.
Claude Code is useful for making targeted script changes, debugging, and
refactoring — working directly against your local files without manual
uploads. All personal data folders are excluded from Claude Code access
via instructions in `CLAUDE.md`.

---

## Setup

### 1. Install Python
Version 3.10 or higher from [python.org](https://python.org/downloads/)

### 2. Install dependencies
```bash
pip install -r requirements.txt
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
```

### 4. Add your data
- Experience library: `data/experience_library/experience_library.md`
- Resume template: `templates/resume_template.docx`
- Tracker: `data/tracker/job_pipeline.xlsx`

### 5. Build the experience library
```bash
python scripts/phase3_parse_library.py
python scripts/phase3_build_candidate_profile.py
python scripts/phase3_compile_library.py
```

### 6. Run scripts
```bash
python scripts/pipeline_report.py
python scripts/phase2_job_ranking.py
python scripts/phase2_semantic_analyzer.py
python scripts/phase4_resume_generator.py --stage 1 --role [role]
python scripts/phase4_resume_generator.py --stage 3 --role [role]
python scripts/phase4_resume_generator.py --stage 4 --role [role]
python scripts/phase5_interview_prep.py --role [role]
python scripts/check_resume.py resumes/tailored/[role]/[resume].docx
```

---

## Project Structure

```
Job_search_agent/
├── data/
│   ├── jobs.csv                  # Pipeline with status + req number tracking
│   ├── job_packages/[role]/      # JD, stage files, interview prep
│   └── experience_library/       # Library source, JSON, candidate profile
├── resumes/tailored/             # Generated resumes (local only)
├── templates/resume_template.docx
├── scripts/
│   ├── pipeline_report.py        # Pipeline metrics + duplicate req detection
│   ├── phase2_job_ranking.py     # Keyword scoring + req number tracking
│   ├── phase2_semantic_analyzer.py
│   ├── phase3_parse_library.py
│   ├── phase3_build_candidate_profile.py
│   ├── phase3_compile_library.py
│   ├── phase4_resume_generator.py
│   ├── phase5_interview_prep.py  # Web search + resume-grounded stories
│   ├── check_resume.py
│   └── utils/pii_filter.py       # PII stripping — safe for GitHub
├── example_data/
├── CLAUDE.md                     # Claude Code project conventions and safety rules
├── .env                          # API keys and PII — never committed
├── .gitignore
├── requirements.txt
└── README.md
```

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
- Security-conscious development practices
- Git version control and GitHub portfolio publishing
- AI-assisted development workflow with Claude Code

---

## Author

R. Todd Drake — Portfolio project, actively developed.  
Built from scratch as a real-world introduction to Python, API development,
and AI agent design — applied directly to an active senior defense SE job search.

---

## License

This project is for personal and portfolio use.
