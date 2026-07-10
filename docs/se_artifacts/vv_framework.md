# Verification and Validation Framework
# AI Job Search Agent
Version 1.0 | April 2026

Parent document: `docs/se_artifacts/conops.md`
Sibling documents: `docs/se_artifacts/requirements_functional.md`, `docs/se_artifacts/requirements_nonfunctional.md`

---

## 1. Purpose and Scope

This document defines the verification and validation framework for the AI Job Search Agent and provides the Requirements Traceability Matrix (RTM) mapping every functional and non-functional requirement to its verification method and evidence.

**Verification** confirms that the system was built correctly -- that each requirement is satisfied by the implementation.

**Validation** confirms that the system was built for the right purpose -- that the pipeline, taken as a whole, delivers the desired effect defined in the ConOps.

---

## 2. Verification Methods

Four verification methods are used. Each requirement is assigned the most appropriate method based on the nature of the requirement.

| Method | Code | Definition | Application |
|--------|------|------------|-------------|
| Test | T | Execution of the system or a component against defined inputs, with pass/fail criteria checked against expected outputs. | Functional behavior, output structure, error handling, PII stripping, data integrity. |
| Inspection | I | Review of source code, configuration files, documentation, or output artifacts against defined criteria. | Naming conventions, file structure, git configuration, documentation completeness, hardcoded value checks. |
| Analysis | A | Examination of system behavior, design decisions, or outputs using reasoning, calculation, or tracing -- without executing the system. | Architectural constraints, traceability claims, count assertions, dependency relationships. |
| Demonstration | D | Execution of the system in its operational context to show that it behaves as intended, observed by the verifier. | End-to-end workflow execution, human-in-the-loop touchpoints, usability behaviors, CLI behavior. |

---

## 3. Verification Tiers

The existing pytest suite provides the primary verification mechanism. It is structured in two tiers:

| Tier | Command | Trigger | Purpose |
|------|---------|---------|---------|
| Tier 1 -- Mock | `pytest tests/ -m "not live" -v` | Every commit, CI via GitHub Actions | Verifies functional behavior without API calls. No API key required. |
| Tier 2 -- Live | `pytest -m live -v` | Before promoting a phase, after API changes | Verifies API integration with real Anthropic API calls. Requires `ANTHROPIC_API_KEY`. |

All Tier 1 tests must pass before any commit to main. Tier 2 tests are run manually at defined promotion gates.

---

## 4. Validation Approach

Validation operates at the system level and confirms the desired effect from the ConOps:

> A job seeker maximizes the probability of securing a qualified position by producing consistently high-quality, accurately tailored application materials and interview preparation at a pace and volume that manual effort cannot sustain -- without sacrificing accuracy or introducing fabricated experience.

Validation is assessed against four observable outcomes:

| Validation Criterion | Evidence |
|----------------------|----------|
| VC-1: Decision quality | Phase 2 ranking and semantic analysis outputs demonstrably inform PURSUE / CONSIDER / SKIP decisions. User can articulate fit rationale grounded in scores. |
| VC-2: Output accuracy | Generated resumes and cover letters contain no fabricated claims. All content traceable to experience library. Quality checker scripts pass without violations. |
| VC-3: Interview readiness | Interview prep packages are stage-appropriate, contain employer-attributed STAR stories, and surface real gaps with honest responses. |
| VC-4: Throughput | User can process multiple simultaneous applications without degradation in output quality relative to single-application baseline. |

Validation is not automated -- it is assessed by the operator through use. The system's operational history (applications submitted, interviews secured, interview stages advanced) constitutes the primary validation evidence.

---

## 5. Requirements Traceability Matrix

### 5.1 Legend

| Column | Description |
|--------|-------------|
| ID | Requirement identifier |
| Method | T = Test, I = Inspection, A = Analysis, D = Demonstration |
| Tier | 1 = Mock test suite, 2 = Live API test, I = Inspection/manual, D = Demonstration |
| Evidence | Test file, script, artifact, or observation that satisfies the requirement |
| Status | Pass / Partial / Open |

**Status definitions:**
- **Pass** -- requirement is fully satisfied by existing implementation and evidence
- **Partial** -- requirement is partially satisfied; gap noted
- **Open** -- requirement is not yet satisfied or not yet verified

---

### 5.2 Functional Requirements Traceability

#### Capability 1 -- Candidate Data Management

