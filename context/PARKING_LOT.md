# Parking Lot
# Load for: planning next development session, prioritizing work items
# When an Item is complete summarize in context/PARKING_LOT_DONE.md
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
  - Note: Completed Items compiled in context/PARKING_LOT_DONE.md to reduce the size of working files.