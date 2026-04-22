# Job Package Initializer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `scripts/init_job_package.py`, a CLI utility that creates a new job package folder and blank `job_description.txt`, appends a row to `jobs.csv`, and opens the file for editing — with full conflict detection.

**Architecture:** Single script with injectable side-effect functions for full testability. Conflict detection reads `jobs.csv` and the filesystem before any write. All conflict branches (true duplicate, folder collision with suffix prompt, inactive reactivation) exit cleanly without partial state.

**Tech Stack:** Python stdlib only — `argparse`, `csv`, `os`, `re`, `subprocess`, `sys`, `datetime`. No Anthropic API calls, no external dependencies.

---

## Files

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `scripts/init_job_package.py` | CLI entry point, validators, CSV/filesystem ops, conflict detection, main orchestration |
| Create | `tests/utils/test_init_job_package.py` | Unit tests — mocks all side effects |
| Modify | `context/SCRIPT_INDEX.md` | Add row for `init_job_package.py` |
| Modify | `docs/features/job_package_initializer/feature_job_package_init.md` | Resolve open REVIEW annotation |

---

### Task 1: Script skeleton, arg parsing, input validation

**Files:**
- Create: `scripts/init_job_package.py`
- Create: `tests/utils/test_init_job_package.py`

- [ ] **Step 1: Create the test file with failing validation tests**

```python
# tests/utils/test_init_job_package.py
import pytest


def test_validate_role_accepts_valid_name():
    from scripts.init_job_package import validate_role
    validate_role("Anduril_EW_SE")  # should not raise


def test_validate_role_rejects_slash():
    from scripts.init_job_package import validate_role
    with pytest.raises(ValueError, match="invalid characters"):
        validate_role("Anduril/EW/SE")


def test_validate_role_rejects_backslash():
    from scripts.init_job_package import validate_role
    with pytest.raises(ValueError, match="invalid characters"):
        validate_role("Anduril\\EW")


def test_validate_role_rejects_empty():
    from scripts.init_job_package import validate_role
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_role("")


def test_validate_req_accepts_valid_req():
    from scripts.init_job_package import validate_req
    validate_req("REQ-12345")  # should not raise


def test_validate_req_rejects_empty():
    from scripts.init_job_package import validate_req
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_req("")
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/utils/test_init_job_package.py -v
```

Expected: ImportError or ModuleNotFoundError — `init_job_package` module does not exist yet.

- [ ] **Step 3: Create the script skeleton with validators**

```python
# scripts/init_job_package.py
# ==============================================
# init_job_package.py
# Creates a new job package folder, empty job_description.txt,
# and a new row in jobs.csv. Opens the file for editing.
#
# Usage:
#   python -m scripts.init_job_package --role Anduril_EW_SE --req REQ-12345
# ==============================================

import argparse
import csv
import os
import re
import subprocess
import sys
from datetime import date

JOBS_CSV = "data/jobs.csv"
PACKAGES_DIR = "data/job_packages"
ACTIVE_STATUSES = {"", "PURSUE", "CONSIDER", "APPLIED"}


def validate_role(role: str) -> None:
    if not role:
        raise ValueError("--role cannot be empty")
    if re.search(r'[/\\:*?"<>|]', role):
        raise ValueError(f"--role contains invalid characters: {role!r}")


def validate_req(req: str) -> None:
    if not req:
        raise ValueError("--req cannot be empty")


if __name__ == "__main__":
    pass
```

- [ ] **Step 4: Run tests to confirm they pass**

```
pytest tests/utils/test_init_job_package.py -v
```

Expected: all 6 PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/init_job_package.py tests/utils/test_init_job_package.py
git commit -m "feat: scaffold init_job_package with input validators"
```

---

### Task 2: CSV loading and conflict detection

**Files:**
- Modify: `scripts/init_job_package.py`
- Modify: `tests/utils/test_init_job_package.py`

- [ ] **Step 1: Add failing tests for load_csv_rows and check_conflicts**

```python
# Append to tests/utils/test_init_job_package.py

import csv


def test_load_csv_rows_returns_list_of_dicts(tmp_path):
    from scripts.init_job_package import load_csv_rows
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text("package_folder,status,req_number\nAnduril_SE,PURSUE,REQ-1\n")
    rows = load_csv_rows(str(csv_file))
    assert len(rows) == 1
    assert rows[0]["package_folder"] == "Anduril_SE"
    assert rows[0]["req_number"] == "REQ-1"


