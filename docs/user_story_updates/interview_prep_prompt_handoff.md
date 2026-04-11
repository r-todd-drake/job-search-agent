# Phase 5 Stage Awareness — Prompt String Handoff
Date: 2026-04-09
Status: Ready for drop-in — no architectural changes required

---

## Context

The four prompt strings below are finalized and ready to replace the placeholder values
in the `STAGE_PROFILES` dictionary. This is a drop-in replacement only — no changes
to architecture, function signatures, or test structure.

---

## Drop-in Replacements

### `STAGE_PROFILES["recruiter"]["questions_prompt"]`

```python
"questions_prompt": """
Generate exactly 4 questions for a candidate to ask at the end of a recruiter screen.
The questions should signal that the candidate is serious, prepared, and professional
without asking technical or program-specific questions the recruiter cannot answer.

Question categories to cover:
1. Company direction, growth areas, or recent news the candidate can reference naturally
2. Culture, team environment, or what makes people stay at the company
3. Interview process — who is next in the process, what will they be evaluating, timeline to decision
4. One logistics or role clarification question if anything material remains unaddressed (clearance, location, remote/onsite)

Constraints:
- Questions must be answerable by a recruiter without program or technical knowledge
- Do not ask about architecture, tooling, program pain points, or technical environment
- Do not ask questions already answered in the job description
- Tone: engaged, collegial, unhurried — not transactional
- Format: numbered list, each question followed by one sentence explaining what it signals to the interviewer
"""
```

---

### `STAGE_PROFILES["hiring_manager"]["questions_prompt"]`

```python
"questions_prompt": """
Generate exactly 4 questions for a candidate to ask at the end of a hiring manager interview
for a defense systems engineering role. The questions should signal program awareness,
results orientation, and genuine interest in the manager's vision.

Question categories to cover:
1. Current program pain points — where is the pressure coming from (schedule, architecture debt, stakeholder friction)?
2. What the team needs that it does not currently have — what gap does this hire fill?
3. What success looks like at 6 months versus what disappointment looks like — what are the real expectations?
4. The hiring manager's vision for where the technical effort (MBSE, architecture, or the relevant discipline) goes from here

Constraints:
- Questions must require insider knowledge to answer well — not answerable from the job description alone
- Do not ask about company culture, interview process, or logistics — those belong in the recruiter screen
- Do not ask questions that make the candidate sound uncertain about fit or qualifications
- Tone: peer-level engagement with someone senior — collaborative, direct, curious about the problem
- Format: numbered list, each question followed by one sentence explaining what it signals to the interviewer
"""
```

---

### `STAGE_PROFILES["team_panel"]["questions_prompt"]`

```python
"questions_prompt": """
Generate exactly 4 questions for a candidate to ask at the end of a team panel interview
for a defense systems engineering role. The questions should signal technical credibility,
process fluency, and peer-level awareness of where the hard work actually lives.

Question categories to cover:
1. Day-to-day working environment — tools cadence, model governance, or workflow specifics
   that only someone who has done this work before would think to ask about
2. Where the hard interface or integration problems are concentrated right now
3. What processes are working well and what is still being figured out — invites honest answer
4. How the team handles disagreements on architecture or design decisions — signals maturity
   and interest in team dynamics at a working level

Constraints:
- Questions must require hands-on program knowledge to answer — not answerable from the JD alone
- Do not ask about company direction, culture, salary, or interview process
- Do not ask questions that sound like a candidate evaluating risk — ask like a peer evaluating the work
- Avoid questions that could be read as critical of the program or the team
- Tone: direct, collegial, technically confident — peer to peer, not candidate to evaluator
- Format: numbered list, each question followed by one sentence explaining what it signals to the interviewer
"""
```

---

### `STAGE_PROFILES["team_panel"]["peer_frame_prompt"]`

```python
"peer_frame_prompt": """
For the gap identified above, generate a Peer Frame response suitable for delivery
to a working-level engineer in a team panel interview.

The Peer Frame must:
1. Acknowledge the specific gap honestly — no softening, no hedging
2. Demonstrate that the candidate understands why this gap matters operationally,
   not just that the gap exists — show awareness of where the friction point actually lives
3. Pivot to a question or observation that signals domain fluency — the candidate
   should sound like someone who has worked adjacent to this problem before

Tone: direct and collegial — peer to peer, not candidate to evaluator.
Do not use polished redirect language or reassurance framing — those belong in
the hiring manager response, not here.
A Peer Frame that ends with a genuine question is strongly preferred over one
that ends with a reassurance statement.

Length: 2–3 sentences maximum.
Label the output: Peer Frame:
"""
```

---

## Implementation Notes

- The `peer_frame_prompt` is called once per gap in a loop — not once for all gaps combined.
  Confirm the Section 3 loop structure handles per-gap invocation correctly.
- All four prompts assume role context, JD content, and candidate background are already
  present in the system prompt or prepended to the messages array. The prompts do not
  repeat that scaffolding.
- The questions prompts specify a numbered list with a one-sentence signal explanation
  after each question. The output formatter should render the signal explanation visually
  distinct from the question itself (e.g., indented or italicized in the docx output).

---

*No other changes. Resume task 11.*
