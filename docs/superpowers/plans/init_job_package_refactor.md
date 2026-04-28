# init_job_package Interactive Field Collection Refactor

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an interactive prompt sequence to `init_job_package.py` so that company, title, location, salary_range, and url are collected at initialization time and written to the jobs.csv row — eliminating the manual backfill step.

**Architecture:** Add a new pure function `collect_optional_fields(input_fn)` that prompts for the 5 optional fields and returns a dict with None for skipped fields. Update `append_csv_row` to accept and write those values. Update `main` to call the prompt sequence and pass the result to the CSV appender. `date_found` already auto-populates via `str(date.today())` — no change needed there.

**Tech Stack:** Python 3.11 stdlib only — `csv`, `datetime`, `unittest.mock` in tests. No new dependencies.

---

## Summary of Changes

### Functions that change

| Function | Change |
|---|---|
| `append_csv_row(csv_path, role, req)` | Add parameter `extra_fields: dict \| None = None`; if provided, merge values into row before writing (None → `""`) |
| `main(role, req, ...)` | Call `collect_optional_fields(input_fn)` after folder-collision loop; pass result as 4th arg to `csv_appender` |

### Functions added

| Function | Responsibility |
|---|---|
| `collect_optional_fields(input_fn=input)` | Prompt for company, title, location, salary_range, url; return dict with None for skipped fields |
| `OPTIONAL_FIELD_PROMPTS` (module constant) | Ordered list of `(csv_key, display_label)` pairs driving the prompt loop |

### Functions that stay the same

`validate_role`, `validate_req`, `load_csv_rows`, `check_conflicts`, `create_job_folder`, `create_job_description`, `open_file_in_editor`

---

## Prompt Sequence

Prompts appear after conflict detection and the folder-collision suffix loop, immediately before `folder_creator` is called.

```
Company (Enter to skip): Acme Defense
Title (Enter to skip): Senior Software Engineer
Location (Enter to skip): Austin TX
Salary range (Enter to skip): $130k-$160k
URL (Enter to skip): https://jobs.acme.com/REQ-99
```

**Skip behavior:** User presses Enter → raw input is `""` after `.strip()` → stored as `None` in the returned dict → written as `""` in the CSV cell.

**Non-empty input:** `.strip()` is applied; non-empty string stored as-is in the dict.

**`date_found`:** Already auto-populated in `append_csv_row` via `str(date.today())`. No prompt, no user input.

**`status`:** Remains blank (`""`) on initialization, meaning NEW. No change.

---

## Existing Tests — Breakage Assessment

File: `tests/utils/test_init_job_package.py` — 25 tests

### Tests that BREAK (2)

These two tests call `main` with a mocked `csv_appender` and assert a 3-argument call. After the refactor, `main` passes a 4th positional argument (`extra_fields`). Both tests also lack an `input_fn` injection — `collect_optional_fields` would block on real stdin.

| Test | Line | Why it breaks | Fix |
|---|---|---|---|
| `test_main_happy_path_calls_all_side_effects` | 161 | Missing `input_fn`; mock assertion checks 3-arg call | Inject `input_fn=lambda _: ""`; update `mock_csv_appender` assertion to include `extra_fields` |
| `test_main_folder_collision_prompts_for_suffix_and_creates_with_new_name` | 248 | `input_fn=lambda _: "_2"` feeds into all 6 calls (1 suffix + 5 fields); mock assertion checks 3-arg call | Replace `lambda _: "_2"` with `MagicMock(side_effect=["_2", "", "", "", "", ""])`; update `mock_csv_appender` assertion |

### Tests that are safe — no changes needed (23)

