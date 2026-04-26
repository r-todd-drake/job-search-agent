# Phase 6 — Networking and Outreach Support (MVP)

## User Story and Acceptance Criteria

### User Story

"As a senior defense SE candidate managing an active job search, I want a contact tracking pipeline and staged message generator so that I can build and activate a professional network that surfaces opportunities and converts warm contacts into referrals for specific roles."

---

### Acceptance Criteria

#### AC-1 — Contact tracking schema

- `contact_pipeline.xlsx` is the sole contact data store — both machine-readable (script reads it directly via openpyxl) and human-facing. Mirrors the conventions of `job_pipeline_example.xlsx`. *(DA-1: contacts.csv removed; see Review Annotations.)*
- `contact_pipeline.xlsx` is gitignored (contains real names and personal relationship data)
- A `contact_pipeline_example.xlsx` with fictional data (Jane Q. Applicant identity) is tracked in `example_data/`
- `contact_pipeline.xlsx` contains the following columns:

| Column | Description | Written by |
|---|---|---|
| `contact_name` | Full name | User |
| `company` | Current employer | User |
| `title` | Their role | User |
| `linkedin_url` | Profile link | User |
| `warmth` | Cold / Acquaintance / Former Colleague / Strong | User |
| `source` | How identified (LinkedIn search, industry publication, referral, former colleague) | User |
| `first_contact` | Date of Stage 1 outreach | Script (Stage 1 confirm) |
| `response_date` | Date of first response — manual only; script never writes | User |
| `stage` | Current stage: 1 / 2 / 3 / 4 | Script (on confirm) |
| `status` | Active / Warm / Activated / No Response / Declined / Referred / Closed | Script (Stage 4 → Closed); otherwise user |
| `role_activated` | Job package folder name if Stage 2 activated (e.g., `vehicle-systems-lead-saronic`) | Script (Stage 2 confirm) |
| `referral_bonus` | Known referral bonus amount if available — blank if unknown | User |
| `notes` | Freeform — recruiter name, conversation summary, follow-up cues | User |

---

#### AC-2 — Script interface

- Script is invoked as: `python -m scripts.phase6_networking --contact "[contact_name]" --stage [1|2|3|4]`
- `--contact` matches against `contact_name` column in `contact_pipeline.xlsx` (case-insensitive, partial match acceptable if unambiguous; error if ambiguous or not found)
- `--stage` selects the message generation mode (see AC-3); if `--stage` does not match the contact's current `stage` value in the xlsx, the script prints a warning and proceeds
- At Stage 2, `--role [role]` is also required; script raises a clear error if omitted
- `--list` flag prints all contacts as a table (`contact_name`, `company`, `stage`, `status`, `role_activated`), sorted by stage ascending — no message generation
- Script reads candidate background from `context/candidate/candidate_config.yaml` via the existing `candidate_config.py` loader
- Script reads job package JD at Stage 2 from `data/job_packages/[role]/job_description.txt`
- PII in API calls is stripped via `pii_filter.py` consistent with all other phases

---

#### AC-3 — Stage definitions and message generation

Each stage produces a message calibrated to the contact's warmth level and the current ask.

**Stage 1 — Initial outreach (no specific role)**
- Goal: open a relationship or re-activate a dormant one; no immediate ask
- Output: LinkedIn connection request (300 character hard limit enforced) + optional follow-up message if already connected
- Warmth variants: all four tiers (Cold, Acquaintance, Former Colleague, Strong) produce distinct tone and content; see DA-4
- References candidate background from `candidate_config.yaml` to personalize the angle
- Does not reference a specific role or opening

**Stage 2 — Referral activation (role-specific)**
- Goal: convert a warm contact into a referral submission for a specific role
- Requires `--role` flag; reads JD from job package
- Output: LinkedIn message or email draft calibrated to warmth level
- Referral bonus angle included when `referral_bonus` column is populated in `contact_pipeline.xlsx`; framed neutrally as mutual upside, not transactional pressure
- Referral bonus angle omitted (not invented) when field is blank
- Message references specific role title and company; does not paste JD content verbatim
- Warmth variants: all four tiers produce different levels of directness and personalization in the ask; see DA-4

**Stage 3 — Follow-up**
- Goal: re-engage a contact who has not responded to Stage 1 or Stage 2 outreach
- Output: brief follow-up message (shorter than Stage 1/2; acknowledges prior message)
- Does not repeat the full pitch from the prior stage
- Warmth-calibrated: cold follow-ups are lighter than warm ones

**Stage 4 — Close the loop**
- Goal: update the contact after the role resolves (offer accepted, withdrawn, rejected)
- Output: brief closing message — thanks, outcome summary, keep the relationship warm
- Does not burn the contact regardless of role outcome

