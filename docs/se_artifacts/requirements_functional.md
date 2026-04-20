# Functional Requirements

# AI Job Search Agent

Version 1.0 | April 2026

Parent document: `docs/se_artifacts/conops.md`

---

## Overview

This document defines the functional requirements for the AI Job Search Agent. Requirements are organized by capability area and use mixed modal verb convention: **shall** denotes a hard requirement; **should** denotes preferred behavior where some implementation flexibility exists.

Each requirement carries the following attributes:

|Attribute|Description|
|-|-|
|ID|FR-[seq] -- flat sequential across all capability areas|
|Statement|What the system shall or should do|
|Phase|Pipeline phase(s) where this requirement applies|
|Priority|High / Medium / Low|
|Notes|Clarifications, constraints, or known limitations|

---

## Capability Areas

1. [Candidate Data Management](#1-candidate-data-management)
2. [Role Ingestion and Pipeline Management](#2-role-ingestion-and-pipeline-management)
3. [Role Ranking and Fit Analysis](#3-role-ranking-and-fit-analysis)
4. [Resume Generation](#4-resume-generation)
5. [Cover Letter Generation](#5-cover-letter-generation)
6. [Quality Control](#6-quality-control)
7. [Interview Preparation](#7-interview-preparation)
8. [Post-Interview Capture](#8-post-interview-capture)
9. [Security and Privacy](#9-security-and-privacy)
10. [Human-in-the-Loop Workflow](#10-human-in-the-loop-workflow)
11. [System Integrity](#11-system-integrity)

---

## 1. Candidate Data Management

*Covers the experience library, candidate profile, and PII configuration -- the factual baseline all downstream capabilities depend on.*

|ID|Statement|Phase|Priority|Notes|
|-|-|-|-|-|
|FR-001|The system shall maintain a human-editable markdown source file as the authoritative record of candidate experience.|0, 3|High|`experience_library.md` is the only file a human edits directly.|
|FR-002|The system shall compile the markdown source into a structured JSON representation suitable for API consumption.|0, 3|High|`experience_library.json` is always compiled output -- never edited directly.|
|FR-003|The system shall support re-compilation of a single employer section without requiring a full library rebuild.|3|Medium|Enables faster iteration during targeted edits.|
|FR-004|The system shall generate a candidate profile document from the current compiled library.|0, 3|High|`candidate_profile.md` is derived from the library -- not maintained independently.|
|FR-005|The system shall assign a unique identifier to each bullet in the compiled library.|3|High|Required for traceability between library entries and generated resume content.|
|FR-006|The system shall support flagging individual bullets as priority entries that are always included in resume generation regardless of keyword score.|3, 4|High|Priority flag set in library source; honored by Phase 4 Stage 1.|
|FR-007|The system shall support flagging individual bullets as requiring verification before use.|3|Medium|VERIFY metadata in library source. Flags unconfirmed claims for human review.|
|FR-008|The system shall flush all pending bullets before transitioning between employer sections during library parsing.|3|High|Prevents silent data loss at section boundaries. Resolved by library_parser.py fix (Apr 2026).|
|FR-009|The system should detect and report bullet count discrepancies between the markdown source and compiled JSON.|3|Medium|Data integrity check -- catches silent drops during parsing.|
|FR-010|The system shall support tracking which resume roles each library bullet has been used in.|3|Low|`Used in:` metadata in library source.|

---

## 2. Role Ingestion and Pipeline Management

*Covers role discovery, status tracking, duplicate detection, and pipeline health reporting.*

|ID|Statement|Phase|Priority|Notes|
|-|-|-|-|-|
|FR-011|The system shall maintain a structured inventory of roles under consideration in a CSV file.|1|High|`jobs.csv` -- manually populated by user.|
|FR-012|The system shall produce a pipeline health report showing role counts by status.|1|High|Includes counts for all defined status values.|
|FR-013|The system shall detect and report duplicate requisition numbers within the pipeline.|1, 2|High|Prevents duplicate applications to the same posted role.|
|FR-014|The system shall read application tracker data from `data/tracker/job_pipeline.xlsx` as an input to pipeline reporting.|1|Medium|Tracker and CSV serve complementary roles -- tracker holds richer application state.|
|FR-015|The system shall support the following role status values: blank (new), PURSUE, CONSIDER, SKIP, APPLIED.|1|High|Status values defined in ConOps Section 6, Phase 1.|
|FR-016|The system shall restrict downstream processing (ranking, resume generation) to roles with actionable status values (PURSUE, CONSIDER).|1, 2|High|Prevents wasted API calls on SKIP or unreviewed roles.|

---

## 3. Role Ranking and Fit Analysis

*Covers keyword scoring, semantic analysis, and fit-based prioritization.*

|ID|Statement|Phase|Priority|Notes|
|-|-|-|-|-|
|FR-017|The system shall score each role against the candidate's confirmed skills and experience using keyword matching.|2|High|Keyword list derived from experience library and candidate profile.|
|FR-018|The system shall perform semantic fit analysis on PURSUE and CONSIDER roles using the Claude API.|2|High|Nuanced fit assessment beyond keyword matching.|
|FR-019|The system shall produce a per-role semantic fit report as output of Phase 2 analysis.|2|High|Report persisted to `data/job_packages/[role]/`.|
|FR-020|The system shall not perform semantic analysis on roles with SKIP status.|2|High|Enforced by status filter before API call.|
|FR-021|The system should present ranked role output in a format that supports user decision-making on PURSUE / CONSIDER / SKIP assignment.|2|Medium|Ranking is an input to the human decision -- not a substitute for it.|

---

## 4. Resume Generation

*Covers the four-stage tailored resume generation workflow.*

|ID|Statement|Phase|Priority|Notes|
|-|-|-|-|-|
|FR-022|The system shall generate a tailored resume draft using keyword and semantic bullet selection from the experience library.|4|High|Stage 1 output: `stage1_draft.txt`.|
|FR-023|The system shall always include priority-flagged bullets in Stage 1 output regardless of keyword score.|4|High|Priority bullets appear first in candidate list.|
|FR-024|The system shall generate core competencies from the job description as part of Stage 1 output.|4|High|Competencies derived from JD -- not hardcoded.|
|FR-025|The system shall select a professional summary from the library as part of Stage 1 output.|4|High|Summary selected from compiled library summaries section.|
|FR-026|The system shall perform a semantic coherence check and ATS keyword gap analysis at Stage 3.|4|High|Stage 3 output: `stage3_review.txt`.|
|FR-027|The system shall generate a formatted .docx resume from the approved stage file using a user-supplied template.|4|High|Stage 4 output. Template in `templates_local/resume_template.docx`.|
|FR-028|The system shall treat plain text stage files as the authoritative record of resume content. The .docx is presentation layer only.|4|High|.docx is never edited directly.|
|FR-029|The system shall not generate resume content that cannot be traced to a confirmed entry in the experience library.|4|High|Core accuracy constraint -- no fabrication.|
|FR-030|The system should provide wording suggestions at Stage 3 that are grounded in confirmed candidate background.|4|Medium|Suggestions must not introduce unconfirmed claims.|

---

## 5. Cover Letter Generation

*Covers the four-stage tailored cover letter generation workflow.*

|ID|Statement|Phase|Priority|Notes|
|-|-|-|-|-|
|FR-031|The system shall generate a tailored cover letter draft aligned with the resume content for the same role.|4|High|Stage 1 output: `cl_stage1_draft.txt`.|
|FR-032|The system shall generate a plain-text application paragraph (150--250 words) suitable for online application fields.|4|High|Included in Stage 1 output alongside the formal letter.|
|FR-033|The system shall extract the hiring manager name from the job description if present and use it in the letter salutation.|4|Medium|Falls back to generic salutation if not found.|
|FR-034|The system shall incorporate gap filtering from the resume Stage 3 review file when available.|4|Medium|Prevents cover letter from contradicting resume gap analysis.|
|FR-035|The system shall generate a formatted .docx cover letter with the formal letter on page 1 and the application paragraph on page 2.|4|High|Stage 4 output.|
|FR-036|The system shall not generate cover letter content that cannot be traced to confirmed candidate experience.|4|High|Same accuracy constraint as resume generation.|

---

## 6. Quality Control

*Covers automated checking of generated resume and cover letter content.*

|ID|Statement|Phase|Priority|Notes|
|-|-|-|-|-|
|FR-037|The system shall perform string-matching quality checks on generated resume content before Stage 4 output.|4|High|Checks include: em dash detection, lapsed certification language, known gap terms.|
|FR-038|The system shall perform API-based quality assessment on generated resume content to detect implied gap fulfillment, banned language, and generic phrasing.|4|High|Two-layer check: string matching + API assessment.|
|FR-039|The system shall perform the same two-layer quality check on generated cover letter content.|4|High|`check_cover_letter.py` mirrors `check_resume.py` structure.|
|FR-040|The system shall flag any use of em dashes in generated content as a quality violation.|4|High|Em dashes are a known AI-generated content signal. En dashes only.|
|FR-041|The system shall flag any reference to lapsed or unverified certifications in generated content.|4|High|Applies to any certification flagged as lapsed or unverified in the experience library.|
|FR-042|The system should flag generic opener phrases in cover letter content as a quality violation.|4|Medium|e.g. "I am writing to express my interest..."|
|FR-043|The system shall flag any language that implies fulfillment of a confirmed experience gap as a quality violation.|4|High|Gap-filling language is a fabrication risk.|

---

## 7. Interview Preparation

*Covers stage-aware prep package generation.*

|ID|Statement|Phase|Priority|Notes|
|-|-|-|-|-|
|FR-044|The system shall generate a stage-appropriate interview preparation package for each scheduled interview.|5|High|Valid stages: recruiter, hiring_manager, team_panel.|
|FR-045|The system shall support three distinct interview stages with differentiated content registers and section depth.|5|High|Stage label and description written to output file header.|
|FR-046|The system shall generate employer-attributed STAR stories with probe branches as part of the prep package.|5|High|Every story must name employer, title, and dates.|
|FR-047|The system shall perform a two-tier gap analysis (REQUIRED / PREFERRED) grounded in the full job description text.|5|High|Full JD used -- not truncated. No inference from industry norms.|
|FR-048|The system shall extract salary guidance from the job description and anchor it to the nearest $5,000 increment.|5|Medium|Salary anchor included in prep package.|
|FR-049|The system shall conduct company and role research via web search as part of prep package generation.|5|High|Web search tool enabled on Phase 5 API calls.|
|FR-050|The system shall produce prep package output in both plain text (.txt) and formatted Word document (.docx).|5|High|.txt for VS Code review and workshopping; .docx for reading and printing.|
|FR-051|The system shall produce separate output files for each interview stage without collision.|5|High|Files named `interview_prep_[stage].txt` / `.docx`.|
|FR-052|The system shall load resume content from stage files, not from .docx output.|5|High|Falls back to `stage2_approved.txt` if `stage4_final.txt` not present.|

---

## 8. Post-Interview Capture

*Covers debrief, thank-you letter generation, and workshop capture.*

|ID|Statement|Phase|Priority|Notes|
|-|-|-|-|-|
|FR-053|The system shall capture structured post-interview debrief data immediately after each interview.|5|High|Output: `debrief_[stage]_[interview-date]_filed-[produced-date].json`.|
|FR-054|The system shall support both interactive (guided questionnaire) and YAML-based offline debrief workflows.|5|Medium|`--interactive` for guided capture; `--init` / `--convert` for YAML workflow.|
|FR-055|The system shall generate AI follow-up questions per debrief section in interactive mode.|5|Medium|One optional follow-up question per section via API call.|
|FR-056|The system shall generate a personalized thank-you letter for each interviewer from the filed debrief JSON.|5|High|One letter per interviewer. Output: `thankyou_[stage]_[interviewer].txt` and `.docx`.|
|FR-057|The system shall support panel interviews with multiple interviewers via a panel label parameter.|5|Medium|`--panel_label` flag on `phase5_thankyou.py`.|
|FR-058|The system shall parse workshopped interview prep content and persist refined stories, gaps, and questions to a persistent interview library.|5|High|`interview_library.json` -- reusable across future roles.|
|FR-059|The system shall append or update existing entries in the interview library without overwriting unrelated content.|5|High|Workshop capture is additive -- not destructive.|

---

## 9. Security and Privacy

*Covers PII protection and data handling.*

|ID|Statement|Phase|Priority|Notes|
|-|-|-|-|-|
|FR-060|The system shall strip all candidate PII from content before any API call.|All|High|`pii_filter.py` loads PII values from `.env` at runtime. No PII hardcoded in scripts.|
|FR-061|The system shall load PII values from environment variables, not from source code.|All|High|`.env` file excluded from version control via `.gitignore`.|
|FR-062|The system shall exclude all personal data from version control.|All|High|Experience library, resumes, job packages, tracker, and candidate background files gitignored.|
|FR-063|The system should strip PII from debrief content before interactive mode API calls.|5|High|All responses PII-stripped before the API call in `--interactive` mode.|

---

## 10. Human-in-the-Loop Workflow

*Covers defined human review and approval checkpoints.*

|ID|Statement|Phase|Priority|Notes|
|-|-|-|-|-|
|FR-064|The system shall require human review and status assignment for all new roles before downstream processing begins.|1|High|No role proceeds to ranking without an assigned status.|
|FR-065|The system shall require human review and approval of the Stage 2 resume draft before Stage 3 processing.|4|High|`stage2_approved.txt` is the human-approved record.|
|FR-066|The system shall require human review and approval of the Stage 2 cover letter draft before Stage 3 processing.|4|High|`cl_stage2_approved.txt` is the human-approved record.|
|FR-067|The system shall not submit applications autonomously. Human submission is always required.|All|High|System produces materials; human executes submission.|
|FR-068|The system should provide overwrite protection with confirmation prompt when output files already exist.|All|Medium|Prevents accidental overwrite of approved stage files.|

---

## 11. System Integrity

*Covers pipeline consistency, test coverage, and development conventions.*

|ID|Statement|Phase|Priority|Notes|
|-|-|-|-|-|
|FR-069|The system shall maintain a two-tier automated test suite covering all pipeline phases.|All|High|Tier 1: mock suite (no API key); Tier 2: live API.|
|FR-070|The system shall pass all Tier 1 mock tests before any commit to the main branch.|All|High|304 tests as of Apr 2026. CI via GitHub Actions.|
|FR-071|The system shall use en dashes only in all generated text content. Em dashes are prohibited.|All|High|Em dashes are a known AI-generated content signal. Enforced by quality checkers.|
|FR-072|The system shall use a consistent model string across all API calls.|All|Medium|Current model: `claude-sonnet-4-20250514`. Defined in DECISIONS_LOG.|
|FR-073|The system shall use underscores for all file and folder names. Hyphens and spaces are prohibited.|All|Low|Naming convention -- enforced by CLAUDE.md.|
|FR-074|The system should be executable from the project root for all scripts.|All|Medium|`python scripts/[script].py` -- no path manipulation required.|
|FR-075|The system shall be compatible with Python 3.11 and above.|All|High|No backslash escapes inside f-string expressions. No syntax requiring 3.12+.|

---

## Requirements Summary

|Capability Area|Count|High|Medium|Low|
|-|-|-|-|-|
|1. Candidate Data Management|10|7|2|1|
|2. Role Ingestion and Pipeline Management|6|5|1|0|
|3. Role Ranking and Fit Analysis|5|4|1|0|
|4. Resume Generation|9|7|2|0|
|5. Cover Letter Generation|6|5|1|0|
|6. Quality Control|7|6|1|0|
|7. Interview Preparation|9|8|1|0|
|8. Post-Interview Capture|7|4|3|0|
|9. Security and Privacy|4|4|0|0|
|10. Human-in-the-Loop Workflow|5|4|1|0|
|11. System Integrity|7|4|2|1|
|**Total**|**75**|**58**|**16**|**2**|

---

## Related Documents

|Document|Location|Purpose|
|-|-|-|
|ConOps|`docs/se_artifacts/conops.md`|Operational context and system concept|
|Non-Functional Requirements|`docs/se_artifacts/requirements_nonfunctional.md`|Quality, security, performance constraints|
|V&V Framework and RTM|`docs/se_artifacts/vv_framework.md`|Verification and validation approach; requirements traceability matrix|
|Decisions Log|`context/DECISIONS_LOG.md`|Architecture and coding decisions|