All other tests are unaffected:
- `test_validate_role_*` (3 tests) — pure function, no change
- `test_validate_req_*` (2 tests) — pure function, no change
- `test_load_csv_rows_*` (1 test) — pure function, no change
- `test_check_conflicts_*` (6 tests) — pure function, no change
- `test_create_job_folder_*` (1 test) — pure function, no change
- `test_create_job_description_*` (1 test) — pure function, no change
- `test_append_csv_row_adds_row` (1 test) — called with 3 positional args; new `extra_fields` param defaults to `None`, so existing call still works
- `test_append_csv_row_sets_date_found` (1 test) — same as above
- `test_open_file_in_editor_*` (3 tests) — pure function, no change
- `test_main_true_duplicate_exits_without_side_effects` (1 test) — returns 1 before `collect_optional_fields` is called; `input_fn` never reached
- `test_main_inactive_reactivation_exits_with_instructions` (1 test) — same, returns 1 early

---

## New Test Cases (10)

All added to `tests/utils/test_init_job_package.py`. Update the top-level import block to add `collect_optional_fields` alongside the existing imports.

### Task 1 tests — `collect_optional_fields`

```python
def test_collect_optional_fields_all_provided():
    responses = iter(["Acme Corp", "Software Engineer", "Austin TX", "$120k-$150k", "https://jobs.acme.com/123"])
    result = collect_optional_fields(input_fn=lambda _: next(responses))
    assert result == {
        "company": "Acme Corp",
        "title": "Software Engineer",
        "location": "Austin TX",
        "salary_range": "$120k-$150k",
        "url": "https://jobs.acme.com/123",
    }


def test_collect_optional_fields_all_skipped():
    result = collect_optional_fields(input_fn=lambda _: "")
    assert result == {
        "company": None,
        "title": None,
        "location": None,
        "salary_range": None,
        "url": None,
    }


def test_collect_optional_fields_mixed():
    responses = iter(["Acme Corp", "", "Austin TX", "", ""])
    result = collect_optional_fields(input_fn=lambda _: next(responses))
    assert result["company"] == "Acme Corp"
    assert result["title"] is None
    assert result["location"] == "Austin TX"
    assert result["salary_range"] is None
    assert result["url"] is None


def test_collect_optional_fields_strips_whitespace():
    result = collect_optional_fields(input_fn=lambda _: "  Acme Corp  ")
    assert result["company"] == "Acme Corp"


def test_collect_optional_fields_prompt_labels():
    prompts_seen = []

    def capture_input(prompt):
        prompts_seen.append(prompt)
        return ""

    collect_optional_fields(input_fn=capture_input)
    assert len(prompts_seen) == 5
    assert any("Company" in p for p in prompts_seen)
    assert any("Title" in p for p in prompts_seen)
    assert any("Location" in p for p in prompts_seen)
    assert any("Salary" in p for p in prompts_seen)
    assert any("URL" in p for p in prompts_seen)
```

### Task 2 tests — `append_csv_row` with `extra_fields`

```python
def test_append_csv_row_full_row_completeness(tmp_path):
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "company,title,location,salary_range,url,req_number,date_found,status,package_folder\n"
    )
    extra_fields = {
        "company": "Acme Corp",
        "title": "Software Engineer",
        "location": "Austin TX",
        "salary_range": "$120k-$150k",
        "url": "https://jobs.acme.com/123",
    }
    append_csv_row(str(csv_file), "Acme_SE", "REQ-1", extra_fields)
    rows = list(csv.DictReader(open(str(csv_file))))
    assert rows[0]["company"] == "Acme Corp"
    assert rows[0]["title"] == "Software Engineer"
    assert rows[0]["location"] == "Austin TX"
    assert rows[0]["salary_range"] == "$120k-$150k"
    assert rows[0]["url"] == "https://jobs.acme.com/123"
    assert rows[0]["req_number"] == "REQ-1"
    assert rows[0]["package_folder"] == "Acme_SE"
    assert rows[0]["date_found"] == str(date.today())


def test_append_csv_row_extra_fields_none_becomes_empty_string(tmp_path):
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "company,title,location,salary_range,url,req_number,date_found,status,package_folder\n"
    )
    extra_fields = {"company": None, "title": "Engineer", "location": None, "salary_range": None, "url": None}
    append_csv_row(str(csv_file), "Acme_SE", "REQ-1", extra_fields)
    rows = list(csv.DictReader(open(str(csv_file))))
    assert rows[0]["company"] == ""
    assert rows[0]["title"] == "Engineer"
    assert rows[0]["location"] == ""
    assert rows[0]["salary_range"] == ""
    assert rows[0]["url"] == ""
```