---

#### AC-4 — Output format

- All generated messages are printed to terminal (not saved to file) — the candidate copies and pastes into LinkedIn or email
- Stage 1 connection request output includes character count so the candidate can verify the 300-character limit before sending
- Output is clearly labeled with stage, contact name, warmth level, and any length constraint
- At Stage 2, output includes a one-line role fit rationale the candidate can use to calibrate before sending

---

#### AC-5 — Cross-pipeline integration (flag only — not automated)

- When `pipeline_report.py` runs, if any active contact's `role_activated` field matches an active job in `jobs.csv`, a note is printed: "Contact [name] at [company] is activated for [role] — current role status: [status]"
- This is a read-only flag; no automatic status updates between pipelines
- Implementation deferred to after Phase 6 core is stable — noted here as a designed integration point

---

#### AC-6 — Testability

- Script exposes a `generate_message()` function importable by tests (no module-level execution)
- Tier 1 mock tests cover: schema validation, stage routing logic, character count enforcement (>300 Cold/Strong; >180 Acquaintance/Former Colleague), missing `--role` error at Stage 2, placeholder presence in Acquaintance/Former Colleague output, absence of placeholder in Cold/Strong output, `--list` output format and sort order, xlsx write-back per stage, `response_date` never written
- Tier 2 live tests cover: Stage 1 and Stage 2 message generation via Claude API with fixture contact (Jane Q. Applicant / Acme Defense Systems), all four warmth tiers exercised for Stage 1
- Fixture contacts defined in `tests/fixtures/contact_fixture.py` — fictional identity only. Four variants of Jane Q. Applicant against Acme Defense Systems:

| Variant | `warmth` | `notes` content | Purpose |
|---|---|---|---|
| Cold | Cold | *(blank)* | No placeholder; full 300-char budget |
| Acquaintance | Acquaintance | "Met at AUSA Annual Meeting 2024, discussed LTAMDS program sustainment" | Provides shared touchpoint context; placeholder `[HOW YOU KNOW THIS PERSON]` must appear in output |
| Former Colleague | Former Colleague | "Worked together at Raytheon, Advanced Concepts group, 2019–2022" | Provides shared employer context; placeholder `[WHERE YOU WORKED TOGETHER]` must appear in output |
| Strong | Strong | "Close colleague from Raytheon; collaborated on multiple capture efforts" | No placeholder; full 300-char budget |

- All existing 392 mock tests continue to pass after Phase 6 is merged

---

### Out of Scope

- **Autonomous contact discovery** — identifying contacts via web search, LinkedIn search, industry publications, or any automated scraping. Deferred to Phase 7, which will discover both roles and contacts and feed both Phase 2 and Phase 6.
- **LinkedIn API integration** — LinkedIn blocks automation. All outreach is manual; the script generates message text only.
- **Email sending** — script produces draft text; candidate sends manually.
- **Message history storage** — sent messages, timestamps, and response content are tracked in the `notes` field of `contact_pipeline.xlsx` by the candidate. No automated logging of sent messages.
- **Contact discovery guidance** — search query recommendations for finding contacts on LinkedIn or elsewhere. This belongs to Phase 7.
- **Per-contact YAML or folder structure** — contacts do not accumulate artifacts the way job applications do; flat CSV is the correct data model.
- **Referral bonus lookup** — the script uses the `referral_bonus` field only if the candidate has populated it manually. No automated lookup.
- **Phase 5 next-steps reference** — PARKING_LOT item 5 (add Phase 6 prompt to Phase 4 Stage 4 next steps output) remains deferred until Phase 6 is stable and promoted.

---

## Review Annotations

*This section is populated during the Chat spec review step. Do not fill in manually.*

### DA-1 — Drop contacts.csv; use contact_pipeline.xlsx as sole data store (2026-04-26)

**As specified:** `contacts.csv` was the machine-readable pipeline spine; `contact_pipeline.xlsx` was a separate human-facing view mirroring the CSV structure.

**Decision:** Drop `contacts.csv`. The script reads `contact_pipeline.xlsx` directly via `openpyxl`, exactly as `pipeline_report.py` reads `job_pipeline.xlsx`. One file, one source of truth.

**Rationale:** No sync mechanism was defined between the two files. In practice the user would edit the xlsx (easier) and the CSV would drift. The existing job pipeline pattern already solves this correctly — there was no reason to diverge from it.

**Impact on AC-1:** Remove the `contacts.csv` and `contacts_template.csv` artifacts. The `contact_pipeline.xlsx` (and its `example_data/contact_pipeline_example.xlsx` counterpart) remain as specified. The field schema in AC-1 is unchanged — it now describes the xlsx columns rather than CSV fields.

