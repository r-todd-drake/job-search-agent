# Phase 5 Library Integration -- Plan Review
# Reviewer: Claude (Sonnet 4.6)
# Date: 2026-04-16
# Source documents reviewed:
#   - 2026-04-16-phase5-library-integration.md (implementation plan)
#   - phase5_library_integration_amended.md (AC / feature spec)
#
# PURPOSE: Pre-dispatch review. Apply all REQUIRED items before handing to
#          an agentic worker. ADVISORY items are judgment calls.
# ==========================================================================

## Overall Assessment

Plan is well-structured and ready to dispatch after the items below are
resolved. The TDD discipline is correctly enforced, the additive-only
architecture is sound, and the no-regression requirement is explicit
throughout.

Two items (R1, R2) will produce broken or incorrect code if not fixed.
The remaining four are clarity and correctness issues that reduce
implementor freelancing risk.

---

## Required Fixes (will produce broken or incorrect code if missed)

---

### R1 -- `dir()` guard in Task 3 is incorrect

**Location:** Task 3, `generate_prep()` changes, second injection block

**Current code:**
```python
if gap_seeds:
    if 'all_debriefs_for_signal' not in dir():
        all_debriefs_for_signal = _load_all_debriefs_safe()
    for g in gap_seeds:
        ...
```

**Problem:** `dir()` returns module-level names inside a function, not local
variables. This condition will always evaluate to `True`, causing
`load_all_debriefs()` to be called twice on every run where both story
and gap seeds are present.

**Fix:** Replace both injection blocks with a single load before either block:

```python
    # Load debrief history once for both story and gap signal injection
    all_debriefs_for_signal = _load_all_debriefs_safe() if (story_seeds or gap_seeds) else []

    # Inject performance signal into story seeds
    if story_seeds:
        for s in story_seeds:
            signal = _get_story_signal_safe(s.get("id"), all_debriefs_for_signal)
            if signal:
                s["_performance_signal"] = signal

    # Inject performance signal into gap seeds
    if gap_seeds:
        for g in gap_seeds:
            signal = _get_gap_signal_safe(g.get("gap_label"), all_debriefs_for_signal)
            if signal:
                g["_performance_signal"] = signal
```

---

### R2 -- Task 5 does not warn against duplicate `role_debriefs` load

**Location:** Task 5 implementation section, opening instructions

**Problem:** Tasks 4 and 5 both modify `generate_prep()`. Task 4 adds:
```python
role_debriefs = _load_role_debriefs_safe(role_name)
salary_actuals = _load_salary_actuals_safe(role_debriefs)
```
Task 5 uses `role_debriefs` for the continuity section but is written
as a standalone task. A subagent implementing Task 5 after Task 4 will
add a second `role_debriefs = _load_role_debriefs_safe(role_name)` call,
loading the same data twice and masking any state mutations between calls.

**Fix:** Add the following callout at the top of Task 5's implementation
section:

> **IMPORTANT:** `role_debriefs` is already assigned in Task 4 via
> `role_debriefs = _load_role_debriefs_safe(role_name)`. Do not declare
> it again in Task 5 -- reuse the existing variable. If implementing
> Task 5 without Task 4 complete, assign it once at the top of the
> block you are adding and note it for Task 4 integration.

---

## Advisory Items (reduce freelancing risk and spec drift)

---

### A1 -- `role_name` source is never specified

**Location:** Tasks 4 and 5, all calls to `_load_role_debriefs_safe(role_name)`

**Problem:** The plan uses `role_name` as the argument but never identifies
where it comes from inside `generate_prep()`. The function receives
`role_data` as a dict -- an implementor will have to guess the correct key.
If they guess wrong, `load_debriefs()` silently returns `[]` (absent
directory) and the feature appears to work while never actually loading
anything.

**Fix:** Add a note at first use in Task 4:

> `role_name` is the role identifier used as the `data/debriefs/`
> subdirectory name -- e.g., `"Viasat_SE_IS"`. Verify the exact key
> from `role_data` against the existing `generate_prep()` signature
> before implementing. Expected: `role_name = role_data["role_id"]`
> or equivalent -- confirm against the live file.

---

### A2 -- AC "others noted" requirement is unimplemented and unacknowledged

**Location:** Task 4, `_build_section1_prompt()` salary block; AC section
"Salary Section -- Debrief Actuals Override"

**Problem:** The AC states: *"If salary data exists in multiple debriefs,
the most recent is used **and others noted**."* The plan implements
most-recent-wins correctly but never renders any "others noted" output.
This is either a deliberate scope reduction or an oversight -- but it is
not called out anywhere in the plan.