### Task 3 tests — `main` integration

```python
def test_main_optional_fields_passed_to_csv_appender(tmp_path):
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "package_folder,status,req_number,date_found,company,title,location,salary_range,url\n"
    )
    mock_csv_appender = MagicMock()
    responses = iter(["Acme Corp", "Software Engineer", "", "", ""])

    main(
        role="Acme_SE",
        req="REQ-1",
        packages_dir=str(tmp_path),
        jobs_csv=str(csv_file),
        folder_creator=MagicMock(return_value=str(tmp_path / "Acme_SE")),
        file_creator=MagicMock(return_value=str(tmp_path / "Acme_SE" / "job_description.txt")),
        csv_appender=mock_csv_appender,
        file_opener=MagicMock(),
        folder_exists=lambda p: False,
        input_fn=lambda _: next(responses),
    )

    mock_csv_appender.assert_called_once_with(
        str(csv_file),
        "Acme_SE",
        "REQ-1",
        {"company": "Acme Corp", "title": "Software Engineer", "location": None, "salary_range": None, "url": None},
    )


def test_main_date_found_auto_populated_not_prompted(tmp_path):
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "package_folder,status,req_number,date_found,company,title,location,salary_range,url\n"
    )
    prompt_count = 0

    def counting_input_fn(_):
        nonlocal prompt_count
        prompt_count += 1
        return ""

    main(
        role="Acme_SE",
        req="REQ-1",
        packages_dir=str(tmp_path),
        jobs_csv=str(csv_file),
        folder_creator=MagicMock(return_value=str(tmp_path / "Acme_SE")),
        file_creator=MagicMock(return_value=str(tmp_path / "Acme_SE" / "job_description.txt")),
        csv_appender=MagicMock(),
        file_opener=MagicMock(),
        folder_exists=lambda p: False,
        input_fn=counting_input_fn,
    )

    assert prompt_count == 5  # company, title, location, salary_range, url — not date_found


def test_main_prompts_not_shown_on_true_duplicate(tmp_path):
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "package_folder,status,req_number,date_found\nAcme_SE,PURSUE,REQ-1,2026-01-01\n"
    )
    prompt_count = 0

    def counting_input_fn(_):
        nonlocal prompt_count
        prompt_count += 1
        return ""

    exit_code = main(
        role="Acme_SE",
        req="REQ-1",
        packages_dir=str(tmp_path),
        jobs_csv=str(csv_file),
        folder_creator=MagicMock(),
        file_creator=MagicMock(),
        csv_appender=MagicMock(),
        file_opener=MagicMock(),
        folder_exists=lambda p: False,
        input_fn=counting_input_fn,
    )

    assert exit_code == 1
    assert prompt_count == 0
```

---

## Implementation Tasks

### Task 1: Add `collect_optional_fields` and its tests

**Files:**
- Modify: `scripts/init_job_package.py` (add constant + function)
- Modify: `tests/utils/test_init_job_package.py` (update import, add 5 tests)

- [ ] **Step 1.1: Add `collect_optional_fields` to the import block in the test file**

In `tests/utils/test_init_job_package.py`, update the top-level import to:

```python
from scripts.init_job_package import (
    validate_role,
    validate_req,
    load_csv_rows,
    check_conflicts,
    create_job_folder,
    create_job_description,
    append_csv_row,
    open_file_in_editor,
    collect_optional_fields,
    main,
)
```

