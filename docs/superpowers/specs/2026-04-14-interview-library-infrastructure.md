# Interview Library Infrastructure -- Design Spec

**Date:** 2026-04-14
**Status:** Ready to build
**Session scope:** Library infrastructure only -- see "Out of Scope" before starting

---

## Purpose of This Document

This spec is written for a fresh Claude Code session. It contains everything needed
to build the interview library infrastructure without reference to prior conversations.
Read this document completely before entering Plan mode.

---

## Where This Fits -- Phase 5 Workflow

Phase 5 owns everything from interview prep generation through post-interview capture
and library maintenance. The full workflow is documented at:
`docs/features/phase5_workflow_orchestration/phase5_workflow_orchestration.md`

The short version:

```
1. phase5_interview_prep.py   -- generates prep package (.docx / .txt)
2. Workshop with Claude Chat  -- candidate refines stories, gaps, questions
3. phase5_workshop_capture.py -- parses workshopped .docx, writes to library  [NOT YET BUILT]
4. Candidate conducts interview
5. phase5_debrief.py          -- captures what happened                        [BUILT]
6. phase5_interview_prep.py   -- next stage, now library-seeded                [FUTURE]
```

The interview library sits at the center of this cycle. It is the persistent,
cross-role store of vetted stories, gap responses, and questions. Every feature
in steps 3 and 6 depends on it existing.

---

## What Is Already Built

| Script | Status | Notes |
|--------|--------|-------|
| `scripts/phase5_interview_prep.py` | Built, user-tested | Large file -- do not modify in this session |
| `scripts/phase5_debrief.py` | Built, user-tested | 51 tests passing |
| `tests/test_phase5_debrief.py` | Built, 51 tests | Do not modify in this session |

---

## What This Session Builds

Three artifacts, all foundational -- nothing else touches them yet:

1. `data/interview_library.json` -- initialized empty; written by future scripts
2. `data/interview_library_tags.json` -- controlled tag vocabulary
3. `scripts/interview_library_parser.py` -- read-only query module

The capture script (`phase5_workshop_capture.py`) and library integration into
`phase5_interview_prep.py` are separate features built after this one. Do not
start them in this session.

---

## Key Design Decisions (From Review Session 2026-04-14)

These decisions are locked. Do not re-open them in Plan mode.

**Build order is fixed:** Library infrastructure first. Workshop capture second.
Debrief redesign third. Library integration into prep fourth. This sequence is
non-negotiable -- each step depends on the prior one.

**Library is cross-role, not role-scoped.** Content captured from one role's
prep is available to seed all future roles. Tag-based filtering ensures only
relevant content surfaces for a given role.

**Parser is read-only with no side effects.** It must be safely importable by
`phase5_interview_prep.py` without triggering any writes or initialization.

**Library init is non-destructive.** If `interview_library.json` already exists,
its content is never overwritten on init. If it does not exist, it is created
with empty arrays.

**Tags not in vocabulary produce a warning but do not block any operation.**
The vocabulary is a guide, not a hard gate.

**The debrief will be redesigned** in a future session to pre-populate from the
library (list-select UX for stories/gaps/questions). That redesign depends on
this infrastructure. The current `phase5_debrief.py` is correct as-is for now.

---

## Acceptance Criteria

### 1. Interview Library File (`data/interview_library.json`)

- File is initialized as `{ "stories": [], "gap_responses": [], "questions": [] }`
  if it does not exist
- Existing content is never overwritten on init
- Three top-level arrays: `stories`, `gap_responses`, `questions`

**Each `stories` entry schema:**
```json
{
  "id": "g2ops-mbse-bottleneck",
  "title": "Short human-readable label from story header",
  "tags": ["mbse", "systems-engineering"],
  "employer": "G2 Ops",
  "title_held": "Systems Engineer",
  "dates": "2021 -- 2023",
  "situation": "...",
  "task": "...",
  "action": "...",
  "result": "...",
  "if_probed": "..." ,
  "notes": null,
  "source": "workshopped",
  "roles_used": ["Viasat_SE_IS"],
  "last_updated": "2026-04-14"
}
```

- `id`: unique slug auto-generated from employer + primary tag
- `if_probed`: null if absent
- `notes`: null on creation; reserved for manual annotation
- `source`: always `"workshopped"` on creation
- `roles_used`: seeded with the capture role slug at creation

**Each `gap_responses` entry schema:**
```json
{
  "id": "ip-networking-expertise",
  "gap_label": "IP Networking Expertise",
  "severity": "required",
  "tags": ["domain-gap", "tools-gap"],
  "honest_answer": "...",
  "bridge": "...",
  "redirect": "...",
  "notes": null,
  "source": "workshopped",
  "roles_used": ["Viasat_SE_IS"],
  "last_updated": "2026-04-14"
}
```

- `severity`: `"required"` or `"preferred"`
- `honest_answer`, `bridge`, `redirect`: the gap response triad

