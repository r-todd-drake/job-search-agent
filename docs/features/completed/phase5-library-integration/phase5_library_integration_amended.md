# Phase 5 Library Integration (Amended)

## Amendment Notes
*This proposal supersedes the previous `phase5_library_integration_proposal.md`.*

*Changes from previous version:*
- *Continuity summary updated to reflect multi-interviewer debrief structure*
- *Story and gap performance signal AC added -- landed/response_felt history*
  *surfaced alongside seeded content*
- *Thank you letter notification added as terminal output after prep generation*
- *Panel label threading added to debrief file location logic*

---

## User Story and Acceptance Criteria

### User Story
"As a job seeker running interview prep for a role -- whether for a first stage or a
subsequent stage after prior interviews -- I want Phase 5 to seed its story, gap, and
question output from my vetted interview library, surface performance history on seeded
content, and incorporate continuity from prior debriefs -- so that each prep package
builds on polished, role-tested content and keeps me consistent across stages."

---

### CC Session Guidance -- Read Before Starting

This feature modifies `phase5_interview_prep.py`, which is a large file with complex
generation logic. Read the full script before planning any changes.

**Before writing code, assess session scope:**

- If context window usage after loading all required files exceeds ~40%, split
  into two sessions:
  - Session A: Library seeding logic (stories, gaps, questions) and performance
    signal surfacing
  - Session B: Debrief continuity section, salary actuals override, debrief-to-library
    notification, and thank you letter notification

- If a self-contained sub-task (e.g., the continuity summary renderer) is
  well-specified and does not require awareness of the full generation pipeline,
  consider spawning a subagent to build and test it, then integrate the output
  into the main tab

- The main tab must own integration and regression testing of the full generation
  pipeline. Subagents own isolated, testable sub-components only

Do not modify generation prompts without understanding the full prompt construction
pipeline. Each section prompt is built by a dedicated `_build_*` function -- locate
and understand these before touching them.

---

### Acceptance Criteria (AC)

#### Prerequisite

This feature depends on the library infrastructure built in the Phase 5 Workshop
Capture proposal: `interview_library.json`, `interview_library_tags.json`, and
`interview_library_parser.py` must exist and pass their tests before this feature
is built.

#### Library-Seeded Story Generation

- Before generating Section 2 (Story Bank), Phase 5 calls
  `interview_library_parser.get_stories()` filtered by tags matched to the JD
  and the current stage
- If one or more vetted stories are found:
  - Each matching story is passed to `_build_section2_prompt()` as a seed block
    alongside existing story context
  - The generation prompt instructs the model to tailor the vetted story to the
    current role and stage rather than generating cold
  - Each seeded story in the output is labeled `(library-seeded)` in both .txt
    and .docx output
  - The original vetted story text is not reproduced verbatim -- output is a
    role-tailored version grounded in the library facts
- If no vetted stories are found, generation proceeds as current with no change
  to output or labeling
- A prep package may contain a mix of seeded and cold-generated stories

#### Story and Gap Performance Signal

- When a story or gap response is seeded from the library, Phase 5 checks all
  debrief files across all roles for entries where that library item was used
  (matched by `library_id` in stories_used, or by normalized gap label in
  gaps_surfaced)
- If prior usage is found, a performance note is surfaced inline in the prep
  package immediately below the seeded item:
  `"Used N times across roles: [yes x2 / partially x1]"` for stories
  `"Used N times across roles: [strong x1 / adequate x2]"` for gap responses
- If no prior debrief usage is found, no performance note is shown -- absence
  of note is sufficient
- Performance note appears in both .txt and .docx output
- Performance note does not affect generation -- it is an informational annotation
  for the candidate, not a seeding signal

#### Library-Seeded Gap Responses

- Before generating Section 3 (Gap Preparation), Phase 5 calls
  `interview_library_parser.get_gap_responses()` filtered by gap label matched
  against JD-identified gaps
- If a vetted gap response is found:
  - The vetted honest answer / bridge / redirect triad is passed as a seed to
    `_build_gap_prompt()`
  - Output is tailored to the current role and stage
  - Output is labeled `(library-seeded)` in the prep package
- If no vetted response is found, generation proceeds as current

#### Library-Seeded Questions

- Before generating Section 4 (Questions to Ask), Phase 5 calls
  `interview_library_parser.get_questions()` filtered by stage and relevant tags
- If vetted questions are found:
  - Matching questions are passed to the questions generation prompt as candidates
    to include or adapt
  - Output questions that derive from library entries are labeled `(library-seeded)`
- If no vetted questions are found, generation proceeds as current

#### Salary Section -- Debrief Actuals Override

