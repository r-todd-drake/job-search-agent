# Concept of Operations (ConOps)
# AI Job Search Agent
Version 1.0 | April 2026

---

## 1. Purpose and Scope

This document establishes the operational concept for the AI Job Search Agent -- a multi-phase pipeline system that enables a job seeker to maximize the probability of securing a qualified position by producing consistently high-quality, accurately tailored application materials and interview preparation at a pace and volume that manual effort cannot sustain, without sacrificing accuracy or introducing fabricated experience.

This ConOps describes the operational environment, user context, desired effects, system concept, and phase-by-phase workflow. It serves as the parent document for functional and non-functional requirements and the verification and validation framework.

**Scope:** Single-user operational implementation. The architecture is designed to be portable to any job seeker who completes the candidate onboarding process (Phase 0). No multi-user or shared-instance capability is within current scope.

---

## 2. Desired Effect

> A job seeker maximizes the probability of securing a qualified position by producing consistently high-quality, accurately tailored application materials and interview preparation at a pace and volume that manual effort cannot sustain -- without sacrificing accuracy or introducing fabricated experience.

**Operationalizing "qualified position":** The system does not assume domain or role fit. Fit is assessed dynamically by the system's own ranking capability -- keyword scoring and semantic analysis against the candidate's confirmed background. A qualified position is one the system scores as PURSUE or CONSIDER based on that grounded assessment.

**The enabling dependency:** Every downstream output -- ranked roles, tailored resumes, cover letters, interview prep packages -- depends on a single source of candidate truth: the experience library and candidate profile. These are not data files. They are the system's factual baseline. Without them, the system cannot operate. Their construction and validation is therefore a precondition, not a setup step.

---

## 3. Operational Environment

### 3.1 User Profile

The system is operated by a single user: a job seeker managing an active, high-volume search across multiple simultaneous applications. The user is expected to:

- Maintain the experience library and candidate profile as the authoritative record of confirmed experience
- Provide job descriptions as system inputs
- Execute human-in-the-loop review at defined pipeline checkpoints
- Workshop interview stories and refine generated materials using Claude web chat as a complementary tool

The user is not assumed to be a developer. The system is designed so that ongoing operation requires only script execution and file editing -- no code changes required for normal use.

### 3.2 Operational Constraints

- **Accuracy over completeness:** The system shall never fabricate, infer, or extrapolate experience not confirmed in the experience library. A gap in output is preferable to a fabricated claim.
- **PII protection:** All candidate personally identifiable information is stripped before any data leaves the local machine via API call.
- **Human authority:** The system produces drafts and recommendations. All final application materials require human review and approval at defined checkpoints. The system does not submit applications autonomously.
- **Single source of truth:** For resume and cover letter generation, plain text stage files are the authoritative record of approved content. Document outputs (.docx) are presentation layer only and are never edited directly. Interview preparation materials follow a different pattern -- the .docx is a working document that may be marked up during story workshopping and read back into the pipeline via workshop capture.

### 3.3 Operational Context -- Two Modes

The system operates in two distinct modes that are kept deliberately separate:

**Development Mode** -- Building and improving the pipeline. Performed using Claude Code in VS Code, working directly against local files. Governed by `DECISIONS_LOG.md` and the V&V framework. Changes require passing the full mock test suite before commit.

**Implementation Mode** -- Applying the pipeline to an active job search. Performed through script execution and Claude web chat. Governed by pipeline status and candidate background context files. No code changes occur in this mode.

This separation prevents implementation-time shortcuts from degrading pipeline integrity and keeps the portfolio codebase clean.

---

## 4. Baseline -- Manual Approach and Its Limitations

Before this system, the job seeker's baseline process was:

- Manual role discovery across job boards -- unsystematic, time-consuming, no scoring
- Resume tailoring by editing a master resume -- high cognitive load, inconsistent quality, risk of stale or inaccurate content
- Cover letters written from scratch per role -- slow, variable quality
- Interview preparation assembled manually -- incomplete, not role-specific, not stage-aware
- No structured capture of interview outcomes or story performance

**Limiting factors of the baseline:**

| Constraint | Effect |
|------------|--------|
| Time per application | Limits volume; forces triage by gut feel rather than data |
| Cognitive load of tailoring | Degrades quality under high volume |
| No structured experience baseline | Increases risk of inconsistency and fabrication |
| No role fit scoring | Applications pursued without objective fit assessment |
| No stage-aware interview prep | Same preparation regardless of interview type or interviewer |
| No post-interview capture | Outcomes and story performance not retained for future use |

The system is designed to address each of these constraints directly.

---

## 5. System Concept

The AI Job Search Agent is a locally executed, multi-phase pipeline that transforms a job description and a grounded candidate experience library into a complete, tailored application package -- including a scored fit assessment, tailored resume, cover letter, and stage-specific interview preparation materials.

