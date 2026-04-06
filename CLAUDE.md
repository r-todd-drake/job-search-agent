# CLAUDE.md — Job Search Agent Project

## Project Overview
AI-powered job search automation system. Python scripts for job ranking, resume generation, and interview prep.

## CRITICAL SAFETY RULES — READ BEFORE EVERY ACTION

### Never read, access, or touch these files/folders:
- .env — contains API keys and PII
- data/ — contains personal career data, resumes, job packages
- resumes/ — contains tailored resume documents
- outputs/ — contains generated reports
- templates/ — contains resume template

**Important:** .gitignore does NOT prevent Claude's tools (Glob, Read) from accessing these paths.
Never use Glob, Read, or any tool to browse or read files in the above directories, even if asked to explore the project structure.

### Safe to read and edit:
- scripts/*.py — all Python automation scripts
- scripts/utils/*.py — utility scripts
- README.md
- requirements.txt
- CLAUDE.md
- PROJECT_CONTEXT.md

### Git safety:
- Never run git add . — always stage specific files
- Never commit .env or data/ or resumes/
- Always run git status before committing
- Verify .gitignore has dot prefix before any git operations

## Code Style
- Python scripts — en dashes in strings, not em dashes
- No hardcoded PII — all personal data via .env variables
- All API calls must use strip_pii() from scripts/utils/pii_filter.py
- Follow existing script patterns for consistency

## Project Structure
See README.md for full structure.
Key scripts: phase2_job_ranking.py, phase2_semantic_analyzer.py, phase3_*.py, phase4_resume_generator.py, phase5_interview_prep.py

## When asked to modify scripts:
1. Read the existing script first
2. Make targeted changes only
3. Run syntax check after editing
4. Never modify data files directly

## When asked to develop scripts:
1. Read the prompt, and any provided files first
2. Plan the proposed solution, do not begin developing the      script until there is a 95% propobability of successfully meeting the requiremnet articulated in the prompt. Ask clarifying questions to close the probability of scussess gap if necessary.
3. Run syntax check after development.
