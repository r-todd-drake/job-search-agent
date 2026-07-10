# Non-Functional Requirements
# AI Job Search Agent
Version 1.0 | April 2026

Parent document: `docs/se_artifacts/conops.md`
Sibling document: `docs/se_artifacts/requirements_functional.md`

---

## Overview

This document defines the non-functional requirements for the AI Job Search Agent. These requirements constrain how the system behaves rather than what it does. They apply across all pipeline phases unless a specific phase is noted.

Requirements use mixed modal verb convention: **shall** denotes a hard requirement; **should** denotes preferred behavior where some implementation flexibility exists.

Each requirement carries the following attributes:

| Attribute | Description |
|-----------|-------------|
| ID | NFR-[seq] -- flat sequential across all capability areas |
| Statement | What the system shall or should do |
| Category | Capability area this requirement belongs to |
| Phase | Pipeline phase(s) where this requirement applies |
| Priority | High / Medium / Low |
| Notes | Clarifications, constraints, or known limitations |

---

## Category Areas

1. [Performance](#1-performance)
2. [Reliability](#2-reliability)
3. [Security](#3-security)
4. [Maintainability](#4-maintainability)
5. [Usability](#5-usability)
6. [Portability](#6-portability)

---

## 1. Performance

*Covers API efficiency, token usage, and pipeline execution time.*

| ID | Statement | Category | Phase | Priority | Notes |
|----|-----------|----------|-------|----------|-------|
| NFR-001 | The system shall restrict semantic analysis API calls to roles with actionable status values (PURSUE, CONSIDER) only. | Performance | 2 | High | Prevents unnecessary API spend on SKIP or unreviewed roles. Enforced by status filter before API call. |
| NFR-002 | The system shall strip PII from all content before API calls, keeping prompt payloads to the minimum necessary. | Performance | All | High | PII stripping also reduces token count in prompts. |
| NFR-003 | The system should complete a single-stage resume generation run (Stage 1 or Stage 3) within a time that does not interrupt the user's workflow. | Performance | 4 | Medium | No hard SLA -- async execution with terminal progress output is the current implementation. |
| NFR-004 | The system should complete a full interview prep package generation within a time that does not interrupt the user's workflow. | Performance | 5 | Medium | Web search adds latency -- progress output required so the user knows the script is running. |
| NFR-005 | The system shall not make redundant API calls for content already generated in a prior stage. | Performance | 4, 5 | High | Stage files are the source of truth -- downstream stages read from files, not re-generate. |

---

## 2. Reliability

*Covers output consistency, error handling, and data integrity.*

| ID | Statement | Category | Phase | Priority | Notes |
|----|-----------|----------|-------|----------|-------|
| NFR-006 | The system shall produce deterministic output structure across repeated runs for the same inputs. | Reliability | All | High | Output content may vary by API response, but file structure, naming, and stage sequence shall be consistent. |
| NFR-007 | The system shall not silently discard data during library parsing. | Reliability | 3 | High | All bullets in the markdown source shall appear in the compiled JSON. Resolved by library_parser.py fix (Apr 2026). |
| NFR-008 | The system shall detect and report duplicate requisition numbers before processing proceeds. | Reliability | 1, 2 | High | Prevents duplicate applications. Detection runs in both Phase 1 and Phase 2. |
| NFR-009 | The system shall provide overwrite protection with a confirmation prompt when output files already exist. | Reliability | All | High | Prevents accidental overwrite of human-approved stage files. |
| NFR-010 | The system shall report progress to the terminal during long-running API operations. | Reliability | 2, 4, 5 | Medium | User must be able to distinguish a running script from a hung one. |
| NFR-011 | The system shall handle API errors gracefully and report them to the user without silent failure. | Reliability | All | High | No silent failures -- all API errors surfaced to terminal. |
| NFR-012 | The system shall fall back to an available earlier stage file when the preferred stage file is not present. | Reliability | 5 | Medium | Phase 5 falls back to `stage2_approved.txt` if `stage4_final.txt` is not present. |

---

## 3. Security

*Covers PII protection, credential management, and data exposure.*

| ID | Statement | Category | Phase | Priority | Notes |
|----|-----------|----------|-------|----------|-------|
| NFR-013 | The system shall store all credentials and PII values in environment variables loaded at runtime. | Security | All | High | `.env` file -- never committed. No credentials or PII hardcoded in source. |
| NFR-014 | The system shall exclude all personal data from version control via `.gitignore`. | Security | All | High | Covers experience library, resumes, job packages, tracker, candidate background, and debrief files. |
| NFR-015 | The system shall strip all PII from content before any data leaves the local machine via API call. | Security | All | High | `pii_filter.py` enforces this at runtime. Applies to all phases including interactive debrief mode. |
| NFR-016 | The system shall not log, cache, or persist raw API responses containing PII. | Security | All | High | API responses written to stage files only after PII stripping is confirmed. |
| NFR-017 | The system shall restrict Claude Code file system access to non-personal directories via `CLAUDE.md`. | Security | All | High | `CLAUDE.md` is the correct access control boundary -- `.gitignore` does not restrict Claude Code. |
| NFR-018 | The system should audit committed scripts for hardcoded role-specific strings or example values drawn from real applications. | Security | All | Medium | Parking Lot item 9. Residual risk after PII filter and gitignore controls. |

---

## 4. Maintainability

*Covers code structure, testability, documentation, and change management.*

| ID | Statement | Category | Phase | Priority | Notes |
|----|-----------|----------|-------|----------|-------|
| NFR-019 | The system shall maintain a two-tier automated test suite with mock and live API tiers covering all pipeline phases. | Maintainability | All | High | Tier 1: no API key required, runs in CI. Tier 2: live API, run before promoting a phase. |
| NFR-020 | The system shall pass all Tier 1 mock tests before any commit to the main branch. | Maintainability | All | High | CI enforced via GitHub Actions. 308+ tests as of Apr 2026. |
| NFR-021 | All pipeline scripts shall be importable as modules without executing top-level side effects. | Maintainability | All | High | Required for pytest testability. Module-level execution removed from all phase scripts. |
| NFR-022 | Shared parsing and utility logic shall be extracted to importable modules rather than duplicated across scripts. | Maintainability | All | Medium | `library_parser.py`, `pii_filter.py`, `debrief_utils.py`, `interview_library_parser.py`. |
| NFR-023 | The system shall use a single shared utility for PII stripping across all scripts. | Maintainability | All | High | `pii_filter.py` -- not reimplemented per script. |
| NFR-024 | Architecture and coding decisions shall be documented in `DECISIONS_LOG.md` at the time the decision is made. | Maintainability | All | Medium | Decisions log is the authoritative record of why the system is built the way it is. |
| NFR-025 | The system shall use explicit git staging. `git add .` is prohibited. | Maintainability | All | Medium | Enforced via CLAUDE.md with explicit safety rationale. Claude Code may use `git add .` only after running `git status` and verifying no forbidden files are staged. Policy documented following a prior incident where a misnamed `.gitignore` caused personal data and API keys to be pushed to GitHub. |
| NFR-026 | The system shall maintain fixture identity separate from candidate identity in all test data. | Maintainability | All | High | Test fixture identity: Jane Q. Applicant / Acme Defense Systems / ADS-12345. No real candidate data in tests. |
| NFR-027 | The system should extract shared quality-checking logic into a common utility module if a third checking script is added. | Maintainability | All | Low | Deferred -- two checkers do not justify the abstraction. Reevaluate at three. |

---

## 5. Usability

*Covers the operator experience -- how the system behaves from the user's perspective.*

| ID | Statement | Category | Phase | Priority | Notes |
|----|-----------|----------|-------|----------|-------|
| NFR-028 | All scripts shall be executable from the project root without path manipulation. | Usability | All | High | `python scripts/[script].py` -- consistent across all phases. |
| NFR-029 | All scripts shall use `argparse` for CLI argument handling. | Usability | All | Medium | Enables `--help` on every script. Consistent interface across pipeline. |
| NFR-030 | Scripts with required arguments shall prompt interactively when those arguments are omitted rather than failing silently. | Usability | All | Medium | Phase 5 interview stage prompt is the reference implementation. |
| NFR-031 | The system shall support a `--dry_run` flag on scripts where API calls are expensive, to validate configuration without making API calls. | Usability | 5 | Medium | Implemented on `phase5_interview_prep.py`. |
| NFR-032 | Stage files shall be human-readable plain text suitable for review and editing in VS Code. | Usability | 4, 5 | High | Stage files are the primary human interaction surface -- not the .docx outputs. |
| NFR-033 | The system shall write stage label and description to the header of interview prep output files so the register is immediately clear on opening. | Usability | 5 | Medium | User may open multiple stage files -- header prevents confusion. |
| NFR-034 | The system should produce output file names that are self-describing and include role, stage, and date where applicable. | Usability | All | Medium | Enables navigation without opening files. e.g. `debrief_hiring_manager_2026-04-15_filed-2026-04-15.json`. |

---

## 6. Portability

*Covers environment compatibility, dependency management, and transferability to a new user.*

| ID | Statement | Category | Phase | Priority | Notes |
|----|-----------|----------|-------|----------|-------|
| NFR-035 | The system shall be compatible with Python 3.11 and above. | Portability | All | High | No backslash escapes inside f-string expressions. No syntax requiring 3.12+. |
| NFR-036 | The system shall declare all runtime dependencies in `requirements.txt` and all test dependencies in `requirements-dev.txt`. | Portability | All | High | Separate files allow production installs without test tooling. |
| NFR-037 | The system shall provide an `.env.example` file documenting all required environment variables without containing real values. | Portability | All | High | Enables a new user to configure the system without reading source code. |
| NFR-038 | The system shall provide example data using fictional identities that demonstrate pipeline behavior without exposing real candidate data. | Portability | All | Medium | `example_data/` -- fictional names and values only. Jane Q. Applicant / Acme Defense Systems. |
| NFR-039 | The system shall be operable on any platform supporting Python 3.11+ without OS-specific dependencies. | Portability | All | Medium | No platform-specific path separators or shell dependencies in script logic. |
| NFR-040 | The candidate onboarding process (Phase 0) shall be documented sufficiently for a new user to build a working experience library without developer assistance. | Portability | 0 | Medium | Parking Lot item 12. Deliverable: structured prompts and instructions for capturing existing resume experience into the working library format. Current implementation is semi-manual. |

---

## Requirements Summary

| Category | Count | High | Medium | Low |
|----------|-------|------|--------|-----|
| 1. Performance | 5 | 3 | 2 | 0 |
| 2. Reliability | 7 | 5 | 2 | 0 |
| 3. Security | 6 | 5 | 1 | 0 |
| 4. Maintainability | 9 | 5 | 3 | 1 |
| 5. Usability | 7 | 2 | 5 | 0 |
| 6. Portability | 6 | 3 | 3 | 0 |
| **Total** | **40** | **23** | **16** | **1** |

---

## Related Documents

| Document | Location | Purpose |
|----------|----------|---------|
| ConOps | `docs/se_artifacts/conops.md` | Operational context and system concept |
| Functional Requirements | `docs/se_artifacts/requirements_functional.md` | What the system shall do |
| V&V Framework and RTM | `docs/se_artifacts/vv_framework.md` | Verification and validation approach; requirements traceability matrix |
| Decisions Log | `context/DECISIONS_LOG.md` | Architecture and coding decisions |
