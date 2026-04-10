# Interview Prep Stage Awareness Design
# Phase 5 — Interview Stage Awareness Update

Date: 2026-04-09
Status: Approved — ready for implementation planning

---

## Purpose

Update `scripts/phase5_interview_prep.py` to generate stage-appropriate interview prep packages.
The current script produces a single format regardless of interview type. A recruiter screen,
hiring manager interview, and team panel require fundamentally different preparation. This update
adds an `--interview_stage` parameter that drives stage-specific logic across all sections.

Source requirements: `docs/user_story_updates/interview_prep_update_proposal.md`

---

## Section 1 — Architecture

### Stage Profile Dictionary

A single `STAGE_PROFILES` dict is added at the top of the script alongside `MODEL` and
`SYSTEM_PROMPT`. It is keyed by stage name and contains all settings that vary by stage.
No stage strings are threaded through individual functions — `generate_prep()` resolves
the active profile once and passes the profile object forward.

```python
STAGE_PROFILES = {
    "recruiter": {
        "label": "Recruiter Screen",
        "description": "Short screen — confirm fit, do not volunteer gaps or technical depth.",
        "story_count": "1-2",
        "story_depth": "headline",       # headline | full | full_technical
        "gap_behavior": "omit",          # omit | note | full | full_peer
        "salary_in_section1": False,
        "section1_focus": "recruiter",
        "questions_prompt": "<stage-specific prompt string>",
    },
    "hiring_manager": {
        "label": "Hiring Manager Interview",
        "description": "60+ min interview — lead with program context awareness and collaborative framing.",
        "story_count": "3-4",
        "story_depth": "full",
        "gap_behavior": "note",
        "salary_in_section1": True,
        "section1_focus": "hiring_manager",
        "questions_prompt": "<stage-specific prompt string>",
    },
    "team_panel": {
        "label": "Team Panel Interview",
        "description": "90 min to 3 hr group interview — lead with technical specificity and process fluency.",
        "story_count": "4-6",
        "story_depth": "full_technical",
        "gap_behavior": "full_peer",
        "salary_in_section1": False,
        "section1_focus": "team_panel",
        "questions_prompt": "<stage-specific prompt string>",
        "peer_frame_prompt": "<peer frame generation prompt — see proposal AC 4a>",
    },
}
```

### Function Signature Change

`generate_prep()` gains a required `interview_stage: str` parameter. Callers pass the
validated stage string; the function resolves the profile internally.

### New Output Constants

`OUTPUT_FILENAME` and `OUTPUT_DOCX_FILENAME` become stage-specific at runtime:
- `interview_prep_recruiter.txt`
- `interview_prep_hiring_manager.txt`
- `interview_prep_team_panel.txt`

---

## Section 2 — CLI & Output

### New CLI Arguments

```
--interview_stage   {recruiter, hiring_manager, team_panel}   optional
--dry_run           flag, no value
```

If `--interview_stage` is omitted, the script prints the three options and prompts the user
to select one interactively before proceeding — consistent with the existing overwrite-protection
`input()` pattern.

Invalid stage values produce a clear error listing valid options.

`--dry_run` loads the resolved stage profile, prints it in readable form, and exits before
any API calls or file writes.

### Output File Header

Two new lines are added to the header block:

```
Stage: Recruiter Screen
Stage note: Short screen — confirm fit, do not volunteer gaps or technical depth.
```

### Overwrite Protection

The overwrite-protection check uses the stage-specific filename. Running recruiter and
hiring_manager preps for the same role produces two separate files without collision.

---

## Section 3 — Per-Section Behavior

### Section 1 — Company & Role Brief

Shared prompt template, parameterized by `section1_focus` from the stage profile:

- **recruiter**: Company overview, recent news, culture signals, interview process context.
  Suppress salary and program/technical depth.
- **hiring_manager**: Full company and business unit overview, program pain point context,
  salary guidance block included.
- **team_panel**: Company overview condensed to 2–3 sentences, emphasis on program-specific
  context, mission area, and technical environment.

### Section 1.5 — Introduce Yourself (NEW)

New section inserted between Company Brief and Story Bank.

The candidate's base intro monologue is stored in `candidate_profile.md` under a
`## INTRO MONOLOGUE` header — no PII in the script, consistent with the existing gaps
extraction pattern. The model receives the base text and tailors register and length to stage:

