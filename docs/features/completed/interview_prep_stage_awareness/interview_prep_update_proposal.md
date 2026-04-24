# Phase 5 Interview Prep Capability Update
## Interview Stage Awareness

---

## User Story

**As a** job seeker using the interview prep generator,
**I want** the prep package to be tailored to the type and stage of interview I am preparing for,
**so that** the content, story depth, gap handling, and questions to ask are appropriate for my audience and advance me effectively through each stage of the hiring process.

---

## Background & Context

The current Phase 5 generator produces a single prep package format regardless of interview type. In practice, a recruiter screen, a hiring manager interview, and a team panel require fundamentally different preparation — both in what the candidate presents and what questions they ask. This update adds an `--interview_stage` parameter that drives stage-specific logic across all four sections of the prep package.

Three stages are defined:

- **recruiter** — short screen (typically under 60 minutes); audience is a recruiter or HR coordinator; goal is to confirm the candidate is not a disqualifying risk and meets hiring manager criteria; candidate should not volunteer gaps or lead with technical depth
- **hiring_manager** — medium interview (60+ minutes); audience is the hiring manager; goal is to answer "can I work with this person and do they understand the problem?"; candidate leads with program context awareness and collaborative framing
- **team_panel** — long group interview (90 minutes to 3 hours); audience is 2–4 working-level team members; goal is peer credibility — "can we work with this person day to day?"; candidate leads with technical specificity and process fluency

---

## Acceptance Criteria

### AC 1 — Stage Parameter Exists and Is Required

- The generator accepts `--interview_stage` as a CLI parameter with valid values: `recruiter`, `hiring_manager`, `team_panel`
- If `--interview_stage` is not provided, the generator prompts the user to select a stage before proceeding
- Invalid values produce a clear error message listing valid options
- Stage value is written to the output file header alongside role and generation date

---

### AC 2 — Section 1 (Company & Role Brief) Adjusts by Stage

| Stage | Behavior |
|---|---|
| recruiter | Include company overview, recent news, culture signals, and interview process context. Suppress detailed program/technical content. |
| hiring_manager | Include full company and business unit overview. Add program pain point context where available from JD or web search. Include salary guidance. |
| team_panel | Condense company overview to 2–3 sentences. Emphasize program-specific context, mission area, and technical environment details. |

---

### AC 3 — Section 2 (Story Bank) Adjusts by Stage

**Story count and depth:**

| Stage | Stories | Depth |
|---|---|---|
| recruiter | 1–2 | Headline + one-sentence result only. No STAR expansion. |
| hiring_manager | 3–4 | Full STAR with one "if probed" branch per story. |
| team_panel | Full bank (4–6) | Full STAR with technical detail, tool-specific language, and peer-credible specificity. |

**Gap handling in story bank:**

| Stage | Behavior |
|---|---|
| recruiter | Suppress gap references entirely. Do not surface gaps in story framing. |
| hiring_manager | Include gap awareness note where a story might brush against a known gap. No full gap prep block. |
| team_panel | Full gap awareness integrated into story framing where relevant. |

**Role fit assessment:**

- Include at all stages, but condense to 2 sentences for recruiter stage.

---

### AC 4 — Section 3 (Gap Preparation) Adjusts by Stage

| Stage | Behavior |
|---|---|
| recruiter | Omit Section 3 entirely. Add a note: "Gap prep omitted — do not volunteer gaps in a recruiter screen." |
| hiring_manager | Include full gap prep block: Gap, Honest Answer, Bridge, Redirect. Include hard questions list. |
| team_panel | Include full gap prep block with all five elements including Peer Frame. See AC 4a for peer framing specification and draft prompt. |

---

### AC 5 — Section 4 (Questions to Ask) Is Stage-Specific

Questions are generated from a stage-specific prompt, not a shared prompt with filtering. Each stage has a distinct question set:

**Recruiter stage questions — signal: I've done my homework and I'm a serious candidate:**
- Company direction, growth areas, recent news
- Culture, team environment, retention
- Interview process — who is next, what are they evaluating, timeline
- Logistics confirmations (clearance, location, remote/onsite) if not already addressed

**Hiring manager stage questions — signal: I understand programs and I want to know if this problem is worth solving:**
- Current program pain points — schedule pressure, architecture debt, stakeholder friction
- What the team needs that it does not currently have
- What success looks like at 6 months vs. a disappointment
- Hiring manager's vision for the MBSE or architecture effort going forward