The pipeline is structured in eight phases, each producing defined outputs that serve as inputs to subsequent phases. Human review is built into the workflow at defined checkpoints rather than bolted on at the end.

**Core design principles:**

- **Grounded outputs:** All generated content is derived from the experience library. The system cannot introduce claims the library does not support.
- **Verifiable traceability:** Every output traces to a confirmed source -- experience library entry, job description requirement, or explicit user decision.
- **Accuracy before volume:** Quality controls (checker scripts, human review stages) are embedded in the workflow, not optional post-processing.
- **Separation of concerns:** Development and implementation are kept in separate workflows with separate tooling. The pipeline serves the job search; it does not complicate it.

---

## 6. Phase Overview

### Phase 0 -- Candidate Onboarding *(Precondition)*

**Purpose:** Establish the factual baseline that all downstream phases depend on.

**Inputs:** Candidate's source resumes, professional history, certifications, clearance status, PII

**Process:**
- Experience extraction from source resumes (semi-manual: structured prompts guide extraction)
- Experience library construction -- structured markdown source compiled to JSON
- Candidate profile generation from library
- PII filter configuration (.env)
- Library quality review -- verify completeness, flag unverifiable claims, confirm no fabrication

**Outputs:** `experience_library.json`, `candidate_profile.md`, `.env` (PII configuration)

**Exit criterion:** Library passes quality review. Candidate profile accurately reflects confirmed experience. PII filter validated against all PII values.

**Note:** Phase 0 is a one-time initialization with ongoing maintenance. The library is updated whenever new confirmed experience is available -- after each role, after each tailoring session that produces validated new bullets.

---

### Phase 1 -- Pipeline Management

**Purpose:** Maintain a structured, de-duplicated inventory of roles under consideration and produce pipeline health metrics.

**Inputs:** `jobs.csv` (manually populated with role metadata), `data/tracker/job_pipeline.xlsx` (application tracker -- read by pipeline report script)

**Process:**
- Pipeline report generation -- counts by status, duplicate requisition number detection
- Status assignment workflow -- user assigns PURSUE / CONSIDER / SKIP to new roles

**Outputs:** `pipeline_report_[date_time].txt`, updated `jobs.csv`

**Human touchpoint:** User reviews all new roles and assigns status before any downstream processing.

---

### Phase 2 -- Role Ranking and Fit Analysis

**Purpose:** Replace gut-feel application decisions with scored, evidence-based fit assessment.

**Inputs:** `data/job_packages/[role]/job_description.txt`, `jobs.csv`, experience library keywords

**Process:**
- Keyword scoring against confirmed candidate skills and experience
- Semantic fit analysis via Claude API -- nuanced fit assessment beyond keyword matching
- Duplicate requisition number detection

**Outputs:** Ranked role list, semantic fit reports per role

**Decision gate:** User confirms PURSUE / CONSIDER / SKIP assignments informed by scores before resume generation begins.

---

### Phase 3 -- Experience Library Maintenance

**Purpose:** Keep the candidate's factual baseline current, structured, and machine-readable.

**Inputs:** `experience_library.md` (human-edited source)

**Process:**
- Full library parse -- markdown source compiled to structured JSON
- Single-employer re-parse for targeted updates
- Candidate profile rebuild from current library

**Outputs:** `experience_library.json`, `candidate_profile.md`

**Integrity rule:** The markdown source is the only file a human edits. The JSON is always compiled output -- never edited directly.

---

### Phase 4 -- Resume and Cover Letter Generation

**Purpose:** Produce a tailored, accurate, ATS-ready resume and cover letter for each pursued role.

**Inputs:** `data/job_packages/[role]/job_description.txt`, `experience_library.json`, `candidate_profile.md`, `templates_local/resume_template.docx`

**Resume process (four stages):**

| Stage | Type | Output | Description |
|-------|------|--------|-------------|
| 1 | Automated | `stage1_draft.txt` | Keyword + semantic bullet selection; priority bullets always included; core competencies and summary generated |
| 2 | Human review | `stage2_approved.txt` | User reviews draft, swaps bullets, adjusts wording |
| 3 | Automated | `stage3_review.txt` | Semantic coherence check, wording suggestions, ATS keyword gap analysis |
| 4 | Automated | `[Role]_Resume.docx` | Template-based .docx generation; auto quality check |

**Cover letter process (four stages):**

| Stage | Type | Output | Description |
|-------|------|--------|-------------|
| 1 | Automated | `cl_stage1_draft.txt` | Traditional letter + plain-text application paragraph |
| 2 | Human review | `cl_stage2_approved.txt` | User verifies all claims against confirmed experience |
| 3 | Automated | `cl_stage3_review.txt` | Two-layer quality check -- string matching + API assessment |
| 4 | Automated | `[Role]_CoverLetter.docx` | Template-based .docx generation |