**Each `questions` entry schema:**
```json
{
  "id": "integration-challenge-current-program",
  "stage": "hiring_manager",
  "category": "integration-challenge",
  "text": "What is the most significant integration challenge on the current program?",
  "tags": ["integration", "program-delivery"],
  "notes": null,
  "source": "workshopped",
  "roles_used": ["Viasat_SE_IS"],
  "last_updated": "2026-04-14"
}
```

- `stage`: `"recruiter"` / `"hiring_manager"` / `"team_panel"`
- `category`: category label inferred from question content

---

### 2. Tag Vocabulary (`data/interview_library_tags.json`)

File structure:
```json
{
  "tags": [
    "leadership",
    "cross-functional",
    "technical-credibility",
    "ambiguity",
    "stakeholder-management",
    "program-delivery",
    "systems-engineering",
    "communication",
    "conflict-resolution",
    "domain-gap",
    "tools-gap",
    "clearance",
    "salary",
    "culture-fit",
    "mbse",
    "requirements-analysis",
    "integration",
    "v-and-v",
    "architecture",
    "domain-translation"
  ]
}
```

- Tags not in vocabulary produce a warning but do not block any operation
- New tags may be added manually at any time

---

### 3. Library Parser (`scripts/interview_library_parser.py`)

**Public interface:**

```python
def get_stories(tags=None, role=None, stage=None) -> list
def get_gap_responses(tags=None, role=None, gap_label=None) -> list
def get_questions(tags=None, role=None, stage=None) -> list
```

- Filtering is additive (AND logic across all provided filters)
- All parameters are optional; omitting all returns all entries of that type
- Returns empty list (not error) when no entries match
- Returns empty list (not error) if `interview_library.json` does not exist
- Returns empty list (not error) if `data/` directory does not exist
- No side effects on import -- safe to import without initializing any files
- Reads from `data/interview_library.json` relative to project root
- Does not write to any file

**Filtering behavior:**

- `tags`: returns entries where entry tags and filter tags share at least one value
- `role`: returns entries where `roles_used` contains the role slug
- `stage`: for questions only -- returns entries where `stage` matches exactly
- `gap_label`: for gap responses only -- normalized match (lowercase, stripped)

---

### 4. Tests (`tests/test_interview_library_parser.py`)

Unit tests must cover:

- `get_stories` with no filters: returns all stories
- `get_stories` filtered by single tag: returns only matching entries
- `get_stories` filtered by role: returns only entries used for that role
- `get_stories` filtered by tag + role (AND logic): returns intersection
- `get_stories` when library file absent: returns empty list, no error
- `get_stories` when library is empty (`[]`): returns empty list
- `get_gap_responses` filtered by `gap_label`: normalized match works
- `get_gap_responses` filtered by tag: returns matching entries
- `get_questions` filtered by stage: returns only that stage
- `get_questions` filtered by stage + tag: AND logic
- Library init: empty arrays written when file absent
- Library init: existing content preserved when file present
- Tag vocabulary: known tag present in file; structure is valid JSON with `tags` array

---

## Files to Read Before Starting

Read these before entering Plan mode:

1. `docs/features/phase5_workshop_capture/proposal.md` -- full AC for the capture
   script that will consume this infrastructure (read to understand consumer needs)
2. `docs/features/phase5_library_integration/proposal.md` -- AC for library
   integration into prep (read to understand the other consumer)
3. `scripts/phase5_debrief.py` -- understand existing patterns (imports, structure,
   CLAUDE.md compliance)
4. `CLAUDE.md` -- safety rules and code style (en dashes, strip_pii, no hardcoded PII)

Do NOT read or modify:
- `data/` (personal data)
- `scripts/phase5_interview_prep.py` (not in scope -- large file, leave alone)

---

## Session Management Guidance

This feature has two sub-components: the data files and the parser module.
Both are small enough to build in a single session.

If context window usage approaches 40% before tests are written, prioritize
the parser module and its tests. The JSON schema files can be committed without
tests (they are data, not logic).

Do not compress or skip tests to fit within a session. A partial build with
full tests is preferable to a complete build with untested code.

---

## Out of Scope for This Session

Do not build any of the following -- they are separate features with their own proposals:

- `phase5_workshop_capture.py` -- capture script (next feature after this one)
- Any changes to `phase5_interview_prep.py`
- Any changes to `phase5_debrief.py`
- The debrief redesign (list-select UX, pre-populated from library)
- Semantic or embedding-based story retrieval
- Editing or deleting library entries via script
- Any UI or web interface
- The `--from-debrief` intake path

---

## Definition of Done

- [ ] `data/interview_library.json` initializes correctly (empty arrays, non-destructive)
- [ ] `data/interview_library_tags.json` exists with full initial tag set
- [ ] `scripts/interview_library_parser.py` passes all tests
- [ ] `tests/test_interview_library_parser.py` -- all tests passing
- [ ] `python -m py_compile scripts/interview_library_parser.py` returns OK
- [ ] All new files committed to `master`
