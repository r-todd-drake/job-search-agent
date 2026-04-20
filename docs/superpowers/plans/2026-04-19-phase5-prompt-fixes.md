# Phase 5 Prompt Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix two prompt engineering bugs in `phase5_interview_prep.py`: (1) duplicate salary guidance when actuals are present alongside a JD salary range, and (2) the gap prompt incorrectly flags MBSE as a gap and redirects to non-existent experience instead of the real Shield AI domain story.

**Architecture:** Both fixes are targeted prompt-string changes inside `_build_section1_prompt` and `_build_gap_prompt`. No new functions, no schema changes, no new files. Each fix is verified by a new test that asserts the guardrail text is present in the API payload.

**Tech Stack:** Python 3, pytest, `unittest.mock`

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `scripts/phase5_interview_prep.py` | `_build_section1_prompt`: add salary-actuals-exclusivity guardrail |
| Modify | `scripts/phase5_interview_prep.py` | `_build_gap_prompt`: add confirmed-skills guardrail + redirect honesty rule |
| Modify | `tests/phase5/test_interview_prep.py` | Add two new tests — one per fix |

No other files touched.

---

## Task 1: Fix salary duplicate — add actuals-exclusivity guardrail to Section 1 prompt

**Root cause:** When `salary_actuals` is present, the actuals block is injected into the Section 1 prompt. But the full JD text (first 2500 chars) is also in the same prompt. If the JD contains a posted salary range, Claude reads both and may generate salary guidance from each source, producing duplicate content in the output.

**Fix:** When `salary_actuals` is not None, append a one-line exclusivity instruction immediately after the actuals block: `"IMPORTANT: Do not re-derive or add salary guidance from the job description. Use ONLY the salary actuals block above as written."` This is appended to `salary_block` inside the `if salary_actuals:` branch of `_build_section1_prompt`.

**Files:**
- Modify: `scripts/phase5_interview_prep.py` — `_build_section1_prompt` (lines 269–308)
- Modify: `tests/phase5/test_interview_prep.py` — add `test_salary_actuals_prompt_contains_exclusivity_guardrail`

- [ ] **Step 1: Write the failing test**

Append to `tests/phase5/test_interview_prep.py`:

```python
def test_salary_actuals_prompt_contains_exclusivity_guardrail():
    """When salary_actuals are present, the Section 1 prompt must instruct Claude
    not to re-derive salary from the JD — preventing duplicate salary guidance."""
    from scripts.phase5_interview_prep import _build_section1_prompt, STAGE_PROFILES

    salary_data = {"found": True, "text": "$150,000 – $175,000", "guidance": "anchor at $168k"}
    actuals = {
        "range_given_min": 145000,
        "range_given_max": 175000,
        "candidate_anchor": 168000,
        "candidate_floor": 152000,
        "stage": "recruiter",
        "interview_date": "2026-04-10",
    }
    profile = STAGE_PROFILES["hiring_manager"]
    prompt = _build_section1_prompt("JD text with $150k-$175k range", salary_data, profile,
                                    salary_actuals=actuals)
    assert "Do not re-derive" in prompt, (
        "Actuals guardrail must tell Claude not to re-derive salary from JD"
    )
    assert "SALARY ACTUALS" in prompt
```

- [ ] **Step 2: Run the test to confirm it fails**

```bash
python -m pytest tests/phase5/test_interview_prep.py::test_salary_actuals_prompt_contains_exclusivity_guardrail -v
```

Expected: `FAILED` — `AssertionError: Actuals guardrail must tell Claude not to re-derive salary from JD`

- [ ] **Step 3: Implement the fix**

In `scripts/phase5_interview_prep.py`, locate `_build_section1_prompt`. Find the `if salary_actuals:` branch (around line 282). The current block ends with:

```python
            salary_block = (
                f"\nSALARY ACTUALS (reported from {act_stage} on {act_date} -- use these, not estimates):\n"
                f"Range given by interviewer: {min_str} -- {max_str}\n"
                f"Candidate anchor stated: {anchor_str}\n"
                f"Candidate floor: {floor_str}\n"
                f"Note: these are reported actuals from a prior interview for this role. "
                f"Present them as confirmed data, not as analysis.\n"
            )
```

Replace it with:

```python
            salary_block = (
                f"\nSALARY ACTUALS (reported from {act_stage} on {act_date} -- use these, not estimates):\n"
                f"Range given by interviewer: {min_str} -- {max_str}\n"
                f"Candidate anchor stated: {anchor_str}\n"
                f"Candidate floor: {floor_str}\n"
                f"Note: these are reported actuals from a prior interview for this role. "
                f"Present them as confirmed data, not as analysis.\n"
                f"IMPORTANT: Do not re-derive or add salary guidance from the job description. "
                f"Use ONLY the salary actuals block above as written.\n"
            )
```

