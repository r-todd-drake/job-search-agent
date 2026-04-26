# Phase 6 — Networking and Outreach Support: Design Spec
**Date:** 2026-04-26
**Status:** Approved — ready for implementation planning

---

## Overview

A contact-centric outreach script that generates warmth-calibrated LinkedIn and email messages across four relationship stages. The candidate manages a single `contact_pipeline.xlsx` tracker; the script reads it, generates message text, and writes stage advances back on confirm. All message output is printed to terminal for manual copy-paste — no automated sending.

---

## 1. Architecture and Data Flow

### Files

| File | Tracked | Purpose |
|---|---|---|
| `scripts/phase6_networking.py` | Yes | Main script |
| `data/tracker/contact_pipeline.xlsx` | No (gitignored) | Live contact tracker — single source of truth |
| `example_data/contact_pipeline_example.xlsx` | Yes | Fictional example (Jane Q. Applicant) for onboarding |
| `tests/phase6/__init__.py` | Yes | Package init |
| `tests/phase6/test_phase6_networking.py` | Yes | Tier 1 mock tests |
| `tests/phase6/test_phase6_networking_live.py` | Yes | Tier 2 live API tests |
| `tests/fixtures/contact_fixture.py` | Yes | Fictional fixture contacts (all 4 warmth variants) |

### Runtime Flow

```
CLI args parsed
  → load contact row from contact_pipeline.xlsx (openpyxl)
  → validate: contact found? unambiguous? stage valid? --role present if Stage 2?
  → load candidate background from context/candidate/candidate_config.yaml (via candidate_config.py)
  → load JD from data/job_packages/[role]/job_description.txt (Stage 2 only)
  → generate_message(stage, contact, candidate, jd_text)
      → _build_stage{N}_prompt(contact, candidate, jd_text)
          → _warmth_context(warmth) → placeholder instruction for Claude
      → Claude API call (MODEL_SONNET; strip_pii applied)
  → print labeled output to terminal
  → "Did you send this? (y/n)"
  → on y: write stage advance + date/status fields back to xlsx
```

### Module Boundary

`generate_message()` is a **pure function** — takes all context as arguments, returns a message string. No file I/O, no user prompts inside it. The CLI layer owns all I/O: xlsx reads, output printing, the y/n confirm, and xlsx write-back. This boundary makes `generate_message()` importable and directly testable per AC-6.

---

## 2. Script Interface

### Invocation

```bash
python -m scripts.phase6_networking --contact "Jane Smith" --stage 1
python -m scripts.phase6_networking --contact "Jane Smith" --stage 2 --role acme-systems-se
python -m scripts.phase6_networking --list
```

### Arguments

| Argument | Required | Behaviour |
|---|---|---|
| `--contact` | Yes (unless `--list`) | Case-insensitive partial match against `contact_name`. Error if ambiguous (multiple matches) or not found. |
| `--stage` | Yes (unless `--list`) | Integer 1–4. Error if out of range. |
| `--role` | Stage 2 only | Required at Stage 2; clear error if omitted. Ignored at all other stages. |
| `--list` | No | Prints all contacts as a formatted table: `contact_name`, `company`, `stage`, `status`, `role_activated` (blank if none). Sorted by stage ascending. No message generation. Mutually exclusive with `--contact`/`--stage`. |

### Stage Mismatch Behaviour

If `--stage N` does not match the contact's current `stage` value in the xlsx, the script prints a warning and proceeds:

```
Warning: contact_pipeline.xlsx shows Jane Smith at stage 1, but --stage 3 was requested. Generating Stage 3 message anyway.
```

Rationale: the script's job is to generate the message the user asked for. The xlsx stage is informational state — the user may legitimately want to generate a message for a different stage (e.g., previewing Stage 2 language, or catching up after forgetting to confirm a prior send). Aborting on mismatch would be too restrictive. The warning ensures the user is aware of the discrepancy without blocking them.

---

## 3. Contact Tracker Schema

`contact_pipeline.xlsx` columns (single sheet):

| Column | Type | Written by |
|---|---|---|
| `contact_name` | string | User |
| `company` | string | User |
| `title` | string | User |
| `linkedin_url` | string | User |
| `warmth` | string: Cold / Acquaintance / Former Colleague / Strong | User |
| `source` | string | User |
| `first_contact` | date | Script (Stage 1 confirm) |
| `response_date` | date | User only — script never writes |
| `stage` | integer 1–4 | Script (on confirm) |
| `status` | string: Active / Warm / Activated / No Response / Declined / Referred / Closed | Script (Stage 4 confirm → Closed); otherwise user |
| `role_activated` | string | Script (Stage 2 confirm — value of `--role`) |
| `referral_bonus` | string | User — blank if unknown |
| `notes` | string | User — freeform; read by script for context |

### xlsx Write-Back Rules (on `y` confirm)

| Stage confirmed | Fields written |
|---|---|
| Stage 1 | `stage` → 2, `first_contact` → today's date |
| Stage 2 | `stage` → 3, `role_activated` → `--role` value |
| Stage 3 | `stage` → 4 |
| Stage 4 | `status` → `Closed` |

`response_date` is **never written by the script** — it reflects an external event (a reply) the script cannot observe.

---

## 4. Message Generation

### Function Signatures

```python
def generate_message(stage, contact, candidate, jd_text=None) -> str
def _build_stage1_prompt(contact, candidate) -> str
def _build_stage2_prompt(contact, candidate, jd_text) -> str
def _build_stage3_prompt(contact, candidate) -> str
def _build_stage4_prompt(contact, candidate) -> str
def _warmth_context(warmth) -> str
```

### Warmth Tiers

