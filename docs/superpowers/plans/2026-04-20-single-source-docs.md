# Single-Source Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fragment-based document assembly system so that shared sections across README.md and context/PROJECT_CONTEXT.md have one canonical source and stay synchronized.

**Architecture:** Canonical content lives in individual fragment files under `docs/fragments/`. Document templates in `docs/templates/` reference fragments via `{{include: name}}` markers. A stdlib Python build script resolves markers and writes assembled outputs to their existing paths. A pre-commit hook warns when assembled files are staged without corresponding fragment/template changes.

**Tech Stack:** Python stdlib only (argparse, pathlib, re). Shell script for pre-commit hook. No new pip dependencies.

---

## File Map

| Action | Path | Purpose |
|--------|------|---------|
| Create | `docs/fragments/audit_report.md` | AC-1 artifact — audit findings |
| Create | `docs/fragments/current_phase_status.md` | Canonical phase table |
| Create | `docs/fragments/project_split.md` | Canonical dev vs implementation description |
| Create | `docs/fragments/project_structure.md` | Canonical directory tree |
| Create | `docs/fragments/key_commands.md` | Canonical quick reference commands |
| Create | `docs/templates/README.md` | README template with 3 include markers |
| Create | `docs/templates/PROJECT_CONTEXT.md` | PROJECT_CONTEXT template with 4 include markers |
| Create | `scripts/utils/build_docs.py` | Assembler script |
| Create | `tests/utils/test_build_docs.py` | Unit tests for build_docs core functions |
| Modify | `context/SCRIPT_INDEX.md` | Add build_docs.py entry |
| Create | `.git/hooks/pre-commit` | Reminder hook (not tracked by git) |
| Modify | `README.md` | Assembled output (overwritten by build script) |
| Modify | `context/PROJECT_CONTEXT.md` | Assembled output (overwritten by build script) |

---

## Task 1: Write the Audit Report

**Files:**
- Create: `docs/fragments/audit_report.md`

- [ ] **Step 1: Create the fragments directory and write the audit report**

Create `docs/fragments/audit_report.md` with this exact content:

```markdown
# Document Audit Report
Generated: 2026-04-20
Audited by: Claude Code (brainstorming session)

Documents audited: README.md, context/PROJECT_CONTEXT.md, context/DECISIONS_LOG.md,
context/SCRIPT_INDEX.md, context/DATA_FLOW.md, context/STAGE_FILES.md,
context/SCHEMA_REFERENCE.md, context/PARKING_LOT.md, CLAUDE.md

---

## Exact Duplicates

| Fragment | Section | Present in | Canonical source | Drift notes |
|---|---|---|---|---|
| `current_phase_status.md` | Phase table | README.md, PROJECT_CONTEXT.md | README.md | PROJECT_CONTEXT has "Competet" typo in Phase 4 |

## Near-Duplicates (same concept, different wording)

| Fragment | Section | Present in | Canonical source | Drift notes |
|---|---|---|---|---|
| `project_split.md` | Dev vs Implementation | README.md, PROJECT_CONTEXT.md, DECISIONS_LOG.md | README.md | README has full detail; others are shortened |
| `project_structure.md` | Directory tree | README.md (full), PROJECT_CONTEXT.md (abbreviated) | README.md | PROJECT_CONTEXT abbreviated version replaced by full |
| `key_commands.md` | Quick reference commands | README.md (embedded in Setup), PROJECT_CONTEXT.md (standalone) | PROJECT_CONTEXT.md | Used in PROJECT_CONTEXT only — README keeps run scripts verbatim |

## In-Scope Documents

- README.md — contains 3 of 4 shared sections
- context/PROJECT_CONTEXT.md — contains all 4 shared sections; highest drift risk

## Out-of-Scope Documents (hand-maintained)

- CLAUDE.md — Claude Code config; cannot be a generated artifact
- context/DECISIONS_LOG.md — specialized technical reference; sections serve distinct purposes
- context/SCRIPT_INDEX.md, DATA_FLOW.md, STAGE_FILES.md, SCHEMA_REFERENCE.md — already single-source
- context/PARKING_LOT.md — working list; all content unique

## key_commands Decision

PROJECT_CONTEXT version is better organized (grouped by phase, includes test commands).
README run scripts are embedded in a numbered setup walkthrough — different purpose and audience.
Using PROJECT_CONTEXT version in README would duplicate test commands (already in Setup step 6).
Decision: key_commands fragment used by PROJECT_CONTEXT only. README template keeps run scripts verbatim.
```

