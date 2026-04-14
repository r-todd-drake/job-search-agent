# Post-Interview Debrief Capture

## User Story and Acceptance Criteria

### User Story
"As a job seeker who has just completed an interview, I want a structured debrief workflow that captures how the interview went, what content came up, what salary information was exchanged, and what I told the interviewer -- so that I have a reliable record to feed future prep, track advancement likelihood, and maintain consistency across interview stages for the same role."

### Acceptance Criteria (AC)

**Debrief Template (`interview_debrief_template.md`)**
- Template exists at `docs/features/post-interview-debrief/interview_debrief_template.md`
- Template contains the following sections:
  - **Interview Metadata**: date, role slug, company, interviewer name and title, interview stage (recruiter screen / hiring manager / panel / final), format (phone / video / onsite)
  - **Advancement Read**: single-select field with four values -- `for sure`, `maybe`, `doubt it`, `definitely not` -- plus a free-text notes field
  - **Stories Used**: list of stories the candidate told, each with: theme tag(s), brief description of how it was framed, and a `landed` field (yes / partially / no)
  - **Gaps Surfaced**: list of gaps that came up, each with: gap label, how the candidate responded, and a `response_felt` field (strong / adequate / weak)
  - **Salary Exchange**: structured fields for -- range given by interviewer (min/max), candidate anchor provided (if any), candidate floor disclosed (if any), and a free-text notes field; all fields optional
  - **Continuity -- What I Said**: free-text section capturing any specific claims, commitments, framings, or positions given to this interviewer that should not be contradicted in future stages (e.g., years of experience cited, availability date, relocation stance, interest level framing)
  - **Open Notes**: unstructured free-text field for anything else worth capturing

**Debrief Script (`phase5_debrief.py`)**
- Script exists at `scripts/phase5_debrief.py`
- Accepts `--role [role-slug]` and `--stage [stage]` as arguments
- On launch, presents each template section interactively as a guided questionnaire
- For structured fields (advancement read, landed, response_felt), presents valid options and validates input
- For free-text fields, accepts open input with no validation
- Script has latitude to ask one follow-up question per section if a response suggests something worth capturing (e.g., if `landed = no`, prompt: "anything you'd do differently?")
- On completion, writes a populated debrief file to `data/debriefs/[role-slug]/debrief_[stage]_[date].json`
- JSON output schema matches the template sections above
- Script does not infer or generate content -- it only captures what the candidate provides

**Output File**
- Debrief file is valid JSON
- File is saved to the correct path and named correctly
- All optional fields are present in the output with null values if not provided (no silent omissions)
- Role slug in filename matches the `--role` argument exactly

### Out of Scope
- Parsing or ingesting debrief files into Phase 5 -- that is Feature C
- Extracting or normalizing stories and gap responses into the interview library -- that is Feature B
- Any automated scoring, sentiment analysis, or AI assessment of how the interview went
- Integration with calendar, email, or any external system
- Multi-interviewer panel capture within a single debrief session (one debrief file per interviewer per stage)
- Editing or amending a previously saved debrief file
