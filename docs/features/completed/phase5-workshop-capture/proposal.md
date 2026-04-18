# Phase 5 Workshop Capture and Interview Library Infrastructure

## User Story and Acceptance Criteria

### User Story
"As a job seeker who has workshopped interview prep materials with Claude Chat and received
a revised .docx, I want a capture script that parses that document and writes durable,
role-portable content into a structured interview library -- so that polished stories, gap
responses, and questions are available to seed future prep across all roles rather than
being rebuilt from scratch each time."

---

### CC Session Guidance -- Read Before Starting

This feature has two coupled sub-systems: the capture script and the library infrastructure
it writes to. Before writing any code, assess whether both sub-systems can be built in a
single session given current context window usage.

**If the session is approaching context limits, or if the spec review added significant
complexity, split into two CC sessions:**

- Session A: Library infrastructure only
  (`interview_library.json` schema, `interview_library_tags.json`,
  `interview_library_parser.py`, and all associated unit tests)
- Session B: Capture script only
  (`phase5_workshop_capture.py` and its tests), loading Session A output as context

**If a sub-task within a session is large and self-contained (e.g., the full parser module
with filtering logic), consider spawning a subagent** to build and test it in parallel,
then integrate the output. The main tab should orchestrate, not absorb everything.

Do not compress or skip tests to fit within a session. A partial build with full tests is
preferable to a complete build with untested code.

---

### Acceptance Criteria (AC)

#### Interview Library File (`data/interview_library.json`)

- File is initialized as `{ "stories": [], "gap_responses": [], "questions": [] }` if it
  does not exist; existing content is never overwritten on init
- Three top-level arrays: `stories`, `gap_responses`, `questions`
- Each `stories` entry contains:
  - `id`: unique slug auto-generated from employer + theme tag
    (e.g., `g2ops-mbse-bottleneck`)
  - `title`: short human-readable label derived from the story header in the .docx
  - `tags`: array of theme tags drawn from controlled vocabulary
  - `employer`: employer name as it appears in the story
  - `title_held`: job title held at that employer
  - `dates`: date range string as captured in the .docx
  - `situation`: vetted situation text, interviewer context stripped
  - `task`: vetted task text
  - `action`: vetted action text
  - `result`: vetted result text
  - `if_probed`: vetted probe branch text, or null if absent
  - `notes`: null on capture; available for manual annotation post-capture
  - `source`: `workshopped`
  - `roles_used`: array of role slugs this story has appeared in (seeded with capture role)
  - `last_updated`: ISO date string
- Each `gap_responses` entry contains:
  - `id`: unique slug auto-generated from gap label
    (e.g., `ip-networking-expertise`)
  - `gap_label`: gap label as it appears in the .docx header
    (e.g., `IP Networking Expertise`)
  - `severity`: `required` or `preferred` parsed from `[REQUIRED]` / `[PREFERRED]` tag
  - `tags`: array of theme tags
  - `honest_answer`: vetted honest answer text
  - `bridge`: vetted bridge text
  - `redirect`: vetted redirect text
  - `notes`: null on capture
  - `source`: `workshopped`
  - `roles_used`: array of role slugs
  - `last_updated`: ISO date string
- Each `questions` entry contains:
  - `id`: unique slug auto-generated from question text
  - `stage`: interview stage this question was written for
    (`recruiter` / `hiring_manager` / `team_panel`)
  - `category`: category label inferred from question content
    (e.g., `integration-challenge`, `success-metrics`, `mbse-evolution`)
  - `text`: the question text, stripped of interviewer-specific rationale
  - `tags`: array of theme tags
  - `notes`: null on capture
  - `source`: `workshopped`
  - `roles_used`: array of role slugs
  - `last_updated`: ISO date string

#### Tag Vocabulary (`data/interview_library_tags.json`)

- File exists at `data/interview_library_tags.json`
- Initial tag set covers:
  `leadership`, `cross-functional`, `technical-credibility`, `ambiguity`,
  `stakeholder-management`, `program-delivery`, `systems-engineering`,
  `communication`, `conflict-resolution`, `domain-gap`, `tools-gap`,
  `clearance`, `salary`, `culture-fit`, `mbse`, `requirements-analysis`,
  `integration`, `v-and-v`, `architecture`, `domain-translation`
- Tags not in vocabulary produce a warning on capture but do not block the write
- New tags may be added to the vocabulary file manually at any time

#### Library Parser (`scripts/interview_library_parser.py`)