**Fix (choose one and make it explicit):**

Option A -- Defer explicitly. Add to Task 4:
> Note: The AC requirement to note other salary exchanges is deferred.
> `load_salary_actuals()` returns the most recent only. A follow-on
> task can add a count line if desired.

Option B -- Implement minimally. After the actuals block in
`_build_section1_prompt()`, add:
```python
if len([d for d in debriefs if (d.get("salary_exchange") or {}).get("range_given_min")
        or (d.get("salary_exchange") or {}).get("range_given_max")]) > 1:
    salary_block += (
        f"Note: {prior_count} additional salary exchange(s) on record "
        f"for this role -- most recent used above.\n"
    )
```
Either option is acceptable. Leaving it unaddressed risks an agentic
worker freelancing a solution mid-task.

---

### A3 -- Misleading test name in Task 6

**Location:** Task 6, test `test_debrief_to_library_notification_printed`

**Problem:** This test does not assert that anything is printed to
terminal. It validates that `find_unmatched_debrief_content()` returns
a ghost story ID. The name implies it tests print output, which it does
not -- the actual print logic lives in `main()` and is untested here.

**Fix:** Rename to `test_find_unmatched_returns_ghost_story_id` to
accurately reflect what is being asserted. If print output should also
be tested, add a `capsys` assertion:
```python
captured = capsys.readouterr()
assert "Debrief content found" in captured.out
```
and keep the original name.

---

### A4 -- Parallel dispatch note omits main tab integration requirement

**Location:** Parallel Dispatch Note at top of plan

**Problem:** The CC Session Guidance in the AC explicitly states:
*"The main tab must own integration and regression testing of the full
generation pipeline. Subagents own isolated, testable sub-components only."*
The plan's Parallel Dispatch Note dispatches Task 2 as a subagent
modifying `phase5_interview_prep.py` but does not reference this
constraint. An agentic orchestrator could proceed to Task 3 before the
main tab has verified integrated behavior.

**Fix:** Append to the Parallel Dispatch Note:

> **Integration gate:** Before dispatching Task 3, the main tab must
> run the full `tests/phase5/test_interview_prep.py` suite against the
> merged output of Task 1 and Task 2. Do not proceed to Task 3 on
> subagent green alone.

---

## AC Alignment Check

All 19 items in the plan's Spec Coverage Matrix map to AC requirements
in the amended feature spec. No AC items are missing from the plan.

| AC Requirement | Plan Task | Status |
|---|---|---|
| get_stories() filtered by JD tags | Task 2 | OK |
| Seed block in _build_section2_prompt() | Task 2 | OK |
| (library-seeded) label instructed | Task 2 | OK |
| Performance signal for stories | Task 3 | OK -- pending R1 fix |
| Performance signal for gap responses | Task 3 | OK -- pending R1 fix |
| get_gap_responses() filtered by tags | Task 2 | OK |
| Seed triad in _build_gap_prompt() | Task 2 | OK |
| get_questions() filtered by tags + stage | Task 2 | OK |
| Library question candidates in prompt | Task 2 | OK |
| Salary actuals override -- most recent | Task 4 | OK |
| Salary actuals -- others noted | Task 4 | GAP -- see A2 |
| Multiple debriefs -- most recent wins | Task 4 | OK |
| Continuity section when debriefs exist | Task 5 | OK -- pending R2 note |
| No continuity when no debriefs | Task 5 | OK |
| Panel label in continuity header | Task 1 | OK |
| Continuity in .txt and .docx | Task 5 | OK |
| Debrief-to-library notification | Task 6 | OK |
| Thank you letter notification | Task 6 | OK |
| Thank you with --panel_label | Task 6 | OK |
| No-regression: absent library | Task 6 | OK |
| No-regression: absent debriefs dir | Task 6 | OK |
| No-regression: both absent | Task 6 | OK |
| phase5_debrief_utils isolated + tested | Task 1 | OK |

---

## Summary

| ID | Severity | Location | Action |
|---|---|---|---|
| R1 | Required | Task 3 | Replace dir() guard with single pre-block load |
| R2 | Required | Task 5 | Add role_debriefs reuse callout |
| A1 | Advisory | Tasks 4+5 | Document role_name source key |
| A2 | Advisory | Task 4 | Resolve "others noted" gap explicitly |
| A3 | Advisory | Task 6 | Rename misleading test or add capsys assert |
| A4 | Advisory | Dispatch note | Add main tab integration gate |
