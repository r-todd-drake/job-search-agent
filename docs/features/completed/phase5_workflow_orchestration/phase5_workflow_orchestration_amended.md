# Phase 5 Workflow -- Feature Map and Orchestration (Amended)

## Amendment Notes
*This document supersedes the previous `phase5_workflow_orchestration.md`.*

*Changes from previous version:*
- *Multi-interviewer debrief structure reflected throughout*
- *Panel label threading added to Step 5 and downstream steps*
- *Step 5.5 added: thank you letter generation*
- *Story and gap performance signal added to Step 6 description*
- *Feature status table updated with thank you letter feature*
- *Two-panel session handling explained in panel interview note*

---

## Workflow Overview

```
                        ┌─────────────────────────────┐
                        │   interview_library.json     │
                        │   (cross-role, persistent)   │
                        │                              │
                        │  stories []                  │
                        │  gap_responses []            │
                        │  questions []                │
                        └────────────┬────────────────┘
                                     │ seeds                  ▲ captures
                                     │                        │
          ┌──────────────────────────▼────────────────────────┴──────────────┐
          │                                                                   │
          │   PHASE 5 INTERVIEW PREP WORKFLOW  (per role, per stage)         │
          │                                                                   │
          │  1. phase5_interview_prep.py  ──────────────►  .docx / .txt      │
          │          │                                      prep package      │
          │          │ (library-seeded if available)               │          │
          │          │ (performance signal on seeded content)      │          │
          │          │                                             │          │
          │  2. Workshop with Claude Chat  ◄────────────────────  │          │
          │          │ refine stories, gaps, questions             │          │
          │          │ add interviewer context                     │          │
          │          │                                             │          │
          │  3. phase5_workshop_capture.py  ────────────────────► │          │
          │          │ parse revised .docx                         │          │
          │          │ strip interviewer context                   │          │
          │          │ write durable content to library            │          │
          │          │                                             │          │
          │  4. Candidate conducts interview                       │          │
          │          │                                             │          │
          │  5. phase5_debrief.py  ─────────────────────────────► │          │
          │          │ capture what happened                       │          │
          │          │ interviewers array (name, title, notes)     │          │
          │          │ stories used + landed ratings               │          │
          │          │ gaps surfaced + response ratings            │          │
          │          │ salary exchange                             │          │
          │          │ what_i_said continuity notes                │          │
          │          │                                             │          │
          │  5.5 phase5_thankyou.py  ───────────────────────────► │          │
          │          │ one letter per interviewer                  │          │
          │          │ personalized from interviewer notes         │          │
          │          │ consistent with what_i_said                 │          │
          │          │                                             │          │
          │  6. phase5_interview_prep.py (next stage)             │          │
          │          │ library-seeded from step 3                  │          │
          │          │ performance signal from prior debriefs      │          │
          │          │ continuity summary from step 5              │          │
          │          │ salary actuals from step 5                  │          │
          │          └─────────────────────────────────────────── ┘          │
          │                                                                   │
          └───────────────────────────────────────────────────────────────────┘
```

---

## Feature Status and Dependencies

| Feature | Script(s) | Status | Depends On |
|---|---|---|---|
| Interview prep generation | `phase5_interview_prep.py` | ✅ Built, user-tested | JD, candidate profile, experience library, tailored resume |
| Post-interview debrief | `phase5_debrief.py` | ✅ Built, user-tested -- amendment pending | None |
| Interview library infrastructure | `interview_library.json`, `interview_library_tags.json`, `interview_library_parser.py` | 🔲 Proposed | None -- foundational |
| Workshop capture | `phase5_workshop_capture.py` | 🔲 Proposed | Library infrastructure |
| Phase 5 library integration | `phase5_interview_prep.py` extensions | 🔲 Proposed | Library infrastructure, workshop capture, debrief amendment |
| Thank you letter generator | `phase5_thankyou.py` | 🔲 Proposed | Debrief amendment |