- Phase 5 checks for debrief files at `data/debriefs/[role]/` for the current role
- Debrief file location logic accounts for panel label in filename when present
- If no debrief files exist, or none contain populated salary fields:
  - Salary section renders as current -- generated analysis based on JD signals
- If one or more debrief files contain populated salary fields:
  - Generated salary analysis is replaced with actuals from the most recent
    debrief containing salary data
  - Displayed fields: range given by interviewer (min/max), candidate anchor if
    provided, candidate floor if provided
  - Section header updated to indicate these are reported actuals, not estimates
  - If salary data exists in multiple debriefs, the most recent is used and
    others noted

#### Continuity Summary -- Appended Section

- Phase 5 checks for debrief files for the current role
- If no debrief files exist: no continuity section appended; no placeholder shown
- If one or more debrief files exist:
  - A *Continuity Summary* section is appended at the end of the prep package
  - For each prior debrief, sorted chronologically:
    - Stage, panel label (if present), date
    - All interviewers: name, title for each entry in the `interviewers` array
    - Advancement read assessment
    - Stories used: tags and framing labels only (not full STAR text)
    - Gaps surfaced: gap labels and `response_felt` ratings
    - Full contents of the `what_i_said` field; if empty, stage is still listed
      with a note that no continuity data was captured
  - Section is labeled as a reference record, not prep guidance
  - Section appears in both .txt and .docx output

#### Debrief-to-Library Notification

- After generating the prep package, Phase 5 checks debrief files for the current
  role for stories or gap responses not yet present in `interview_library.json`
- Match logic: story matched by primary theme tag + employer; gap matched by
  normalized gap label
- If unmatched debrief content is found:
  - Prints to terminal:
    `"Debrief content found that is not in your interview library."`
    `"Run: python scripts/phase5_workshop_capture.py --role [role] --stage [stage]"`
    `"to review and add workshopped content to the library."`
  - Notification only -- does not block or delay prep package output
  - Phase 5 does not write to the library automatically

#### Thank You Letter Notification

- After generating the prep package, if a debrief file exists for the current
  role and stage (and panel label if applicable), Phase 5 prints to terminal:
  `"Debrief found for this stage. Generate thank you letters:"`
  `"Run: python scripts/phase5_thankyou.py --role [role] --stage [stage]"`
  (with `--panel_label` appended if the debrief file includes one)
- Notification only -- does not generate letters or block output

#### No-Regression Guarantee

- All existing Phase 5 behavior is preserved when no library or debrief data exists
- Phase 5 does not error if `interview_library.json` is absent -- proceeds as current
- Phase 5 does not error if `data/debriefs/` is absent or empty -- proceeds as current
- Existing prompt construction functions are extended, not replaced -- seed content
  injected as additional input blocks
- Stage profiles in `STAGE_PROFILES` are not modified

#### Output Labeling

- `(library-seeded)` label appears inline next to the story, gap, or question heading
- Performance signal appears on the line immediately below the label
- Labels appear in both .txt and .docx outputs
- No "cold-generated" label added -- absence of label is sufficient

#### Tests

Unit tests cover:

- Library-seeded story path: seed block injected when library returns match
- Cold story path: prompt unchanged when library returns no match
- Performance signal: correct count and rating summary when debrief history exists;
  no note when no history exists
- Library-seeded gap path: triad injected when library returns match
- Cold gap path: prompt unchanged when library returns no match
- Library-seeded question path: candidates injected when library returns match
- Salary override: no debrief / debrief without salary / debrief with salary /
  multiple debriefs (most recent wins)
- Continuity summary: no debriefs / single interviewer debrief / multi-interviewer
  debrief / multiple debriefs sorted correctly / empty what_i_said handled
- Panel label: debrief file located correctly with and without panel label
- Debrief-to-library notification: triggers when unmatched content found / does
  not trigger when all matched / does not trigger when no debriefs
- Thank you letter notification: triggers when debrief exists for current stage /
  does not trigger when no debrief for current stage
- No-regression: absent library / absent debriefs dir / both absent

---

### Out of Scope

- Automatic library writes from debrief data without user review
- Semantic or embedding-based story retrieval -- tag filtering via parser only
- Modifying the Stage 1 / Stage 2 generation split or the .docx formatting pipeline
- Any changes to Phase 1 through Phase 4 behavior
- Scoring or ranking vetted stories against each other
- Changes to `phase5_debrief.py` or `phase5_workshop_capture.py`
- Thank you letter generation -- `phase5_thankyou.py` proposal

---

## Review Annotations

*This section is populated during the Chat spec review step. Do not fill in manually.*
