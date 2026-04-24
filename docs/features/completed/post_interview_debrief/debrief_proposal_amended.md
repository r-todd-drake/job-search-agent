# Post-Interview Debrief Capture (Amended)

## Amendment Notes
*This proposal supersedes the original `completed_post_interview_debrief_proposal.md`.*

*Changes from original:*
- *`interviewer_name` and `interviewer_title` flat fields replaced by `interviewers` array*
- *Each interviewer entry includes `notes` field for personalization context*
- *`--panel_label` optional argument added to support multi-panel interview sessions*
- *Filename pattern updated to include panel label when provided*
- *One-interviewer-per-file constraint removed -- one file per interview session*

---

## User Story and Acceptance Criteria

### User Story
"As a job seeker who has just completed an interview, I want a structured debrief
workflow that captures how the interview went, who was in the room, what content came
up, what salary information was exchanged, and what I told the interviewers -- so that
I have a reliable record to feed future prep, generate personalized thank you letters,
track advancement likelihood, and maintain consistency across interview stages."

---

### Acceptance Criteria (AC)

#### Debrief Template (`templates/interview_debrief_template.yaml`)

- Template contains the following sections:
  - **Interview Metadata**: date, role slug, company, interview stage, format,
    optional panel label, and an `interviewers` array (see below)
  - **Interviewers Array**: one entry per interviewer present in the session, each
    containing:
    - `name`: interviewer name
    - `title`: interviewer title
    - `notes`: free-text field capturing anything specific and notable about this
      interviewer -- a question they asked that stood out, background from LinkedIn
      research, a program or project they mentioned, a shared experience, or anything
      that would support a personalized follow-up
  - **Advancement Read**: single-select field (`for_sure` / `maybe` / `doubt_it` /
    `definitely_not`) plus free-text notes field
  - **Stories Used**: list of stories told during the session, each with theme tag(s),
    brief description of how it was framed, and a `landed` field
    (`yes` / `partially` / `no`)
  - **Gaps Surfaced**: list of gaps that came up, each with gap label, how the
    candidate responded, and a `response_felt` field (`strong` / `adequate` / `weak`)
  - **Salary Exchange**: structured fields for range given by interviewer (min/max),
    candidate anchor provided (if any), candidate floor disclosed (if any), and a
    free-text notes field; all fields optional
  - **Continuity -- What I Said**: free-text section capturing specific claims,
    commitments, framings, or positions given during this session that must not be
    contradicted in future stages (years of experience cited, availability date,
    relocation stance, interest level framing)
  - **Open Notes**: unstructured free-text for anything else worth capturing

#### Debrief Script (`scripts/phase5_debrief.py`)

- Accepts `--role [role-slug]` and `--stage [stage]` as required arguments
- Accepts `--panel_label [label]` as an optional argument for distinguishing
  multiple panel sessions at the same stage (e.g., `se_team`, `business_leaders`)
- Panel label is free-text; no controlled vocabulary enforced -- flexibility
  takes priority over consistency here
- On launch, presents each template section interactively as a guided questionnaire
- For the `interviewers` section:
  - Prompts for the first interviewer's name, title, and notes
  - After each entry, asks: `"Add another interviewer? (y/n):"`
  - Continues until the user declines
  - Minimum one interviewer entry required; script does not proceed without it
- For structured fields (advancement read, landed, response_felt), presents valid
  options and validates input
- For free-text fields, accepts open input with no validation
- Script has latitude to ask one AI-generated follow-up question per section if a
  response suggests something worth capturing; follow-up is optional for the user
- On completion, writes a populated debrief file to
  `data/debriefs/[role]/debrief_[stage]_[panel_label]_[interview-date]_filed-[produced-date].json`
  when `--panel_label` is provided, or
  `data/debriefs/[role]/debrief_[stage]_[interview-date]_filed-[produced-date].json`
  when it is not
- JSON output schema matches the template sections above
- Script does not infer or generate content -- captures only what the candidate provides

#### Output File Schema

```json
{
  "metadata": {
    "role": "Viasat_SE_IS",
    "stage": "panel",
    "panel_label": "se_team",
    "company": "Viasat",
    "interviewers": [
      {
        "name": "...",
        "title": "...",
        "notes": "Asked specifically about MBSE toolchain governance. LinkedIn shows..."
      },
      {
        "name": "...",
        "title": "...",
        "notes": "Mentioned current pain point with interface definition across subsystems."
      }
    ],
    "interview_date": "2026-04-20",
    "format": "video",
    "produced_date": "2026-04-20"
  },
  "advancement_read": {
    "assessment": "maybe",
    "notes": "..."
  },
  "stories_used": [
    {
      "tags": ["mbse", "program-delivery"],
      "framing": "...",
      "landed": "yes",
      "library_id": null
    }
  ],
  "gaps_surfaced": [
    {
      "gap_label": "IP Networking Expertise",
      "response_given": "...",
      "response_felt": "adequate"
    }
  ],
  "salary_exchange": {
    "range_given_min": null,
    "range_given_max": null,
    "candidate_anchor": null,
    "candidate_floor": null,
    "notes": null
  },
  "what_i_said": "...",
  "open_notes": "..."
}
```

- All optional fields present in output with null values if not provided
- `panel_label` present in metadata when provided; null when not provided
- Role slug in filename matches `--role` argument exactly

#### Modes

- `--init`: creates a YAML draft pre-filled with role, stage, panel label (if provided),
  and date for manual completion
- `--convert`: validates the YAML draft and writes JSON output; validates that
  `interviewers` array contains at least one entry with a non-null `name`
- `--interactive`: guided questionnaire with optional AI follow-up questions

#### Tests

Unit tests cover:

- Single interviewer entry: name, title, notes captured correctly
- Multiple interviewer entries: array populated correctly, all entries present in output
- Panel label present: included in metadata and filename
- Panel label absent: null in metadata, omitted from filename
- Minimum interviewer validation: convert mode rejects file with empty interviewers array
- Existing tests for validation, enum enforcement, salary casting, and file output
  continue to pass

---

### Out of Scope

- Parsing or ingesting debrief files into Phase 5 prep generation -- Phase 5
  Library Integration proposal
- Extracting stories and gap responses into the interview library -- Phase 5
  Workshop Capture proposal
- Thank you letter generation -- `phase5_thankyou.py` proposal
- Automated scoring, sentiment analysis, or AI assessment of interview outcome
- Integration with calendar, email, or any external system
- Editing or amending a previously saved debrief file

---

## Review Annotations

*This section is populated during the Chat spec review step. Do not fill in manually.*