**Build order is constrained:**
1. Debrief amendment (`phase5_debrief.py`) -- foundational; unlocks thank you letters
   and correct continuity summary structure
2. Library infrastructure -- foundational; unlocks workshop capture and library integration
3. Workshop capture and thank you letter generator -- can be built in parallel after
   their respective dependencies are met
4. Phase 5 library integration -- last; requires library infrastructure, at least one
   completed capture run for meaningful integration testing, and debrief amendment

---

## Data Flows by Step

### Step 1 -- Generate Prep Package

**Script:** `phase5_interview_prep.py --role [role] --interview_stage [stage]`

**Reads:**
- `data/job_packages/[role]/job_description.txt`
- `data/experience_library/candidate_profile.md`
- `data/experience_library/experience_library.json`
- `data/job_packages/[role]/stage4_final.txt` (or `stage2_approved.txt`)
- `data/interview_library.json` *(once Phase 5 library integration is built)*
- `data/debriefs/[role]/` *(once Phase 5 library integration is built)*

**Writes:**
- `data/job_packages/[role]/interview_prep_[stage].txt`
- `data/job_packages/[role]/interview_prep_[stage].docx`

**Terminal notifications (once library integration is built):**
- If unmatched debrief content found: prompt to run `phase5_workshop_capture.py`
- If debrief exists for current stage: prompt to run `phase5_thankyou.py`

---

### Step 2 -- Workshop with Claude Chat

**No script.** User pastes prep package into Claude Chat and workshops:
- Introduction monologue register and framing
- STAR story accuracy, specificity, and delivery
- Gap response confidence and redirect strength
- Questions to ask -- selection and tailoring to the specific interviewer
- Integration of interviewer-specific context (background research, known programs,
  anticipated focus areas)

**Output:** Revised `.docx` saved to
`data/job_packages/[role]/interview_prep_[stage].docx`

**Note:** Interviewer-specific context added during workshopping is intentionally
present in the workshopped .docx -- it is useful for interview preparation. The
capture script strips this content before writing to the library.

---

### Step 3 -- Capture Workshopped Content

**Script:** `phase5_workshop_capture.py --role [role] --stage [stage]`

**Reads:**
- `data/job_packages/[role]/interview_prep_[stage].docx` (workshopped version)
- `data/interview_library_tags.json`

**Writes:**
- `data/interview_library.json` (appends new entries; updates `roles_used` on
  matched duplicates)

**What is captured (durable, role-portable):**
- Stories: employer, title, dates, STAR components, if-probed branch, theme tags
- Gap responses: gap label, severity, honest answer, bridge, redirect, theme tags
- Questions: question text, stage, category, theme tags

**What is stripped (stage or interviewer-specific):**
- Introduction monologue and all Section 1 content
- Delivery register notes and italicized coaching lines
- Story-to-question routing tables
- Short tenure explanation
- Hard questions lists
- Closing question tactic
- Salary guidance
- Interviewer background context and personalization notes
- Section rationale lines

---

### Step 4 -- Conduct Interview

No script. Candidate uses the workshopped .docx as reference material.

**Panel interview note:** When a stage involves multiple panel sessions with
different audiences (e.g., a technical SE panel and a business leaders panel),
each session is treated as a separate interview:
- Separate prep run: `phase5_interview_prep.py --interview_stage panel`
  for each session, distinguished by stage focus and workshopped separately
- Separate debrief: `phase5_debrief.py --stage panel --panel_label [label]`
  for each session
- Separate thank you letters: `phase5_thankyou.py --stage panel
  --panel_label [label]` for each session
- Both debriefs feed the continuity summary for the next stage prep run

---

### Step 5 -- Capture Debrief

**Script:** `phase5_debrief.py --role [role] --stage [stage]`
(with `--panel_label [label]` when distinguishing multiple panel sessions)

**Reads:** Nothing -- interactive capture only.

