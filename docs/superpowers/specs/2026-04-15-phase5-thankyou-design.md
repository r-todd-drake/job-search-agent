# Design: phase5_thankyou.py -- Post-Interview Thank You Letter Generator

**Date:** 2026-04-15
**Status:** Approved
**Proposal:** `docs/features/phase5-thankyou-letters/phase5_thankyou_proposal.md`

---

## Overview

A focused, self-contained script that reads a filed debrief JSON and generates one personalized
thank you letter per interviewer -- as `.txt` and `.docx` -- using a single Claude API call per
letter. No subagents. No multi-turn. Context window pressure is low.

---

## Architecture

One script (`scripts/phase5_thankyou.py`), one test file (`tests/test_phase5_thankyou.py`).
All logic is in the script; no new shared utilities.

Function layout mirrors `phase5_interview_prep.py`:

```
CONFIGURATION block         -- paths, MODEL constant, SYSTEM_PROMPT
_infer_tone(title)          -- maps title string to tone instruction string
_find_debrief(...)          -- glob + select most-recent debrief file
_load_inputs(...)           -- loads JD, resume, candidate profile; returns dict + warnings list
_build_letter_prompt(...)   -- assembles user message per interviewer
generate_letters(client, .) -- iterates interviewers, calls API, writes .txt/.docx per letter
main()                      -- argparse, validation, client init, calls generate_letters
```

---

## CLI Arguments

```
python scripts/phase5_thankyou.py --role Viasat_SE_IS --stage hiring_manager
python scripts/phase5_thankyou.py --role Viasat_SE_IS --stage panel --panel_label se_team
```

- `--role` (required): role slug matching `data/job_packages/[role]/`
- `--stage` (required): interview stage (matches debrief stage field)
- `--panel_label` (optional): panel label used in debrief filename

---

## Debrief File Selection (`_find_debrief`)

Two glob patterns, selected based on whether `--panel_label` is provided:

- **Without label:** `debrief_{stage}_[0-9]*_filed-*.json`
  Matches only unlabeled files -- date starts immediately after stage.
- **With label:** `debrief_{stage}_{panel_label}_*_filed-*.json`
  Matches only that specific label.

These patterns are structurally distinct and do not overlap.

If multiple files match, sort by filename descending (the `filed-{date}` suffix makes
lexicographic sort equivalent to chronological sort). Take the first. Print a notice to
terminal listing all matches and which was selected.

If zero matches, exit with a clear error showing the expected path pattern.

---

## Input Loading (`_load_inputs`)

Returns a dict and a list of warnings printed before generation begins.

| Input | Path | Missing behavior |
|---|---|---|
| Debrief JSON | `data/debriefs/[role]/debrief_...json` | Handled by `_find_debrief` before this call |
| Job description | `data/job_packages/[role]/job_description.txt` | Exit with error |
| Resume | `stage4_final.txt` then `stage2_approved.txt` | Warning; generation proceeds |
| Candidate profile | `data/experience_library/candidate_profile.md` | Exit with error |

All text sent to the API passes through `strip_pii()` before inclusion in the prompt.

---

## Tone Calibration (`_infer_tone`)

Pure function. Maps `title` string (case-insensitive keyword match) to a tone instruction
string included in the user prompt:

| Title contains | Tone instruction |
|---|---|
| `engineer`, `se`, `architect`, `developer`, `scientist` | `"peer-level technical -- write as one engineer to another; reference the specific work discussed"` |
| `director`, `vp`, `president`, `bd`, `manager`, `pm`, `program` | `"mission outcomes and strategic framing -- lead with impact and organizational fit"` |
| `recruiter`, `talent`, `hr`, `sourcer` | `"professional and warm -- process-aware, collegial, not overly technical"` |
| no match / null title | defaults to professional/recruiter tone |

---

## Letter Generation

**Approach:** Approach A -- single user prompt per interviewer with inline tone instruction.
One system prompt. One `client.messages.create` call per interviewer. No web search tool.

**API call parameters:**
- `model`: `claude-sonnet-4-20250514`
- `max_tokens`: `800` (sufficient for 3-4 paragraphs; mirrors project MODEL constant pattern)
- `system`: `SYSTEM_PROMPT` (defined at module level)
- `messages`: single user message from `_build_letter_prompt`

