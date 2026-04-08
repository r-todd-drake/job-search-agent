# check_cover_letter.py — Design Spec
Date: 2026-04-08

## Purpose

Quality checker for cover letter drafts. Mirrors `check_resume.py` architecture.
Catches violations before the cover letter is finalized and converted to `.docx`.

## Position in Workflow

```
cl_stage1_draft.txt       <- phase4_cover_letter.py --stage 1
cl_stage2_approved.txt    <- user edits manually
cl_stage3_review.txt      <- check_cover_letter.py  [THIS SCRIPT]
cl_stage4_final.txt       <- user saves manually
[role]_CoverLetter.docx   <- phase4_cover_letter.py --stage 4
```

## Usage

```
python -m scripts.check_cover_letter --role [role]
```

Example:
```
python -m scripts.check_cover_letter --role BAH_LCI_MBSE
```

## Inputs

| File | Path | Required |
|------|------|----------|
| Cover letter draft | `data/job_packages/[role]/cl_stage2_approved.txt` | Yes |
| Candidate background | `context/CANDIDATE_BACKGROUND.md` | Yes |

## Output

| File | Path |
|------|------|
| Review findings | `data/job_packages/[role]/cl_stage3_review.txt` |

- All stdout captured to `cl_stage3_review.txt` (same pattern as `check_results.txt`)
- Validation errors (missing files) still print to terminal and exit before capture
- Exit code 0 = PASS, 1 = FAIL

Output format: findings-only report. No copy of the cover letter text embedded in the output.

## Architecture — Two-Layer

### Layer 1: String Matching

Fast pre-flight checks. No API call. Same rules as `check_resume.py`.

**Hardcoded rules (identical to check_resume.py):**

| Rule | Pattern | Fix |
|------|---------|-----|
| Em dash | `—` | Replace with en dash `–` |
| CompTIA Security+ | `CompTIA Security+` | Remove — certification lapsed |
| Active TS/SCI | `Active TS/SCI` | Use "Current TS/SCI" between employers |
| Plank Holder (capitalized) | `Plank Holder` | Use "Plank Owner" |
| plank holder (lowercase) | `plank holder` | Use "Plank Owner" |
| plankowner (one word) | `plankowner` | Use "Plank Owner" |
| safety-critical | `safety-critical` | Use "mission-critical" |

**Dynamic gap term rules:**
- Extracted from `## Confirmed Gaps` section of `CANDIDATE_BACKGROUND.md`
- Same extraction logic as `check_resume.py` (parenthetical terms, ALL-CAPS acronyms, CamelCase product names)
- Word-boundary match, case-insensitive, flags each term once
- Skip blank lines; skip lines starting with `##`

### Layer 2: API Assessment

Single API call. Purpose: detect violations that string matching cannot catch — specifically **implied fulfillment of confirmed gaps**.

Core concern: cover letter prose can claim or imply experience in a gap area without naming the gap term directly (e.g., "hands-on experience deploying cloud infrastructure" implies AWS/Azure/GCP, which is a confirmed gap). Layer 2 is designed to catch this class of violation.

**Prompt instructs the API to assess:**
1. **Implied gap fulfillment** — language that conveys experience, ownership, or authority in a confirmed gap area without naming the term directly. This is the primary purpose of the Layer 2 call.
2. **Explicit gap claims** — direct references the Layer 1 string match may have missed
3. **Banned / corrected language** — violations from the `## Banned / Corrected Language` section
4. **Generic opener phrases** — e.g., "I am excited to apply", "I am writing to express my interest", or similar filler openers the generator is instructed to avoid
5. **Fabricated or unverifiable claims** — metrics, outcomes, or experience not grounded in the candidate's confirmed background

**Context passed to API:**
- `## Confirmed Gaps` section from `CANDIDATE_BACKGROUND.md`
- `## Banned / Corrected Language` section from `CANDIDATE_BACKGROUND.md`
- Cover letter text (PII stripped via `strip_pii()`)

**Output schema:** Same JSON array as `check_resume.py`:
```json
{
  "violation_type": "short label",
  "line_reference": "line N or N/A",
  "flagged_text": "exact quoted text (keep short)",
  "suggested_fix": "specific correction"
}
```

**JSON parse failure:** Falls back to raw output, counted as 1 finding (same behavior as `check_resume.py`).

## Summary / Exit Code

```
============================================================
SUMMARY
============================================================
Layer 1: N violation(s)
Layer 2: N finding(s)
Total:   N

Status: PASS
-- or --
Status: FAIL – N violation(s) found. Correct cl_stage2_approved.txt and rerun.
============================================================
```

Exit 1 if "Status: FAIL" in captured output, else exit 0.

## What This Script Does NOT Do

- Does not read `cl_stage4_final.txt` — source is always `cl_stage2_approved.txt`
- Does not produce a machine-parsed output structure — `cl_stage3_review.txt` is human-read only
- Does not embed a copy of the cover letter in the output
- Does not share code with `check_resume.py` — deferred to parking lot item 12 pending a third checker

## Model

`claude-sonnet-4-20250514` — same as all other scripts in the project.

## Deferred

- Shared `check_utils.py` module — see parking lot item 12. Reevaluate if a third checker is added.
