# Phase 5 Integration -- Interview Library and Debrief Awareness

## User Story and Acceptance Criteria

### User Story
"As a job seeker running interview prep for a role I have already interviewed for or workshopped stories against, I want Phase 5 to seed its story and gap output from my vetted interview library and append a continuity summary from prior debriefs -- so that the prep package builds on what I have already polished and keeps me consistent across interview stages."

### Acceptance Criteria (AC)

**Library-Seeded Story Generation**
- Before generating a STAR story for a given theme, Phase 5 calls `interview_library_parser.get_stories()` filtered by relevant tag(s) and role slug
- If one or more vetted stories are found:
  - The vetted story is passed to the generation prompt as a seed -- the AI tailors it to the current role and stage rather than generating cold
  - The output story is clearly labeled `(library-seeded)` in the prep package
  - The original vetted story text is not reproduced verbatim -- the output is a role-tailored version
- If no vetted stories are found for a theme, generation proceeds as current with no change to output or labeling
- Seeding behavior applies per-theme -- a prep package may contain a mix of seeded and cold-generated stories

**Library-Seeded Gap Responses**
- Before generating a gap response, Phase 5 calls `interview_library_parser.get_gap_responses()` filtered by gap label and role slug
- If a vetted gap response is found:
  - The vetted Gap / Honest Answer / Redirect triad is passed as a seed to the generation prompt
  - Output is tailored to the current role and stage
  - Output is labeled `(library-seeded)` in the prep package
- If no vetted response is found, generation proceeds as current

**Salary Section -- Conditional Display**
- Phase 5 checks for the presence of debrief files at `data/debriefs/[role-slug]/` for the current role
- If no debrief files exist, or no debrief files contain populated salary fields:
  - Salary section renders as currently -- generated analysis based on market data and JD signals
- If one or more debrief files exist with populated salary fields:
  - Generated salary analysis is replaced with actuals from the most recent debrief that contains salary data
  - Displayed fields: range given by interviewer (min/max), candidate anchor (if provided), candidate floor (if provided)
  - Section header updated to reflect that these are reported actuals, not generated estimates
  - If salary data exists in multiple debriefs for the role, the most recent is used and the others are noted

**Continuity Summary -- Appended Section**
- Phase 5 checks for debrief files for the current role
- If no debrief files exist: no continuity section is appended, no placeholder shown
- If one or more debrief files exist:
  - A *Continuity Summary* section is appended at the end of the prep package
  - For each prior debrief (sorted chronologically): stage, date, interviewer name/title, and the full contents of the `what_i_said` field are listed
  - Advancement read is included per stage
  - Stories used and gaps surfaced are listed per stage (labels only -- not full text)
  - Section is clearly labeled as a reference record, not prep guidance
  - If `what_i_said` is empty for a debrief, that stage is still listed with a note that no continuity data was captured

**Debrief-to-Library Pipeline**
- After generating the prep package, Phase 5 checks debrief files for the current role for any stories or gap responses not yet present in `interview_library.json`
- If debrief-captured content is found that has no matching library entry (matched by theme tag + brief description):
  - Phase 5 prints a prompt to the terminal: "Debrief content found that is not in your interview library. Run `phase_workshop.py --from-debrief` to review and add."
  - Phase 5 does not automatically write to the library -- candidate review is required before intake
  - This is a notification only; it does not block or delay the prep package output

**No Regression**
- All existing Phase 5 behavior is preserved when no library or debrief data exists for a role
- Phase 5 does not error or warn if `interview_library.json` is absent -- it proceeds as current
- Phase 5 does not error or warn if `data/debriefs/` is absent or empty -- it proceeds as current

**Tests**
- Unit tests cover: library-seeded story path vs. cold-generation path, library-seeded gap path vs. cold-generation path, salary section conditional rendering (no data / partial data / full data), continuity summary rendering (no debriefs / one debrief / multiple debriefs), debrief-to-library notification trigger, no-regression path (no library, no debriefs)

### Out of Scope
- Automatic library writes from debrief data without candidate review
- Semantic or embedding-based story retrieval -- tag-based filtering via `interview_library_parser` only
- Modifying the Phase 5 Stage 1 / Stage 2 split or the `.docx` output format
- Any changes to Phase 1 through Phase 4 behavior
- Scoring or ranking vetted stories against each other
