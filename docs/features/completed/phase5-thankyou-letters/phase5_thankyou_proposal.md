# Phase 5 Post-Interview Thank You Letter Generator

## User Story and Acceptance Criteria

### User Story
"As a job seeker who has just completed an interview and filed a debrief, I want a
script that generates a personalized thank you letter for each interviewer -- drawing
from the debrief notes, job description, and tailored resume -- so that each letter
is specific to that person, consistent with what I said in the interview, and ready
to send within hours of the conversation."

---

### CC Session Guidance -- Read Before Starting

This is a focused, self-contained script. It reads structured inputs and calls the
Claude API once per interviewer to generate a short letter. Context window pressure
should be low.

If the debrief file contains multiple interviewers, the script generates one letter
per interviewer in sequence -- each API call is independent. No subagent deployment
needed for the initial build.

Read `phase5_interview_prep.py` for API call and .docx output patterns before
writing -- follow the same conventions for client initialization, system prompt
structure, and file output.

---

### Acceptance Criteria (AC)

#### Script (`scripts/phase5_thankyou.py`)

- Exists at `scripts/phase5_thankyou.py`
- Accepts `--role [role-slug]` and `--stage [stage]` as required arguments
- Accepts `--panel_label [label]` as optional argument, matching the debrief
  file naming convention from `phase5_debrief.py`
- Locates the debrief file at:
  `data/debriefs/[role]/debrief_[stage]_[panel_label]_[date]_filed-[date].json`
  (with or without panel label, matching the filed debrief)
- If multiple debrief files exist for the same role/stage/panel_label combination,
  uses the most recently filed one and prints a notice to terminal
- If no matching debrief file is found, exits with a clear error message showing
  the expected path

#### Input Loading

- Loads the debrief JSON file
- Loads `data/job_packages/[role]/job_description.txt`
- Loads the tailored resume: `data/job_packages/[role]/stage4_final.txt` if present,
  falling back to `stage2_approved.txt`
- Loads `data/experience_library/candidate_profile.md`
- If JD or candidate profile is missing, exits with a clear error; resume is
  optional (letters generate without it, with a terminal warning)

#### Letter Generation -- One Per Interviewer

- Iterates over the `interviewers` array in the debrief metadata
- For each interviewer, makes one API call to generate a letter
- Each letter is personalized using:
  - Interviewer name and title
  - `interviewer_notes` field -- specific question asked, background detail,
    program mentioned, shared experience, or any other captured context
  - Stories that landed well (`landed: yes`) from the debrief -- referenced
    naturally, not recited
  - `what_i_said` continuity field -- letter stays consistent with stated positions
  - Stage and role context from the JD
  - Candidate's relevant background from the profile and resume
- If `interviewer_notes` is null or empty for an interviewer, the letter is still
  generated but a terminal warning is printed:
  `"No interviewer notes for [name] -- letter will be less personalized"`

#### Letter Content Requirements

- Length: 3-4 short paragraphs; reads naturally in under 90 seconds
- Paragraph 1: genuine, specific opening -- references something from the
  conversation drawn from `interviewer_notes`; never generic ("Thank you for
  taking the time")
- Paragraph 2: brief reinforcement of fit -- one specific capability or experience
  that connects to what was discussed; grounded in a landed story or a stated
  strength from the debrief
- Paragraph 3: forward-looking close -- expresses continued interest, references
  next steps if known from the debrief, stays confident without being presumptuous
- Optional paragraph 4: only if a meaningful gap or concern surfaced during the
  interview that warrants a brief, confident reframe -- not defensive, not
  over-explained; omit if no gap worth addressing
- Tone calibrated to interviewer background:
  - Technical interviewer (SE, engineer): peer-level, specific to the work
  - Business/executive interviewer (director, BD, PM): mission outcomes and
    strategic framing
  - Recruiter: professional, warm, process-aware
  - Tone inference based on `title` field; if ambiguous, defaults to professional
- Uses en dashes, never em dashes
- Does not reproduce verbatim STAR story text from the prep package
- Does not introduce claims or experience not in the candidate profile or resume

#### Output Files

- One `.txt` file per interviewer written to
  `data/job_packages/[role]/thankyou_[stage]_[panel_label]_[interviewer_lastname]_[date].txt`
- One `.docx` file per interviewer written to the same directory with the same
  naming pattern
- If a file already exists for that interviewer and date, prompts:
  `"thankyou_[...].txt already exists. Overwrite? (y/n):"`
- After all letters are written, prints a summary:
  `"Generated N thank you letters:"` followed by each output path

#### System Prompt

- Instructs the model to write a professional post-interview thank you letter
- Emphasizes: specific over generic, confident over effusive, brief over thorough
- Instructs: no em dashes, no hollow openers, no restating the candidate's full
  background
- Instructs: use `interviewer_notes` as the personalization anchor -- if it contains
  a specific question the interviewer asked, open by referencing it; if it contains
  background research, weave it in naturally
- Instructs: stay consistent with `what_i_said` -- do not introduce new positions
  or walk back stated ones

#### Tests

Unit tests cover:

- Single interviewer: letter generated, output files written with correct naming
- Multiple interviewers: one letter per interviewer, independent output files
- Panel label present: included in output filename
- Panel label absent: omitted from output filename
- Missing `interviewer_notes`: letter generated, terminal warning printed
- Most-recent-file selection: correct file chosen when multiple debriefs match
- Missing debrief file: exits with clear error
- Missing JD: exits with clear error
- Missing resume: warning printed, generation proceeds
- Tone calibration: technical title produces peer-level framing signal in prompt;
  executive title produces mission-outcomes framing signal

---

### Out of Scope

- Sending letters via email or any external integration
- HTML or formatted email output -- .txt and .docx only
- Generating letters without a filed debrief -- debrief is required input
- Editing or regenerating individual paragraphs interactively
- Letter quality scoring or A/B variants
- Any changes to `phase5_debrief.py` or `phase5_interview_prep.py`

---

## Review Annotations

*This section is populated during the Chat spec review step. Do not fill in manually.*
