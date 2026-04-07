# AI Job Search Agent — Project Context
Last updated: 05 Apr 2026

## About This File
Lean index file for quick orientation. Load supporting context files as needed.
Do not bulk-load all context files into every session — load only what is relevant.

## What This Project Is
A multi-phase AI-powered job search automation system built as both a practical tool for managing an active senior defense SE job search and a portfolio project demonstrating Python development, API integration, and AI agent design.

Candidate: R. Todd Drake — Senior Systems Engineer, San Diego CA, Current TS/SCI.

## Project Split — Development vs Implementation

### Development (Claude Code in VS Code)
Building and improving the pipeline tools. Script editing, debugging, refactoring, architecture decisions, library maintenance, new phase development.
Reference: context/DECISIONS_LOG.md for coding conventions and architecture decisions.

### Implementation (Claude web chat)
Applying the tools to the active job search. Resume tailoring, interview prep, story workshopping, pipeline management, recruiter communications.
Reference: context/PIPELINE_STATUS.md and context/CANDIDATE_BACKGROUND.md.

## Current Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Pipeline report + tracker schema | Complete |
| 2 | Job ranking + semantic fit analysis | Complete |
| 3 | Experience library — structured JSON + shared parser | Complete |
| 4 | Resume generation + cover letter — tailored .docx per application | Prototype |
| 5 | Interview prep — web search, story bank, gap analysis | Prototype |
| 6 | Networking and outreach support | Planned |
| 7 | Search agent — automated role discovery | Planned |

## Non-Negotiable Rules (always in scope)
- En dashes only — never em dashes (em dashes signal AI-generated content)
- Stage files are source of truth — never edit .docx directly
- Never git add . — always stage files explicitly
- Never fabricate or infer experience — ask if unclear
- PII stripped from all API calls via pii_filter.py

## Supporting Context Files
Load these as needed for the session type:

| File | Load When |
|------|-----------|
| context/CANDIDATE_BACKGROUND.md | Resume tailoring, interview prep, story workshopping |
| context/PIPELINE_STATUS.md | Pipeline management, application decisions, recruiter comms |
| context/DECISIONS_LOG.md | Script development, architecture decisions, coding conventions |
| context/PARKING_LOT.md | Planning next development session, prioritizing work items |

## Project Structure (top level)
```
Job_search_agent/
├── context/                  — context data store (this file + 4 supporting files)
├── data/                     — personal data, local only, never committed
├── resumes/tailored/         — generated resumes, local only
├── templates/                — resume template, local only
├── scripts/                  — all automation scripts
├── example_data/             — fictional reference data
├── CLAUDE.md                 — Claude Code conventions and safety rules
├── .env                      — API keys and PII, never committed
├── .gitignore
├── requirements.txt
└── README.md
```

## Quick Reference — Key Commands
```
# Pipeline
python scripts/pipeline_report.py
python scripts/phase2_job_ranking.py
python scripts/phase2_semantic_analyzer.py

# Resume generation
python scripts/phase4_resume_generator.py --stage 1 --role [role]
python scripts/phase4_resume_generator.py --stage 3 --role [role]
python scripts/phase4_resume_generator.py --stage 4 --role [role]

# Interview prep
python scripts/phase5_interview_prep.py --role [role]

# Library maintenance
python scripts/phase3_parse_library.py
python scripts/phase3_parse_employer.py "[employer name]"
python scripts/phase3_compile_library.py
```