### DA-2 — Interactive confirm before advancing stage in xlsx (2026-04-26)

**As specified:** AC-2 did not define a stage-advance mechanism (script was message-generation only).

**Decision:** After printing the generated message, the script prompts "Did you send this? (y/n)". On `y`, it writes the updated `stage` (and any relevant date fields) back to `contact_pipeline.xlsx`. On `n`, no write occurs.

**Rationale:** Generating a message and sending it are two separate moments. Auto-advancing on generation would corrupt the tracker if the user decides not to send. An explicit `--advance` flag was considered but adds flag-memorization overhead during active outreach sessions. The interactive confirm costs one keypress and keeps the xlsx accurate.

**Impact on AC-2:** Add post-generation confirm prompt and xlsx write-back to the script interface definition.

### DA-3 — xlsx field update rules per stage confirm (2026-04-26)

**Decision:** On `y` confirm, the script updates the following fields:

| Stage confirmed | Fields written |
|---|---|
| Stage 1 | `stage` → 2, `first_contact` → today |
| Stage 2 | `stage` → 3, `role_activated` → value of `--role` argument |
| Stage 3 | `stage` → 4 |
| Stage 4 | `status` → `Closed` |

**`response_date` is always manual** — the script never writes it. The user fills it in when a contact actually replies.

**Rationale:** `response_date` reflects an external event (a reply) that the script cannot observe. All other date/state fields that advance as a direct result of the user sending a message are reasonable to auto-populate on confirm.

### DA-4 — Four distinct warmth tiers, not three (2026-04-26)

**Clarification:** The spec grouped "Acquaintance/Former Colleague" together in stage descriptions, implying three effective tiers. This is incorrect.

**Decision:** All four warmth values represent distinct relationship types with different personalization angles:

| Warmth | Relationship context | Message can reference |
|---|---|---|
| Cold | No prior contact | Candidate background + target company only |
| Acquaintance | Different employer; met at conference, event, or worked on adjacent/shared project | The specific shared external touchpoint |
| Former Colleague | Same employer | Shared employer, team, or internal projects |
| Strong | Close professional relationship | Full shared history; most direct ask |

**Impact on AC-3:** Four distinct prompt variants per stage (not two), calibrated to these relationship contexts. The candidate's `notes` field in the xlsx is the expected source for the specific shared touchpoint (event name, project name) that personalizes Acquaintance messages.

### DA-5 — Interactive contextual prompts for warmth tiers that require a shared touchpoint (2026-04-26)

**Decision:** For warmth tiers that require a shared touchpoint (Former Colleague, Acquaintance), the script instructs Claude to emit explicit `[PLACEHOLDER]` markers in the generated output rather than prompting the user interactively before generation:

| Warmth | Placeholder emitted |
|---|---|
| Former Colleague | `[WHERE YOU WORKED TOGETHER]` |
| Acquaintance | `[HOW YOU KNOW THIS PERSON]` |
| Cold | *(no placeholder — no shared context exists)* |
| Strong | *(no placeholder — relationship is direct)* |

The user fills in placeholders when copy-pasting into LinkedIn or email.

**Rationale:** Consistent with the overall generate→review→send workflow. Simpler to implement (no interactive prompt loop). The tradeoff — Claude writes around a placeholder rather than weaving specific context into the prose — is acceptable given that the user is already editing before sending.

**Architecture boundary:** All I/O (xlsx read, output printing, y/n confirm, xlsx write-back) lives in the CLI layer. `generate_message()` is a pure function — no prompting inside it. This keeps it importable and testable per AC-6.

**Impact on AC-6:** Tier 1 mock tests call `generate_message()` directly; placeholder presence in output is a testable assertion for Acquaintance and Former Colleague warmth variants.

### DA-6 — Stage 1 character budget split for placeholder warmth tiers (2026-04-26)

**Issue:** For Acquaintance and Former Colleague warmth tiers, Stage 1 generates a connection request with a placeholder (DA-5). The placeholder will be replaced with real text before sending, so the 300-char limit must account for expansion.

**Decision:** At Stage 1, the prompt targets a lower character budget based on warmth tier:

| Warmth | Prompt target | Headroom for placeholder fill |
|---|---|---|
| Acquaintance / Former Colleague | ~180 chars | ~120 chars |
| Cold / Strong | 300 chars (full budget) | n/a |

Script output for placeholder tiers shows two values: chars generated and chars remaining for the placeholder fill. If generated text exceeds the tier target, script re-prompts Claude once with the overage flagged. If still over after retry, prints with a warning so the user can trim manually.

**Impact on AC-4:** Output for Stage 1 placeholder tiers reads `[142 chars generated | ~158 chars remaining for your replacement]` rather than a single char count.
