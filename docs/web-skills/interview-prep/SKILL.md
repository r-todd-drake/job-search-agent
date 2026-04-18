---
name: interview-prep
description: Generate a tailored interview prep package as a formatted Word document (.docx) for a specific job application. Use this skill whenever the user asks to create, build, generate, or update an interview prep package, interview brief, prep document, or interview guide. Also trigger when the user says things like "build me a prep package for my next interview", "update the prep doc", "I have an interview with X, prepare me", or references a specific interview stage (recruiter screen, hiring manager, chief engineer, panel). Requires a candidate profile (candidate_profile.md) and job description. Adapts document sections and depth based on interview stage. Always produces a .docx file — never a markdown summary.
---

# Interview Prep Package Generator

Produces a staged, adaptive Word document prep package grounded in a verified candidate profile. Each package is calibrated to the interview stage, interviewer background, and role context. The output is always a .docx file.

## Before you write a single line of code

1. Confirm `candidate_profile.md` is loaded — it is the ground truth for all candidate facts. Never hallucinate credentials, stories, or employers not listed there.
2. Read the job description in full. Extract: required qualifications, preferred qualifications, role scope, reporting structure if stated, and any language that signals pain points or priorities.
3. Identify the interview stage (see Stage Matrix below).
4. If an interviewer name is provided, research their background before building the package. A Chief Engineer with a submarine officer background requires different framing than an HR generalist recruiter.
5. Read `references/stage-matrix.md` to confirm section set for this stage.
6. Read `references/design-tokens.md` for all formatting constants before writing any JS.

---

## Stage Matrix

Five defined stages. Each has a required section set and a set of conditional sections.

| Stage | Typical duration | Audience | Package depth |
|---|---|---|---|
| `recruiter` | 20–30 min | HR / talent acquisition | Lean — intro, stories, gap prep, salary, questions |
| `hiring-manager` | 45–60 min | Direct hiring manager | Full — all sections including role context |
| `chief-engineer` | 30–60 min | Technical authority, CE or equivalent | Full + interviewer brief + technical depth callouts |
| `panel` | 60–90 min | Multi-interviewer panel | Full + per-interviewer sections |
| `final` | 60–90 min | Executive or cross-functional | Full + strategic framing, culture fit emphasis |

See `references/stage-matrix.md` for the complete section list per stage.

---

## Section Catalogue

Every section has an ID, a stage availability rule, and content guidance. Sections marked **required** must appear at that stage. Sections marked **conditional** appear only when the relevant input is available.

### COVER
**Available:** all stages | **Required:** all stages

Single block at top of document. Fields:
- Document title: "Interview Prep Package"
- Role: job title — company name, division if known
- Stage: human-readable stage label + interviewer name if known
- Format: duration, medium (Zoom/onsite), interviewer location if known
- Prepared: date

### INTERVIEWER-BRIEF
**Available:** hiring-manager, chief-engineer, panel, final | **Required:** when interviewer name is known

Research the interviewer before writing this section. Use web search. Structure:
- Name, title, company tenure, location
- Career background summary (prior roles, education, domain credentials)
- Tint box: one-paragraph narrative synthesis of who this person is
- Two-column layout: Background bullets left | What this means for you right
- Alert box: single highest-signal strategic insight about this interviewer

If interviewer background cannot be found, note this and include generic guidance for the likely audience type instead.

### ROLE-CONTEXT
**Available:** hiring-manager, chief-engineer, panel, final | **Required:** hiring-manager and above

Covers:
- Org structure: where this role sits, who it reports to, peer roles if known
- Scope clarification: note any delta between JD language and what the recruiter/prior interview revealed
- How the candidate framed any disclosed gaps in earlier stages — preserve this language exactly, it is established context
- Alert box: any role-level insight that changes interview strategy

### INTRODUCE-YOURSELF
**Available:** all stages | **Required:** all stages

Stage-calibrated version of the intro monologue. Rules:
- Recruiter stage: ~60 seconds, no technical depth, no volunteering gaps
- HM and above: ~90 seconds, can include one concrete credential signal
- **Never use "most recently" for Overmatch** — always "the work I'm most known for"
- Closing sentence is a confident frame, not a plea — delivery note must say "deliver flat"
- Tint box wraps the script; delivery notes in two-column layout below

### STORY-BANK
**Available:** all stages | **Required:** all stages

Contains:
1. Role fit assessment paragraph (2–3 sentences max)
2. Key themes to lead with (2–3 bullet themes, not more)
3. Story routing table (required at HM stage and above; optional at recruiter)
4. Individual story blocks

**Story routing table** — three columns: "If he/she asks..." | "Lead with" | "Backup"
Rows cover the 6–8 most likely question types for this role and stage.

**Story block structure** — each story uses this exact sequence:
- Story title + employer/program tag on same line (italic gray tag)
- SITUATION label + body (omit if context is obvious from setup)
- TASK label + body
- ACTION label + body
- RESULT label + body
- IF PROBED label + body (italic) — the insight or meta-lesson, not just more detail

