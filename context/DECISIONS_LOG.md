# Decisions Log
# Load for: script development, architecture decisions, coding conventions
Last updated: 05 Apr 2026

## Project Split
- Development = building pipeline tools (CC in VS Code)
- Implementation = applying tools to active job search (Claude web chat)
These are separate concerns — keep them in separate Claude projects where possible.

## Language & Style (applies to all generated content)
- En dashes only — never em dashes. Em dashes signal AI-generated content.
  This applies to: resume bullets, cover letters, interview prep, code comments,
  strings in scripts, and any generated text.
- No fabricated or unverifiable metrics
- No em dashes in any output — replace all occurrences before delivery

## Architecture Decisions

### Phase 3 — Library Parser
- Shared parsing logic extracted to utils/library_parser.py
- phase3_parse_library.py = thin wrapper, imports from library_parser
- phase3_parse_employer.py = single-employer re-parse (faster iteration)
  Usage: python scripts/phase3_parse_employer.py "employer name"
  Add --keywords flag to regenerate keywords via API
- No top-level side effects in library_parser — safe to import from any script

### Phase 4 — Resume Generator
- Four-stage async workflow with human review at Stage 2
- Stage files are source of truth — .docx is presentation layer only
- PII stripped via strip_pii() from utils/pii_filter.py before all API calls
- Priority bullets: "priority": true in JSON = always included in Stage 1
  regardless of keyword score. Appears first in candidate list.
- Template-based .docx generation — styles defined once in Word template

### Phase 5 — Interview Prep
- Web search via Anthropic API tool (type: web_search_20250305)
- Resume bullets loaded from stage4_final.txt (falls back to stage2_approved.txt)
- Stage files are source of truth — never read .docx for resume content
- Two-tier gap analysis: REQUIRED vs PREFERRED, sourced from full JD text
- Full JD passed to gap prompt (not truncated) to catch preferred qualifications
- Employer-attributed STAR stories — every story must name employer, title, dates
- Salary extracted from JD with anchor rounded to nearest $5k
- Outputs: interview_prep.txt + interview_prep.docx
- Story workshopping done in Claude web chat, not in script

### Phase 6 — Networking (planned)
- Standalone script — not integrated into Phase 4 or 5
- LinkedIn search guidance + outreach message templates
- User performs LinkedIn searches manually — script provides queries and filters
- Once stable: Phase 4 Stage 4 output should reference Phase 6

### Security
- pii_filter.py strips PII before all API calls — loads from .env
- .env variables: ANTHROPIC_API_KEY, CANDIDATE_NAME, CANDIDATE_PHONE,
  CANDIDATE_EMAIL, CANDIDATE_LINKEDIN, CANDIDATE_GITHUB
- pii_filter.py is on GitHub — contains no personal data
- All personal data excluded from git via .gitignore
- CLAUDE.md prohibits CC from writing to data/, resumes/, outputs/, templates/, .env
- .gitignore does NOT restrict CC tool access — CLAUDE.md is the right control

### Git
- Never recommend the user employ git add . — always stage explicitly
- .gitignore must have dot prefix — verify before committing
- Commit messages describe code changes, not personal data content
- Anthropic API: inputs not used for model training (commercial terms confirmed)

## API Configuration
- Model: claude-sonnet-4-20250514
- Credits: $25 loaded, auto-reload at $5 with $15
- Claude Pro subscribed — Claude Code bills against Pro, scripts bill against API credits
- These are separate billing systems

## jobs.csv Schema
company, title, location, salary_range, url, req_number, date_found, status, package_folder

## Script Naming Conventions
- Phase scripts: phase[N]_[description].py
- Utility scripts: utils/[description].py
- Diagnostic scripts: utils/diagnose_[description].py — local only, gitignored by name
- Output files per role: data/job_packages/[role]/[filename]

## Experience Library Conventions
- experience_library.md = human-readable source — edit this
- experience_library.json = compiled output — never edit directly
- Bullet format: "- [text]" with metadata on indented lines below
- Priority bullet: add "*PRIORITY: true*" as first metadata line
- Theme header: "### Theme: [name]"
- Flagged bullet: add "[FLAGGED – reason]" inline in bullet text
- Verify item: add "*[VERIFY: description]*" as metadata line
- Used in: "*Used in: [role1], [role2]*"

## Coding Conventions
- Python 3.x
- All scripts runnable from project root: python scripts/[script].py
- argparse for CLI arguments
- dotenv for environment variables
- Overwrite protection with confirmation prompt for output files
- Progress printed to terminal during long operations
- En dashes in all string content, never em dashes