- [ ] **Step 1.2: Add the 5 new `collect_optional_fields` tests**

Append to `tests/utils/test_init_job_package.py` (after the existing `test_append_csv_row_sets_date_found` test, before the `test_open_file_in_editor_*` block):

```python
def test_collect_optional_fields_all_provided():
    responses = iter(["Acme Corp", "Software Engineer", "Austin TX", "$120k-$150k", "https://jobs.acme.com/123"])
    result = collect_optional_fields(input_fn=lambda _: next(responses))
    assert result == {
        "company": "Acme Corp",
        "title": "Software Engineer",
        "location": "Austin TX",
        "salary_range": "$120k-$150k",
        "url": "https://jobs.acme.com/123",
    }


def test_collect_optional_fields_all_skipped():
    result = collect_optional_fields(input_fn=lambda _: "")
    assert result == {
        "company": None,
        "title": None,
        "location": None,
        "salary_range": None,
        "url": None,
    }


def test_collect_optional_fields_mixed():
    responses = iter(["Acme Corp", "", "Austin TX", "", ""])
    result = collect_optional_fields(input_fn=lambda _: next(responses))
    assert result["company"] == "Acme Corp"
    assert result["title"] is None
    assert result["location"] == "Austin TX"
    assert result["salary_range"] is None
    assert result["url"] is None


def test_collect_optional_fields_strips_whitespace():
    result = collect_optional_fields(input_fn=lambda _: "  Acme Corp  ")
    assert result["company"] == "Acme Corp"


def test_collect_optional_fields_prompt_labels():
    prompts_seen = []

    def capture_input(prompt):
        prompts_seen.append(prompt)
        return ""

    collect_optional_fields(input_fn=capture_input)
    assert len(prompts_seen) == 5
    assert any("Company" in p for p in prompts_seen)
    assert any("Title" in p for p in prompts_seen)
    assert any("Location" in p for p in prompts_seen)
    assert any("Salary" in p for p in prompts_seen)
    assert any("URL" in p for p in prompts_seen)
```

- [ ] **Step 1.3: Run the tests to verify the 5 new tests fail with ImportError**

```
pytest tests/utils/test_init_job_package.py -v
```

Expected: `ImportError: cannot import name 'collect_optional_fields'` — all tests in the file will error (not just the 5 new ones). That is correct.

- [ ] **Step 1.4: Add `OPTIONAL_FIELD_PROMPTS` and `collect_optional_fields` to `scripts/init_job_package.py`**

Insert after the `ACTIVE_STATUSES` line (line 21) and before `validate_role`:

```python
OPTIONAL_FIELD_PROMPTS = [
    ("company", "Company"),
    ("title", "Title"),
    ("location", "Location"),
    ("salary_range", "Salary range"),
    ("url", "URL"),
]


def collect_optional_fields(input_fn=input) -> dict:
    fields = {}
    for key, label in OPTIONAL_FIELD_PROMPTS:
        raw = input_fn(f"{label} (Enter to skip): ").strip()
        fields[key] = raw if raw else None
    return fields
```

- [ ] **Step 1.5: Run the full test suite to verify all 30 tests pass**

```
pytest tests/utils/test_init_job_package.py -v
```

Expected: 30 passed (25 original + 5 new). No failures.

- [ ] **Step 1.6: Commit**

```bash
git add scripts/init_job_package.py tests/utils/test_init_job_package.py
git commit -m "feat(phase1): add collect_optional_fields to init_job_package"
```

---

### Task 2: Update `append_csv_row` to accept `extra_fields`

**Files:**
- Modify: `scripts/init_job_package.py` (update `append_csv_row` signature + body)
- Modify: `tests/utils/test_init_job_package.py` (add 2 new tests)

- [ ] **Step 2.1: Add 2 new failing tests for `append_csv_row` with `extra_fields`**

Append to `tests/utils/test_init_job_package.py` (after `test_append_csv_row_sets_date_found`):