- Module exists at `scripts/interview_library_parser.py`
- Exposes:
  - `get_stories(tags=None, role=None, stage=None)` -- returns matching story entries
  - `get_gap_responses(tags=None, role=None, gap_label=None)` -- returns matching gap entries
  - `get_questions(tags=None, role=None, stage=None)` -- returns matching question entries
- Filtering is additive (AND logic across all provided filters)
- Returns empty list (not error) when no entries match
- Returns empty list (not error) if `interview_library.json` does not exist
- Importable by `phase5_interview_prep.py` without side effects

#### Capture Script (`scripts/phase5_workshop_capture.py`)

- Script exists at `scripts/phase5_workshop_capture.py`
- Accepts `--role [role-slug]` and `--stage [stage]` as required arguments
- Locates the workshopped .docx at
  `data/job_packages/[role]/interview_prep_[stage].docx`
- If the file does not exist, exits with a clear error message and path shown
- Extracts document text using the same extraction approach as the existing codebase
- Parses Section 2 (Story Bank) into story entries:
  - Detects story blocks by `## STORY N --` header pattern
  - Extracts employer, title, dates from the `Employer:` line
  - Extracts STAR components by bold label (`**Situation**`, `**Task**`, etc.)
  - Extracts `**If Probed**` branch if present
  - Strips delivery notes, routing tables, and any italicized stage-register lines
  - Auto-assigns tags based on story content using tag vocabulary matching;
    prints suggested tags to terminal for user confirmation before writing
- Parses Section 3 (Gap Preparation) into gap response entries:
  - Detects gap blocks by `**GAP N --` header pattern
  - Extracts gap label and severity from header
  - Extracts `**Honest answer:**`, `**Bridge:**`, `**Redirect:**` components
  - Strips short tenure explanation section (not portable)
  - Strips hard questions list (role-specific)
  - Strips any italicized note-card or stage-register lines
- Parses Section 4 (Questions to Ask) into question entries:
  - Detects question blocks by `**Q[N]` header pattern
  - Extracts question text (the quoted question line)
  - Strips italicized rationale lines ("Signals you're already thinking about the work")
  - Strips closing question (interviewer-specific tactic, not portable as a library item)
  - Assigns stage from `--stage` argument
- Before writing, prints a summary of all parsed entries to terminal and prompts:
  `"Write N stories, N gap responses, N questions to interview_library.json? (y/n):"`
- On confirmation:
  - Checks for duplicate IDs before writing; if a duplicate is found, prompts:
    `"Entry [id] already exists. Skip / overwrite / rename? (s/o/r):"`
  - Appends confirmed entries to `interview_library.json`
  - Adds `--role` slug to `roles_used` on any existing entry that was matched as a
    duplicate (skip path) -- preserving the cross-role usage record
  - Prints count of entries written and skipped
- On rejection (user enters `n`): exits without writing, no file modified
- Does not infer or generate content -- parses only what the document contains

#### Duplicate Detection

- Duplicate check for stories: match on `employer` + primary tag
- Duplicate check for gap responses: match on normalized `gap_label`
- Duplicate check for questions: match on first 60 characters of `text`
- On skip: `roles_used` array is updated to include current role slug if not already present
- On overwrite: entry is replaced in full; `roles_used` is merged (not reset)

#### Tests

Unit tests cover:

- Story block parsing: employer/title/dates extraction, STAR component extraction,
  if-probed extraction, delivery note stripping
- Gap block parsing: label and severity extraction, triad extraction,
  short tenure section exclusion, note-card line stripping
- Question block parsing: question text extraction, rationale stripping,
  closing question exclusion
- Tag vocabulary validation: known tag passes, unknown tag warns but does not block
- Duplicate detection: story match, gap match, question match
- Skip path: `roles_used` updated, entry not overwritten
- Overwrite path: entry replaced, `roles_used` merged
- Parser filtering: `get_stories` by tag, by role, combined;
  `get_gap_responses` by gap_label; `get_questions` by stage
- Parser no-file behavior: returns empty list when library absent
- Library init: empty arrays written when file absent; existing content preserved

---

### Out of Scope

- Parsing Section 1 (Introduce Yourself monologue) -- stage and register-specific,
  not portable as a library item
- Parsing salary guidance -- role and stage-specific
- Parsing story-to-question routing tables -- role-specific, not portable
- Semantic or embedding-based story retrieval -- tag filtering is sufficient for initial build
- Editing or deleting existing library entries via script -- manual JSON edits acceptable
- Automatic capture without user confirmation -- user review before any write is required
- Any UI or web interface
- Integration of library content back into `phase5_interview_prep.py` -- that is the
  Phase 5 Library Integration feature (separate proposal)

---

## Review Annotations

*This section is populated during the Chat spec review step. Do not fill in manually.*
