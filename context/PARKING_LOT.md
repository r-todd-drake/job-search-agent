# Parking Lot
# Load for: planning next development session, prioritizing work items
Last updated: 11 Apr 2026

## Active Items

### Development

1. **Phase 5 updates** *(urgent — affects active interview prep)*
   - Duplicate salary guidance in the prep package — reconcile to a single anchor and remove the duplicate section
   - Gap 1 redirect fabricates an MBSE gap that doesn't exist — rewrite around the real Shield AI story (domain gap, not MBSE gap)
   - Add UCSD Systems Engineering certificate program to CANDIDATE_BACKGROUND and experience library education section
   - Remove Security+ language entirely — lapsed, not flagged

2. **candidate_profile.md rebuild**
   - CompTIA Security+ lapsed — must be flagged not omitted
   - HAIPE experience needs adding (confirmed from KForce/NGLD-M)
   - Rebuild from current experience_library.json via phase3_build_candidate_profile.py

3. **Phase 5 — HAIPE gap false positive** *(blocked by item 2)*
   - Phase 5 gap analysis sometimes flags HAIPE as a gap
   - KForce/NGLD-M has confirmed HAIPE-enabled architecture experience
   - Fix: update candidate_profile.md (item 2 above) — should resolve automatically

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

6. **Experience library update workflow**
   - Process to add new bullets written during resume tailoring back into library
   - NG SE Man2 book club bullet, compensation bullets, Army expansion not yet in library
   - Need structured intake process: draft bullet to verify to library entry

7. **Phase 5 Stage 2 — revision stage** *(proper pipeline extension)*
   - Add a Stage 2 to phase5_interview_prep.py — similar to how Phase 4 has multiple stages
   - Stage 1 generates the initial prep package
   - Stage 2 accepts workshop notes or a corrected prep file and produces a clean revised version
   - Could also flag experience library updates automatically

8. **library_parser.py — last-bullet drop bug**
   - Parser silently drops the last bullet in an employer section when immediately followed by `## PROFESSIONAL SUMMARIES`
   - Documented in `test_parse_library_bullet_count_matches_source` (currently a known failing test)
   - Fix: flush the pending bullet before resetting `current_employer`
   - Data integrity risk for any library rebuild — fix before next library update

9. **Script identifier audit — GitHub exposure risk**
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

10. **check_utils.py shared module — deferred**
    - Concept: extract shared logic (gap term extraction, Layer 1 rules, output formatting)
      from check_resume.py and check_cover_letter.py into scripts/utils/check_utils.py
    - Reevaluate if a third checking module is added — two checkers don't justify the abstraction

11. **Phase 7 — Search agent**
    - Automated role discovery: Google, USAJobs, ClearanceJobs
    - NOT LinkedIn (blocks automation)
    - Deferred — lower priority than Phase 6

12. **capabilities.md — traceability document**
    - Maps script capabilities to project phases
    - Deferred until Phase 5 fully stable

## Standing / Evergreen Tasks
- **Experience library tool equivalence review**
  - After any tool clarification or correction (e.g., Cameo = MagicDraw), verify
    that affected bullets use consistent naming across all employer sections
  - Trigger: any update to the Confirmed Tools line in CANDIDATE_BACKGROUND.md
  - Goal: prevent Phase 5 false gap flags caused by naming inconsistency

## Future / Speculative Ideas
*(Not ready to scope or build — needs further refinement before moving to Active)*

- **Interview follow-up capture and library**
  - Concept A: structured debrief workflow — interview the candidate post-interview
    via formatted questionnaire to capture key takeaways; normalize and structure
    output for use in follow-on prep (same role and future roles)
  - Concept B: extraction library — pull workshopped STAR stories and Gap responses
    (Gap, Honest answer, Redirect) into reusable libraries, similar to phase3_parse_library.py
  - These may be one feature or two — needs design spike to define flow, artifacts,
    and primary user before scoping
  - Design spike recommended via Claude web chat before bringing back here to build

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