```python
def test_append_csv_row_full_row_completeness(tmp_path):
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "company,title,location,salary_range,url,req_number,date_found,status,package_folder\n"
    )
    extra_fields = {
        "company": "Acme Corp",
        "title": "Software Engineer",
        "location": "Austin TX",
        "salary_range": "$120k-$150k",
        "url": "https://jobs.acme.com/123",
    }
    append_csv_row(str(csv_file), "Acme_SE", "REQ-1", extra_fields)
    rows = list(csv.DictReader(open(str(csv_file))))
    assert rows[0]["company"] == "Acme Corp"
    assert rows[0]["title"] == "Software Engineer"
    assert rows[0]["location"] == "Austin TX"
    assert rows[0]["salary_range"] == "$120k-$150k"
    assert rows[0]["url"] == "https://jobs.acme.com/123"
    assert rows[0]["req_number"] == "REQ-1"
    assert rows[0]["package_folder"] == "Acme_SE"
    assert rows[0]["date_found"] == str(date.today())


def test_append_csv_row_extra_fields_none_becomes_empty_string(tmp_path):
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "company,title,location,salary_range,url,req_number,date_found,status,package_folder\n"
    )
    extra_fields = {"company": None, "title": "Engineer", "location": None, "salary_range": None, "url": None}
    append_csv_row(str(csv_file), "Acme_SE", "REQ-1", extra_fields)
    rows = list(csv.DictReader(open(str(csv_file))))
    assert rows[0]["company"] == ""
    assert rows[0]["title"] == "Engineer"
    assert rows[0]["location"] == ""
    assert rows[0]["salary_range"] == ""
    assert rows[0]["url"] == ""
```

- [ ] **Step 2.2: Run to verify the 2 new tests fail**

```
pytest tests/utils/test_init_job_package.py::test_append_csv_row_full_row_completeness tests/utils/test_init_job_package.py::test_append_csv_row_extra_fields_none_becomes_empty_string -v
```

Expected: 2 FAILED — `append_csv_row` does not accept a 4th argument.

- [ ] **Step 2.3: Update `append_csv_row` in `scripts/init_job_package.py`**

Replace the existing `append_csv_row` function with:

```python
def append_csv_row(csv_path: str, role: str, req: str, extra_fields: dict | None = None) -> None:
    with open(csv_path, newline="", encoding="utf-8") as f:
        fieldnames = csv.DictReader(f).fieldnames or []
    row = {field: "" for field in fieldnames}
    row["package_folder"] = role
    row["req_number"] = req
    row["date_found"] = str(date.today())
    if extra_fields:
        for key, value in extra_fields.items():
            if key in row:
                row[key] = value if value is not None else ""
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerow(row)
```

- [ ] **Step 2.3a: Verify `test_append_csv_row_adds_row` still writes empty strings for unset fields**

After implementing the change in Step 2.3, run this test in isolation:

```
pytest tests/utils/test_init_job_package.py::test_append_csv_row_adds_row -v
```

Expected: PASS. This test calls `append_csv_row` with 3 positional args (no `extra_fields`). The new `extra_fields` param defaults to `None`, so the row is built with `{field: "" for field in fieldnames}` as before — all fields including company, title, location, salary_range, and url are present in the row as `""` (empty string, not absent). Confirm the test passes without modification.

- [ ] **Step 2.4: Run the full test suite to verify all 32 tests pass**

```
pytest tests/utils/test_init_job_package.py -v
```

Expected: 32 passed (30 from Task 1 + 2 new). No failures. The existing 3-argument callers in the existing tests continue to work because `extra_fields` defaults to `None`.

- [ ] **Step 2.5: Commit**

```bash
git add scripts/init_job_package.py tests/utils/test_init_job_package.py
git commit -m "feat(phase1): append_csv_row accepts optional extra_fields dict"
```

---

### Task 3: Update `main` and fix the 2 broken tests; add 3 new main tests