- [ ] **Step 2: Commit**

```bash
git add docs/fragments/audit_report.md
git commit -m "docs: add fragment audit report (AC-1)"
```

---

## Task 2: Write the Four Fragment Files

**Files:**
- Create: `docs/fragments/current_phase_status.md`
- Create: `docs/fragments/project_split.md`
- Create: `docs/fragments/project_structure.md`
- Create: `docs/fragments/key_commands.md`

- [ ] **Step 1: Write `docs/fragments/current_phase_status.md`**

Content is the phase table from README.md. Section heading stays in the template — not in the fragment.

```markdown
<!-- fragment: current_phase_status -->
| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Pipeline report script and tracker schema | ✅ Complete |
| 2 | Job ranking and semantic fit analysis | ✅ Complete |
| 3 | Experience knowledge base — structured JSON library with shared parsing module | ✅ Complete |
| 4 | Automated resume + cover letter generation — tailored .docx per application | ✅ Complete |
| 5 | Interview preparation — stage-aware prep packages (recruiter / hiring manager / team panel) | ✅ Complete |
| 6 | Networking and outreach support — LinkedIn search guidance and message templates | ⏳ Planned |
| 7 | Search agent — automated role discovery | ⏳ Planned |
```

- [ ] **Step 2: Write `docs/fragments/project_split.md`**

Content is the body of the "Development vs Implementation" section from README.md.
Source: README.md lines 35–45 (the two bold-intro paragraphs, minus the `##` heading).

```markdown
<!-- fragment: project_split -->
This project is split into two distinct workflows:

**Development** — building and improving the pipeline tools.
Performed using Claude Code in VS Code, working directly against local files.
Reference: `context/DECISIONS_LOG.md` for coding conventions and architecture.

**Implementation** — applying the tools to an active job search.
Performed using Claude web chat for resume tailoring, interview prep,
story workshopping, and pipeline management.
Reference: `context/PIPELINE_STATUS.md` and `context/CANDIDATE_BACKGROUND.md`.
```

- [ ] **Step 3: Write `docs/fragments/project_structure.md`**

