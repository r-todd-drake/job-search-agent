# Docx Salary Content Injection Fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the independent "Salary Guidance" injection in `generate_prep_docx` so the .docx faithfully renders only what is in the .txt source.

**Architecture:** Single-function fix. `generate_prep_docx` (lines 863-866 of `phase5_interview_prep.py`) appends a "Salary Guidance" section directly from `salary_data['guidance']` — a code path entirely independent of the .txt. The fix removes those 4 lines, removes the now-unused `salary_data` parameter from the function signature, and updates the one call site. The .txt already contains all salary content the AI was asked to generate (via the prompt); the docx should render only that.

**Tech Stack:** Python 3, python-docx, pytest

---

## Root Cause (confirmed by code audit)

`generate_prep_docx` in `scripts/phase5_interview_prep.py` at lines 863–866:

```python
    # Salary guidance
    if salary_data['found']:
        add_heading("Salary Guidance", level=1)
        add_normal(salary_data['guidance'])
```

This runs **after** all section text has been rendered via `parse_and_add_section`. It appends a standalone "Salary Guidance" heading + the raw extracted guidance string directly from `salary_data` — content that was never written to the .txt. For the `hiring_manager` stage, the AI-generated `section1` already contains salary content (the prompt explicitly instructs it to "Include salary guidance block"), so the .txt has salary sections within Section 1. The docx then renders those (matching the .txt) and then appends this additional injected section — creating the third salary entry.

---

## File Map

| Action | File | What changes |
|--------|------|--------------|
| Modify | `scripts/phase5_interview_prep.py:754-868` | Remove injection block; remove `salary_data` parameter |
| Modify | `scripts/phase5_interview_prep.py:1153-1157` | Update call site — remove `salary_data` argument |
| Modify | `tests/phase5/test_interview_prep.py` | Add failing test (Task 1), update it after fix (Task 2) |

---

### Task 1: Write the failing test

**Files:**
- Modify: `tests/phase5/test_interview_prep.py`

- [ ] **Step 1: Add the failing test to the test file**

Append this function to `tests/phase5/test_interview_prep.py` (after the last test, before EOF):

```python
def test_generate_prep_docx_does_not_inject_salary_guidance():
    """Docx must render only section text — no content from salary_data injected."""
    import tempfile
    from pathlib import Path
    from docx import Document
    from scripts.phase5_interview_prep import generate_prep_docx, STAGE_PROFILES

    salary_data = {
        'found': True,
        'text': '$150,000 - $180,000',
        'guidance': 'SENTINEL_SALARY_INJECTION_TEXT'
    }
    profile = STAGE_PROFILES['hiring_manager']

    with tempfile.TemporaryDirectory() as tmpdir:
        docx_path = Path(tmpdir) / "test_prep.docx"
        generate_prep_docx(
            str(docx_path),
            role="test_role",
            resume_source="test_stage.txt",
            stage_profile=profile,
            section1="Section one content. No salary here.",
            section_intro="Intro content.",
            section2="Story bank content.",
            section3="Gap prep content.",
            section4="Questions content.",
            salary_data=salary_data,
        )
        doc = Document(str(docx_path))
        all_text = "\n".join(p.text for p in doc.paragraphs)

    assert "SENTINEL_SALARY_INJECTION_TEXT" not in all_text, (
        "generate_prep_docx must not inject salary_data['guidance'] — .txt is source of truth"
    )
    assert "Salary Guidance" not in all_text, (
        "generate_prep_docx must not add a 'Salary Guidance' heading — it is not present in the .txt"
    )
```

- [ ] **Step 2: Run the test — verify it FAILS**

```
python -m pytest tests/phase5/test_interview_prep.py::test_generate_prep_docx_does_not_inject_salary_guidance -v
```

Expected: FAIL with `AssertionError: generate_prep_docx must not inject salary_data['guidance']`

If it passes, the injection is already gone — stop and investigate before continuing.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/phase5/test_interview_prep.py
git commit -m "test: assert generate_prep_docx does not inject salary content outside .txt"
```

---

### Task 2: Fix the injection and clean up the parameter

**Files:**
- Modify: `scripts/phase5_interview_prep.py:754-868` (function signature + body)
- Modify: `scripts/phase5_interview_prep.py:1153-1157` (call site)
- Modify: `tests/phase5/test_interview_prep.py` (update test to new signature)

- [ ] **Step 1: Remove the injection block and the `salary_data` parameter**

In `scripts/phase5_interview_prep.py`, replace the current function signature and closing block:

**Current signature (line 754):**
```python
def generate_prep_docx(output_path, role, resume_source, stage_profile,
                        section1, section_intro, section2, section3, section4,
                        salary_data, continuity_section=""):
