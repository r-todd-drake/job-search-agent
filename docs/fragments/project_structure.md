<!-- fragment: project_structure -->
```
Job_search_agent/
├── .github/workflows/test.yml            # GitHub Actions CI — mock suite on every push
├── context/                              # Context data store
│   ├── PROJECT_CONTEXT.md                # Lean index — load this first
│   ├── DECISIONS_LOG.md                  # Coding conventions + architecture decisions
│   ├── PARKING_LOT.md                    # Outstanding work items and priorities
│   ├── CANDIDATE_BACKGROUND.md           # Career background (local only)
│   └── PIPELINE_STATUS.md                # Active applications (local only)
├── data/
│   ├── jobs.csv                          # Pipeline — status + req number tracking
│   ├── job_packages/[role]/              # JD, stage files, interview prep (active)
│   │   └── inactive/[role]/              # Rejected / ghosted / withdrawn roles
│   ├── debriefs/[role]/                  # Post-interview debrief JSON (local only)
│   ├── interview_library.json           # Persistent story/gap/question library (local only)
│   └── experience_library/              # Library source, JSON, candidate profile
├── docs/
│   ├── features/                         # Requirements artifacts per capability
│   │   ├── README.md                     # Feature folder process and conventions
│   │   ├── user_story_template.md        # Template for new proposals
│   │   └── completed/                    # Built and tested features
│   ├── fragments/                        # Canonical shared content — edit these, not assembled docs
│   │   ├── audit_report.md               # Document audit findings (AC-1)
│   │   ├── current_phase_status.md       # Canonical phase table
│   │   ├── key_commands.md               # Canonical quick reference commands
│   │   ├── project_split.md              # Canonical dev vs implementation description
│   │   └── project_structure.md          # Canonical directory tree (this file)
│   ├── superpowers/
│   │   ├── specs/                        # Design specs (how to build it)
│   │   └── plans/                        # Implementation plans (how to execute)
│   ├── templates/                        # Document assembly templates ({{include:}} markers)
│   │   ├── README.md                     # Template for README.md
│   │   └── PROJECT_CONTEXT.md            # Template for context/PROJECT_CONTEXT.md
│   └── capabilities.md                   # Script-to-phase traceability (in progress)
├── example_data/
|   ├── job_packages/[role]/              # Example JD, stage files
|   ├── outputs/                          # Example generated reports, pipeline_reports, ranking_reports, semantic_analysis_reports
|   ├── tracker/job_pipeline_example.xlsx # Example job pipeline tracker
|   │    └── README.txt                   # Tracker workbook README
|   └── jobs.csv                          # Example Pipeline - status + req number tracking
├── outputs                               # Generated reports, pipeline_reports, ranking_reports, semantic_analysis_reports
├── resumes/tailored/                     # Generated resumes (local only)
├── templates/                            # Script input templates (tracked — YAML, plain-text)
│   └── interview_debrief_template.yaml   # Debrief YAML template for --init mode
├── templates_local/                      # Binary/personal templates (local only)
│   └── resume_template.docx              # Resume template (local only)
├── scripts/
│   ├── init_job_package.py               # Initialize new job package folder, job_description.txt, and jobs.csv row
│   ├── pipeline_report.py                # Pipeline metrics + duplicate req detection
│   ├── phase2_job_ranking.py             # Keyword scoring + req number tracking
│   ├── phase2_semantic_analyzer.py       # Claude API semantic fit analysis
│   ├── phase3_parse_library.py           # Full library parse (thin wrapper)
│   ├── phase3_parse_employer.py          # Single-employer re-parse
│   ├── phase3_build_candidate_profile.py
│   ├── phase3_compile_library.py
│   ├── phase4_resume_generator.py        # Four-stage resume generation
│   ├── phase4_cover_letter.py            # Staged cover letter generator
│   ├── phase5_interview_prep.py          # Stage-aware interview prep (recruiter/HM/team panel)
│   ├── phase5_debrief.py                  # Post-interview debrief capture (--init/--convert/--interactive)
│   ├── phase5_thankyou.py                # Post-interview thank-you letter generation (one per interviewer)
│   ├── phase5_workshop_capture.py        # Parses workshopped prep .docx into interview_library.json
│   ├── phase5_debrief_utils.py           # Shared utility — load filed debrief JSON
│   ├── interview_library_parser.py       # Shared module — read/write interview_library.json
│   ├── check_resume.py                   # Two-layer resume quality check (string matching + API)
│   ├── check_cover_letter.py             # Two-layer cover letter quality check
│   └── utils/
│       ├── build_docs.py                 # Assemble README + PROJECT_CONTEXT from fragments
│       ├── library_parser.py             # Shared parsing logic (no side effects)
│       ├── normalize_library.py          # One-time cleanup — merge tranche-suffixed employer sections
│       └── pii_filter.py                 # PII stripping — safe for GitHub
├── tests/                                # Two-tier pytest suite (mock + live)
│   ├── conftest.py                       # Shared fixtures and fictional test identity
│   ├── fixtures/                         # Fictional test data (Jane Q. Applicant / Acme)
│   ├── utils/                            # pii_filter, library_parser, build_docs tests
│   └── phase1/ … phase5/                 # Per-phase test files mirroring scripts/
├── CLAUDE.md                             # Claude Code conventions and safety rules
├── pytest.ini                            # Test config: pythonpath, live marker
├── requirements.txt                      # Runtime dependencies
├── requirements-dev.txt                  # Test dependencies (pytest, pytest-mock)
├── .env                                  # API keys and PII — never committed
├── .env.example                          # Environment variable template
├── .gitignore
└── README.md
```
