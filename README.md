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
| 1 | Manual workflow foundations — pipeline report script and tracker schema | ✅ Complete |
| 2 | Job ranking and semantic fit analysis — keyword scoring + Claude API | ✅ Complete |
| 3 | Experience knowledge base — structured JSON from resume library | ⏳ Planned |
| 4 | Automated resume generation — tailored .docx output per application | ⏳ Planned |
| 5 | Networking and intelligence agents — recruiter ID, company briefs, interview prep | ⏳ Planned |

---

## System Architecture

```
Job Sources (LinkedIn, Indeed, ClearanceJobs, company pages)
      ↓
Discovery Agent  →  jobs.csv
      ↓
Ranking Agent  →  ranked_jobs.csv  (keyword scoring + semantic fit score)
      ↓
Resume Generator  →  resumes/tailored/[role]/[company]_[role]_Resume.docx
      ↓
Networking Agent  →  linkedin_message.txt + company_brief.txt
      ↓
Interview Prep Agent  →  interview_pack.txt
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

### 5. Run scripts
```bash
# Generate pipeline report from tracker
python scripts/pipeline_report.py

# Score and rank jobs from jobs.csv
python scripts/phase2_job_ranking.py

# Run semantic fit analysis via Claude API
python scripts/phase2_semantic_analyzer.py
```

---

## Project Structure

```
Job_search_agent/
├── data/
│   ├── tracker/                  # Application tracking spreadsheet (local only)
│   ├── job_packages/             # Per-job folders, each containing:
│   │   └── [role]/               #   job_description.txt (local only)
│   └── experience_library/       # Structured experience knowledge base (local only)
├── example_data/                 # Fictional example data for reference
│   ├── jobs.csv                  # Sample jobs.csv showing expected format
│   ├── job_packages/             # Sample job description files
│   ├── tracker/                  # Tracker schema reference and example file
│   └── outputs/                  # Sample script outputs
├── resumes/
│   ├── master_resume.docx        # Base resume (local only)
│   └── tailored/                 # Tailored resumes and cover letters (local only)
│       └── [role]/               # One subfolder per role, matching job_packages/
│           ├── [Company]_[Role]_Resume.docx
│           └── [Company]_[Role]_CoverLetter.docx
├── prompts/                      # Reusable LLM prompt templates
├── scripts/                      # All Python automation scripts
├── templates/                    # Networking message templates
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

Phase 4 generates tailored resume and cover letter packages for each role.
The tailoring workflow uses:

1. `data/job_packages/[role]/job_description.txt` — the job posting
2. `data/experience_library/experience_library.md` — approved bullet library
3. `resumes/master_resume.docx` — base resume content

Output is written to `resumes/tailored/[role]/` with one subfolder per
application, named to match the corresponding `job_packages/` folder.
This structure allows the ranking agent and resume generator to pair
job descriptions with tailored outputs automatically.

---

## Skills Demonstrated

- Python scripting and file I/O
- REST API integration (Anthropic Claude API)
- Prompt engineering for structured LLM outputs
- Agent design and multi-step workflow orchestration
- Data processing with openpyxl
- Document generation with python-docx
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