```

**New signature:**
```python
def generate_prep_docx(output_path, role, resume_source, stage_profile,
                        section1, section_intro, section2, section3, section4,
                        continuity_section=""):
```

**Remove lines 863-866 entirely** (the injection block):
```python
    # Salary guidance
    if salary_data['found']:
        add_heading("Salary Guidance", level=1)
        add_normal(salary_data['guidance'])
```

The function should end at `doc.save(output_path)` with nothing after it except the closing of the function.

- [ ] **Step 2: Update the call site**

In `scripts/phase5_interview_prep.py`, the call to `generate_prep_docx` around lines 1153-1157:

**Current:**
```python
        generate_prep_docx(
            output_docx_path, role_name, resume_source, profile,
            section1, section_intro, section2, section3, section4,
            salary_data, continuity_section=continuity_text
        )
```

**New:**
```python
        generate_prep_docx(
            output_docx_path, role_name, resume_source, profile,
            section1, section_intro, section2, section3, section4,
            continuity_section=continuity_text
        )
```

- [ ] **Step 3: Update the test to match the new signature**

In `tests/phase5/test_interview_prep.py`, update `test_generate_prep_docx_does_not_inject_salary_guidance`:

Remove the `salary_data` dict and the `salary_data=salary_data` argument from the call, and tighten the assertions:

```python
def test_generate_prep_docx_does_not_inject_salary_guidance():
    """Docx must render only section text — no standalone Salary Guidance section injected."""
    import tempfile
    from pathlib import Path
    from docx import Document
    from scripts.phase5_interview_prep import generate_prep_docx, STAGE_PROFILES

    profile = STAGE_PROFILES['hiring_manager']

    with tempfile.TemporaryDirectory() as tmpdir:
        docx_path = Path(tmpdir) / "test_prep.docx"
        generate_prep_docx(
            str(docx_path),
            role="test_role",
            resume_source="test_stage.txt",
            stage_profile=profile,
            section1="Section one content. No salary here.",
            section_intro="Intro content.",
            section2="Story bank content.",
            section3="Gap prep content.",
            section4="Questions content.",
        )
        doc = Document(str(docx_path))
        all_text = "\n".join(p.text for p in doc.paragraphs)

    assert "Salary Guidance" not in all_text, (
        "generate_prep_docx must not add a standalone 'Salary Guidance' heading"
    )
```

- [ ] **Step 4: Run the syntax check**

```
python -m py_compile scripts/phase5_interview_prep.py && echo "OK"
```

Expected: `OK`

- [ ] **Step 5: Run the target test — verify it passes**

```
python -m pytest tests/phase5/test_interview_prep.py::test_generate_prep_docx_does_not_inject_salary_guidance -v
```

Expected: PASSED

- [ ] **Step 6: Run the full phase5 test suite — verify no regressions**

```
python -m pytest tests/phase5/ -v
```

Expected: all tests pass.

- [ ] **Step 7: Run the full test suite**

```
python -m pytest tests/ -m "not live" -v
```

Expected: all non-live tests pass (308+ passing).

- [ ] **Step 8: Commit the fix**

```bash
git add scripts/phase5_interview_prep.py tests/phase5/test_interview_prep.py
git commit -m "fix: remove salary_data injection from generate_prep_docx — docx renders .txt only"
```

---

## Self-Review

**Spec coverage:**
- Bug: third "Salary Guidance" section in .docx not present in .txt → Task 2 removes lines 863-866 (the injection).
- Rule: .txt is source of truth, .docx must be a faithful render of it → enforced by removing the independent injection path.
- Signature cleanup: `salary_data` parameter is now unused → removed in Task 2 Step 1.
- Call site updated to match new signature → Task 2 Step 2.
- Test covers the specific regression → Task 1 + Task 2 Step 3.

**Placeholder scan:** None found. All code blocks are complete and literal.

**Type consistency:** `generate_prep_docx` signature is consistent between function definition (Task 2 Step 1), call site (Task 2 Step 2), and test (Task 2 Step 3).

**What this does NOT fix:**
- The .txt having two salary sections within Section 1 (PARKING_LOT item 1 — duplicate salary guidance in the prompt/AI output). That is a separate issue with `_build_section1_prompt` and the AI content generation, tracked separately.