- [ ] **Step 4: Run the test to confirm it passes**

```bash
python -m pytest tests/phase5/test_interview_prep.py::test_salary_actuals_prompt_contains_exclusivity_guardrail -v
```

Expected: `PASSED`

- [ ] **Step 5: Run the full Phase 5 test suite to confirm no regressions**

```bash
python -m pytest tests/phase5/test_interview_prep.py -v
```

Expected: all existing tests pass, new test passes.

- [ ] **Step 6: Syntax check**

```bash
python -m py_compile scripts/phase5_interview_prep.py && echo "OK"
```

Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git add scripts/phase5_interview_prep.py tests/phase5/test_interview_prep.py
git commit -m "fix: add salary-actuals exclusivity guardrail to Section 1 prompt"
```

---

## Task 2: Fix Gap 1 fabrication — add confirmed-skills guardrail and redirect honesty rule

**Root cause:** `_build_gap_prompt` instructs Claude to find gaps by cross-referencing the JD against the candidate profile. Two problems:
1. If a skill (e.g., MBSE) appears in the candidate's Confirmed Tools but has limited depth, Claude sometimes still flags it as a gap — ignoring the confirmed experience.
2. The Redirect field sometimes redirects to experience the candidate does not hold (fabricating an MBSE story). The real redirect should be to adjacent domain exposure (e.g., Shield AI work as domain exposure, not MBSE production work).

**Fix:** After the STEP 2 cross-reference instruction in `_build_gap_prompt`, insert two guardrails:
1. **Confirmed-skills guardrail:** "Do not flag as a gap any skill, tool, or methodology that appears in the candidate's Confirmed Tools or Confirmed Skills sections — even if the candidate's depth is limited. Presence in Confirmed Tools or Skills means the gap does not exist."
2. **Redirect honesty rule:** "In the Redirect field: pivot ONLY to experience explicitly stated in the candidate profile. Never suggest the candidate claim experience they do not hold. If the candidate has adjacent domain exposure (e.g., short-term engagement in a related domain), frame the redirect around that specific domain context — not around methodology depth they may not have."

**Files:**
- Modify: `scripts/phase5_interview_prep.py` — `_build_gap_prompt` (around line 478)
- Modify: `tests/phase5/test_interview_prep.py` — add `test_gap_prompt_contains_confirmed_skills_guardrail` and `test_gap_prompt_contains_redirect_honesty_rule`

- [ ] **Step 1: Write the failing tests**

Append to `tests/phase5/test_interview_prep.py`:

```python
def test_gap_prompt_contains_confirmed_skills_guardrail():
    """Gap prompt must instruct Claude not to flag skills listed in Confirmed Tools/Skills
    as gaps — even if the candidate's depth in that area is limited."""
    from scripts.phase5_interview_prep import _build_gap_prompt, STAGE_PROFILES

    profile_with_mbse = (
        "## Confirmed Tools\nCameo Systems Modeler, DoDAF, MBSE\n\n"
        "## Confirmed Skills\nSystems architecture\n"
    )
    prompt = _build_gap_prompt(
        "JD requires MBSE experience",
        "gaps section",
        profile_with_mbse,
        STAGE_PROFILES["hiring_manager"],
        library_seeds=None,
    )
    assert "Confirmed Tools" in prompt or "confirmed tools" in prompt.lower(), (
        "Prompt must reference Confirmed Tools in the guardrail"
    )
    assert "do not flag" in prompt.lower(), (
        "Prompt must explicitly instruct Claude not to flag confirmed skills as gaps"
    )


def test_gap_prompt_contains_redirect_honesty_rule():
    """Redirect field must be constrained to verified experience — no fabrication."""
    from scripts.phase5_interview_prep import _build_gap_prompt, STAGE_PROFILES

    prompt = _build_gap_prompt(
        "JD text", "gaps section", "candidate profile",
        STAGE_PROFILES["team_panel"],
        library_seeds=None,
    )
    assert "Redirect" in prompt
    assert "explicitly stated" in prompt or "explicitly present" in prompt, (
        "Redirect rule must require experience to be explicitly stated in the profile"
    )