| ID | Method | Tier | Evidence | Status |
|----|--------|------|----------|--------|
| FR-001 | I | I | `data/experience_library/experience_library.md` exists as human-editable source. JSON is compiled output only. | Pass |
| FR-002 | T | 1 | `tests/phase3/test_compile_library.py`, `tests/utils/test_library_parser.py` | Pass |
| FR-003 | T | 1 | `tests/phase3/test_parse_employer.py` | Pass |
| FR-004 | T | 1 | `tests/phase3/test_build_candidate_profile.py` | Pass |
| FR-005 | T | 1 | `tests/utils/test_library_parser.py` -- `test_parse_library_bullet_ids_assigned` | Pass |
| FR-006 | T | 1 | `tests/utils/test_library_parser.py` -- `test_parse_library_priority_bullet_flagged` | Pass |
| FR-007 | T | 1 | `tests/utils/test_library_parser.py` -- VERIFY metadata parsing | Pass |
| FR-008 | T | 1 | `tests/utils/test_library_parser.py` -- `test_parse_library_bullet_count_matches_source`. Fixed Apr 2026. | Pass |
| FR-009 | A | I | Bullet count discrepancy detection -- currently implicit via FR-008 test. Explicit reporting not yet implemented. | Partial |
| FR-010 | I | I | `Used in:` metadata present in library source. Not currently machine-validated. | Partial |

#### Capability 2 -- Role Ingestion and Pipeline Management

| ID | Method | Tier | Evidence | Status |
|----|--------|------|----------|--------|
| FR-011 | I | I | `jobs.csv` schema defined in DECISIONS_LOG. Manually populated by user. | Pass |
| FR-012 | T | 1 | `tests/phase1/test_pipeline_report.py` | Pass |
| FR-013 | T | 1 | `tests/phase1/test_pipeline_report.py` -- duplicate req detection. `tests/phase2/test_job_ranking.py` -- duplicate detection in ranking. | Pass |
| FR-014 | T | 1 | `tests/phase1/test_pipeline_report.py` -- tracker read | Pass |
| FR-015 | T | 1 | `tests/phase2/test_job_ranking.py` -- status value handling | Pass |
| FR-016 | T | 1 | `tests/phase2/test_job_ranking.py` -- actionable status filter | Pass |

#### Capability 3 -- Role Ranking and Fit Analysis

| ID | Method | Tier | Evidence | Status |
|----|--------|------|----------|--------|
| FR-017 | T | 1 | `tests/phase2/test_job_ranking.py` -- keyword scoring | Pass |
| FR-018 | T | 2 | `tests/phase2/test_semantic_analyzer.py` -- live API required for full validation | Pass |
| FR-019 | T | 1 | `tests/phase2/test_semantic_analyzer.py` -- report output | Pass |
| FR-020 | T | 1 | `tests/phase2/test_semantic_analyzer.py` -- SKIP status filter | Pass |
| FR-021 | D | D | Ranked output format reviewed during operational use. | Pass |

#### Capability 4 -- Resume Generation

| ID | Method | Tier | Evidence | Status |
|----|--------|------|----------|--------|
| FR-022 | T | 1 | `tests/phase4/test_resume_generator.py` -- Stage 1 bullet selection | Pass |
| FR-023 | T | 1 | `tests/phase4/test_resume_generator.py` -- priority bullet inclusion | Pass |
| FR-024 | T | 1 | `tests/phase4/test_resume_generator.py` -- `test_run_stage1_creates_draft_file` verifies file creation and presence of SUMMARY and EXPERIENCE sections. CORE COMPETENCIES section present in mock response but not explicitly asserted in test. | Partial |
| FR-025 | T | 1 | `tests/phase4/test_resume_generator.py` -- `test_run_stage1_creates_draft_file` asserts "SUMMARY" in output. Section presence verified; library sourcing not tested -- mock uses hardcoded response, not library selection logic. | Partial |
| FR-026 | T | 1 | `tests/phase4/test_resume_generator.py` -- Stage 3 coherence check | Pass |
| FR-027 | T | 1 | `tests/phase4/test_resume_generator.py` -- Stage 4 .docx generation | Pass |
| FR-028 | I | I | Stage files are source of truth by convention. .docx generated from stage file, never edited directly. Enforced by DECISIONS_LOG and CLAUDE.md. | Pass |
| FR-029 | T + A | 1 | `tests/phase4/test_check_resume.py` -- fabrication detection. Analysis: all Stage 1 inputs sourced from library. | Pass |
| FR-030 | T | 2 | `tests/phase4/test_resume_generator.py` -- Stage 3 wording suggestions. Full validation requires live API. | Pass |

