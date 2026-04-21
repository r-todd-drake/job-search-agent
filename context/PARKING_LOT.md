# Parking Lot
# Load for: planning next development session, prioritizing work items
Last updated: 21 Apr 2026

## Active Items

### Development

4. **Phase 6 — Networking support**
   - Scoped and ready to build
   - Standalone script: python scripts/phase6_networking.py --role [role]
   - Section 1: LinkedIn search guidance (queries, filters, who to look for)
   - Section 2: Connection request message (300 char limit)
   - Section 3: Follow-up message after connecting
   - Section 4: Cold outreach / InMail template
   - Section 5: Informational interview request
   - User performs LinkedIn searches manually — script provides guidance
   - Once stable: add Phase 6 reference to Phase 4 Stage 4 next steps output

5. **Phase 4 Stage 4 — Add Phase 6 prompt to next steps**
   - Deferred until Phase 6 is stable

8. **Script identifier audit — GitHub exposure risk**
   - Concern: hardcoded strings in scripts or comments that combine identifiers
     (company name + req number, role title, folder path, salary) could narrow
     attribution even if no direct PII is present
   - Scope: audit all committed scripts for hardcoded role-specific strings,
     example values drawn from real applications, and folder path defaults that
     include role or employer names
   - Remediation: replace with generic placeholders (e.g., [company], [role]);
     confirm example_data/ uses only fictional names and values
   - Out of scope: generic company name mentions in comments explaining script
     logic at a conceptual level — those are not a risk
   - Note: pii_filter.py, .gitignore on data/ and resumes/, and CLAUDE.md
     restrictions already cover the high-risk surface; this audit targets
     residual risk in script code and comments

9. **check_utils.py shared module — deferred**
    - Concept: extract shared logic (gap term extraction, Layer 1 rules, output formatting)
      from check_resume.py and check_cover_letter.py into scripts/utils/check_utils.py
    - Reevaluate if a third checking module is added — two checkers don't justify the abstraction

10. **Phase 7 — Search agent**
    - Automated role discovery: Google, USAJobs, ClearanceJobs
    - NOT LinkedIn (blocks automation)
    - Deferred — lower priority than Phase 6

11. **Phase 0 — Candidate Onboarding Process documentation**
    - Document the structured prompts and instructions to capture existing experinect in the form of resumes into the working experience library.

12. **Folder naming QC -- underscores throughout
    - Normalize all folder names to underscores to match file naming convention. Find-and-replace folder path strings in scripts, then rename actual directories. docs/ and context/ are low-effort (documentation only). data/job_packages/ and any role folder references in scripts are the higher-effort surface. Defer until a natural touch-point -- do not sprint this standalone.

13. **Single source of infrmation for documents with duplicative sections
    - Several project documents (README, PROJECT_CONTEXT, and others identified during the build audit) contain overlapping sections -- current phase status, project structure, script inventory, employer list, and similar reference content. When one document is updated, the others fall out of sync. There is currently no mechanism to detect or correct this drift. This feature establishes a fragment-based single-source-of-truth pattern: canonical content lives in one file, documents are assembled from fragments plus document-specific content via a build script.
    - `docs\features\single_source_documents_proposal\single_source_docs_proposal.md`
    
## Standing / Evergreen Tasks
- **Experience library tool equivalence review**
  - After any tool clarification or correction (e.g., Cameo = MagicDraw), verify
    that affected bullets use consistent naming across all employer sections
  - Trigger: any update to the Confirmed Tools line in CANDIDATE_BACKGROUND.md
  - Goal: prevent Phase 5 false gap flags caused by naming inconsistency

## Future / Speculative Ideas
*(Not ready to scope or build — needs further refinement before moving to Active)*

- **Qualitative fit assessment — design spike**
  - Concept: develop a candidate profile document that describes the candidate
    holistically; use it as the basis for a manager-lens fit assessment against
    incoming JDs rather than keyword/semantic matching
  - Flow: profile → qualitative role fit assessment → targeted evidence retrieval
    from experience library — inverting the current keyword-first approach
  - Open questions:
    - Profile structure: narrative vs. capability dimensions?
    - Primary user: job seeker tool or recruiter/hiring manager tool?
    - Relationship to candidate_profile.md rebuild (item 2) — foundation or
      separate artifact?
  - Note: may be more valuable as a complementary recruiter-facing tool than
    as a job seeker capability — needs further refinement before scoping
  - Do not begin development until design spike is complete

