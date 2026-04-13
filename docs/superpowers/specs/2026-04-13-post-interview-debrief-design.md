# Post-Interview Debrief Capture — Design Spec

**Date:** 2026-04-13
**Feature:** A (of 3-part sequence: A=capture, B=library extraction, C=Phase 5 integration)
**Proposal:** `docs/features/post-interview-debrief/proposal.md`

---

## Overview

Feature A captures a structured post-interview debrief and writes it to a JSON data store consumed by Feature C (phase5-library-integration). It is built in two sub-capabilities that share a single script and identical output schema:

- **A1 (MVP):** User fills a YAML template manually; a converter script validates and produces JSON
- **A2 (Follow-on):** An interactive guided questionnaire with AI-assisted follow-up questions produces JSON directly

Both write to `data/debriefs/[role-slug]/` — the path already referenced in the phase5-library-integration proposal.

---

## Architecture

### A1 — Template Fill Workflow

1. User runs `python scripts/phase_debrief.py --role X --stage Y --init`
2. Script creates `data/debriefs/X/` if needed, then writes a pre-populated YAML draft to `data/debriefs/X/debrief_[stage]_draft.yaml` with `role`, `stage`, and `produced_date` already filled in
3. User opens the draft in any editor and fills in the remaining fields
4. User runs `python scripts/phase_debrief.py --role X --stage Y --convert`
5. Script validates required fields and enum values, then writes JSON to `data/debriefs/X/debrief_[stage]_[interview-date]_filed-[produced-date].json`

### A2 — Interactive Workflow

1. User runs `python scripts/phase_debrief.py --role X --stage Y --interactive`
2. Script walks through each template section as a guided questionnaire
3. After each section response, passes the answer to Claude to decide if a follow-up question is warranted
4. On completion, writes the same JSON output schema as A1

### Format split

- **YAML:** authoring format — human-readable, easy to hand-edit, exposes the user to structured data
- **JSON:** output/data store format — consumed by Feature C, exposes the user to the downstream format

---

## YAML Template

**Reference template location:** `docs/features/post-interview-debrief/interview_debrief_template.yaml`

**Draft location (created by `--init`):** `data/debriefs/[role]/debrief_[stage]_draft.yaml`

```yaml
# Post-Interview Debrief
# Fill in all fields. Leave optional fields as null if not applicable.

metadata:
  role: "Viasat_SE_IS"          # pre-filled by --init
  stage: "hiring_manager"        # pre-filled by --init
  company: null                  # e.g. "Viasat"
  interviewer_name: null         # e.g. "Jane Smith"
  interviewer_title: null        # e.g. "Director of Systems Engineering"
  interview_date: null           # YYYY-MM-DD -- drives output filename
  format: null                   # phone | video | onsite
  produced_date: "2026-04-13"   # pre-filled by --init

advancement_read:
  assessment: null               # for_sure | maybe | doubt_it | definitely_not
  notes: null

stories_used:
  - tags: []                     # e.g. [leadership, cross-functional]
    framing: null                # brief description of how it was told
    landed: null                 # yes | partially | no

gaps_surfaced:
  - gap_label: null              # e.g. "no cleared SCIF experience"
    response_given: null
    response_felt: null          # strong | adequate | weak

salary_exchange:                 # all fields optional
  range_given_min: null
  range_given_max: null
  candidate_anchor: null
  candidate_floor: null
  notes: null

what_i_said: null                # free text -- claims, commitments, framings to stay consistent on

open_notes: null                 # anything else worth capturing
```

**Enum values:**
- `stage`: `recruiter_screen` | `hiring_manager` | `panel` | `final`
- `format`: `phone` | `video` | `onsite`
- `assessment`: `for_sure` | `maybe` | `doubt_it` | `definitely_not`
- `landed`: `yes` | `partially` | `no`
- `response_felt`: `strong` | `adequate` | `weak`

---

## Converter Script — `phase_debrief.py`

### Interface

```
python scripts/phase_debrief.py --role ROLE --stage STAGE --init
python scripts/phase_debrief.py --role ROLE --stage STAGE --convert
python scripts/phase_debrief.py --role ROLE --stage STAGE --interactive
```