#### Capability 5 -- Cover Letter Generation

| ID | Method | Tier | Evidence | Status |
|----|--------|------|----------|--------|
| FR-031 | T | 1 | `tests/phase4/test_cover_letter.py` -- Stage 1 draft generation | Pass |
| FR-032 | T | 1 | `tests/phase4/test_cover_letter.py` -- `test_run_cl_stage1_creates_draft_file` verifies file creation (len > 50). No test verifies application paragraph as a separate section or enforces 150--250 word count constraint. | Partial |
| FR-033 | T | 1 | `tests/phase4/test_cover_letter.py` -- hiring manager name extraction | Pass |
| FR-034 | T | 1 | `tests/phase4/test_cover_letter.py` -- gap filter incorporation | Pass |
| FR-035 | T | 1 | `tests/phase4/test_cover_letter.py` -- Stage 4 .docx two-page structure | Pass |
| FR-036 | T + A | 1 | `tests/phase4/test_check_cover_letter.py` -- fabrication detection. Analysis: all Stage 1 inputs sourced from library. | Pass |

#### Capability 6 -- Quality Control

| ID | Method | Tier | Evidence | Status |
|----|--------|------|----------|--------|
| FR-037 | T | 1 | `tests/phase4/test_check_resume.py` -- string matching layer | Pass |
| FR-038 | T | 1 | `tests/phase4/test_check_resume.py` -- API assessment layer | Pass |
| FR-039 | T | 1 | `tests/phase4/test_check_cover_letter.py` -- two-layer check | Pass |
| FR-040 | T | 1 | `tests/phase4/test_check_resume.py` -- em dash detection. `tests/phase4/test_check_cover_letter.py` -- em dash detection. | Pass |
| FR-041 | T | 1 | `tests/phase4/test_check_resume.py` -- lapsed certification flag. `tests/phase4/test_check_cover_letter.py` -- lapsed certification flag. | Pass |
| FR-042 | T | 1 | `tests/phase4/test_check_cover_letter.py` -- generic opener detection | Pass |
| FR-043 | T | 1 | `tests/phase4/test_check_resume.py` -- gap-filling language flag. `tests/phase4/test_check_cover_letter.py` -- gap-filling language flag. | Pass |

#### Capability 7 -- Interview Preparation

| ID | Method | Tier | Evidence | Status |
|----|--------|------|----------|--------|
| FR-044 | T | 1 | `tests/phase5/test_interview_prep.py` -- prep package generation | Pass |
| FR-045 | T | 1 | `tests/phase5/test_interview_prep.py` -- stage differentiation | Pass |
| FR-046 | T | 2 | `tests/phase5/test_interview_prep.py` -- STAR story generation. Full employer attribution requires live API validation. | Pass |
| FR-047 | T | 1 | `tests/phase5/test_interview_prep.py` -- two-tier gap analysis, full JD input | Pass |
| FR-048 | T | 1 | `tests/phase5/test_interview_prep.py` -- salary extraction and anchoring | Pass |
| FR-049 | T | 2 | `tests/phase5/test_interview_prep.py` -- web search integration. Live API required for full validation. | Pass |
| FR-050 | T | 1 | `tests/phase5/test_interview_prep.py` -- .txt and .docx output | Pass |
| FR-051 | T | 1 | `tests/phase5/test_interview_prep.py` -- stage-specific file naming, no collision | Pass |
| FR-052 | T | 1 | `tests/phase5/test_interview_prep.py` -- stage file fallback logic | Pass |

#### Capability 8 -- Post-Interview Capture

| ID | Method | Tier | Evidence | Status |
|----|--------|------|----------|--------|
| FR-053 | T | 1 | `tests/test_phase5_debrief.py` -- structured debrief capture | Pass |
| FR-054 | T | 1 | `tests/test_phase5_debrief.py` -- interactive and YAML workflow modes | Pass |
| FR-055 | T | 2 | `tests/test_phase5_debrief.py` -- AI follow-up question generation. Live API required. | Pass |
| FR-056 | T | 1 | `tests/test_phase5_thankyou.py` -- thank-you letter generation per interviewer | Pass |
| FR-057 | T | 1 | `tests/test_phase5_thankyou.py` -- panel label support | Pass |
| FR-058 | T | 1 | `tests/test_phase5_workshop_capture.py` -- story, gap, question persistence | Pass |
| FR-059 | T | 1 | `tests/test_phase5_workshop_capture.py` -- additive write, no destructive overwrite | Pass |

