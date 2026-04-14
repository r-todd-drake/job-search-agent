# Workshop Capture and Interview Library

## User Story and Acceptance Criteria

### User Story
"As a job seeker who has workshopped and vetted interview stories and gap responses, I want a structured intake process and a queryable JSON library so that polished, role-tested content is available to seed future interview prep rather than being regenerated cold each time."

### Acceptance Criteria (AC)

**Interview Library File (`interview_library.json`)**
- File exists at `data/interview_library.json`
- File contains two top-level arrays: `stories` and `gap_responses`
- Each `stories` entry contains:
  - `id`: unique slug (e.g., `led-cross-functional-eo-rewrite`)
  - `title`: short human-readable label
  - `tags`: array of theme tags drawn from a controlled vocabulary (see Tag Vocabulary below)
  - `role_context`: the role slug(s) this story has been used or workshopped for
  - `stage`: interview stage(s) where this story has been used (recruiter / hiring-manager / panel / general)
  - `situation`: vetted situation text
  - `task`: vetted task text
  - `action`: vetted action text
  - `result`: vetted result text
  - `notes`: optional free-text field for workshop observations (e.g., "lands better when result is quantified")
  - `source`: one of `workshopped` | `debrief-captured` | `manual`
  - `last_updated`: ISO date string
- Each `gap_responses` entry contains:
  - `id`: unique slug (e.g., `no-cleared-scif-experience`)
  - `gap_label`: the gap as Phase 5 would name it
  - `tags`: array of theme tags
  - `role_context`: role slug(s) this response has been used or workshopped for
  - `gap`: the honest acknowledgment of the gap
  - `honest_answer`: the direct, non-defensive answer
  - `redirect`: the redirect to a strength or relevant evidence
  - `notes`: optional free-text workshop observations
  - `source`: one of `workshopped` | `debrief-captured` | `manual`
  - `last_updated`: ISO date string

**Tag Vocabulary**
- Controlled vocabulary defined in `data/interview_library_tags.json`
- Initial tag set covers: `leadership`, `cross-functional`, `technical-credibility`, `ambiguity`, `stakeholder-management`, `program-delivery`, `systems-engineering`, `communication`, `conflict-resolution`, `domain-gap`, `tools-gap`, `clearance`, `salary`, `culture-fit`
- New tags may be added to the vocabulary file; tags not in the vocabulary produce a validation warning on intake

**Workshop Intake Script (`phase_workshop.py`)**
- Script exists at `scripts/phase_workshop.py`
- Accepts `--type [story|gap]` and `--role [role-slug]` as arguments
- Presents a guided questionnaire to capture each required field
- For STAR stories: prompts each component (S / T / A / R) in sequence, then prompts for tags, stage, and notes
- For gap responses: prompts gap label, gap, honest answer, redirect, then tags and notes
- Validates that all required fields are populated before writing
- Validates tags against the controlled vocabulary; warns on unknown tags but does not block
- On completion, appends the new entry to `interview_library.json` with `source: workshopped` and current date
- Script does not generate or infer content -- it captures what the candidate provides verbatim
- If `interview_library.json` does not exist, script initializes it with empty arrays before appending

**Library Parser (`interview_library_parser.py`)**
- Module exists at `scripts/interview_library_parser.py`
- Exposes at minimum: `get_stories(tags=None, role=None, stage=None)` and `get_gap_responses(tags=None, role=None)`
- Filtering is additive (AND logic across provided filters)
- Returns empty list (not error) when no entries match
- Importable by Phase 5 without side effects

**Tests**
- Unit tests cover: story entry schema validation, gap entry schema validation, tag vocabulary enforcement warning, parser filtering logic (by tag, by role, by stage, combined), empty library initialization, append-without-duplicate behavior

### Out of Scope
- Automated extraction from debrief files into the library -- debrief capture is Feature A; pipeline from debrief to library is Feature C
- Editing or deleting existing library entries via script (manual JSON edits are acceptable for now)
- Semantic search or embedding-based retrieval -- tag-based filtering is sufficient for initial build
- Story quality scoring or ranking
- Any UI or web interface