Stories must be drawn only from `candidate_profile.md` CANONICAL BULLETS and EMPLOYER HISTORY. Do not invent or embellish. If a story requires verification, flag it with a comment in the document.

**Story selection by stage:**
- Recruiter: 2–3 stories maximum, no depth stories
- HM and above: 4 stories, with routing table
- Chief engineer: 4 stories, lead story selected for technical audience credibility

### GAP-PREPARATION
**Available:** all stages | **Required:** all stages

Always includes the short tenure explanation for Saronic (5 months). Template:

For role-specific gaps: drawn from JD gap analysis. Structure each gap as:
- Gap label (what the JD requires that the candidate lacks)
- Honest answer (what to say if directly asked)
- Bridge (what adjacent experience applies)
- Redirect (how to reframe toward genuine strengths)

**Gap framing rule:** gaps are capability pivots, not apologies. Never frame a gap as a deficit without a redirect. Never recommend volunteering a gap that has not been surfaced by the interviewer.

**Reserve pivot section** (HM stage and above, when a role-level mismatch is possible):
If the candidate's fit is strongest for a variation of the role rather than the exact JD, define the reserve pivot language here. This is a last-resort recovery move, not an opening gambit. The pivot must be framed as a capability reframe, not a request to be considered for a different role. See `references/pivot-framing.md` for language patterns.

### QUESTIONS-TO-ASK
**Available:** all stages | **Required:** all stages

Stage-calibrated question set:
- Recruiter: 3–4 questions, focus on role context, team culture, process/next steps, and one proactive neutralizer if a known concern exists (e.g., commute, location)
- HM and above: 2–3 questions, focus on technical and strategic calibration

Each question gets: the question text in a tint box + a "why this works" explanation below.

### SALARY-GUIDANCE
**Available:** recruiter, hiring-manager | **Conditional:** only when salary range is known

Fields:
- Posted range
- Realistic offer zone (with rationale)
- Suggested anchor (pre-rounded for natural delivery)
- If asked script
- Floor: do not accept below X

### FORMAT-AND-LOGISTICS
**Available:** hiring-manager, chief-engineer, panel, final | **Required:** at these stages

Two-column layout:
- Left: call logistics (duration, medium, interviewer location, time zone note)
- Right: time budget (how to allocate the minutes)

Plus: how to close the call (tint box with closing script) and a final alert box with the single most important thing to remember.

---

## Editorial Rules

These rules apply to every package regardless of stage. They are non-negotiable.

**Punctuation:**
- N-dashes (–) only. Never m-dashes (—). M-dashes are a common AI-generation tell.
- Smart quotes in all body text.

**Candidate framing:**
- "Active [clearance]" when candidate is employed; "Current [clearance]" when between roles.
- "Built and led" not "managed" for team leadership.
- "Mission-critical" not "safety-critical" — candidate has never held safety authority.
- Specify platform types: maritime, UAS, ground — never generic "autonomous systems."

**Story integrity:**
- Every story detail must be traceable to `candidate_profile.md`.
- If a story requires a detail not in the profile, flag it: *[verify before interview]*.
- Do not add metrics, percentages, or outcomes not confirmed in the profile.

**Gap framing:**
- Never volunteer a gap that has not been surfaced.
- Never frame a gap without a redirect.
- Gaps disclosed in prior interview stages must be acknowledged and preserved — do not pretend they were not disclosed.

**Tone:**
- Engineering leadership audience: lead with outcomes and owned decisions, not process compliance.
- Recruiter audience: accessible, confident, no jargon depth.
- A closing sentence is a confident frame, not a plea. Always note "deliver flat."

---

## JavaScript Generation

Use `docx` npm package (already installed globally). Always set page size to US Letter explicitly. Reference `references/design-tokens.md` for all color, spacing, and typography constants before writing any code.

Key layout components — use these helper patterns consistently:

| Component | Use case |
|---|---|
| `tintBox()` | Scripts, framing text, story blocks, key context |
| `alertBox()` | Single highest-signal callout per section — use sparingly |
| `twoCol()` | Side-by-side comparisons, delivery notes vs. strategic notes |
| `storyBlock()` | All STAR stories — standardized label/body sequence |
| `routingTable()` | Story routing — always three columns |
| `rule()` | Section dividers |
| `label()` | All-caps small gray field labels above body text |

See `references/design-tokens.md` for exact implementation of each.

After generating, always validate:
```bash
python /mnt/skills/public/docx/scripts/office/validate.py output.docx
```

Copy final output to `/mnt/user-data/outputs/` and call `present_files`.

---

## Reference Files

Read these before generating — do not reconstruct from memory:

- `references/stage-matrix.md` — complete section list per stage, with required/conditional flags
- `references/design-tokens.md` — all JS helper functions, color constants, typography, spacing
- `references/pivot-framing.md` — reserve pivot language patterns for role mismatch scenarios
