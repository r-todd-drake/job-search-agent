
# Parking Lot

__Load for: planning next development session, prioritizing work items__  
*When an Item is complete summarize in context/PARKING_LOT_DONE.md*  
Last updated: 23 Apr 2026 (items 12, 15, 16 completed; codebase cleanup items 1-4)

## Active Items

### Development

17. __URGENT — Generalize candidate data out of all scripts__ *(GitHub exposure risk)*
   - Problem: `phase3_build_candidate_profile.py` and other scripts contain hardcoded
     personal information (intro monologue, short tenure explanation, education, military
     service, clearance, confirmed gaps) that is specific to one candidate. Scripts pushed
     to GitHub expose this information and cannot be used by anyone else without modification.
   - Goal 1: Scripts should be usable by any candidate who downloads them from GitHub
   - Goal 2: All candidate-specific content must live outside tracked scripts
   - Proposed approach: design a candidate data layer — likely a combination of `.env`
     (for PII: name, contact, clearance) and a tracked template/config file
     (for career narrative: intro monologue, short tenure explanation, known facts,
     confirmed gaps) that each candidate fills in for themselves
   - Candidates to assess: how much of `KNOWN_FACTS`, `INTRO_MONOLOGUE`, and
     `SHORT_TENURE_EXPLANATION` can be externalized to `.env` vs. a YAML/markdown
     template vs. left as structured prompts for the candidate to fill in
   - Do NOT begin implementation until the data layer design is decided
   - __Interim mitigation (in progress):__ manual scrub of all scripts containing PII;
     add affected scripts to `.gitignore` until they are generalized

4. __Phase 6 — Networking support__
   - Scoped and ready to build
   - Standalone script: python scripts/phase6_networking.py --role [role]
   - Section 1: LinkedIn search guidance (queries, filters, who to look for)
   - Section 2: Connection request message (300 char limit)
   - Section 3: Follow-up message after connecting
   - Section 4: Cold outreach / InMail template
   - Section 5: Informational interview request
   - User performs LinkedIn searches manually — script provides guidance
   - Once stable: add Phase 6 reference to Phase 4 Stage 4 next steps output

5. Phase 4 Stage 4 — Add Phase 6 prompt to next steps
   - Deferred until Phase 6 is stable

8. Script identifier audit — GitHub exposure risk
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

9. check_utils.py shared module — deferred
    - Concept: extract shared logic (gap term extraction, Layer 1 rules, output formatting)
      from check_resume.py and check_cover_letter.py into scripts/utils/check_utils.py
    - Reevaluate if a third checking module is added — two checkers don't justify the abstraction

10. Phase 7 — Search agent
    - Automated role discovery: Google, USAJobs, ClearanceJobs
    - NOT LinkedIn (blocks automation)
    - Deferred — lower priority than Phase 6

11. Phase 0 — Candidate Onboarding Process documentation
    - Document the structured prompts and instructions to capture existing experinect in the form of resumes into the working experience library.

### Housekeeping

14. Create scripts/config.py — shared constants
    - 9+ scripts each hardcode the same path and model strings independently
    - Proposed constants: JOBS_PACKAGES_DIR, EXPERIENCE_LIBRARY_JSON, CANDIDATE_PROFILE_PATH,
      RESUMES_DIR, RESUME_TEMPLATE, MODEL_SONNET, MODEL_HAIKU
    - Key benefit: model version upgrade requires 1 edit instead of 9
    - Note: phase5_debrief.py intentionally uses Haiku (cost optimization) — config.py makes this explicit
    - Medium effort: requires updating all callers after extracting constants

## Standing / Evergreen Tasks

- experience library tool equivalence review**
  - After any tool clarification or correction (e.g., Cameo = MagicDraw), verify
    that affected bullets use consistent naming across all employer sections
  - Trigger: any update to the Confirmed Tools line in CANDIDATE_BACKGROUND.md
  - Goal: prevent Phase 5 false gap flags caused by naming inconsistency

## Future / Speculative Ideas

 (Not ready to scope or build — needs further refinement before moving to Active)*

- Qualitative fit assessment — design spike
  - Concept: develop a candidate profile document that describes the candidate holistically; use it as the basis for a manager-lens fit assessment against incoming JDs rather than keyword/semantic matching
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

 Note: Completed Items compiled in context/PARKING_LOT_DONE.md to reduce the size of working files.