### `--init` behavior

- Creates `data/debriefs/[role]/` if it does not exist
- Warns and prompts for confirmation if draft already exists (mirrors `check_overwrite()` pattern from `phase4_cover_letter.py`)
- Copies reference template, pre-fills `role`, `stage`, `produced_date`
- Prints the path to the created draft

### `--convert` behavior

- Reads `data/debriefs/[role]/debrief_[stage]_draft.yaml`
- **Required field validation:** `interview_date`, `metadata.format`, `advancement_read.assessment` -- names missing field, exits without writing
- **Enum validation:** `format`, `assessment`, `landed`, `response_felt` -- names field, lists accepted values, exits without writing
- No partial writes -- JSON only written if all validation passes
- Builds filename from `interview_date` and `produced_date` fields in the YAML
- Writes JSON to `data/debriefs/[role]/debrief_[stage]_[interview-date]_filed-[produced-date].json`
- Prints confirmation with output path

### `--interactive` behavior

- Walks through each section as a guided questionnaire
- Enum fields: displays valid options, re-prompts on invalid input (loops, does not exit)
- List sections (`stories_used`, `gaps_surfaced`): after each entry asks "Add another? (y/n)"
- After each section response, calls Claude to decide if a follow-up question is warranted
- Claude returns a question string or empty -- if empty, moves on silently
- Follow-up asked at most once per section, never chained
- Applies same validation rules as `--convert` before writing
- Writes same JSON output schema as A1

### AI follow-up system prompt (A2)

> "You are a debrief assistant. Given a candidate's response to a post-interview debrief section, decide if one targeted follow-up question would capture something valuable. If yes, return the question only. If no, return nothing. Do not assess, score, or infer anything about the interview outcome."

---

## JSON Output Schema

**Location:** `data/debriefs/[role]/debrief_[stage]_[interview-date]_filed-[produced-date].json`

```json
{
  "metadata": {
    "role": "Viasat_SE_IS",
    "stage": "hiring_manager",
    "company": "Viasat",
    "interviewer_name": "Jane Smith",
    "interviewer_title": "Director of Systems Engineering",
    "interview_date": "2026-04-10",
    "format": "video",
    "produced_date": "2026-04-13"
  },
  "advancement_read": {
    "assessment": "maybe",
    "notes": "Felt strong on technical but stumbled on the budget question."
  },
  "stories_used": [
    {
      "tags": ["leadership", "cross-functional"],
      "framing": "Led EO rewrite across three orgs under a hard deadline",
      "landed": "yes"
    }
  ],
  "gaps_surfaced": [
    {
      "gap_label": "no cleared SCIF experience",
      "response_given": "Acknowledged gap, redirected to adjacent classified work",
      "response_felt": "adequate"
    }
  ],
  "salary_exchange": {
    "range_given_min": 145000,
    "range_given_max": 165000,
    "candidate_anchor": 160000,
    "candidate_floor": null,
    "notes": null
  },
  "what_i_said": "Cited 12 years systems engineering experience. Said earliest start date is 6 weeks. Did not disclose floor.",
  "open_notes": null
}
```

**Schema rules:**
- All fields present even when null -- Feature C reads without defensive checks
- Salary values stored as numbers, not strings
- `stories_used` and `gaps_surfaced` always arrays, even if empty (`[]`)

---

## Out of Scope (inherited from proposal)

- Parsing debrief files into Phase 5 -- Feature C
- Extracting stories and gap responses into the interview library -- Feature B
- AI assessment, scoring, or sentiment analysis of interview outcomes
- Integration with calendar, email, or external systems
- Multi-interviewer panel capture in a single session
- Editing or amending a previously saved debrief file

---

## Downstream Compatibility

The JSON schema is designed against the phase5-library-integration proposal (`docs/features/phase5-library-integration/proposal.md`), which reads:
- `data/debriefs/[role-slug]/` for salary fields and continuity summary
- `what_i_said`, `advancement_read`, `stories_used` (labels), `gaps_surfaced` (labels) per debrief file
