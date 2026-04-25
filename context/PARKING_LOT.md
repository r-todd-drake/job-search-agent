
# Parking Lot

__Load for: planning next development session, prioritizing work items__  
*When an Item is complete summarize in context/PARKING_LOT_DONE.md*  
Last updated: 23 Apr 2026 (items 12, 15, 16 completed; codebase cleanup items 1-4)

## Active Items

### Development

17a. __URGENT — Remove PII from scripts; house in `context/candidate/` data store__
   - Problem: 6 scripts are gitignored because they contain hardcoded personal data
     (education, military history, certs, confirmed gaps, intro monologue, short tenure
     explanation). They need to be back on GitHub as shareable framework code.
   - Decided architecture: `context/candidate/` folder
     - Entire folder gitignored via `context/candidate/*` (single rule)
     - Exception: `context/candidate/candidate_config.example.yaml` tracked —
       blank template with comments; what a new user fills in when they clone the repo
     - `context/candidate/candidate_config.yaml` — structured career narrative:
       education, certs, military service, confirmed skills, confirmed gaps,
       intro monologue, short tenure explanation
     - `.env` — already handles scalar PII (name, phone, email, clearance, API key);
       extend with any remaining scalars not already covered
   - New loader: `scripts/utils/candidate_config.py` (tracked) — loads and exposes
     all fields from `candidate_config.yaml`; gitignored scripts import from here
     instead of defining constants locally; scripts become PII-free
   - Also move `context/CANDIDATE_BACKGROUND.md` and `context/PIPELINE_STATUS.md`
     into `context/candidate/` for complete separation of project docs from personal data
     (requires updating `.gitignore`, `CLAUDE.md`, and `PROJECT_CONTEXT.md` references)
   - Refactor order: (1) audit 5 remaining gitignored scripts to inventory all hardcoded
     PII; (2) design `candidate_config.yaml` schema to cover all fields; (3) build loader;
     (4) refactor scripts one at a time and restore to git tracking as each is cleaned
   - Sets up the 17b pattern naturally: `context/domain/` for domain config
   - Can proceed concurrently with 17b — they touch different parts of the codebase
   - Design summary: `docs/superpowers/specs/2026-04-25-candidate-data-store.md`
   - __Interim:__ affected scripts remain gitignored until refactored

17b. __NOT URGENT — Generalize domain-specific vocabulary and prompt language__
   - Problem: tag lists, keyword sets, and prompt language are tuned for defense SE;
     the pipeline cannot serve a different domain without modifying scripts directly
   - Examples: `data/interview_library_tags.json` (20-tag defense vocabulary),
     system prompt phrases like "defense and aerospace", "TS/SCI", "MBSE" in Phase 4/5
   - Goal: `context/domain/domain_config.yaml` (gitignored) holds all domain-specific
     config; `context/domain/domain_config.example.yaml` (tracked) ships as blank template
   - Pattern mirrors 17a — do NOT begin until 17a loader design is finalized, since
     the same pattern will apply

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