def test_check_conflicts_true_duplicate_active_status():
    from scripts.init_job_package import check_conflicts
    rows = [{"package_folder": "Anduril_SE", "status": "PURSUE", "req_number": "REQ-1"}]
    assert check_conflicts(rows, "Anduril_SE", "REQ-1") == "true_duplicate"


def test_check_conflicts_true_duplicate_blank_status():
    from scripts.init_job_package import check_conflicts
    rows = [{"package_folder": "Anduril_SE", "status": "", "req_number": "REQ-1"}]
    assert check_conflicts(rows, "Anduril_SE", "REQ-1") == "true_duplicate"


def test_check_conflicts_true_duplicate_applied_same_role():
    # APPLIED is an active status — same role + same req# is still a hard duplicate
    from scripts.init_job_package import check_conflicts
    rows = [{"package_folder": "Anduril_SE", "status": "APPLIED", "req_number": "REQ-1"}]
    assert check_conflicts(rows, "Anduril_SE", "REQ-1") == "true_duplicate"


def test_check_conflicts_inactive_skip():
    from scripts.init_job_package import check_conflicts
    rows = [{"package_folder": "Anduril_SE", "status": "SKIP", "req_number": "REQ-1"}]
    assert check_conflicts(rows, "Anduril_SE", "REQ-1") == "inactive_reactivation"


def test_check_conflicts_inactive_ghosted():
    from scripts.init_job_package import check_conflicts
    rows = [{"package_folder": "Anduril_SE", "status": "GHOSTED", "req_number": "REQ-1"}]
    assert check_conflicts(rows, "Anduril_SE", "REQ-1") == "inactive_reactivation"


def test_check_conflicts_same_req_different_employer_no_conflict():
    # Same req# but different package_folder = different employer — allow creation
    from scripts.init_job_package import check_conflicts
    rows = [{"package_folder": "Anduril_SE", "status": "PURSUE", "req_number": "REQ-1"}]
    assert check_conflicts(rows, "Boeing_SE", "REQ-1") is None


def test_check_conflicts_no_conflict():
    from scripts.init_job_package import check_conflicts
    rows = [{"package_folder": "Anduril_SE", "status": "PURSUE", "req_number": "REQ-1"}]
    assert check_conflicts(rows, "Boeing_SE", "REQ-999") is None
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/utils/test_init_job_package.py -v -k "csv or conflict"
```

Expected: AttributeError — `load_csv_rows` and `check_conflicts` not defined.

- [ ] **Step 3: Add load_csv_rows and check_conflicts to the script**

Add after `validate_req`:

```python
def load_csv_rows(csv_path: str) -> list:
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def check_conflicts(rows: list, role: str, req: str) -> str | None:
    for row in rows:
        if row.get("req_number", "").strip() == req.strip():
            status = row.get("status", "").strip().upper()
            if status not in ACTIVE_STATUSES:
                return "inactive_reactivation"
            if row.get("package_folder", "").strip() == role.strip():
                return "true_duplicate"
            # same req#, different package_folder = different employer, no conflict
    return None
```

- [ ] **Step 4: Run all tests**

```
pytest tests/utils/test_init_job_package.py -v
```

Expected: all 14 PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/init_job_package.py tests/utils/test_init_job_package.py
git commit -m "feat: add CSV loading and conflict detection to init_job_package"
```

---

### Task 3: Side-effect functions

**Files:**
- Modify: `scripts/init_job_package.py`
- Modify: `tests/utils/test_init_job_package.py`

- [ ] **Step 1: Add failing tests for side-effect functions**

