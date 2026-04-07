# CLAUDE.md — Job Search Agent Project

## Project Overview
AI-powered job search automation system. Python scripts for job ranking, resume generation, and interview prep.

## CRITICAL SAFETY RULES — READ BEFORE EVERY ACTION

### Never read, access, or touch these files/folders:
- .env — contains API keys and PII
- data/ — contains personal career data, resumes, job packages
- resumes/ — contains tailored resume documents
- outputs/ — contains generated reports

**Important:** .gitignore does NOT prevent Claude's tools (Glob, Read) from accessing these paths.
Never use Glob, Read, or any tool to browse or read files in the above directories, even if asked to explore the project structure.

### Safe to read and edit:
- scripts/*.py — all Python automation scripts
- scripts/utils/*.py — utility scripts
- context/*.md — candidate background, decisions log, project context
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
### Key scripts:
- scripts/phase2_job_ranking.py
- scripts/phase2_semantic_analyzer.py
- scripts/phase3_*.py
- scripts/phase4_resume_generator.py
- scripts/phase4_cover_letter.py
- scripts/phase5_interview_prep.py
- scripts/pipeline_report.py
- scripts/check_resume.py

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
