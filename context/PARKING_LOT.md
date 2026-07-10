
# Parking Lot

__Load for: planning next development session, prioritizing work items__  
*When an Item is complete summarize in context/PARKING_LOT_DONE.md*  
Last updated: 10 Jun 2026 (backlog re-prioritized per rework brief: distribution promoted, instrumentation added, Phase 7 deferred, provider abstraction noted low)

## Active Items

### Development

18. __TOP PRIORITY — Referral and warm-intro engine (Phase 6 expansion)__
   - Distribution is the real job-search bottleneck — getting seen (referrals, warm
     intros, escaping the ATS pile), not producing more materials
   - Build on phase6_networking.py: referral targeting, warm-intro path mapping,
     follow-through cadence across the contact pipeline
   - Keep the terminal-only / no-auto-send posture — deliberate constraint, avoids
     LinkedIn ToS exposure

19. __PRIORITY — Results instrumentation — publishable metrics snapshot__
   - pipeline_report.py already computes the core aggregates (applications, response
     rate, interview-advance rate, response time)
   - Add a PII-free snapshot mode/output the README Results section can be refreshed
     from — aggregate figures only, no company names, no salary data
   - Also capture time-per-package (currently TBD in README Results)
   - Doubles as a genuine V&V capability consistent with project discipline

17b. __NOT URGENT — Generalize domain-specific vocabulary and prompt language__
   - Problem: tag lists, keyword sets, and prompt language are tuned for defense SE;
     the pipeline cannot serve a different domain without modifying scripts directly
   - Examples: `templates/interview_library_tags.json` (defense-tuned tag vocabulary),
     system prompt phrases like "defense and aerospace", "TS/SCI", "MBSE" in Phase 4/5
   - Goal: `context/domain/domain_config.yaml` (gitignored) holds all domain-specific
     config; `context/domain/domain_config.example.yaml` (tracked) ships as blank template
   - Pattern mirrors 17a — do NOT begin until 17a loader design is finalized, since
     the same pattern will apply

5. __Phase 4 Stage 4 — Add Phase 6 prompt to next steps__
   - Phase 6 is now stable — this item is unblocked
   - Add a note to the Stage 4 output of phase4_resume_generator.py pointing to phase6_networking.py
   - Goal: remind user to build contact outreach after submitting each application

9. check_utils.py shared module — deferred
    - Concept: extract shared logic (gap term extraction, Layer 1 rules, output formatting)
      from check_resume.py and check_cover_letter.py into scripts/utils/check_utils.py
    - Reevaluate if a third checking module is added — two checkers don't justify the abstraction

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

15. This is a Phase 5 gap detection issue — the kind of terminology inconsistency the synonym audit item in the parking lot was meant to catch. "Class 3 UAS" didn't get flagged because it's plausible-sounding defense language, not an obvious hallucination. Worth adding a specific check for UAS Group classification language (Group 1-5, not Class) to that audit when you get back to it.    

## Standing / Evergreen Tasks

- experience library tool equivalence review**
  - After any tool clarification or correction (e.g., Cameo = MagicDraw), verify
    that affected bullets use consistent naming across all employer sections
  - Trigger: any update to the Confirmed Tools line in CANDIDATE_BACKGROUND.md
  - Goal: prevent Phase 5 false gap flags caused by naming inconsistency

## Future / Speculative Ideas

 (Not ready to scope or build — needs further refinement before moving to Active)*

10. Phase 7 — Search agent — DEFERRED / OPTIONAL
    - Automated role discovery: Google, USAJobs, ClearanceJobs
    - Downgraded 10 Jun 2026: least differentiated, most brittle component — scrapers
      break, anti-bot measures escalate, ToS/legal gray areas; time saved is marginal
      (manual role entry takes seconds). Defensible value lives in phases 3–6.
    - If ever revived: sanctioned APIs/feeds only (e.g. USAJobs has an API) — no HTML
      scraping of ToS-restricted sites
    - NOT LinkedIn (blocks automation)

20. Provider abstraction layer — keep low
    - Optional abstraction over the LLM provider call
    - Only matters if the project is repositioned as a product or to demonstrate
      provider-agnostic architecture — over-engineering for a single-user personal tool

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