```python
# Append to tests/utils/test_init_job_package.py

import os
from unittest.mock import patch, MagicMock


def test_create_job_folder_creates_directory(tmp_path):
    from scripts.init_job_package import create_job_folder
    path = create_job_folder(str(tmp_path), "Anduril_SE")
    assert os.path.isdir(path)
    assert path.endswith("Anduril_SE")


def test_create_job_description_creates_empty_file(tmp_path):
    from scripts.init_job_package import create_job_description
    folder = tmp_path / "Anduril_SE"
    folder.mkdir()
    jd_path = create_job_description(str(folder))
    assert os.path.isfile(jd_path)
    assert open(jd_path).read() == ""


def test_append_csv_row_adds_row(tmp_path):
    from scripts.init_job_package import append_csv_row
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "package_folder,status,req_number,date_found,company,title,location,salary_range,url\n"
    )
    append_csv_row(str(csv_file), "Anduril_SE", "REQ-1")
    rows = list(csv.DictReader(open(str(csv_file))))
    assert len(rows) == 1
    assert rows[0]["package_folder"] == "Anduril_SE"
    assert rows[0]["req_number"] == "REQ-1"
    assert rows[0]["status"] == ""


def test_append_csv_row_sets_date_found(tmp_path):
    from scripts.init_job_package import append_csv_row
    from datetime import date
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "package_folder,status,req_number,date_found,company,title,location,salary_range,url\n"
    )
    append_csv_row(str(csv_file), "Anduril_SE", "REQ-1")
    rows = list(csv.DictReader(open(str(csv_file))))
    assert rows[0]["date_found"] == str(date.today())


def test_open_file_in_editor_calls_code(tmp_path):
    from scripts.init_job_package import open_file_in_editor
    dummy_file = str(tmp_path / "job_description.txt")
    open(dummy_file, "w").close()
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        open_file_in_editor(dummy_file)
    call_args = mock_run.call_args[0][0]
    assert call_args[0] == "code"
    assert dummy_file in call_args


def test_open_file_in_editor_falls_back_when_code_not_found(tmp_path):
    from scripts.init_job_package import open_file_in_editor
    dummy_file = str(tmp_path / "job_description.txt")
    open(dummy_file, "w").close()
    with patch("subprocess.run", side_effect=FileNotFoundError):
        with patch("sys.platform", "win32"):
            with patch("os.startfile", create=True) as mock_startfile:
                open_file_in_editor(dummy_file)
    mock_startfile.assert_called_once_with(dummy_file)


def test_open_file_in_editor_non_fatal_when_both_fail(tmp_path, capsys):
    from scripts.init_job_package import open_file_in_editor
    dummy_file = str(tmp_path / "job_description.txt")
    open(dummy_file, "w").close()
    with patch("subprocess.run", side_effect=FileNotFoundError):
        with patch("sys.platform", "win32"):
            with patch("os.startfile", create=True, side_effect=Exception("fail")):
                open_file_in_editor(dummy_file)  # must not raise
    captured = capsys.readouterr()
    assert "Warning" in captured.out
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/utils/test_init_job_package.py -v -k "create or append or open"
```

Expected: AttributeError — functions not defined.

- [ ] **Step 3: Implement side-effect functions**

Add after `check_conflicts`:

```python
def create_job_folder(packages_dir: str, role: str) -> str:
    folder_path = os.path.join(packages_dir, role)
    os.makedirs(folder_path, exist_ok=False)
    return folder_path


def create_job_description(folder_path: str) -> str:
    jd_path = os.path.join(folder_path, "job_description.txt")
    open(jd_path, "w").close()
    return jd_path


def append_csv_row(csv_path: str, role: str, req: str) -> None:
    with open(csv_path, newline="", encoding="utf-8") as f:
        fieldnames = csv.DictReader(f).fieldnames or []
    row = {field: "" for field in fieldnames}
    row["package_folder"] = role
    row["req_number"] = req
    row["date_found"] = str(date.today())
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerow(row)


def open_file_in_editor(file_path: str) -> None:
    try:
        result = subprocess.run(["code", file_path])
        if result.returncode == 0:
            return
    except FileNotFoundError:
        pass
    try:
        if sys.platform == "win32":
            os.startfile(file_path)
        elif sys.platform == "darwin":
            subprocess.run(["open", file_path])
        else:
            subprocess.run(["xdg-open", file_path])
        return
    except Exception:
        pass
    print(f"Warning: could not open {file_path} automatically. Open it manually.")
```

- [ ] **Step 4: Run all tests**

```
pytest tests/utils/test_init_job_package.py -v
```

Expected: all 21 PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/init_job_package.py tests/utils/test_init_job_package.py
git commit -m "feat: add side-effect functions to init_job_package"
```

---

### Task 4: main() — happy path and all conflict branches

**Files:**
- Modify: `scripts/init_job_package.py`
- Modify: `tests/utils/test_init_job_package.py`

- [ ] **Step 1: Add failing tests for main()**

```python
# Append to tests/utils/test_init_job_package.py