Content is the full annotated directory tree from README.md.
Source: README.md — the entire body under `## Project Structure` (the ` ``` ` fenced block and any prose before it, minus the `##` heading). The opening ` ``` ` and closing ` ``` ` fence are part of the fragment.

Open README.md and copy everything between (and including) the ` ```  ` that opens the tree and the ` ``` ` that closes it, then prepend the fragment comment:

```markdown
<!-- fragment: project_structure -->
```

Then paste the full fenced directory tree block from README.md verbatim.

Verify the fragment starts with `<!-- fragment: project_structure -->` and ends with the closing ` ``` ` of the directory tree.

- [ ] **Step 4: Write `docs/fragments/key_commands.md`**

Content is the body of "Quick Reference — Key Commands" from `context/PROJECT_CONTEXT.md`.
Source: PROJECT_CONTEXT.md lines 106–134 (everything after the `## Quick Reference — Key Commands` heading, minus the heading itself).

The file must start with the fragment comment on line 1, followed by the content blocks exactly
as they appear in PROJECT_CONTEXT.md (triple-backtick fenced blocks with the command groups).
Open PROJECT_CONTEXT.md, copy everything from line 106 to the end of file, paste into
`docs/fragments/key_commands.md`, then prepend `<!-- fragment: key_commands -->` as line 1.

The resulting file structure should be:
- Line 1: `<!-- fragment: key_commands -->`
- Lines 2+: the triple-backtick fenced block(s) from PROJECT_CONTEXT.md verbatim, containing:
  - `# Tests`, `pytest` commands
  - `# Pipeline`, `# Resume generation`, `# Cover letter`, `# Interview prep`, `# Library maintenance` groups
  - All `python scripts/...` commands

- [ ] **Step 5: Verify fragment comment lines**

Each fragment must start with `<!-- fragment: [name] -->` as its first line.
Run a quick check:

```bash
head -1 docs/fragments/current_phase_status.md
head -1 docs/fragments/project_split.md
head -1 docs/fragments/project_structure.md
head -1 docs/fragments/key_commands.md
```

Expected output:
```
<!-- fragment: current_phase_status -->
<!-- fragment: project_split -->
<!-- fragment: project_structure -->
<!-- fragment: key_commands -->
```

- [ ] **Step 6: Commit**

```bash
git add docs/fragments/current_phase_status.md docs/fragments/project_split.md docs/fragments/project_structure.md docs/fragments/key_commands.md
git commit -m "docs: add canonical fragment files (AC-2)"
```

---

## Task 3: Write the Template Files

**Files:**
- Create: `docs/templates/README.md`
- Create: `docs/templates/PROJECT_CONTEXT.md`

**Rule:** Section headings (`## Heading`) stay in the template. Fragment content replaces only the section body. The assembled header comment is NOT in templates — the build script prepends it.

- [ ] **Step 1: Create `docs/templates/README.md`**

Copy the current `README.md` to `docs/templates/README.md`, then make three replacements:

**Replacement 1** — under `## Project Phases`, replace the entire table body with the marker:

Before (the table, approximately lines 21–29 of README.md):
```
| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Pipeline report script and tracker schema | ✅ Complete |
...
| 7 | Search agent — automated role discovery | ⏳ Planned |
```

After:
```
{{include: current_phase_status}}
```

**Replacement 2** — under `## Development vs Implementation`, replace the two bold-intro paragraphs with the marker:

Before (the two `**Development**` / `**Implementation**` paragraphs):
```
This project is split into two distinct workflows:

**Development** — building and improving the pipeline tools.
...
Reference: `context/PIPELINE_STATUS.md` and `context/CANDIDATE_BACKGROUND.md`.
```

After:
```
{{include: project_split}}
```

**Replacement 3** — under `## Project Structure`, replace the fenced directory tree block with the marker:

Before (the ` ``` ` ... ` ``` ` block containing the directory tree):
```
```
Job_search_agent/
├── .github/workflows/test.yml
...
└── README.md
```
```

After:
```
{{include: project_structure}}
```

Verify: `docs/templates/README.md` contains exactly three `{{include:` markers and no assembled header comment.

```bash
grep -c "{{include:" docs/templates/README.md
```

Expected: `3`

- [ ] **Step 2: Create `docs/templates/PROJECT_CONTEXT.md`**

Copy the current `context/PROJECT_CONTEXT.md` to `docs/templates/PROJECT_CONTEXT.md`, then make four replacements:

**Replacement 1** — under `## Project Split — Development vs Implementation`, replace the body (two bold-intro paragraphs):

Before:
```
### Development (Claude Code in VS Code)
Building and improving the pipeline tools. Script editing, debugging, refactoring, architecture decisions, library maintenance, new phase development.
Reference: context/DECISIONS_LOG.md for coding conventions and architecture decisions.

### Implementation (Claude web chat)
Applying the tools to the active job search. Resume tailoring, interview prep, story workshopping, pipeline management, recruiter communications.
Reference: context/PIPELINE_STATUS.md and context/CANDIDATE_BACKGROUND.md.
```

After:
```
{{include: project_split}}
```

**Replacement 2** — under `## Current Phase Status`, replace the entire phase table:

Before (the full phase table):
```
| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Pipeline report + tracker schema | Complete |
...
| 7 | Search agent — automated role discovery | Planned |
```

After:
```
{{include: current_phase_status}}
```

**Replacement 3** — under `## Project Structure (top level)`, replace the fenced directory tree:

Before (the ` ``` ` ... ` ``` ` block):
```
```
Job_search_agent/
├── .github/workflows/test.yml — CI: mock suite on every push
...
└── README.md
```
```

After:
```
{{include: project_structure}}
```

**Replacement 4** — under `## Quick Reference — Key Commands`, replace all content (the ` ``` ` blocks):

Before (the full commands block):
```
```
# Tests (run after any script change)
pytest tests/ -m "not live" -v
...
python scripts/phase3_compile_library.py
```
```

After:
```
{{include: key_commands}}
```

Verify: `docs/templates/PROJECT_CONTEXT.md` contains exactly four `{{include:` markers and no assembled header comment.

```bash
grep -c "{{include:" docs/templates/PROJECT_CONTEXT.md
```

Expected: `4`

- [ ] **Step 3: Commit**

```bash
git add docs/templates/README.md docs/templates/PROJECT_CONTEXT.md
git commit -m "docs: add document templates with include markers (AC-3)"
```

---

## Task 4: Write Tests for build_docs.py

**Files:**
- Create: `tests/utils/test_build_docs.py`

- [ ] **Step 1: Write the test file**

Create `tests/utils/test_build_docs.py`:

```python
import pytest
from pathlib import Path

from scripts.utils.build_docs import (
    ASSEMBLED_HEADER,
    find_markers,
    assemble_document,
)


class TestFindMarkers:
    def test_single_marker(self):
        content = "Before\n{{include: my_fragment}}\nAfter"
        assert find_markers(content) == ["my_fragment"]

    def test_multiple_markers(self):
        content = "{{include: frag_a}}\n\n{{include: frag_b}}"
        assert find_markers(content) == ["frag_a", "frag_b"]

    def test_no_markers(self):
        content = "No markers here at all"
        assert find_markers(content) == []

    def test_marker_with_underscore_name(self):
        content = "{{include: current_phase_status}}"
        assert find_markers(content) == ["current_phase_status"]


class TestAssembleDocument:
    def test_replaces_single_marker(self, tmp_path):
        frags = tmp_path / "fragments"
        frags.mkdir()
        (frags / "my_frag.md").write_text("Fragment body")

        result = assemble_document("Before\n{{include: my_frag}}\nAfter", frags)

        assert "Fragment body" in result
        assert "{{include: my_frag}}" not in result

    def test_replaces_multiple_markers(self, tmp_path):
        frags = tmp_path / "fragments"
        frags.mkdir()
        (frags / "a.md").write_text("AAA")
        (frags / "b.md").write_text("BBB")

        result = assemble_document("{{include: a}}\n{{include: b}}", frags)

        assert "AAA" in result
        assert "BBB" in result

    def test_prepends_assembled_header(self, tmp_path):
        frags = tmp_path / "fragments"
        frags.mkdir()

        result = assemble_document("No markers", frags)

        assert result.startswith(ASSEMBLED_HEADER)

    def test_raises_on_missing_fragment(self, tmp_path):
        frags = tmp_path / "fragments"
        frags.mkdir()

        with pytest.raises(FileNotFoundError, match="missing_frag"):
            assemble_document("{{include: missing_frag}}", frags, template_name="test.md")

    def test_error_message_includes_template_name(self, tmp_path):
        frags = tmp_path / "fragments"
        frags.mkdir()

        with pytest.raises(FileNotFoundError, match="mytemplate.md"):
            assemble_document("{{include: gone}}", frags, template_name="mytemplate.md")

    def test_fragments_not_recursively_processed(self, tmp_path):
        frags = tmp_path / "fragments"
        frags.mkdir()
        (frags / "outer.md").write_text("{{include: inner}}")

        result = assemble_document("{{include: outer}}", frags)

        assert "{{include: inner}}" in result

    def test_assembled_header_not_duplicated_on_repeated_call(self, tmp_path):
        frags = tmp_path / "fragments"
        frags.mkdir()
        (frags / "frag.md").write_text("content")

        template = "{{include: frag}}"
        result = assemble_document(template, frags)

        assert result.count(ASSEMBLED_HEADER) == 1

    def test_no_markers_content_preserved(self, tmp_path):
        frags = tmp_path / "fragments"
        frags.mkdir()
        body = "# Title\n\nSome text\n\nMore text"

        result = assemble_document(body, frags)

        assert body in result
```

- [ ] **Step 2: Run tests — confirm they fail with ImportError (module not yet written)**

```bash
pytest tests/utils/test_build_docs.py -v
```

Expected: All tests fail with `ModuleNotFoundError: No module named 'scripts.utils.build_docs'`

---

## Task 5: Write build_docs.py

**Files:**
- Create: `scripts/utils/build_docs.py`

- [ ] **Step 1: Write the script**

Create `scripts/utils/build_docs.py`:

```python
"""Assemble project documents from templates and fragments.

Usage:
    python scripts/utils/build_docs.py           # assemble all documents
    python scripts/utils/build_docs.py --all     # same as above
    python scripts/utils/build_docs.py --doc README.md   # single document
"""

import argparse
import re
import sys
from pathlib import Path

FRAGMENTS_DIR = Path("docs/fragments")
TEMPLATES_DIR = Path("docs/templates")

ASSEMBLED_HEADER = (
    "<!-- assembled by build_docs.py"
    " -- edit docs/templates/ and docs/fragments/ not this file -->"
)

TARGET_PATHS: dict[str, Path] = {
    "README.md": Path("README.md"),
    "PROJECT_CONTEXT.md": Path("context/PROJECT_CONTEXT.md"),
}

_MARKER_RE = re.compile(r"\{\{include:\s*(\w+)\s*\}\}")


def find_markers(content: str) -> list[str]:
    return _MARKER_RE.findall(content)


def assemble_document(
    template_content: str,
    fragments_dir: Path,
    template_name: str = "unknown",
) -> str:
    missing: list[str] = []

    def _replace(match: re.Match) -> str:
        name = match.group(1)
        fragment_path = fragments_dir / f"{name}.md"
        if not fragment_path.exists():
            missing.append(
                f"ERROR: Fragment '{name}.md' not found"
                f" (referenced in template '{template_name}')"
            )
            return match.group(0)
        return fragment_path.read_text(encoding="utf-8")

    assembled = _MARKER_RE.sub(_replace, template_content)

    if missing:
        raise FileNotFoundError("\n".join(missing))

    return ASSEMBLED_HEADER + "\n" + assembled


def _run(templates: list[str]) -> int:
    assembled_count = 0
    fragment_count = 0
    errors = 0

    for template_name in templates:
        template_path = TEMPLATES_DIR / template_name
        target_path = TARGET_PATHS[template_name]

        try:
            content = template_path.read_text(encoding="utf-8")
            n_fragments = len(find_markers(content))
            output = assemble_document(content, FRAGMENTS_DIR, template_name)
            target_path.write_text(output, encoding="utf-8")
            print(f"  assembled: {template_name} -> {target_path} ({n_fragments} fragment(s))")
            assembled_count += 1
            fragment_count += n_fragments
        except FileNotFoundError as exc:
            print(str(exc))
            errors += 1

    print(
        f"\nDone: {assembled_count} document(s) assembled,"
        f" {fragment_count} fragment(s) resolved",
        end="",
    )
    if errors:
        print(f", {errors} error(s)")
    else:
        print()

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Assemble project documents from templates and fragments."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Assemble all documents (default)")
    group.add_argument(
        "--doc",
        metavar="FILENAME",
        help="Assemble one document by template filename (e.g. README.md)",
    )
    args = parser.parse_args()

    if not TEMPLATES_DIR.exists():
        print(f"ERROR: Templates directory not found: {TEMPLATES_DIR}")
        sys.exit(1)

    if args.doc:
        if args.doc not in TARGET_PATHS:
            known = ", ".join(TARGET_PATHS)
            print(f"ERROR: Unknown document '{args.doc}'. Known: {known}")
            sys.exit(1)
        templates = [args.doc]
    else:
        templates = list(TARGET_PATHS.keys())

    errors = _run(templates)
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the tests — all should pass**

```bash
pytest tests/utils/test_build_docs.py -v
```

Expected output (all green):
```
tests/utils/test_build_docs.py::TestFindMarkers::test_single_marker PASSED
tests/utils/test_build_docs.py::TestFindMarkers::test_multiple_markers PASSED
tests/utils/test_build_docs.py::TestFindMarkers::test_no_markers PASSED
tests/utils/test_build_docs.py::TestFindMarkers::test_marker_with_underscore_name PASSED
tests/utils/test_build_docs.py::TestAssembleDocument::test_replaces_single_marker PASSED
tests/utils/test_build_docs.py::TestAssembleDocument::test_replaces_multiple_markers PASSED
tests/utils/test_build_docs.py::TestAssembleDocument::test_prepends_assembled_header PASSED
tests/utils/test_build_docs.py::TestAssembleDocument::test_raises_on_missing_fragment PASSED
tests/utils/test_build_docs.py::TestAssembleDocument::test_error_message_includes_template_name PASSED
tests/utils/test_build_docs.py::TestAssembleDocument::test_fragments_not_recursively_processed PASSED
tests/utils/test_build_docs.py::TestAssembleDocument::test_assembled_header_not_duplicated_on_repeated_call PASSED
tests/utils/test_build_docs.py::TestAssembleDocument::test_no_markers_content_preserved PASSED
```

- [ ] **Step 3: Run the full mock suite — all existing tests must still pass**

```bash
pytest tests/ -m "not live" -v
```

Expected: all pre-existing tests pass (no regressions).

- [ ] **Step 4: Run syntax check**

```bash
python -m py_compile scripts/utils/build_docs.py && echo "OK"
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add scripts/utils/build_docs.py tests/utils/test_build_docs.py
git commit -m "feat: add build_docs.py assembler script and tests (AC-4)"
```

---

## Task 6: Run the Build Script and Verify Assembled Outputs

**Files:**
- Modify: `README.md` (assembled output)
- Modify: `context/PROJECT_CONTEXT.md` (assembled output)

- [ ] **Step 1: Run the build script**

```bash
python scripts/utils/build_docs.py
```

Expected output:
```
  assembled: README.md -> README.md (3 fragment(s))
  assembled: PROJECT_CONTEXT.md -> context/PROJECT_CONTEXT.md (4 fragment(s))

Done: 2 document(s) assembled, 7 fragment(s) resolved
```

If any error about missing fragment: stop and fix the template or fragment file before continuing.

- [ ] **Step 2: Verify the assembled header in each output**

```bash
head -1 README.md
head -1 context/PROJECT_CONTEXT.md
```

Expected (both):
```
<!-- assembled by build_docs.py -- edit docs/templates/ and docs/fragments/ not this file -->
```

- [ ] **Step 3: Verify fragment content appears in README.md**

```bash
grep -c "Pipeline report script" README.md
grep -c "Development vs Implementation\|development vs implementation" README.md
```

Expected: both return `1` (fragment content present, not duplicated).

- [ ] **Step 4: Verify no include markers remain in assembled outputs**

```bash
grep "{{include:" README.md context/PROJECT_CONTEXT.md
```

Expected: no output (all markers resolved).

- [ ] **Step 5: Verify PROJECT_CONTEXT.md no longer has "Competet" typo**

```bash
grep "Competet" context/PROJECT_CONTEXT.md
```

Expected: no output (phase 4 now reads from the canonical README fragment).

- [ ] **Step 6: Run the build a second time — confirm idempotency**

```bash
python scripts/utils/build_docs.py
```

Expected: same output as Step 1, no changes to file content (running twice produces identical files).

- [ ] **Step 7: Test --doc flag**

```bash
python scripts/utils/build_docs.py --doc README.md
```

Expected:
```
  assembled: README.md -> README.md (3 fragment(s))

Done: 1 document(s) assembled, 3 fragment(s) resolved
```

```bash
python scripts/utils/build_docs.py --doc PROJECT_CONTEXT.md
```

Expected:
```
  assembled: PROJECT_CONTEXT.md -> context/PROJECT_CONTEXT.md (4 fragment(s))

Done: 1 document(s) assembled, 4 fragment(s) resolved
```

- [ ] **Step 8: Commit assembled outputs**

```bash
git add README.md context/PROJECT_CONTEXT.md
git commit -m "docs: rebuild assembled outputs from fragments (AC-6)"
```

---

## Task 7: Write the Pre-Commit Hook

**Files:**
- Create: `.git/hooks/pre-commit` (not tracked by git)

- [ ] **Step 1: Write the hook script**

Create `.git/hooks/pre-commit` with this exact content:

```bash
#!/bin/sh
FRAGMENTS=$(git diff --cached --name-only | grep -E '^docs/(fragments|templates)/')
ASSEMBLED=$(git diff --cached --name-only | grep -E '^(README\.md|context/PROJECT_CONTEXT\.md)$')

if [ -n "$ASSEMBLED" ] && [ -z "$FRAGMENTS" ]; then
  echo ""
  echo "WARNING: Assembled document(s) staged without corresponding fragment/template changes."
  echo "Edits to README.md or context/PROJECT_CONTEXT.md will be overwritten on next build."
  echo "Edit docs/templates/ or docs/fragments/ instead, then run:"
  echo "  python scripts/utils/build_docs.py"
  echo ""
fi

if [ -n "$FRAGMENTS" ]; then
  echo ""
  echo "REMINDER: Fragment or template files modified."
  echo "Run: python scripts/utils/build_docs.py"
  echo "to rebuild assembled documents before pushing."
  echo ""
fi

exit 0
```

- [ ] **Step 2: Make the hook executable**

```bash
chmod +x .git/hooks/pre-commit
```

- [ ] **Step 3: Verify the hook fires on a fragment change**

Stage a trivial whitespace change to any fragment (e.g., add a trailing newline to `docs/fragments/audit_report.md`), then run:

```bash
git diff --staged | head -5
.git/hooks/pre-commit
```

Expected output from hook:
```

REMINDER: Fragment or template files modified.
Run: python scripts/utils/build_docs.py
to rebuild assembled documents before pushing.

```

Un-stage the test change after verifying:

```bash
git restore --staged docs/fragments/audit_report.md
git restore docs/fragments/audit_report.md
```

- [ ] **Step 4: Verify the hook fires on a direct assembled-file edit**

Stage a trivial whitespace edit to README.md (without staging any fragments/templates):

```bash
# Temporarily add a space to line 2 of README.md, then stage it
git add README.md
.git/hooks/pre-commit
```

Expected output from hook:
```

WARNING: Assembled document(s) staged without corresponding fragment/template changes.
Edits to README.md or context/PROJECT_CONTEXT.md will be overwritten on next build.
Edit docs/templates/ or docs/fragments/ instead, then run:
  python scripts/utils/build_docs.py

```

Un-stage after verifying:

```bash
git restore --staged README.md
git restore README.md
```

Note: `.git/hooks/pre-commit` is not committed — it lives outside the tracked tree.

---

## Task 8: Update SCRIPT_INDEX and Final Commit

**Files:**
- Modify: `context/SCRIPT_INDEX.md`

- [ ] **Step 1: Read SCRIPT_INDEX.md to find the utilities section**

Open `context/SCRIPT_INDEX.md` and locate the "One-time / utility scripts" table at the bottom.

- [ ] **Step 2: Add build_docs.py entry**

Add this row to the "One-time / utility scripts" table in `context/SCRIPT_INDEX.md`:

```markdown
| `utils/build_docs.py` | Assemble README.md and PROJECT_CONTEXT.md from templates + fragments. Run after editing any fragment or template. `python scripts/utils/build_docs.py` or `--doc [filename]` |
```

- [ ] **Step 3: Run the full mock suite one final time**

```bash
pytest tests/ -m "not live" -v
```

Expected: all tests pass (including the 12 new build_docs tests).

- [ ] **Step 4: Final commit**

```bash
git add context/SCRIPT_INDEX.md
git commit -m "docs: update SCRIPT_INDEX with build_docs.py entry (AC-7)"
```

---

## Post-Build Workflow Note

**Updating a shared section going forward:**

1. Edit the relevant file in `docs/fragments/` (e.g., update the phase table in `docs/fragments/current_phase_status.md`)
2. Run `python scripts/utils/build_docs.py`
3. Stage fragments, templates, AND assembled outputs together:
   ```bash
   git add docs/fragments/current_phase_status.md README.md context/PROJECT_CONTEXT.md
   git commit -m "docs: update phase status"
   ```
   The pre-commit hook will print the rebuild reminder — that's expected when staging fragment changes alongside assembled outputs.

**Never edit README.md or context/PROJECT_CONTEXT.md directly** — the next build overwrites those edits with no warning.