Four distinct tiers — not grouped. Each has a different personalization angle and placeholder behaviour:

| Warmth | Relationship | Personalization anchor | Placeholder emitted |
|---|---|---|---|
| Cold | No prior contact | Candidate background + target company only | None |
| Acquaintance | Different employer; shared conference, event, or adjacent project | Specific external touchpoint | `[HOW YOU KNOW THIS PERSON]` |
| Former Colleague | Same employer | Shared employer, team, or internal project | `[WHERE YOU WORKED TOGETHER]` |
| Strong | Close professional relationship | Full shared history; most direct ask | None |

`_warmth_context(warmth)` returns an instruction string injected into the stage prompt telling Claude to emit the appropriate placeholder. For Cold and Strong it returns an empty string.

### Stage Definitions

**Stage 1 — Initial outreach**
- Goal: open or re-activate a relationship; no immediate role ask
- Output: script generates **both** a connection request (300-char hard limit) and a follow-up message, separated by a clear divider. The candidate uses whichever applies — connection request if not yet connected, follow-up message if already connected.
- Character budget for connection request varies by warmth tier (see below); follow-up message has no character limit
- Does not reference a specific role or opening

**Stage 2 — Referral activation**
- Goal: convert a warm contact into a referral submission for a specific role
- Reads JD from `data/job_packages/[role]/job_description.txt`
- Referral bonus angle included only when `referral_bonus` column is populated; omitted (never invented) when blank; framed as mutual upside, not transactional pressure
- Output includes a one-line role-fit rationale the candidate can use to calibrate before sending

**Stage 3 — Follow-up**
- Goal: re-engage a contact who has not responded to Stage 1 or Stage 2
- Shorter than Stage 1/2; acknowledges the prior message without repeating the full pitch
- Warmth-calibrated: cold follow-ups are lighter than warm ones

**Stage 4 — Close the loop**
- Goal: update the contact after the role resolves
- Brief closing message; keeps the relationship warm regardless of outcome

### Stage 1 Character Budget

LinkedIn connection requests have a hard 300-character limit. Acquaintance and Former Colleague tiers generate a placeholder that the user will replace with real text before sending. To leave room for that expansion:

| Warmth | Prompt target | Headroom for placeholder fill |
|---|---|---|
| Acquaintance / Former Colleague | ~180 chars | ~120 chars |
| Cold / Strong | 300 chars (full budget) | n/a |

If generated text exceeds the tier target, the script re-prompts Claude once with the overage flagged. If still over after retry, prints with a warning so the user can trim manually.

### Output Format

```
=== Stage 1 — Cold outreach | Jane Smith @ Acme Defense ===

[generated message text]

[147 / 300 characters]                          ← Cold/Strong
[142 chars generated | ~158 chars for your fill] ← Acquaintance/Former Colleague

Did you send this? (y/n):
```

Stage 2 output additionally shows the one-line role-fit rationale before the message:

```
Role fit: [one-line rationale]

[generated message text]
```

---

## 5. Testing

### Tier 1 — Mock tests (`tests/phase6/test_phase6_networking.py`)

- Schema validation: xlsx loaded correctly, required columns present
- Contact lookup: exact match, case-insensitive match, partial match, ambiguous → error, not found → error
- Stage routing: correct `_build_stage{N}_prompt` called per `--stage` value
- Stage 2 without `--role` → error raised before any API call
- Character count: Stage 1 Cold/Strong flagged at >300; Acquaintance/Former Colleague flagged at >180
- Placeholder presence: Acquaintance and Former Colleague outputs contain expected placeholder text; Cold and Strong do not
- `--list` output: correct columns, all fixture contacts represented
- xlsx write-back: Stage 1 confirm writes `stage=2` and `first_contact=today`; Stage 2 writes `role_activated`; Stage 4 writes `status=Closed`; `response_date` never written

### Tier 2 — Live API tests (`tests/phase6/test_phase6_networking_live.py`)

- Stage 1 and Stage 2 generation via real Claude API with Jane Q. Applicant / Acme Defense Systems fixture
- All four warmth tiers exercised for Stage 1

### Fixture (`tests/fixtures/contact_fixture.py`)

Fictional contact data in xlsx-row dict format. Four variants of Jane Q. Applicant — one per warmth tier — against Acme Defense Systems.

### Regression

All 392 existing mock tests must continue to pass after Phase 6 is merged.

---

## 6. Out of Scope (carried from feature spec)

- Autonomous contact discovery (Phase 7)
- LinkedIn API integration — all outreach is manual
- Email sending — script produces draft text only
- Message history storage — tracked manually in `notes` field
- Referral bonus lookup — script reads `referral_bonus` field only if candidate has populated it
- Phase 4 Stage 4 next-steps reference — deferred until Phase 6 is stable

---

## 7. Design Decisions (deviations from original feature spec)

| ID | Decision | Original spec |
|---|---|---|
| DA-1 | Single `contact_pipeline.xlsx`; no `contacts.csv` | contacts.csv as machine-readable spine + separate xlsx |
| DA-2 | Interactive y/n confirm before advancing stage | No stage-advance mechanism defined |
| DA-3 | Per-stage xlsx write-back rules (see Section 3) | Not specified |
| DA-4 | Four distinct warmth tiers; Acquaintance ≠ Former Colleague | Acquaintance/Former Colleague grouped as one tier |
| DA-5 | Claude emits `[PLACEHOLDER]` markers; no interactive pre-generation prompts | Not specified |
| DA-6 | Stage 1 char budget split: ~180 for placeholder tiers, 300 for Cold/Strong | Single 300-char limit for all warmth tiers |

Full rationale for each decision is in `docs/features/phase6_networking_support/phase6_networking_support.md` under Review Annotations.