#### Capability 9 -- Security and Privacy

| ID | Method | Tier | Evidence | Status |
|----|--------|------|----------|--------|
| FR-060 | T | 1 | `tests/utils/test_pii_filter.py` -- PII stripping across all call paths | Pass |
| FR-061 | I | I | `.env` excluded from version control. `pii_filter.py` uses `os.getenv()` -- no hardcoded values. | Pass |
| FR-062 | I | I | `.gitignore` covers `data/`, `resumes/`, `outputs/`, `.env`, candidate background files. | Pass |
| FR-063 | T | 1 | `tests/utils/test_pii_filter.py` -- PII stripping in interactive debrief mode | Pass |

#### Capability 10 -- Human-in-the-Loop Workflow

| ID | Method | Tier | Evidence | Status |
|----|--------|------|----------|--------|
| FR-064 | D | D | Phase 1 status assignment workflow demonstrated during operational use. No role proceeds without assigned status. | Pass |
| FR-065 | D | D | Stage 2 resume review demonstrated during operational use. `stage2_approved.txt` required for Stage 3 to proceed. | Pass |
| FR-066 | D | D | Stage 2 cover letter review demonstrated during operational use. `cl_stage2_approved.txt` required for Stage 3 to proceed. | Pass |
| FR-067 | A | I | System has no submission capability by design. No script contains application submission logic. | Pass |
| FR-068 | T | 1 | `tests/phase4/test_resume_generator.py` -- overwrite protection. `tests/phase4/test_cover_letter.py` -- overwrite protection. | Pass |

#### Capability 11 -- System Integrity

| ID | Method | Tier | Evidence | Status |
|----|--------|------|----------|--------|
| FR-069 | I + T | 1 | `pytest.ini`, `tests/` directory structure, `.github/workflows/test.yml` -- two-tier suite confirmed. | Pass |
| FR-070 | T | 1 | CI badge on README. 304 mock tests passing as of Apr 2026. | Pass |
| FR-071 | T | 1 | `tests/phase4/test_check_resume.py` -- em dash enforcement. `tests/phase4/test_check_cover_letter.py` -- em dash enforcement. | Pass |
| FR-072 | I | I | Model string `claude-sonnet-4-20250514` defined in DECISIONS_LOG. Consistent across all phase scripts. | Pass |
| FR-073 | I | I | `CLAUDE.md` naming convention. Verify during Parking Lot folder QC item. | Partial |
| FR-074 | D | D | All scripts executable from project root via `python scripts/[script].py`. Confirmed during operational use. | Pass |
| FR-075 | T | 1 | pytest run on Python 3.14.3 -- 304 tests pass. Minimum floor remains 3.11+. | Pass |

---

### 5.3 Non-Functional Requirements Traceability

#### Performance

| ID | Method | Tier | Evidence | Status |
|----|--------|------|----------|--------|
| NFR-001 | T | 1 | `tests/phase2/test_semantic_analyzer.py` -- status filter before API call | Pass |
| NFR-002 | T | 1 | `tests/utils/test_pii_filter.py` -- PII stripped before API call | Pass |
| NFR-003 | D | D | Stage generation time observed during operational use. Terminal progress output present. | Pass |
| NFR-004 | D | D | Interview prep generation time observed during operational use. Web search latency expected and documented. | Pass |
| NFR-005 | A + I | I | Stage files read by downstream stages -- no re-generation. Confirmed by inspection of phase4 and phase5 script logic. | Pass |

#### Reliability