- **recruiter**: Concise, high-level, confirms fit signal
- **hiring_manager**: Program-context aware, collaborative framing
- **team_panel**: Technically grounded, peer register

Output and docx gain an "Introduce Yourself" section between Company Brief and Story Bank.

### Section 2 — Story Bank

Controlled by three profile fields:

**Story count** — from `story_count`: `"1-2"`, `"3-4"`, `"4-6"`

**Story depth** — from `story_depth`:
- `headline`: Headline + one-sentence result only. No STAR expansion.
- `full`: Full STAR with one "if probed" branch per story.
- `full_technical`: Full STAR with technical tool specificity and peer-credible detail.

**Gap framing in story bank** — from `gap_behavior`:
- `omit`: Suppress gap references entirely from story framing.
- `note`: Include a light gap awareness note where a story might brush against a gap.
- `full` / `full_peer`: Full gap awareness integrated into story framing.

**Role fit assessment** — included at all stages; condensed to 2 sentences for recruiter.

### Section 3 — Gap Preparation

Behavior driven by `gap_behavior` in the profile:

- **omit** (recruiter): API call is skipped entirely. Static block substituted:
  `"Gap prep omitted — do not volunteer gaps in a recruiter screen."`
- **note** (hiring_manager): Full gap prep, four-element format (Gap, Honest Answer, Bridge, Redirect).
  Includes hard questions list.
- **full_peer** (team_panel): Full gap prep, five-element format — adds Peer Frame element.
  Peer Frame prompt template stored in stage profile. See proposal AC 4a for spec.

**Short tenure explanation (NEW):** Candidate's prepared answer for short-tenure questions is
stored in `candidate_profile.md` under a `## SHORT TENURE EXPLANATION` header — no employer
names in the script. Extracted at runtime and prepended to Section 3 as a fixed block before
the gap analysis. Surfaces at all stages including recruiter (short tenure will come up regardless).

### Section 4 — Questions to Ask

Each stage has a fully separate prompt string stored in the profile's `questions_prompt` field.
Not a shared prompt with filters. Max 4 questions per stage. Each prompt encodes the stage
signal:

- **recruiter**: "I've done my homework and I'm a serious candidate"
- **hiring_manager**: "I understand programs and I want to know if this problem is worth solving"
- **team_panel**: "I've been in this seat before and I will be a peer, not a burden"

Questions that would be inappropriate for the audience are explicitly excluded from that
stage's prompt.

---

## Section 4 — Testing

All tests in `tests/phase5/test_interview_prep.py`. Mock client pattern throughout.

### New tests

| Test | What it verifies |
|---|---|
| `test_invalid_stage_raises_error` | Invalid stage string produces clear error before any API call |
| `test_stage_profile_lookup` | Each stage returns correct profile fields (story count, gap behavior, salary flag) |
| `test_recruiter_skips_gap_api_call` | Mock client receives no Section 3 call for recruiter stage; output contains omission note |
| `test_short_tenure_block_in_output` | Short tenure block is prepended to Section 3 when profile contains the header |
| `test_intro_monologue_in_output` | Intro section appears between Company Brief and Story Bank |
| `test_stage_in_output_header` | Stage label and description appear in output file header |
| `test_stage_specific_filenames` | Output paths use stage-specific filenames |
| `test_dry_run_no_api_calls` | Mock client receives zero calls; function returns without writing files |
| `test_team_panel_peer_frame_bold_in_docx` | `Peer Frame:` label renders bold in team panel docx |

### Updated tests

Existing tests updated to pass `interview_stage="hiring_manager"` to the revised
`generate_prep()` signature. Behavioral coverage unchanged.

---

## Section 5 — Out of Scope

Consistent with the source proposal:

- Post-interview debrief module
- STAR story library extraction
- UI or interactive mode beyond missing-stage fallback
- New story generation
- Changes to resume generation pipeline
- Scoring or ranking of candidate readiness by stage
- Updating pipeline_report to capture interview stage from job_pipeline.xlsx
  *(parking lot: pull stage from job_pipeline.xlsx into pipeline report)*

---

## Section 6 — candidate_profile.md Changes Required

Two new sections must be added to `candidate_profile.md` before running the updated script:

```markdown
## INTRO MONOLOGUE
[Candidate provides base intro text here — model will tailor per stage]

## SHORT TENURE EXPLANATION
[Candidate provides prepared short-tenure explanation here — no employer name in script]
```

The user will populate these sections. The script extracts them by header name at runtime.