**Files:**
- Modify: `scripts/init_job_package.py` (update `main`)
- Modify: `tests/utils/test_init_job_package.py` (fix 2 existing tests, add 3 new tests)

- [ ] **Step 3.1: Add 3 new failing main tests**

Append to `tests/utils/test_init_job_package.py`:

```python
def test_main_optional_fields_passed_to_csv_appender(tmp_path):
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "package_folder,status,req_number,date_found,company,title,location,salary_range,url\n"
    )
    mock_csv_appender = MagicMock()
    responses = iter(["Acme Corp", "Software Engineer", "", "", ""])

    main(
        role="Acme_SE",
        req="REQ-1",
        packages_dir=str(tmp_path),
        jobs_csv=str(csv_file),
        folder_creator=MagicMock(return_value=str(tmp_path / "Acme_SE")),
        file_creator=MagicMock(return_value=str(tmp_path / "Acme_SE" / "job_description.txt")),
        csv_appender=mock_csv_appender,
        file_opener=MagicMock(),
        folder_exists=lambda p: False,
        input_fn=lambda _: next(responses),
    )

    mock_csv_appender.assert_called_once_with(
        str(csv_file),
        "Acme_SE",
        "REQ-1",
        {"company": "Acme Corp", "title": "Software Engineer", "location": None, "salary_range": None, "url": None},
    )


def test_main_date_found_auto_populated_not_prompted(tmp_path):
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "package_folder,status,req_number,date_found,company,title,location,salary_range,url\n"
    )
    prompt_count = 0

    def counting_input_fn(_):
        nonlocal prompt_count
        prompt_count += 1
        return ""

    main(
        role="Acme_SE",
        req="REQ-1",
        packages_dir=str(tmp_path),
        jobs_csv=str(csv_file),
        folder_creator=MagicMock(return_value=str(tmp_path / "Acme_SE")),
        file_creator=MagicMock(return_value=str(tmp_path / "Acme_SE" / "job_description.txt")),
        csv_appender=MagicMock(),
        file_opener=MagicMock(),
        folder_exists=lambda p: False,
        input_fn=counting_input_fn,
    )

    assert prompt_count == 5  # company, title, location, salary_range, url -- not date_found


def test_main_prompts_not_shown_on_true_duplicate(tmp_path):
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "package_folder,status,req_number,date_found\nAcme_SE,PURSUE,REQ-1,2026-01-01\n"
    )
    prompt_count = 0

    def counting_input_fn(_):
        nonlocal prompt_count
        prompt_count += 1
        return ""

    exit_code = main(
        role="Acme_SE",
        req="REQ-1",
        packages_dir=str(tmp_path),
        jobs_csv=str(csv_file),
        folder_creator=MagicMock(),
        file_creator=MagicMock(),
        csv_appender=MagicMock(),
        file_opener=MagicMock(),
        folder_exists=lambda p: False,
        input_fn=counting_input_fn,
    )

    assert exit_code == 1
    assert prompt_count == 0
```

- [ ] **Step 3.2: Run to verify the 3 new tests fail**

```
pytest tests/utils/test_init_job_package.py::test_main_optional_fields_passed_to_csv_appender tests/utils/test_init_job_package.py::test_main_date_found_auto_populated_not_prompted tests/utils/test_init_job_package.py::test_main_prompts_not_shown_on_true_duplicate -v
```

Expected: 3 FAILED — `main` does not yet call `collect_optional_fields` or pass `extra_fields`.

- [ ] **Step 3.3: Update the 2 existing `main` tests that will break**

In `tests/utils/test_init_job_package.py`, replace `test_main_happy_path_calls_all_side_effects`:

