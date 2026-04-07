# Parking Lot
# Load for: planning next development session, prioritizing work items
Last updated: 06 Apr 2026

## Active Items

### Development
1. **Phase 4 — Cover letter generator**
   - Input: JD + stage4_final.txt + candidate_profile.md
   - Output: cover_letter_draft.txt + [role]_CoverLetter.docx
   - Visual style: matches resume template (same header, fonts, color scheme)
   - PII stripped from all API calls
   - Standalone script — not a required Phase 4 stage

2. **Phase 6 — Networking support**
   - Scoped and ready to build
   - Standalone script: python scripts/phase6_networking.py --role [role]
   - Section 1: LinkedIn search guidance (queries, filters, who to look for)
   - Section 2: Connection request message (300 char limit)
   - Section 3: Follow-up message after connecting
   - Section 4: Cold outreach / InMail template
   - Section 5: Informational interview request
   - User performs LinkedIn searches manually — script provides guidance
   - Once stable: add Phase 6 reference to Phase 4 Stage 4 next steps output

3. **Phase 4 Stage 4 — Add Phase 6 prompt to next steps**
   - Deferred until Phase 6 is stable

4. **Experience library update workflow**
   - Process to add new bullets written during resume tailoring back into library
   - NG SE Man2 book club bullet, compensation bullets, Army expansion not yet in library
   - Need structured intake process: draft bullet to verify to library entry

5. **candidate_profile.md rebuild**
   - CompTIA Security+ lapsed — must be flagged not omitted
   - HAIPE experience needs adding (confirmed from KForce/NGLD-M)
   - Rebuild from current experience_library.json via phase3_build_candidate_profile.py

6. **Phase 5 — HAIPE gap false positive**
   - Phase 5 gap analysis sometimes flags HAIPE as a gap
   - KForce/NGLD-M has confirmed HAIPE-enabled architecture experience
   - Fix: update candidate_profile.md (item 5 above) — should resolve automatically

7. **Phase 7 — Search agent**
   - Automated role discovery: Google, USAJobs, ClearanceJobs
   - NOT LinkedIn (blocks automation)
   - Deferred — lower priority than Phase 6

8. **capabilities.md — traceability document**
   - Maps script capabilities to project phases
   - Deferred until Phase 5 fully stable

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

10. **pytest baseline setup**
    - Install pytest and configure for project root discovery
    - Create tests/ folder mirroring scripts/ structure
    - Write baseline tests for existing capabilities — priority order:
      1. utils/pii_filter.py — confirm PII stripping works correctly
      2. utils/library_parser.py — confirm parsing output structure
      3. phase2 scripts — confirm duplicate req number detection
    - Add pytest to requirements.txt
    - Verify VS Code Testing panel discovers tests/ correctly

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
    - Relationship to candidate_profile.md rebuild (item 5) — foundation or
      separate artifact?
  - Note: may be more valuable as a complementary recruiter-facing tool than
    as a job seeker capability — needs further refinement before scoping
  - Do not begin development until design spike is complete
  
## Completed (recent)
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