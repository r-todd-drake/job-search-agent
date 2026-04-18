# Phase 5 Workflow -- Feature Map and Orchestration

This document shows how each built and proposed feature fits into the end-to-end
Phase 5 interview preparation workflow. It is a reference for development sequencing,
dependency management, and understanding what data flows where.

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
          │          │ stories used + landed ratings               │          │
          │          │ gaps surfaced + response ratings            │          │
          │          │ salary exchange                             │          │
          │          │ what_i_said continuity notes                │          │
          │          │                                             │          │
          │  6. phase5_interview_prep.py (next stage)             │          │
          │          │ library-seeded from step 3                  │          │
          │          │ continuity summary from step 5              │          │
          │          │ salary actuals from step 5                  │          │
          │          └─────────────────────────────────────────── ┘          │
          │                                                                   │
          └───────────────────────────────────────────────────────────────────┘
```

---

## Feature Status and Dependencies

| Feature | Script | Status | Depends On |
|---|---|---|---|
| Interview prep generation | `phase5_interview_prep.py` | ✅ Built, user-tested | JD, candidate profile, experience library, tailored resume |
| Post-interview debrief | `phase5_debrief.py` | ✅ Built, user-tested | None |
| Interview library infrastructure | `interview_library.json`, `interview_library_tags.json`, `interview_library_parser.py` | 🔲 Proposed | None -- foundational |
| Workshop capture | `phase5_workshop_capture.py` | 🔲 Proposed | Library infrastructure |
| Phase 5 library integration | `phase5_interview_prep.py` extensions | 🔲 Proposed | Library infrastructure, workshop capture, debrief |

**Build order is constrained:** Library infrastructure must be built first. Workshop
capture and Phase 5 library integration can be built in either order, but integration
cannot be meaningfully tested until at least one capture has been run to populate
the library.

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

**Current behavior:** Generates all sections cold from JD + profile + experience library.

**Future behavior (post library integration):** Seeds stories, gaps, and questions from
`interview_library.json` where tag matches exist. Appends continuity summary and salary
actuals from debrief files if present. Notifies terminal if debrief content is not yet
captured to library.

---

### Step 2 -- Workshop with Claude Chat

**No script.** User pastes prep package content into Claude Chat and workshops: [or provides the .txt file]
- Introduction monologue register and framing
- STAR story accuracy, specificity, and delivery
- Gap response confidence and redirect strength
- Questions to ask -- selection and tailoring to the specific interviewer
- Integration of any additional context (interviewer background, recent company news)

**Output:** Revised `.docx` saved to
`data/job_packages/[role]/interview_prep_[stage].docx`
(overwrites Phase 5 output, or saved with a revised filename by convention).

**Note:** Interviewer-specific context added during workshopping (delivery register
notes, "mirror his language" instructions, rationale for specific question selection)
is intentionally present in the workshopped .docx -- it is useful for the interview
itself. The capture script strips this content before writing to the library.

---

### Step 3 -- Capture Workshopped Content

**Script:** `phase5_workshop_capture.py --role [role] --stage [stage]`

**Reads:**
- `data/job_packages/[role]/interview_prep_[stage].docx` (workshopped version)
- `data/interview_library_tags.json` (tag vocabulary for validation)

**Writes:**
- `data/interview_library.json` (appends new entries; updates `roles_used` on
  existing entries matched as duplicates)

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
- Interviewer background context and "mirror his language" instructions
- Section rationale lines ("Signals you're already thinking about the work")

---

### Step 4 -- Conduct Interview

No script. Candidate uses the workshopped .docx as reference material.

---

### Step 5 -- Capture Debrief

**Script:** `phase5_debrief.py --role [role] --stage [stage] --interactive`

(Or `--init` / `--convert` for the YAML draft path.)

**Reads:** Nothing -- interactive capture only.

**Writes:**
- `data/debriefs/[role]/debrief_[stage]_[interview-date]_filed-[produced-date].json`

**Fields captured:**
- Interview metadata (date, stage, format, interviewer name and title)
- Advancement read assessment and notes
- Stories used: tags, framing, landed rating, library ID (if known)
- Gaps surfaced: gap label, response given, response felt rating
- Salary exchange: range given, candidate anchor, candidate floor
- What I said: continuity notes for future stages
- Open notes

---

### Step 6 -- Generate Next Stage Prep Package

**Script:** `phase5_interview_prep.py --role [role] --interview_stage [next_stage]`

Repeats Step 1, now with library and debrief data available. The cycle continues
for each interview stage until the role is closed (offer, rejection, or withdrawal).

---

## Library Content Lifecycle

A story or gap response enters the library through workshop capture and improves
over time through repeated use:

```
First capture (workshopped)
  → source: workshopped, roles_used: [role_A]
  → tags assigned, content verified by user at capture

Used to seed next role
  → roles_used: [role_A, role_B]
  → seeded version tailored to role_B in prep package
  → user workshops role_B -- refinements captured back to library

Debrief records performance
  → landed: yes/partially/no recorded in debrief file
  → future: story performance aggregation (post-MVP)
```

Stories that land consistently across roles become the candidate's core narrative assets.
Stories that do not land surface as candidates for revision or retirement.

---

## Cross-Role Portability -- Design Rationale

The interview library is deliberately **not role-scoped**. Content captured from one
role's prep is available to seed all future roles.

This is valuable because the highest-effort stories -- Overmatch MBSE bottleneck,
KForce requirements harmonization, Shield AI cross-domain PDR -- are not specific
to one employer or one job title. They are demonstrations of transferable capability
that apply across defense SE roles with different JD language but overlapping
competency requirements.

Tag-based filtering in the parser ensures that only relevant stories are surfaced
for a given role -- a story tagged `mbse` and `systems-engineering` will not seed
a prep package for a role with no MBSE signal in the JD.

---

## What Is Not in Phase 5

For reference, the broader job search system has phases 1-4 that feed into Phase 5.
Phase 5 consumes their outputs but does not modify them:

- **Phase 1-4** produce the tailored resume (`stage4_final.txt`) and the experience
  library (`experience_library.json`) that Phase 5 reads as inputs
- **Phase 6** (proposed networking) is out of scope for this document

Phase 5 owns everything from interview prep generation through post-interview capture
and library maintenance.