**`_build_letter_prompt` content (assembled per interviewer):**
1. Interviewer name, title, and `notes` field -- primary personalization anchor
2. Stories from `stories_used` where `landed == "yes"` -- referenced naturally, not recited
3. `what_i_said` continuity block
4. JD excerpt (first 1500 chars, strip_pii applied)
5. Candidate profile excerpt (first 1000 chars, strip_pii applied)
6. Resume summary if available (strip_pii applied)
7. Tone instruction from `_infer_tone(interviewer['title'])`
8. Letter structure instructions (3-4 paragraphs; if `gaps_surfaced` is non-empty in the
   debrief, include gap labels in the prompt and instruct the model to consider an optional
   P4 reframe -- omit the P4 instruction entirely if `gaps_surfaced` is empty)

If `interviewer['notes']` is null or empty, a warning is printed and generation proceeds.

**System prompt instructs the model to:**
- Write specific over generic, confident over effusive, brief over thorough
- Use en dashes, never em dashes
- Avoid hollow openers ("Thank you for taking the time")
- Use `notes` as the personalization anchor -- open by referencing it
- Stay consistent with `what_i_said`; do not introduce new positions
- Not reproduce verbatim STAR story text
- Not introduce claims not in the candidate profile or resume

---

## Output Files

**Filename construction:**

`interviewer_lastname` = last whitespace-delimited token of `interviewer['name']`, lowercased.
Example: `"John Smith"` → `"smith"`, `"Dr. Mary Jane Watson"` → `"watson"`.
If `name` is null or empty, falls back to `f"interviewer{index+1}"`.

**Paths:**
- With panel label: `data/job_packages/[role]/thankyou_[stage]_[panel_label]_[lastname]_[date].txt`
- Without panel label: `data/job_packages/[role]/thankyou_[stage]_[lastname]_[date].txt`

`[date]` = `str(date.today())` at script start (consistent with project convention).
Same naming pattern for `.docx`.

**Overwrite protection:** Before writing each interviewer's files, check if the `.txt` path
exists. If so, prompt: `"thankyou_[...].txt already exists. Overwrite? (y/n):"`. If `n`,
skip both `.txt` and `.docx` for that interviewer and print a skip notice. Continue to the
next interviewer -- do not abort the run.

**`.docx` generation:** Simple flat document -- title line, metadata line, letter prose.
No heading hierarchy (a letter is flat prose). If docx generation fails, print a warning
and continue (text file is already written).

**Summary block** after all letters are processed:
```
Generated N thank you letters:
  data/job_packages/[role]/thankyou_[...].txt
  ...
```
Skipped interviewers listed separately with reason.

---

## Testing

File: `tests/test_phase5_thankyou.py`
Framework: pytest, monkeypatch, tmp_path, capsys, MagicMock (unittest.mock)
Anthropic client mocked at `generate_letters` call boundary -- no real API calls.

| Test | Verifies |
|---|---|
| `test_infer_tone_technical` | Engineer title → technical tone string |
| `test_infer_tone_executive` | Director title → mission-outcomes tone string |
| `test_infer_tone_recruiter` | Recruiter title → professional/warm tone string |
| `test_infer_tone_default` | Unknown title → professional/warm default |
| `test_single_interviewer` | One interviewer → one .txt + .docx, correct naming |
| `test_multiple_interviewers` | Two interviewers → two independent output files |
| `test_panel_label_in_filename` | panel_label present → appears in output filename |
| `test_no_panel_label_in_filename` | No panel_label → absent from output filename |
| `test_missing_interviewer_notes_warning` | notes=None → letter generated, warning in stdout |
| `test_most_recent_debrief_selected` | Two matching files → newer selected, notice printed |
| `test_missing_debrief_exits` | No matching file → sys.exit with clear message |
| `test_missing_jd_exits` | No job_description.txt → sys.exit with clear message |
| `test_missing_resume_warning` | No stage4/stage2 → warning printed, generation proceeds |
| `test_tone_calibration_in_prompt` | Title drives tone string in assembled user prompt |

---

## Out of Scope

- Sending letters via email or external integration
- HTML or formatted email output
- Generating letters without a filed debrief
- Editing or regenerating individual paragraphs interactively
- Letter quality scoring or A/B variants
- Any changes to `phase5_debrief.py` or `phase5_interview_prep.py`
