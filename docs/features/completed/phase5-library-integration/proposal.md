# Phase 5 Library Integration

## User Story and Acceptance Criteria

### User Story
"As a job seeker running interview prep for a role -- whether for a first stage or a
subsequent stage after prior interviews -- I want Phase 5 to seed its story, gap, and
question output from my vetted interview library and incorporate continuity from prior
debriefs, so that each prep package builds on polished, role-tested content and keeps
me consistent across stages."

---

### CC Session Guidance -- Read Before Starting

This feature modifies `phase5_interview_prep.py`, which is a large file with complex
generation logic. Read the full script before planning any changes.

**Before writing code, assess session scope:**

- If context window usage after loading all required files exceeds ~40%, consider
  splitting into two sessions:
  - Session A: Library seeding logic (stories, gaps, questions) and the parser
    integration calls
  - Session B: Debrief continuity section, salary actuals override, and
    debrief-to-library notification

- If a self-contained sub-task (e.g., the continuity summary renderer) is well-specified
  and does not require awareness of the full generation pipeline, consider spawning a
  subagent to build and test it, then integrate the output into the main tab.

- The main tab should own integration and testing of the full generation pipeline.
  Subagents should own isolated, testable sub-components only.

Do not modify generation prompts without understanding the full prompt construction
pipeline. Each section prompt is built by a dedicated `_build_*` function -- locate
and understand these before touching them.

---

### Acceptance Criteria (AC)

#### Prerequisite

This feature depends on the library infrastructure built in the Phase 5 Workshop Capture
proposal: `interview_library.json`, `interview_library_tags.json`, and
`interview_library_parser.py` must exist and pass their tests before this feature
is built.

#### Library-Seeded Story Generation

- Before generating Section 2 (Story Bank), Phase 5 calls
  `interview_library_parser.get_stories()` filtered by tags matched to the JD and
  the current stage
- If one or more vetted stories are found:
  - Each matching story is passed to the `_build_section2_prompt()` function as a
    seed block alongside the existing story context
  - The generation prompt instructs the model to tailor the vetted story to the
    current role and stage rather than generating cold
  - Each seeded story in the output is labeled `(library-seeded)` in both the .txt
    and .docx output
  - The original vetted story text is not reproduced verbatim -- the output is a
    role-tailored version grounded in the library facts
- If no vetted stories are found for a given theme, generation proceeds as current
  with no change to output or labeling
- A prep package may contain a mix of seeded and cold-generated stories

#### Library-Seeded Gap Responses

- Before generating Section 3 (Gap Preparation), Phase 5 calls
  `interview_library_parser.get_gap_responses()` filtered by gap label matched
  against JD-identified gaps
- If a vetted gap response is found:
  - The vetted honest answer / bridge / redirect triad is passed as a seed to the
    `_build_gap_prompt()` function
  - Output is tailored to the current role and stage
  - Output is labeled `(library-seeded)` in the prep package
- If no vetted response is found for a gap, generation proceeds as current

#### Library-Seeded Questions

- Before generating Section 4 (Questions to Ask), Phase 5 calls
  `interview_library_parser.get_questions()` filtered by stage and relevant tags
- If vetted questions are found:
  - Matching questions are passed to the questions generation prompt as candidates
    to include or adapt
  - Output questions that derive from library entries are labeled `(library-seeded)`
- If no vetted questions are found for the current stage, generation proceeds as current

#### Salary Section -- Debrief Actuals Override

- Phase 5 checks for debrief files at `data/debriefs/[role]/` for the current role
- If no debrief files exist, or no debrief files contain populated salary fields:
  - Salary section renders as currently -- generated analysis based on JD signals
- If one or more debrief files exist with populated salary fields:
  - Generated salary analysis is replaced with actuals from the most recent debrief
    containing salary data
  - Displayed fields: range given by interviewer (min/max), candidate anchor if
    provided, candidate floor if provided
  - Section header updated to indicate these are reported actuals, not estimates
  - If salary data exists in multiple debriefs, the most recent is used and others noted

#### Continuity Summary -- Appended Section

- Phase 5 checks for debrief files for the current role
- If no debrief files exist: no continuity section is appended; no placeholder shown
- If one or more debrief files exist:
  - A *Continuity Summary* section is appended at the end of the prep package
  - For each prior debrief, sorted chronologically:
    - Stage, date, interviewer name and title
    - Advancement read assessment
    - Stories used: tags and framing labels only (not full STAR text)
    - Gaps surfaced: gap labels and `response_felt` ratings
    - Full contents of the `what_i_said` field; if empty, stage is still listed
      with a note that no continuity data was captured
  - Section is labeled as a reference record, not prep guidance
  - Section appears in both .txt and .docx output

#### Debrief-to-Library Notification

- After generating the prep package, Phase 5 checks debrief files for the current role
  for stories or gap responses not yet present in `interview_library.json`
- Match logic: story matched by primary theme tag + employer;
  gap matched by normalized gap label
- If unmatched debrief content is found:
  - Phase 5 prints to terminal:
    `"Debrief content found that is not in your interview library."`
    `"Run: python scripts/phase5_workshop_capture.py --role [role] --stage [stage]"`
    `"to review and add workshopped content to the library."`
  - This is a notification only -- does not block or delay prep package output
  - Phase 5 does not write to the library automatically

#### No-Regression Guarantee

- All existing Phase 5 behavior is preserved when no library or debrief data exists
- Phase 5 does not error or warn if `interview_library.json` is absent -- proceeds as current
- Phase 5 does not error or warn if `data/debriefs/` is absent or empty -- proceeds as current
- Existing prompt construction functions (`_build_section1_prompt`,
  `_build_section2_prompt`, `_build_gap_prompt`, `_build_intro_prompt`) are extended,
  not replaced -- seed content is injected as an additional input block
- Stage profiles in `STAGE_PROFILES` are not modified

#### Output Labeling

- `(library-seeded)` label appears inline in the output next to the story, gap, or
  question heading -- not as a separate section
- Label appears in both .txt and .docx outputs
- Label is omitted entirely when no library seeding occurred -- no "cold-generated" label
  is added; absence of label is sufficient

#### Tests

Unit tests cover:

- Library-seeded story path: seed block injected into prompt when library returns match
- Cold story path: prompt unchanged when library returns no match
- Library-seeded gap path: triad injected into prompt when library returns match
- Cold gap path: prompt unchanged when library returns no match
- Library-seeded question path: candidates injected when library returns match
- Salary override: no debrief / debrief without salary / debrief with salary /
  multiple debriefs (most recent wins)
- Continuity summary: no debriefs / one debrief with `what_i_said` populated /
  one debrief with `what_i_said` empty / multiple debriefs sorted correctly
- Debrief-to-library notification: triggers when unmatched content found /
  does not trigger when all content matched / does not trigger when no debriefs
- No-regression: absent library file / absent debriefs dir / both absent

---

### Out of Scope

- Automatic library writes from debrief data without user review -- notification only
- Semantic or embedding-based story retrieval -- tag filtering via parser only
- Modifying the Stage 1 / Stage 2 generation split or the .docx formatting pipeline
- Any changes to Phase 1 through Phase 4 behavior
- Scoring or ranking vetted stories against each other
- Changes to `phase5_debrief.py`
- Changes to `phase5_workshop_capture.py`

---

## Review Annotations

*This section is populated during the Chat spec review step. Do not fill in manually.*