```python
def test_main_happy_path_calls_all_side_effects(tmp_path, capsys):
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "package_folder,status,req_number,date_found,company,title,location,salary_range,url\n"
    )
    mock_folder_creator = MagicMock(return_value=str(tmp_path / "Anduril_SE"))
    mock_file_creator = MagicMock(
        return_value=str(tmp_path / "Anduril_SE" / "job_description.txt")
    )
    mock_csv_appender = MagicMock()
    mock_file_opener = MagicMock()

    exit_code = main(
        role="Anduril_SE",
        req="REQ-1",
        packages_dir=str(tmp_path),
        jobs_csv=str(csv_file),
        folder_creator=mock_folder_creator,
        file_creator=mock_file_creator,
        csv_appender=mock_csv_appender,
        file_opener=mock_file_opener,
        folder_exists=lambda p: False,
        input_fn=lambda _: "",
    )

    assert exit_code == 0
    mock_folder_creator.assert_called_once_with(str(tmp_path), "Anduril_SE")
    mock_file_creator.assert_called_once_with(str(tmp_path / "Anduril_SE"))
    mock_csv_appender.assert_called_once_with(
        str(csv_file),
        "Anduril_SE",
        "REQ-1",
        {"company": None, "title": None, "location": None, "salary_range": None, "url": None},
    )
    mock_file_opener.assert_called_once()
    captured = capsys.readouterr()
    assert "job_description.txt" in captured.out
```

Replace `test_main_folder_collision_prompts_for_suffix_and_creates_with_new_name`:

```python
def test_main_folder_collision_prompts_for_suffix_and_creates_with_new_name(tmp_path, capsys):
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "package_folder,status,req_number,date_found,company,title,location,salary_range,url\n"
    )

    def folder_exists(path):
        return os.path.basename(path) == "Anduril_SE"

    mock_folder_creator = MagicMock(return_value=str(tmp_path / "Anduril_SE_2"))
    mock_file_creator = MagicMock(
        return_value=str(tmp_path / "Anduril_SE_2" / "job_description.txt")
    )
    mock_csv_appender = MagicMock()
    # First call: suffix prompt returns "_2"; next 5 calls: field prompts return "" (skip all)
    input_fn = MagicMock(side_effect=["_2", "", "", "", "", ""])

    exit_code = main(
        role="Anduril_SE",
        req="REQ-99",
        packages_dir=str(tmp_path),
        jobs_csv=str(csv_file),
        folder_creator=mock_folder_creator,
        file_creator=mock_file_creator,
        csv_appender=mock_csv_appender,
        file_opener=MagicMock(),
        folder_exists=folder_exists,
        input_fn=input_fn,
    )

    assert exit_code == 0
    mock_folder_creator.assert_called_once_with(str(tmp_path), "Anduril_SE_2")
    mock_csv_appender.assert_called_once_with(
        str(csv_file),
        "Anduril_SE_2",
        "REQ-99",
        {"company": None, "title": None, "location": None, "salary_range": None, "url": None},
    )
```

- [ ] **Step 3.4: Run to confirm that the 2 updated tests now fail (because `main` not yet changed)**

```
pytest tests/utils/test_init_job_package.py::test_main_happy_path_calls_all_side_effects tests/utils/test_init_job_package.py::test_main_folder_collision_prompts_for_suffix_and_creates_with_new_name -v
```

Expected: 2 FAILED — `main` still calls `csv_appender` with 3 args.

- [ ] **Step 3.5: Update `main` in `scripts/init_job_package.py`**

First, confirm that `main`'s parameter list includes `input_fn=input` (it should already be there at line 108). If it is absent or has been renamed, restore it to the signature before proceeding:

```python
def main(
    role: str,
    req: str,
    packages_dir: str = PACKAGES_DIR,
    jobs_csv: str = JOBS_CSV,
    folder_creator=create_job_folder,
    file_creator=create_job_description,
    csv_appender=append_csv_row,
    file_opener=open_file_in_editor,
    folder_exists=os.path.exists,
    input_fn=input,
) -> int:
```

Then, in the `main` function body, insert the call to `collect_optional_fields` after the `while folder_exists(...)` loop and before the `folder_creator` call. Change the `csv_appender` call to pass `extra_fields`.

