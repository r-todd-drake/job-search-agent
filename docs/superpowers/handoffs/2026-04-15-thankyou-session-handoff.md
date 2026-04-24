# Session Handoff -- phase5_thankyou.py

**Date:** 2026-04-15
**Feature:** Post-interview thank you letter generator
**Prior session:** Debrief amendment shipped (commit `21f8055`)

---

## Opening Message for Fresh Session

> "We're building `phase5_thankyou.py` -- a post-interview thank you letter generator. The debrief script (`phase5_debrief.py`) was amended today to include an `interviewers` array (name, title, notes) and `--panel_label` support -- the proposal already reflects this. Before writing any code or plan, read the files below in order."

---

## Files to Read (in this order)

| File | Why |
|---|---|
| `CLAUDE.md` | Safety rules, code style (en dashes, PII filter, never touch `data/`) |
| `docs/features/phase5_thankyou_letters/phase5_thankyou_proposal.md` | Full spec -- AC, system prompt, output schema, tests |
| `scripts/phase5_interview_prep.py` | **Primary analog** -- proposal explicitly says to follow its patterns for Claude API calls, system prompt structure, and .docx output |
| `scripts/phase5_debrief.py` | Read `build_json_output` and `run_interactive` to understand the exact debrief JSON schema the thankyou script reads |

**Do NOT read:**
- `phase4_cover_letter.py` -- the proposal points to `interview_prep.py` as the right analog
- Any library infrastructure or workshop capture docs -- different feature chain
- Any files in `data/` -- safety rule

---

## Key Fact to State Explicitly

The `interviewers` array in the debrief JSON is **live as of today** (commit `21f8055`). Each entry has `name`, `title`, `notes`. The `notes` field is the primary personalization anchor for each letter. The fresh session needs to know this is current schema, not future spec.

---

## Workflow

Per `CLAUDE.md`, development follows plan-before-code:

1. Invoke `superpowers:brainstorming` -- explore intent, requirements, and design
2. Invoke `superpowers:writing-plans` -- produce step-by-step implementation plan
3. Use `superpowers:test-driven-development` during implementation
4. Use `superpowers:verification-before-completion` before claiming done

Do not begin implementation until the plan is reviewed and confirmed.
