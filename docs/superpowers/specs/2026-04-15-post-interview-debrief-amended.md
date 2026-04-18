# Post-Interview Debrief -- Amendment Spec

**Date:** 2026-04-15
**Status:** Ready to build
**Supersedes:** `docs/superpowers/specs/2026-04-13-post-interview-debrief-design.md` (original build -- already complete)
**Session scope:** Amendment only -- the original debrief script is built and tested. Do not rebuild it.

---

## How to Use This Document

This spec is written for a fresh Claude Code session using the superpowers plugin.

**Before writing any code or plan:**
1. Read all files listed in "Files to Read Before Starting" below
2. Invoke the `superpowers:brainstorming` skill -- explore intent, requirements, and design
3. Invoke the `superpowers:writing-plans` skill -- produce a step-by-step implementation plan
4. Use `superpowers:test-driven-development` during implementation
5. Use `superpowers:verification-before-completion` before claiming done

Do not begin implementation until the plan is reviewed and confirmed.

---

## Context -- What Is Already Built

The debrief script was built on 2026-04-13 and is production-ready with 51 passing tests.
The original design spec is at `docs/superpowers/specs/2026-04-13-post-interview-debrief-design.md`.

| Artifact | Status |
|---|---|
| `scripts/phase5_debrief.py` | Built, user-tested |
| `tests/test_phase5_debrief.py` | 51 tests passing |
| `templates/interview_debrief_template.yaml` | Built |

**The 51 existing tests are a regression baseline. All must continue to pass after this amendment.**

---

## What This Session Builds -- The Delta Only

Three structural changes to the existing script and template. Nothing else.

### Change 1 -- Interviewers Array

**Current schema** (flat fields in metadata):
```json
"interviewer_name": "Jane Smith",
"interviewer_title": "Director of Systems Engineering"
```

**Amended schema** (array, one entry per person in the room):
```json
"interviewers": [
  {
    "name": "Jane Smith",
    "title": "Director of Systems Engineering",
    "notes": "Asked specifically about MBSE toolchain governance. LinkedIn shows background in DOORS."
  },
  {
    "name": "...",
    "title": "...",
    "notes": "..."
  }
]
```

- `notes` captures anything specific about this interviewer: a question they asked, background from research, a program or project they mentioned, a shared experience -- anything supporting personalized follow-up
- `notes` is free-text, no validation
- Minimum one entry required; `--convert` rejects a file with an empty `interviewers` array or no entry with a non-null `name`

### Change 2 -- Panel Label Argument

- New optional CLI argument: `--panel_label [label]`
- Free-text; no controlled vocabulary
- Used to distinguish multiple panel sessions at the same stage (e.g., `se_team`, `business_leaders`)
- `panel_label` stored as a field in `metadata`; null when not provided

### Change 3 -- Updated Filename Pattern

**Without panel label (existing behavior, unchanged):**
```
data/debriefs/[role]/debrief_[stage]_[interview-date]_filed-[produced-date].json
```

**With panel label (new):**
```
data/debriefs/[role]/debrief_[stage]_[panel_label]_[interview-date]_filed-[produced-date].json
```

---

## Updated Output Schema

```json
{
  "metadata": {
    "role": "Viasat_SE_IS",
    "stage": "panel",
    "panel_label": "se_team",
    "company": "Viasat",
    "interviewers": [
      {
        "name": "Jane Smith",
        "title": "Director of Systems Engineering",
        "notes": "Asked specifically about MBSE toolchain governance."
      },
      {
        "name": "Bob Jones",
        "title": "Senior Systems Engineer",
        "notes": "Mentioned current pain point with interface definition across subsystems."
      }
    ],
    "interview_date": "2026-04-20",
    "format": "video",
    "produced_date": "2026-04-20"
  },
  "advancement_read": { "assessment": "maybe", "notes": "..." },
  "stories_used": [
    { "tags": ["mbse", "program-delivery"], "framing": "...", "landed": "yes", "library_id": null }
  ],
  "gaps_surfaced": [
    { "gap_label": "IP Networking Expertise", "response_given": "...", "response_felt": "adequate" }
  ],
  "salary_exchange": {
    "range_given_min": null, "range_given_max": null,
    "candidate_anchor": null, "candidate_floor": null, "notes": null
  },
  "what_i_said": "...",
  "open_notes": "..."
}
```