**Quality controls:** `check_resume.py` and `check_cover_letter.py` enforce accuracy rules -- no em dashes, no lapsed certifications, no gap-filling language, no fabricated claims.

---

### Phase 5 -- Interview Preparation

**Purpose:** Produce a stage-appropriate, role-specific interview preparation package for each scheduled interview.

**Inputs:** Job description, filed resume stage files, experience library, company research (via web search)

**Process:**
- Stage-aware prep package generation (recruiter / hiring manager / team panel)
- Story bank development -- employer-attributed STAR stories with probe branches
- Gap analysis -- two-tier REQUIRED / PREFERRED, grounded in confirmed experience
- Salary guidance -- extracted from JD, anchored to nearest $5k
- Post-interview debrief capture -- structured JSON per interview stage
- Thank-you letter generation -- one per interviewer from filed debrief
- Workshop capture -- refined stories persisted to interview library for reuse

**Outputs:** `interview_prep_[stage].txt`, `interview_prep_[stage].docx`, `debrief_[stage]_draft.yaml` (intermediate output), `debrief_[stage]_[date].json`, `thankyou_[stage]_[interviewer].docx`, `interview_library.json`

---

### Phase 6 -- Networking Support *(Planned)*

**Purpose:** Support systematic outreach to contacts at target organizations.

**Concept:** Standalone script providing LinkedIn search guidance, connection request templates, follow-up messages, cold outreach / InMail templates, and informational interview requests. User executes LinkedIn searches manually -- script provides queries, filters, and message templates.

---

### Phase 7 -- Search Agent *(Planned)*

**Purpose:** Automated role discovery from public job boards (Google, USAJobs, ClearanceJobs).

**Concept:** Reduces manual role discovery burden. LinkedIn explicitly excluded due to automation restrictions.

---

## 7. Workflow Summary

```
Phase 0:  Onboarding     →  Experience library + candidate profile established
Phase 1:  Pipeline       →  New roles ingested, status assigned
Phase 2:  Ranking        →  Roles scored, PURSUE/CONSIDER/SKIP confirmed
Phase 3:  Library        →  Experience baseline kept current
Phase 4:  Application    →  Tailored resume + cover letter per role
Phase 5:  Interview      →  Stage-aware prep, debrief, thank-you per interview
Phase 6:  Networking     →  Outreach to contacts at target organizations (planned)
Phase 7:  Search Agent   →  Automated role discovery (planned)
```

Human touchpoints occur at: Phase 0 library QC, Phase 1 status assignment, Phase 2 fit decision, Phase 4 Stage 2 resume review, Phase 4 Stage 2 cover letter review, Phase 5 story workshopping.

---

## 8. Key Interfaces

| Interface | From | To | Description |
|-----------|------|----|-------------|
| experience_library.json | Phase 0/3 | Phases 2, 4, 5 | Grounded candidate factual baseline |
| candidate_profile.md | Phase 0/3 | Phases 4, 5 | Compiled candidate profile for API context |
| jobs.csv | Phase 1 | Phase 2 | Role inventory with status and metadata |
| stage2_approved.txt | Phase 4 (human) | Phase 4 Stage 3, Phase 5 | Human-approved resume content |
| interview_library.json | Phase 5 | Phase 5 (future roles) | Persistent workshopped story and gap library |
| debrief JSON | Phase 5 | Phase 5 thank-you | Structured post-interview capture |

---

## 9. Constraints and Assumptions

**Constraints:**
- All API calls use the Anthropic Claude API; no other LLM providers are in scope
- PII must be stripped before every API call -- non-negotiable
- The system does not submit applications; human submission is always required
- Generated content must be verifiable against the experience library -- fabrication is a system failure, not an acceptable gap-fill

**Assumptions:**
- The user maintains the experience library as confirmed, accurate, and current
- Job descriptions are available as plain text inputs
- The user has an Anthropic API key and Claude Pro subscription
- Python 3.11+ is available in the execution environment

---

## 10. Related Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Functional Requirements | `docs/se_artifacts/requirements_functional.md` | What the system shall do |
| Non-Functional Requirements | `docs/se_artifacts/requirements_nonfunctional.md` | Quality, security, performance constraints |
| V&V Framework | `docs/se_artifacts/vv_framework.md` | Verification and validation approach |
| Requirements Traceability Matrix | `docs/se_artifacts/rtm.md` | Requirements to test mapping |
| Decisions Log | `context/DECISIONS_LOG.md` | Architecture and coding decisions |
| Project Context | `context/PROJECT_CONTEXT.md` | Project index and quick reference |
