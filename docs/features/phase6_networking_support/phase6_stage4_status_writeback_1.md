# Phase 6 — Contact Status Vocabulary Implementation

## User Story and Acceptance Criteria

### User Story
"As a job seeker managing a contact pipeline, I want the contact tracker to use a defined status vocabulary so that contact relationships are tracked consistently from identification through resolution."

### Acceptance Criteria (AC)

#### AC-1 — Status vocabulary

The following values are the complete defined vocabulary for the `status` column in `contact_pipeline.xlsx`:

| Value | Meaning | Written by |
|---|---|---|
| `Active` | In pipeline, working through stages | User (initial entry) |
| `Warm` | Contact has responded; relationship is live | User (manual) |
| `Activated` | Contact has been asked for a referral (Stage 2 sent) | Script (Stage 2 confirm) |
| `No Response` | Outreach sent; no reply after follow-up | User (manual) |
| `Declined` | Contact explicitly passed or declined to refer | User (manual) |
| `Referred` | Contact submitted a referral | User (manual) |
| `Closed` | Relationship closed -- loop closed after role resolution (Stage 4) | Script (Stage 4 confirm) |

- `Closed` is a relationship-level terminal state, not an engagement-level state -- it means the full arc is complete for this contact, not just that one role resolved
- `No Response`, `Declined`, and `Referred` are user-managed; the script never writes these
- `Warm` is user-managed; the script cannot observe a reply

#### AC-2 — Script write-back alignment

`_build_write_back()` is updated to write status values consistent with AC-1:

| Stage confirmed | Fields written | Change from current |
|---|---|---|
| Stage 1 | `stage` → 2, `first_contact` → today | No change |
| Stage 2 | `stage` → 3, `role_activated` → `--role` value, `status` → `Activated` | `status` write added |
| Stage 3 | `stage` → 4 | No change |
| Stage 4 | `status` → `Closed` | No change (value already correct per revised vocabulary) |

- Stage 2 is the only stage that gains a new status write-back
- `Closed` at Stage 4 is retained -- it is now explicitly defined as relationship-terminal, which is the correct semantic for a completed Stage 4 close-the-loop message

#### AC-3 — Example tracker update

- `example_data/tracker/contact_pipeline_example.xlsx` is updated so the `status` column uses only values from the AC-1 vocabulary
- No changes to column structure or other example data

#### AC-4 — Test coverage

- Stage 2 write-back unit test updated to assert `status → Activated` in the returned dict
- Stage 4 write-back unit test confirms `status → Closed` (no change to assertion, but now explicitly tested against the defined vocabulary)
- All other stage write-back tests continue to pass unchanged
- All existing 444 mock tests continue to pass after merge

### Out of Scope
- Re-engagement workflow -- resetting status when a closed contact is re-activated for a new role; deferred
- Enforcement of status vocabulary at data entry -- the script does not validate user-entered status values; that is a future data integrity feature
- Any changes to Stage 4 prompt text or output formatting
- `pipeline_report.py` cross-pipeline contact/role flag (AC-5 from original Phase 6 spec) -- remains deferred; separate parking lot item

---

## Review Annotations
*This section is populated during the Chat spec review step (README process step 4). Do not fill in manually.*
