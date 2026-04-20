# library_parser.py Last-Bullet Drop Bug — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the parser silently dropping the last bullet of the final employer section when it is immediately followed by `## PROFESSIONAL SUMMARIES`.

**Architecture:** Single-line guard added to the `## PROFESSIONAL SUMMARIES` branch in `parse_library()`: flush `current_bullet` into `employers[current_employer]['bullets']` before clearing both. Update the test that currently documents the bug (asserts count == 2) to assert the correct count (3) and remove the stale bug-documenting comment.

**Tech Stack:** Python 3, pytest

---

## File Map

| Action | File | What changes |
|--------|------|--------------|
| Modify | `scripts/utils/library_parser.py` | Add flush guard at line 96 (PROFESSIONAL SUMMARIES handler) |
| Modify | `tests/utils/test_library_parser.py` | Update `test_parse_library_bullet_count_matches_source` — correct assertion from 2 → 3, remove bug comment |

---

### Task 1: Harden the test first (TDD — make it fail against the bug)

The existing test `test_parse_library_bullet_count_matches_source` currently **passes** because its assertion (`== 2`) was written to match the buggy behavior. We must flip it to the correct value so it fails before the fix, then passes after.

**Files:**
- Modify: `tests/utils/test_library_parser.py:29-36`

- [ ] **Step 1: Update the test assertion to the correct bullet count**

Replace the entire `test_parse_library_bullet_count_matches_source` function with:

```python
def test_parse_library_bullet_count_matches_source():
    employers, _ = parse_library(str(FIXTURE_MD))
    acme = employers.get("Acme Defense Systems")
    assert acme is not None
    assert len(acme["bullets"]) == 3
```

The fixture (`tests/fixtures/library/experience_library.md`) has three bullet lines under "Acme Defense Systems":
- "Led MBSE development..." (Theme: Systems Architecture, priority)
- "Developed system-of-systems..." (Theme: Systems Architecture)
- "Facilitated IPT working groups..." (Theme: Stakeholder Engagement) ← the dropped bullet

- [ ] **Step 2: Run the test — verify it NOW FAILS (confirming the bug exists)**

```
python -m pytest tests/utils/test_library_parser.py::test_parse_library_bullet_count_matches_source -v
```

Expected output:
```
FAILED tests/utils/test_library_parser.py::test_parse_library_bullet_count_matches_source
AssertionError: assert 2 == 3
```

If it passes with count == 3, the bug is already fixed — stop and investigate before continuing.

- [ ] **Step 3: Commit the updated (failing) test**

```bash
git add tests/utils/test_library_parser.py
git commit -m "test: correct bullet count assertion from 2 to 3 (documents parser drop bug)"
```

---

### Task 2: Fix the parser

**Files:**
- Modify: `scripts/utils/library_parser.py:94-100`

The current `## PROFESSIONAL SUMMARIES` handler (lines 94-100):

```python
        if stripped.startswith('## PROFESSIONAL SUMMARIES'):
            in_summaries = True
            current_employer = None
            current_theme = None
            current_bullet = None
            i += 1
            continue
```

This sets `current_bullet = None` without appending it first, silently discarding the last pending bullet of the preceding employer section.

- [ ] **Step 1: Add the flush guard**

Replace the handler with:

```python
        if stripped.startswith('## PROFESSIONAL SUMMARIES'):
            if current_bullet and current_employer:
                employers[current_employer]['bullets'].append(current_bullet)
            in_summaries = True
            current_employer = None
            current_theme = None
            current_bullet = None
            i += 1
            continue
```

This mirrors the same pattern already used at the `## <employer>` handler (lines 141-143) and the `### <theme>` handler (lines 185-187).

- [ ] **Step 2: Run the failing test — verify it now passes**

```
python -m pytest tests/utils/test_library_parser.py::test_parse_library_bullet_count_matches_source -v
```

Expected output:
```
PASSED
```

- [ ] **Step 3: Run the full parser test suite — verify no regressions**

```
python -m pytest tests/utils/test_library_parser.py -v
```

Expected output: all tests pass. The tests in scope are:
- `test_parse_library_returns_employers_and_summaries`
- `test_parse_library_employer_has_required_fields`
- `test_parse_library_bullet_count_matches_source` ← fixed
- `test_parse_library_priority_bullet_flagged`
- `test_parse_library_bullet_ids_assigned`
- `test_employer_to_filename_produces_safe_string`
- `test_parse_library_malformed_section_raises_not_silently_skips`

- [ ] **Step 4: Run the broader test suite — verify no cross-module regressions**

```
python -m pytest tests/ -v
```

Expected output: all tests pass (73+ tests).

- [ ] **Step 5: Run a syntax check on the modified script**

```
python -m py_compile scripts/utils/library_parser.py && echo "OK"
```

Expected output: `OK`

- [ ] **Step 6: Commit the fix**

```bash
git add scripts/utils/library_parser.py
git commit -m "fix: flush pending bullet before PROFESSIONAL SUMMARIES transition in library_parser"
```

---

## Self-Review

**Spec coverage:**
- Bug: last bullet dropped when parser hits `## PROFESSIONAL SUMMARIES` → Task 2 fixes it.
- Test documents bug with wrong assertion → Task 1 corrects it.
- Data integrity risk noted in PARKING_LOT → resolved by fix; no data migration needed (parser is read-only).

**Placeholder scan:** None found.

**Type consistency:** No new types introduced. `current_bullet` dict structure unchanged. Pattern matches existing flush guards at lines 141-143 and 185-187.

**Edge cases covered by existing tests:**
- `test_parse_library_malformed_section_raises_not_silently_skips` — end-of-file flush (separate code path at lines 235-236, not modified).
- `test_parse_library_priority_bullet_flagged` — confirms bullet metadata preserved after fix (priority bullet is bullet 1, not the dropped bullet 3, so this is an independent check).