from unittest.mock import call


def test_main_happy_path_calls_all_side_effects(tmp_path, capsys):
    from scripts.init_job_package import main
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
    )

    assert exit_code == 0
    mock_folder_creator.assert_called_once_with(str(tmp_path), "Anduril_SE")
    mock_file_creator.assert_called_once()
    mock_csv_appender.assert_called_once()
    mock_file_opener.assert_called_once()
    captured = capsys.readouterr()
    assert "job_description.txt" in captured.out


def test_main_true_duplicate_exits_without_side_effects(tmp_path, capsys):
    from scripts.init_job_package import main
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "package_folder,status,req_number,date_found\nAnduril_SE,PURSUE,REQ-1,2026-01-01\n"
    )
    mock_folder_creator = MagicMock()
    mock_csv_appender = MagicMock()

    exit_code = main(
        role="Anduril_SE",
        req="REQ-1",
        packages_dir=str(tmp_path),
        jobs_csv=str(csv_file),
        folder_creator=mock_folder_creator,
        file_creator=MagicMock(),
        csv_appender=mock_csv_appender,
        file_opener=MagicMock(),
        folder_exists=lambda p: False,
    )

    assert exit_code == 1
    mock_folder_creator.assert_not_called()
    mock_csv_appender.assert_not_called()
    captured = capsys.readouterr()
    assert "REQ-1" in captured.out


def test_main_inactive_reactivation_exits_with_instructions(tmp_path, capsys):
    from scripts.init_job_package import main
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "package_folder,status,req_number,date_found\nAnduril_SE,SKIP,REQ-1,2026-01-01\n"
    )
    mock_folder_creator = MagicMock()

    exit_code = main(
        role="Anduril_SE",
        req="REQ-1",
        packages_dir=str(tmp_path),
        jobs_csv=str(csv_file),
        folder_creator=mock_folder_creator,
        file_creator=MagicMock(),
        csv_appender=MagicMock(),
        file_opener=MagicMock(),
        folder_exists=lambda p: False,
    )

    assert exit_code == 1
    mock_folder_creator.assert_not_called()
    captured = capsys.readouterr()
    assert "reactivat" in captured.out.lower() or "inactive" in captured.out.lower()


def test_main_folder_collision_prompts_for_suffix_and_creates_with_new_name(tmp_path, capsys):
    from scripts.init_job_package import main
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "package_folder,status,req_number,date_found,company,title,location,salary_range,url\n"
    )
    # folder_exists returns True for "Anduril_SE", False for "Anduril_SE_2"
    def folder_exists(path):
        return os.path.basename(path) == "Anduril_SE"

    mock_folder_creator = MagicMock(return_value=str(tmp_path / "Anduril_SE_2"))
    mock_file_creator = MagicMock(
        return_value=str(tmp_path / "Anduril_SE_2" / "job_description.txt")
    )

    exit_code = main(
        role="Anduril_SE",
        req="REQ-99",
        packages_dir=str(tmp_path),
        jobs_csv=str(csv_file),
        folder_creator=mock_folder_creator,
        file_creator=mock_file_creator,
        csv_appender=MagicMock(),
        file_opener=MagicMock(),
        folder_exists=folder_exists,
        input_fn=lambda _: "_2",
    )

    assert exit_code == 0
    mock_folder_creator.assert_called_once_with(str(tmp_path), "Anduril_SE_2")