Replace the section from the `while` loop through `csv_appender(jobs_csv, final_role, req)` with:

```python
    final_role = role
    while folder_exists(os.path.join(packages_dir, final_role)):
        print(f"Warning: folder '{final_role}' already exists in {packages_dir}/.")
        suffix = input_fn("Enter a disambiguating suffix (e.g., '_2'): ").strip()
        if not suffix:
            print("Suffix cannot be empty. Try again.")
            continue
        final_role = role + suffix

    extra_fields = collect_optional_fields(input_fn)

    folder_path = folder_creator(packages_dir, final_role)
    jd_path = file_creator(folder_path)
    csv_appender(jobs_csv, final_role, req, extra_fields)
```

- [ ] **Step 3.6: Run the full test suite**

```
pytest tests/utils/test_init_job_package.py -v
```

Expected: 35 passed (32 from Tasks 1–2 + 3 new). No failures.

- [ ] **Step 3.7: Run broader test suite to confirm no regressions**

```
pytest tests/ -m "not live" -v
```

Expected: all tests pass.

- [ ] **Step 3.8: Commit**

```bash
git add scripts/init_job_package.py tests/utils/test_init_job_package.py
git commit -m "feat(phase1): init_job_package prompts for all jobs.csv fields at init time"
```

---

### Task 4: Update `SCRIPT_INDEX.md`

**Files:**
- Modify: `context/SCRIPT_INDEX.md`

- [ ] **Step 4.1: Verify the path to SCRIPT_INDEX.md, then update the `init_job_package.py` row**

First, confirm the file exists at the expected path:

```
ls context/SCRIPT_INDEX.md
```

Expected: file listed. If the file has moved, locate it with `find . -name "SCRIPT_INDEX.md"` before editing.

The current row in the Initialization table:

```
| `init_job_package.py` | Create a new job package folder, empty `job_description.txt`, and `jobs.csv` row; opens file in editor | `--role` `--req` |
```

Replace with:

```
| `init_job_package.py` | Create a new job package folder, empty `job_description.txt`, and a complete `jobs.csv` row; prompts for company, title, location, salary_range, url (Enter to skip); opens file in editor | `--role` `--req` |
```

- [ ] **Step 4.2: Commit**

```bash
git add context/SCRIPT_INDEX.md
git commit -m "docs: update SCRIPT_INDEX for init_job_package field-collection prompts"
```

---

### Task 5: Update README Daily Workflow step 01

**Files:**
- Modify: `README.md`

Step 01 currently reads:

```
01. Add new roles to jobs.csv (blank status, req number if available)
```

This describes a manual CSV-edit workflow that is superseded by `init_job_package.py`, which now collects all fields interactively at init time. Leaving this unchanged would send new users to manually edit jobs.csv instead of using the script.

- [ ] **Step 5.1: Update README.md Daily Workflow step 01**

Replace the current step 01 line with:

```
01. Run init_job_package.py --role [role] --req [req#] for each new role
   → Prompts for company, title, location, salary_range, url (Enter to skip)
   → Creates job_description.txt and writes a complete jobs.csv row
```

- [ ] **Step 5.2: Commit**

```bash
git add README.md
git commit -m "docs: update Daily Workflow step 01 to use init_job_package prompts"
```

---

## Docs Update Summary

| File | Change needed |
|---|---|
| `context/SCRIPT_INDEX.md` | Yes — update purpose column to mention interactive prompts (Task 4) |
| `README.md` | Yes — update Daily Workflow step 01 from manual CSV-edit to `init_job_package.py` prompt workflow (Task 5) |
| `context/DATA_FLOW.md` | No — `init_job_package` has no entry in DATA_FLOW.md |
| `context/PARKING_LOT.md` | No — no active item tracks this refactor; the speculative xlsx migration note already says "complete this refactor first" — that condition will be satisfied by this work |