| ID | Method | Tier | Evidence | Status |
|----|--------|------|----------|--------|
| NFR-006 | T | 1 | Output file naming and structure consistent across test runs. Stage sequence enforced by script logic. | Pass |
| NFR-007 | T | 1 | `tests/utils/test_library_parser.py` -- `test_parse_library_bullet_count_matches_source`. Fixed Apr 2026. | Pass |
| NFR-008 | T | 1 | `tests/phase1/test_pipeline_report.py`, `tests/phase2/test_job_ranking.py` -- duplicate req detection | Pass |
| NFR-009 | T | 1 | `tests/phase4/test_resume_generator.py`, `tests/phase4/test_cover_letter.py` -- overwrite protection | Pass |
| NFR-010 | I | I | Progress output present in phase2, phase4, phase5 scripts. Confirmed by inspection. | Pass |
| NFR-011 | T | 1 | Error handling tested across phase scripts. No silent failures in test suite. | Pass |
| NFR-012 | T | 1 | `tests/phase5/test_interview_prep.py` -- stage file fallback logic | Pass |

#### Security

| ID | Method | Tier | Evidence | Status |
|----|--------|------|----------|--------|
| NFR-013 | I | I | `.env` excluded from git. All scripts use `os.getenv()`. `pii_filter.py` confirmed on GitHub -- no personal data. | Pass |
| NFR-014 | I | I | `.gitignore` covers all personal data directories. Verified dot prefix present. | Pass |
| NFR-015 | T | 1 | `tests/utils/test_pii_filter.py` -- PII stripping confirmed across all API call paths | Pass |
| NFR-016 | I | I | API responses written to stage files. No raw response logging in any phase script. Confirmed by inspection. | Pass |
| NFR-017 | I | I | `CLAUDE.md` defines access restrictions. `.gitignore` does not restrict Claude Code -- CLAUDE.md is the correct boundary. | Pass |
| NFR-018 | I | I | Parking Lot item 9 -- script identifier audit. Not yet complete. | Open |

#### Maintainability

| ID | Method | Tier | Evidence | Status |
|----|--------|------|----------|--------|
| NFR-019 | I + T | 1 | `pytest.ini`, `tests/` structure, `requirements-dev.txt`, `.github/workflows/test.yml` | Pass |
| NFR-020 | T | 1 | 304 mock tests passing as of Apr 2026. CI green badge on README. | Pass |
| NFR-021 | T | 1 | All phase scripts importable without side effects. Confirmed by pytest import in all test files. | Pass |
| NFR-022 | I | I | `library_parser.py`, `pii_filter.py`, `debrief_utils.py`, `interview_library_parser.py` exist as shared modules. | Pass |
| NFR-023 | I | I | `pii_filter.py` used across all phases. No per-script PII stripping reimplementation. | Pass |
| NFR-024 | I | I | `DECISIONS_LOG.md` current as of Apr 2026. Architecture decisions documented at decision time. | Pass |
| NFR-025 | I | I | `CLAUDE.md` git safety rules documented with incident context. Explicit prohibition on `git add .` without safety check. | Pass |
| NFR-026 | I | I | `conftest.py` uses Jane Q. Applicant / Acme Defense Systems / ADS-12345. No real candidate data in `tests/fixtures/`. | Pass |
| NFR-027 | A | I | Two checker scripts exist. Abstraction deferred until third checker added. Decision documented in Parking Lot. | Pass |

#### Usability

| ID | Method | Tier | Evidence | Status |
|----|--------|------|----------|--------|
| NFR-028 | D | D | All scripts run from project root during operational use. Confirmed. | Pass |
| NFR-029 | I | I | `argparse` used in all phase scripts. `--help` available on all scripts. | Pass |
| NFR-030 | D | D | Phase 5 interactive stage prompt confirmed during operational use. | Pass |
| NFR-031 | T | 1 | `tests/phase5/test_interview_prep.py` -- `--dry_run` flag behavior | Pass |
| NFR-032 | I | I | Stage files are plain text. Readable and editable in VS Code without tooling. | Pass |
| NFR-033 | T | 1 | `tests/phase5/test_interview_prep.py` -- stage label in output file header | Pass |
| NFR-034 | I | I | Output file naming conventions confirmed by inspection of phase4 and phase5 output paths. | Pass |

#### Portability

| ID | Method | Tier | Evidence | Status |
|----|--------|------|----------|--------|
| NFR-035 | T | 1 | 304 tests pass on Python 3.14.3. Minimum floor 3.11+ confirmed by syntax compliance. | Pass |
| NFR-036 | I | I | `requirements.txt` and `requirements-dev.txt` present and current. | Pass |
| NFR-037 | I | I | `.env.example` present with all required variable names and no real values. | Pass |
| NFR-038 | I | I | `example_data/` uses fictional identities. Jane Q. Applicant / Acme Defense Systems throughout. | Pass |
| NFR-039 | A | I | No OS-specific path separators or shell dependencies in script logic. `os.path` and `pathlib` used consistently. | Pass |
| NFR-040 | I | I | Parking Lot item 12 -- Phase 0 onboarding documentation not yet complete. | Open |