```

- [ ] **Step 2: Run the tests to confirm they fail**

```bash
python -m pytest tests/phase5/test_interview_prep.py::test_gap_prompt_contains_confirmed_skills_guardrail tests/phase5/test_interview_prep.py::test_gap_prompt_contains_redirect_honesty_rule -v
```

Expected: both `FAILED`

- [ ] **Step 3: Implement the fix**

In `scripts/phase5_interview_prep.py`, locate `_build_gap_prompt`. Find this block (around line 488):

```python
        f"Do not infer requirements from job type, title, seniority, or industry norms.\n"
        f"Only use what the JD text directly states.\n\n"
        f"FULL JOB DESCRIPTION:\n{jd}\n\n"
        f"STEP 2 -- CROSS-REFERENCE AGAINST CANDIDATE PROFILE:\n"
        f"Compare your extracted lists against the candidate profile below. A gap is valid if:\n"
        f"  - HARD GAP: JD lists it as REQUIRED and it is absent from the candidate's experience\n"
        f"  - PREFERRED GAP: JD lists it as PREFERRED and absent -- flag as lower severity\n\n"
        f"Expect to find 3-5 gaps. If you find zero, re-examine preferred qualifications.\n\n"
```

Replace that entire block with:

```python
        f"Do not infer requirements from job type, title, seniority, or industry norms.\n"
        f"Only use what the JD text directly states.\n\n"
        f"FULL JOB DESCRIPTION:\n{jd}\n\n"
        f"STEP 2 -- CROSS-REFERENCE AGAINST CANDIDATE PROFILE:\n"
        f"Compare your extracted lists against the candidate profile below. A gap is valid if:\n"
        f"  - HARD GAP: JD lists it as REQUIRED and it is absent from the candidate's experience\n"
        f"  - PREFERRED GAP: JD lists it as PREFERRED and absent -- flag as lower severity\n\n"
        f"GUARDRAIL -- Confirmed Tools and Skills are NOT gaps:\n"
        f"Do not flag as a gap any skill, tool, or methodology that appears in the candidate's "
        f"Confirmed Tools or Confirmed Skills sections -- even if the candidate's depth is limited. "
        f"Presence in Confirmed Tools or Skills means that gap does not exist.\n\n"
        f"GUARDRAIL -- Redirect honesty:\n"
        f"In the Redirect field: pivot ONLY to experience explicitly stated in the candidate profile. "
        f"Never suggest the candidate claim experience they do not hold. "
        f"If the candidate has adjacent domain exposure (e.g., a short-term engagement in a related domain), "
        f"frame the redirect around that specific domain context -- not around methodology depth they may not have.\n\n"
        f"Expect to find 3-5 gaps. If you find zero, re-examine preferred qualifications.\n\n"
```

- [ ] **Step 4: Run the new tests to confirm they pass**

```bash
python -m pytest tests/phase5/test_interview_prep.py::test_gap_prompt_contains_confirmed_skills_guardrail tests/phase5/test_interview_prep.py::test_gap_prompt_contains_redirect_honesty_rule -v
```

Expected: both `PASSED`

- [ ] **Step 5: Run the full Phase 5 test suite to confirm no regressions**

```bash
python -m pytest tests/phase5/test_interview_prep.py -v
```

Expected: all existing tests pass, both new tests pass.

- [ ] **Step 6: Syntax check**

```bash
python -m py_compile scripts/phase5_interview_prep.py && echo "OK"
```

Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git add scripts/phase5_interview_prep.py tests/phase5/test_interview_prep.py
git commit -m "fix: add confirmed-skills guardrail and redirect honesty rule to gap prompt"
```

---

## Self-Review

### Spec coverage check

| Requirement | Task |
|-------------|------|
| Salary dupe: reconcile to single anchor when actuals present | Task 1 — exclusivity guardrail in `_build_section1_prompt` |
| Salary dupe: verified by test on API payload | Task 1, Step 1 — `test_salary_actuals_prompt_contains_exclusivity_guardrail` |
| Gap 1: do not flag confirmed tools as gaps | Task 2 — confirmed-skills guardrail in `_build_gap_prompt` |
| Gap 1: redirect to real experience only | Task 2 — redirect honesty rule in `_build_gap_prompt` |
| Gap 1: domain-gap framing for adjacent exposure | Task 2 — "adjacent domain exposure" language in redirect rule |
| No regressions | Tasks 1 and 2 — full suite run before commit |

No gaps found.

### Placeholder scan

No TBDs, TODOs, or vague instructions. All code blocks are complete.

### Type consistency

- `_build_section1_prompt(jd, salary_data, profile, salary_actuals=None)` — signature unchanged, `salary_block` string is extended in place ✓
- `_build_gap_prompt(jd, gaps_section, candidate_profile, profile, library_seeds=None)` — signature unchanged, guardrail text inserted inline ✓
- Test assertions use exact string matches against functions that already exist ✓