## Completed (recent)
- candidate_profile.md rebuild — COMPLETE (21 Apr 2026)
  Security+ flagged as (lapsed); HAIPE-enabled architectures added to KForce employer bullet and confirmed in Domain Knowledge. Profile regenerated 19 Apr 2026.
- Phase 5 HAIPE gap false positive — COMPLETE (21 Apr 2026)
  Resolved by candidate_profile.md rebuild above; HAIPE now confirmed in employer history and Domain Knowledge, preventing Phase 5 from flagging it as a gap.
- Script usage instructions updated to python -m invocation — COMPLETE (21 Apr 2026)
  Header comments and runtime print statements updated across 12 scripts + README.md. Note: build_docs.py and generate_test_fixture.py were out of scope and retain old style.
- Phase 5 prompt fixes — salary duplicate and gap fabrication guardrails — COMPLETE (21 Apr 2026)
  Salary actuals exclusivity guardrail in `_build_section1_prompt`; confirmed-skills guardrail + redirect honesty rule in `_build_gap_prompt`. Commits: 1a2c073, aa46c76. 45 tests pass.
- Experience library update workflow (a script that identifies net-new and variant resume bullets from stage files, stages them for human review) (19 Apr 2026)
  `phase4_backport.py` (full backport script (no API calls, rapidfuzz fuzzy matching))
  `generate_test_fixture.py` (one time fixture generator)
- Updated Security+ status to (lapsed), was already removed from resume generator (19 Apr 2026)
- Added UCSD Systems Engineering certificate program to CANDIDATE_BACKGROUND, phase3_build_candidate_profile.py and experience library education section (19 Apr 2026)
- Interview follow-up capture and library -- COMPLETE (Apr 2026)
  `phase5_debrief.py` (--init/--convert/--interactive), `phase5_workshop_capture.py`, `phase5_thankyou.py`, library integration in `phase5_interview_prep.py`. Full workflow in `docs/phase5_workflow_orchestration_amended.md`.
- library_parser.py last-bullet drop bug — COMPLETE (18 Apr 2026)
  Flush guard added before `## PROFESSIONAL SUMMARIES` transition; test assertion corrected 2→3; 7/7 parser tests pass
- pytest baseline setup — COMPLETE (07 Apr 2026)
  73 mock tests across utils, phases 1–5; CI via GitHub Actions; all passing on master
- Phase 4 cover letter generator — COMPLETE (07 Apr 2026)
  phase4_cover_letter.py built, refactored for testability; in Quick Reference commands
- Overmatch bullet priority flag — COMPLETE (05 Apr 2026)
  Data tagged (*PRIORITY: true*), parser updated, confirmed working in Stage 1
- Phase 5 gap detection fix — COMPLETE
  Two-tier REQUIRED/PREFERRED, full JD used, no inference from industry norms
- Phase 5 web search — COMPLETE (v2)
- Phase 5 resume bullet pull from stage files — COMPLETE (v2)
- Phase 5 .docx output — COMPLETE
- req_number tracking in jobs.csv — COMPLETE
- Duplicate req number detection in pipeline and ranking scripts — COMPLETE
- Experience library cleanup — COMPLETE (05 Apr 2026)
  G2 OPS: 158 to 118 bullets | Summaries: 48 to 26
  Overmatch theme: cleaned to 2 canonical bullets + 2 supporting themes
- Phase 3 architecture refactor — COMPLETE
  Shared library_parser.py module, single-employer re-parse script
- Claude Code setup in VS Code — COMPLETE
  CLAUDE.md configured with access restrictions
- pii_filter.py — COMPLETE (on GitHub)
- check_resume.py — COMPLETE (two-layer: string matching + API assessment)
- check_cover_letter.py — COMPLETE
- V&V framework — COMPLETE (07 Apr 2026)
  Two-tier pytest suite, CI green badge, fixture identity: Jane Q. Applicant / Acme Defense Systems