```

- [ ] **Step 2: Run tests to confirm they fail**

```
pytest tests/utils/test_init_job_package.py -v -k "main"
```

Expected: AttributeError — `main` not defined.

- [ ] **Step 3: Replace the `if __name__` block and add main()**

Replace the `if __name__ == "__main__": pass` block with:

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
    rows = load_csv_rows(jobs_csv)
    conflict = check_conflicts(rows, role, req)

    if conflict == "true_duplicate":
        print(
            f"Error: req# {req!r} already exists in jobs.csv with an active status. "
            "No changes made."
        )
        return 1

    if conflict == "inactive_reactivation":
        print(
            f"Error: req# {req!r} exists in jobs.csv with an inactive status.\n"
            "This looks like a reactivation, not a new role.\n"
            f"To reactivate: manually move the folder from inactive/{role}/ back to "
            f"{packages_dir}/{role}/ and update the status in jobs.csv."
        )
        return 1

    final_role = role
    while folder_exists(os.path.join(packages_dir, final_role)):
        print(f"Warning: folder '{final_role}' already exists in {packages_dir}/.")
        suffix = input_fn("Enter a disambiguating suffix (e.g., '_2'): ").strip()
        if not suffix:
            print("Suffix cannot be empty. Try again.")
            continue
        final_role = role + suffix

    folder_path = folder_creator(packages_dir, final_role)
    jd_path = file_creator(folder_path)
    csv_appender(jobs_csv, final_role, req)

    print(f"\nCreated: {jd_path}")
    print("Next steps:")
    print("  1. Paste the job description text into the file above.")
    print(f"  2. Confirm the role name in the file header matches: {final_role}")

    file_opener(jd_path)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize a new job package.")
    parser.add_argument("--role", required=True, help="Role folder name (underscores, no special chars)")
    parser.add_argument("--req", required=True, help="Requisition number")
    args = parser.parse_args()

    try:
        validate_role(args.role)
        validate_req(args.req)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    sys.exit(main(args.role, args.req))
```

- [ ] **Step 4: Run all tests**

```
pytest tests/utils/test_init_job_package.py -v
```

Expected: all 25 PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/init_job_package.py tests/utils/test_init_job_package.py
git commit -m "feat: implement main() for init_job_package with all conflict branches"
```

---

### Task 5: Update SCRIPT_INDEX.md

**Files:**
- Modify: `context/SCRIPT_INDEX.md`

- [ ] **Step 1: Add a new "Initialization" section before the Pipeline scripts table**

In [context/SCRIPT_INDEX.md](context/SCRIPT_INDEX.md), add a new section immediately before `## Pipeline scripts`:

```markdown
## Initialization

| Script | Purpose | Key flags |
|---|---|---|
| `init_job_package.py` | Create a new job package folder, empty `job_description.txt`, and `jobs.csv` row; opens file in editor | `--role` `--req` |
```

- [ ] **Step 2: Run syntax check on the script**

```
python -m py_compile scripts/init_job_package.py && echo "OK"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add context/SCRIPT_INDEX.md
git commit -m "docs: add init_job_package to SCRIPT_INDEX"
```

---

### Task 6: Resolve open review annotation in feature doc

**Files:**
- Modify: `docs/features/job_package_initializer/feature_job_package_init.md`

- [ ] **Step 1: Replace the REVIEW annotation**

Find:
```
> ⚠ REVIEW: AC-1 assumes default status for a new CSV row is `Applied` — confirm the canonical new-entry status value from `jobs.csv` before build starts.
```

Replace with:
```
> ✅ RESOLVED: Canonical new-entry status is blank (empty string). Confirmed from `phase2_job_ranking.py` status workflow: "blank = new, not yet reviewed". The script sets `status` to `""` on all new rows.
```

- [ ] **Step 2: Commit**

```bash
git add docs/features/job_package_initializer/feature_job_package_init.md
git commit -m "docs: resolve open review item in job package initializer spec"
```

---

## Self-Review

**Spec coverage check:**
- AC-1 (happy path — folder, file, CSV row, confirmation, file open): Task 4 happy path test + Task 3 side-effect functions ✓
- AC-2 (true duplicate — exit no writes): Task 2 conflict detection + Task 4 true_duplicate branch ✓
- AC-3 (folder collision — prompt suffix, loop until unique): Task 4 folder_collision test with input_fn mock ✓
- AC-4 (inactive reactivation — exit with instructions): Task 2 conflict detection + Task 4 inactive_reactivation branch ✓
- AC-5 (next-step prompt — print path + instructions): Task 4 main() implementation ✓
- AC-6 (file open — VS Code with OS fallback, non-fatal failure): Task 3 open_file_in_editor tests ✓
- AC-7 (input validation — role chars, non-empty req): Task 1 validators ✓
- AC-8 (testability — injectable functions, `if __name__` guard): All tasks ✓

**Placeholder scan:** No TBD, TODO, or placeholder text. All code blocks are complete and runnable.

**Type consistency:** `check_conflicts` returns `"true_duplicate"` / `"inactive_reactivation"` / `None` — the same string literals are used in both Task 2 (implementation) and Task 4 (main branches). `main()` parameter names match across definition and test call sites. `ACTIVE_STATUSES` is the single source of truth for active-status classification; `check_conflicts` and its tests both reference it.
