# Plan Review Comments
# experience-library-backport implementation plan
# Reviewed: 19 Apr 2026
# Reviewer: Claude Chat (spec review step per README process)

---

## Overall Assessment

Architecture is correct, test coverage is thorough, and the spec coverage table
is complete. Four issues require resolution before build starts -- two are
blocking. See below.

---

## Issues

### BLOCKING — Library fixture missing from file map and task list

Task 3 tests reference `tests/fixtures/library/experience_library.md` but no
task creates it. The file map (top of plan) lists only:

- `tests/fixtures/stage_files/stage4_final_backport.txt` (created in Task 1)

The library fixture does not appear anywhere in the file map or task steps. CC
will hit `FileNotFoundError` on the first Task 3 test run.

**Resolution needed:** Add a step to Task 1 (or a new Task 1b) to create
`tests/fixtures/library/experience_library.md`. See the Fixture Generator
section below for the recommended approach -- fixture content matters, not
just the existence of the file.

---

### CORRECTNESS — `*Used in:*` parser fragile against real library format

In `extract_library_bullets`, source parsing is:

```python
if stripped.startswith("*Used in:") and current_bullet:
    src_text = stripped.replace("*Used in:", "").replace("*", "").strip()
    current_bullet["sources"] = [s.strip() for s in src_text.split(",")]
```

This works against the simplified test fixture. Against the real library it
will produce empty `sources` arrays for a non-trivial number of bullets for
two reasons:

1. Some bullets have continuation text or `*NOTE:*` lines between the bullet
   text and the `*Used in:*` tag. The current parser assigns sources to
   `current_bullet` only on the immediately following `*Used in:*` line. If
   any other content intervenes, `current_bullet` may have been flushed or
   replaced before the sources line is reached.

2. Some entries use `[CANONICAL -- ...]` annotation blocks that appear before
   `*Used in:*`. These are not currently in the skip list and may interrupt
   the bullet-to-source association.

**Impact:** Source gap detection (AC-3) will produce false positives --
bullets will appear to be missing attribution when the parser simply failed
to read their `*Used in:*` tag. This is a user-trust issue: the user will
open `backport_staged.md`, see source gaps for bullets they know are
correctly attributed, and lose confidence in the output.

**Resolution needed:** Either (a) make the library fixture closely mirror
the real format so this surfaces in tests before build completes, or (b)
make the source parser more tolerant by maintaining `current_bullet`
association across non-bullet lines until the next bullet or section header
is reached. Option (b) is the right fix; option (a) ensures the test catches
it.

---

### CORRECTNESS — Cross-employer false positives not tested

In `main`, employer filtering before `classify_bullet` is correct:

```python
employer_lib_bullets = [b for b in library_bullets if b["employer"] == matched_employer]
result = classify_bullet(bullet["text"], employer_lib_bullets, ...)
```

However, the unit test `test_classify_bullet_present` passes
`LIBRARY_BULLETS_SAMPLE` which contains only "Acme Defense Systems" bullets,
so the test passes regardless of whether employer filtering works. The real
library has 497 bullets across 7 employers. A bullet from a Saronic resume
that fuzzy-matches a G2 OPS bullet at 87% would be classified "present"
(already in library) instead of "net-new" if employer filtering broke down
in `main`.

**Impact:** Net-new bullets silently dropped. Exactly the class of loss this
script is designed to prevent.

**Resolution needed:** Add an integration test that verifies a bullet from
employer A is not suppressed by a high-scoring match from employer B. Can be
done with a two-employer fixture and a bullet designed to match only the
wrong employer's content.

---

## Minor Notes

### Test fixture bullet quality

Bullet 2 in `stage4_final_backport.txt` contains `$45M` -- an unverifiable
metric that violates the project style rules and would never appear in a real
stage file. Not a functional issue, but if someone runs the integration test
against a real role and sees `$45M` in `backport_staged.md` it will be
confusing. A cleaner net-new test bullet is preferable.

### Design question -- fixture vs. real library for integration tests

The blocking issue above raises a broader question: should integration tests
(`test_main_*`) run against the real `experience_library.md` rather than a
synthetic fixture?

- **Pro real library:** catches actual parsing failures (including the
  `*Used in:*` issue above) before they reach production.
- **Con real library:** test becomes environment-dependent, slower, and
  brittle if the library changes.

Recommended resolution: use a fixture that closely mirrors the real library
format rather than a minimal synthetic one. This captures the robustness
benefit without the environment dependency.

---

## Fixture Generator — scripts/utils/generate_test_fixture.py

The library fixture for integration tests should be generated from the real
`experience_library.md` rather than written by hand. This gives the tests
real format fidelity -- multi-line bullets, `### Theme:` headers,
`*Used in:*` tags, `[VERIFY]` and `[FLAGGED]` annotations, the
`## PROFESSIONAL SUMMARIES` stop marker -- without making tests
environment-dependent or brittle.

**Approach:** Add `scripts/utils/generate_test_fixture.py` as a one-time
utility. CC should add this as a new task (Task 1b or similar) in the plan.

**Invocation:**
```bash
python scripts/utils/generate_test_fixture.py --employers 3 --summaries 3
```

**Behavior:**
- Reads `data/experience_library/experience_library.md`
- Takes the first N bullets per employer section (default: 3)
- Takes the first N summaries from the `## PROFESSIONAL SUMMARIES` section
  (default: 3)
- Writes output to `tests/fixtures/library/experience_library.md`
- The generated fixture is committed to the repo and version-controlled
- Regenerate only when the library format changes materially, not on every
  library content update

**Why not use the full real library directly:**
- Tests would be environment-dependent (library not always present in CI)
- Tests would be brittle -- every library update could change test outcomes
- A committed fixture is stable and reviewable

**Why not write the fixture by hand:**
- Hand-written fixtures use simplified format that masks real parsing failures
- The `*Used in:*` fragility issue above would not be caught by a hand-written
  fixture; it would be caught immediately by a generated one

**Placement:** `scripts/utils/` already exists and contains shared utilities
(`pii_filter.py`, `library_parser.py`). The fixture generator fits naturally
there as a development utility, not a phase script.

---

## Summary Table

| Issue | Severity | Blocking build? |
|---|---|---|
| Library fixture missing from file map and task list | High | Yes |
| Fixture generator utility not in plan | High | Yes -- resolves the blocking issue above |
| `*Used in:*` parser fragile against real library format | High | No -- silent failure in production |
| Cross-employer false positives not tested | Medium | No -- silent failure in production |
| `$45M` in test fixture | Low | No |

All issues above should be resolved before build starts. The two
non-blocking parser issues are silent failures -- they won't cause test
failures but will degrade output quality on first real-world run. A
generated fixture (see Fixture Generator section above) will surface the
`*Used in:*` fragility during the build rather than after.

---
*End of review. No open items are pre-resolved -- all require action.*