- `panel_label` present and populated when `--panel_label` is provided; `null` when not
- `interviewer_name` and `interviewer_title` flat fields are removed entirely
- All other fields unchanged from the original schema

---

## Interactive Mode -- Interviewers Capture Loop

In `--interactive` mode, the interviewers section works as follows:

1. Prompt for first interviewer's name, title, and notes
2. After each entry, ask: `"Add another interviewer? (y/n):"`
3. Continue until user declines
4. Minimum one interviewer required -- do not advance past this section without at least one entry with a non-null name

Notes field prompt should make clear what to capture:
`"Notes (questions asked, background, programs mentioned, anything for personalized follow-up):"`

---

## Template Update

`templates/interview_debrief_template.yaml` must be updated to replace the flat
`interviewer_name` / `interviewer_title` fields with an `interviewers` array:

```yaml
metadata:
  role: null
  stage: null
  panel_label: null        # optional -- e.g. "se_team" or "business_leaders"
  company: null
  interviewers:
    - name: null
      title: null
      notes: null          # questions asked, background, programs mentioned, shared experiences
  interview_date: null
  format: null
  produced_date: null
```

---

## New Tests Required

These 6 test cases are additive. All 51 existing tests must continue to pass.

1. **Single interviewer** -- name, title, notes captured correctly in output JSON
2. **Multiple interviewers** -- array populated correctly; all entries present; none dropped
3. **Panel label present** -- `panel_label` included in metadata and in output filename
4. **Panel label absent** -- `panel_label` is `null` in metadata; omitted from filename
5. **Minimum interviewer validation** -- `--convert` rejects a file with an empty `interviewers`
   array; rejects a file where all entries have null `name`; clear error message on rejection
6. **Regression** -- all 51 existing tests pass without modification

---

## Files to Read Before Starting

Read in this order. Do not read files not on this list.

| File | Purpose | Required? |
|---|---|---|
| `CLAUDE.md` | Safety rules, code style (en dashes, no PII, strip_pii usage) | Yes |
| `docs/features/post-interview-debrief/debrief_proposal_amended.md` | Acceptance criteria for the amendment | Yes |
| `docs/superpowers/specs/2026-04-13-post-interview-debrief-design.md` | Original design spec -- read to understand existing behavior; do not reimplement | Reference |
| `scripts/phase5_debrief.py` | Existing script to amend | Yes |
| `tests/test_phase5_debrief.py` | Regression baseline -- 51 tests must pass | Yes |
| `templates/interview_debrief_template.yaml` | YAML template to amend | Yes |

**Do NOT read:**
- `scripts/phase5_interview_prep.py` -- large file, different feature, not in scope
- Any library infrastructure or workshop capture proposals -- different feature chain
- The orchestration doc -- context not needed for this session

---

## Out of Scope for This Session

- Any changes to `phase5_interview_prep.py`
- Library infrastructure (`interview_library.json`, parser, tags)
- Workshop capture script
- Thank you letter generator
- The future debrief redesign (list-select UX, pre-populated from library) -- that is a
  separate feature depending on library infrastructure
- Semantic analysis, scoring, or AI assessment of interview outcome
- Editing or amending previously saved debrief files

---

## Definition of Done

- [ ] `scripts/phase5_debrief.py` accepts `--panel_label` optional argument
- [ ] Flat `interviewer_name` / `interviewer_title` fields replaced by `interviewers` array
- [ ] Each interviewer entry has `name`, `title`, `notes` fields
- [ ] Interactive mode prompts for multiple interviewers with loop; minimum one enforced
- [ ] `--convert` validates minimum one interviewer with non-null `name`
- [ ] `panel_label` in metadata when provided; null when not
- [ ] Filename includes panel label when provided; omits when not
- [ ] `templates/interview_debrief_template.yaml` updated with interviewers array
- [ ] 6 new tests written and passing
- [ ] All 51 existing tests continue to pass
- [ ] `python -m py_compile scripts/phase5_debrief.py` returns OK
- [ ] Changes committed to `master`