**Writes:**
- `data/debriefs/[role]/debrief_[stage]_[date]_filed-[date].json`
- `data/debriefs/[role]/debrief_[stage]_[panel_label]_[date]_filed-[date].json`
  (when panel label is provided)

**Fields captured:**
- Interview metadata: date, stage, format, panel label (if provided)
- Interviewers array: one entry per interviewer, each with name, title, and notes
  (notes captures specific questions asked, background details, programs mentioned,
  shared experiences -- anything supporting personalized follow-up)
- Advancement read assessment and notes
- Stories used: tags, framing, landed rating, library ID (if known)
- Gaps surfaced: gap label, response given, response felt rating
- Salary exchange: range given, candidate anchor, candidate floor
- What I said: continuity notes for future stages
- Open notes

---

### Step 5.5 -- Generate Thank You Letters

**Script:** `phase5_thankyou.py --role [role] --stage [stage]`
(with `--panel_label [label]` when applicable)

**Reads:**
- `data/debriefs/[role]/debrief_[stage]_[...].json` (most recently filed match)
- `data/job_packages/[role]/job_description.txt`
- `data/job_packages/[role]/stage4_final.txt` (or `stage2_approved.txt`)
- `data/experience_library/candidate_profile.md`

**Writes:** One `.txt` and one `.docx` per interviewer:
- `data/job_packages/[role]/thankyou_[stage]_[panel_label]_[lastname]_[date].txt`
- `data/job_packages/[role]/thankyou_[stage]_[panel_label]_[lastname]_[date].docx`

**Personalization sources per letter:**
- `interviewer_notes`: primary personalization anchor -- specific question asked,
  background detail, program mentioned, shared experience
- Landed stories from the debrief: referenced naturally, not recited
- `what_i_said`: letter stays consistent with stated positions
- Interviewer title: drives tone calibration (technical / executive / recruiter)

---

### Step 6 -- Generate Next Stage Prep Package

Repeats Step 1 with library and debrief data now available:
- Stories, gaps, and questions seeded from library where tag matches exist
- Performance signal surfaced for seeded content ("Used N times: yes x2 / partially x1")
- Continuity summary appended from all prior debriefs for this role, showing all
  interviewers per session
- Salary actuals override if salary data captured in any prior debrief
- Terminal notifications for workshop capture and thank you letters if applicable

Cycle continues for each interview stage until the role is closed.

---

## Library Content Lifecycle

```
First capture (workshopped)
  → source: workshopped, roles_used: [role_A]
  → tags assigned, content verified by user at capture

Used to seed next role
  → roles_used: [role_A, role_B]
  → performance signal begins accumulating from debrief landed ratings

Debrief records performance
  → landed: yes/partially/no per story
  → response_felt: strong/adequate/weak per gap response
  → surfaced as performance annotation on next seeded use

Story workshopped again for new role
  → refined version captured back to library
  → roles_used grows, content improves with each cycle
```

Stories that land consistently become the candidate's core narrative assets.
Stories that do not land surface as candidates for revision or retirement.

---

## Cross-Role Portability -- Design Rationale

The interview library is deliberately not role-scoped. Content captured from one
role's prep is available to seed all future roles.

High-effort, high-value stories -- Overmatch MBSE bottleneck, KForce requirements
harmonization, Shield AI cross-domain PDR -- are not specific to one employer or
job title. They demonstrate transferable capability that applies across defense SE
roles with different JD language but overlapping competency requirements.

Tag-based filtering ensures only relevant stories are surfaced for a given role.
A story tagged `mbse` and `systems-engineering` will not seed a prep package for
a role with no MBSE signal in the JD.

---

## What Is Not in Phase 5

- **Phase 1-4** produce the tailored resume (`stage4_final.txt`) and experience
  library (`experience_library.json`) that Phase 5 reads as inputs
- **Phase 6** (proposed networking) is out of scope for this document

Phase 5 owns everything from interview prep generation through post-interview
capture, library maintenance, and thank you letter generation.