**Team panel stage questions — signal: I've been in this seat before and I will be a peer, not a burden:**
- Day-to-day working environment — tools, cadence, model governance
- Where the hard interface or integration problems are right now
- What processes are working and what is still being figured out
- How the team handles disagreements on architecture or design decisions

---

### AC 4a — Peer Framing Element for Team Panel Gap Prep

For team panel stage, each gap entry includes a fifth element — **Peer Frame** — in addition to the standard four (Gap, Honest Answer, Bridge, Redirect).

The peer frame is a 2–3 sentence response calibrated for delivery to a working engineer, not a manager. It differs from the Redirect in register: where a Redirect reassures a manager that risk is manageable, a Peer Frame signals to a colleague that the candidate understands the operational reality of the gap and will not pretend otherwise.

**The five-element structure for team panel gap entries:**

| Element | Purpose | Audience |
|---|---|---|
| Gap | Names the gap plainly | All stages |
| Honest Answer | Acknowledges it without hedging | All stages |
| Bridge | Connects existing experience to the gap | Hiring manager + team panel |
| Redirect | Reframes toward strength; reassures on risk | Hiring manager + team panel |
| Peer Frame | Direct, collegial acknowledgment with operational awareness; often ends with a question | Team panel only |

**Example — Cameo/Teamwork Cloud collaborative environment:**
> Peer Frame: "I've worked extensively in Cameo but not specifically in the TWC multi-user environment — I know the model synchronization workflow is where things get complicated across teams. What does your current branching and merge process look like? I'd want to get up to speed on that fast."

**Draft prompt template for peer frame generation** *(starting point — CC should iterate based on output quality):*

> For each gap identified, generate a peer framing response suitable for delivery in a team panel interview to a working-level engineer. The peer frame should: (1) acknowledge the specific gap honestly without softening or hedging, (2) demonstrate that the candidate understands why the gap matters operationally — not just that it exists, (3) pivot to a question or observation that signals domain fluency. The tone should be direct and collegial — peer to peer, not candidate to evaluator. Avoid polished redirect language. A peer frame that ends with a genuine question is preferred over one that ends with a reassurance. Length: 2–3 sentences maximum.

---

**Constraints applying at all stages:**
- Maximum 4 questions generated per stage
- Questions must not be answerable from the JD alone — they should require insider knowledge to answer well
- Questions that would be inappropriate for the audience (e.g., asking a recruiter about architecture debt) are explicitly excluded from that stage's prompt

---

### AC 6 — Output File Reflects Stage

- Output filename includes stage: e.g., `interview_prep_recruiter.txt`, `interview_prep_hiring_manager.txt`
- File header block includes: Role, Stage, Generated date, Resume source
- A one-line stage description is included at the top of the prep package so the candidate immediately knows the register they are preparing for

---

### AC 7 — Existing Behavior Preserved for Unaffected Elements

- PII stripping via `pii_filter.py` applies at all stages
- Web search for company and role context applies at all stages (condensed for team panel)
- Salary guidance is included for hiring manager stage; omitted for recruiter and team panel stages
- Resume bullet grounding logic is unchanged

---

## Out of Scope

The following are explicitly not part of this update:

- **Post-interview debrief module** — captured separately in the project parking lot; different capability
- **STAR story library extraction** — captured separately in the project parking lot; different capability
- **UI or interactive mode** — CLI parameter only; no interactive prompting beyond the missing-stage fallback in AC 1
- **New story generation** — this update governs depth and selection of existing stories, not generation of new ones
- **Changes to stage file format or resume generation pipeline** — prep generator only
- **Scoring or ranking of candidate readiness by stage** — out of scope for this update

---

## Implementation Notes for Claude Code

- Stage logic should be implemented as a stage profile dictionary or config block, not as scattered conditionals — this makes future stage additions or modifications straightforward
- The Section 4 questions prompt should be a separate prompt template per stage, not a single prompt with stage-conditional filters appended
- Consider a `--dry_run` flag that prints the stage profile that will be applied without running the full generation — useful for validating config before a long API call
- Stage parameter should be added to the job config schema (jobs.csv or equivalent) so it can be set at job tracking time rather than only at prep generation time

---

*Prepared for handoff to Claude Code. All scope decisions above are final unless explicitly revised.*