---

## 6. Verification Status Summary

### Functional Requirements

| Capability Area | Total | Pass | Partial | Open |
|-----------------|-------|------|---------|------|
| 1. Candidate Data Management | 10 | 8 | 2 | 0 |
| 2. Role Ingestion and Pipeline Management | 6 | 6 | 0 | 0 |
| 3. Role Ranking and Fit Analysis | 5 | 5 | 0 | 0 |
| 4. Resume Generation | 9 | 7 | 2 | 0 |
| 5. Cover Letter Generation | 6 | 5 | 1 | 0 |
| 6. Quality Control | 7 | 7 | 0 | 0 |
| 7. Interview Preparation | 9 | 9 | 0 | 0 |
| 8. Post-Interview Capture | 7 | 7 | 0 | 0 |
| 9. Security and Privacy | 4 | 4 | 0 | 0 |
| 10. Human-in-the-Loop Workflow | 5 | 5 | 0 | 0 |
| 11. System Integrity | 7 | 6 | 1 | 0 |
| **Total** | **75** | **69** | **6** | **0** |

### Non-Functional Requirements

| Category | Total | Pass | Partial | Open |
|----------|-------|------|---------|------|
| 1. Performance | 5 | 5 | 0 | 0 |
| 2. Reliability | 7 | 7 | 0 | 0 |
| 3. Security | 6 | 5 | 0 | 1 |
| 4. Maintainability | 9 | 9 | 0 | 0 |
| 5. Usability | 7 | 7 | 0 | 0 |
| 6. Portability | 6 | 5 | 0 | 1 |
| **Total** | **40** | **38** | **0** | **2** |

### Combined Summary

| Status | FR | NFR | Total |
|--------|----|-----|-------|
| Pass | 69 | 38 | 107 |
| Partial | 6 | 0 | 6 |
| Open | 0 | 2 | 2 |
| **Total** | **75** | **40** | **115** |

---

## 7. Open and Partial Items

| ID | Type | Description | Resolution Path |
|----|------|-------------|-----------------|
| FR-009 | Partial | Bullet count discrepancy detection is implicit via FR-008 test -- no explicit reporting implemented. | Implement explicit count reporting in `phase3_parse_library.py` output. |
| FR-010 | Partial | `Used in:` metadata present in library source but not machine-validated. | Add validation step to library parse output or Phase 3 QC report. |
| FR-024 | Partial | `test_run_stage1_creates_draft_file` does not assert "CORE COMPETENCIES" in output. Section present in mock response but not explicitly verified. | Add explicit assertion for CORE COMPETENCIES section. Parking Lot item 14. |
| FR-025 | Partial | Summary section presence verified but library sourcing not tested -- mock response used, not library selection logic. | Add test that verifies summary is drawn from compiled library summaries section. Parking Lot item 14. |
| FR-032 | Partial | No test verifies application paragraph as a separate section or enforces 150--250 word count constraint. | Add explicit paragraph section check and word count assertion. Parking Lot item 14. |
| FR-073 | Partial | Folder naming convention (underscores) not yet fully applied across all directories. | Parking Lot item 13 -- normalize during next natural touch-point. |
| NFR-018 | Open | Script identifier audit not yet complete. Residual risk of hardcoded role-specific strings in committed scripts. | Parking Lot item 9 -- complete audit before next GitHub push of new scripts. |
| NFR-040 | Open | Phase 0 onboarding documentation not yet produced. | Parking Lot item 12 -- structured prompts and instructions for experience extraction. |

---

## 8. Related Documents

| Document | Location | Purpose |
|----------|----------|---------|
| ConOps | `docs/se_artifacts/conops.md` | Operational context and system concept |
| Functional Requirements | `docs/se_artifacts/requirements_functional.md` | What the system shall do |
| Non-Functional Requirements | `docs/se_artifacts/requirements_nonfunctional.md` | Quality, security, performance constraints |
| Decisions Log | `context/DECISIONS_LOG.md` | Architecture and coding decisions |
| Project Context | `context/PROJECT_CONTEXT.md` | Project index and quick reference |
