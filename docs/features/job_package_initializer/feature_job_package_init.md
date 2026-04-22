# Job Package Initializer

## User Story and Acceptance Criteria

### User Story
"As a job seeker managing an active pipeline, I want a CLI script that creates a new job package folder and blank job_description.txt file from a single command so that I eliminate manual folder creation, reduce data entry errors, and land immediately in the right file to paste the job description."

### Acceptance Criteria (AC)

#### AC-1 — Happy Path: New Role Creation
- Script accepts `--role` and `--req` as required named arguments
- Script creates `job_packages/[role]/` directory
- Script creates `job_packages/[role]/job_description.txt` as an empty file
- Script appends a new row to `jobs.csv` with the provided role name, req number, and a default status of `Applied` (or the project's canonical new-entry status — confirm before build)
- Script prints confirmation: created path and next-step instructions (see AC-5)
- Script opens `job_description.txt` for editing (see AC-6)

#### AC-2 — Conflict: True Duplicate (same role name + same req#)
- Script detects that req# already exists in `jobs.csv` with an active status
- Script prints a clear error identifying the existing role and req#
- Script exits without creating any folder or writing any CSV row

#### AC-3 — Conflict: Same Name, Different Req# (distinct roles)
- Script detects that `job_packages/[role]/` already exists but req# does not match any existing entry
- Script warns the user that the folder name is already in use
- Script prompts the user to provide a disambiguating suffix (e.g., `Anduril_EW_SE1`)
- Script re-runs creation logic with the confirmed new name — no folder or CSV write until name is confirmed
- Suffix input is free-form; the script does not enforce a naming convention beyond non-empty

#### AC-4 — Conflict: Inactive Role Reactivation (same req#, inactive status)
- Script detects that req# exists in `jobs.csv` with an inactive status
- Script prints a clear message identifying this as a potential reactivation, not a new role
- Script exits without creating any folder or writing any CSV row
- Script instructs the user to manually move the folder from `inactive/[role]/` back to `job_packages/[role]/` and update the CSV status

#### AC-5 — Next-Step Prompt
- On successful creation, script prints:
  - The full path to the created `job_description.txt`
  - A short instruction: paste the job description text into the file and confirm the role name in the file header matches the folder name

#### AC-6 — File Open Behavior
- Script attempts to open `job_description.txt` using the VS Code CLI (`code`)
- If `code` is not found or fails, script falls back to the OS default text editor (`os.startfile` on Windows, `open` on macOS, `xdg-open` on Linux)
- Script does not control or attempt to control window placement — that is OS/editor-controlled
- File open failure is non-fatal: script prints a warning and exits cleanly if both methods fail

#### AC-7 — Input Validation
- `--role` value is validated against filesystem-safe characters before any folder is created
- `--req` value is validated as non-empty before any CSV write
- Validation errors print a clear message and exit before any side effects

#### AC-8 — Testability
- All side-effectful operations (folder creation, CSV write, file open) are extracted into injectable functions so the happy path and all conflict branches are testable with mocks
- New script follows existing project convention: no module-level execution, entry point guarded by `if __name__ == "__main__"`
- Mock tests cover: happy path, all three conflict cases, validation errors, and file-open fallback

### Out of Scope
- Reactivation automation — moving a folder from `inactive/` to `job_packages/` and updating CSV status remains a manual operation; this script detects the condition and stops cleanly
- Population of `job_description.txt` with any content — file is always created empty
- Creation of any other scaffold files (stage files, prep packages, etc.) — folder contains only `job_description.txt` on init
- Disambiguation of same-name/same-req# roles that differ only by a site URL suffix (e.g., Anduril duplicate listings) — the user resolves this at input time by choosing a unique `--role` value before invoking the script
- Window placement or editor configuration
- Inactive folder creation — all new roles start active; there is no `--inactive` flag

---

## Review Annotations
*This section is populated during the Chat spec review step (README process step 4). Do not fill in manually.*

Open items use `> ⚠ REVIEW:` and must be resolved before build starts.
Resolved items use `> ✅ RESOLVED:` and document what was decided.

> ✅ RESOLVED: Canonical new-entry status is blank (empty string). Confirmed from `phase2_job_ranking.py` status workflow: "blank = new, not yet reviewed". The script sets `status` to `""` on all new rows.
