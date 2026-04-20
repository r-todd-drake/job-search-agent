# Single-Source Documentation — Design Spec
Date: 2026-04-20
Proposal: docs/features/single_source_documents_proposal/single_source_docs_proposal.md

---

## Problem

Several project documents contain overlapping sections — phase status table, project structure
tree, development vs implementation split, and quick reference commands. When one document is
updated, the others fall out of sync. The audit confirmed this has already happened (PROJECT_CONTEXT
has a "Competet" typo in Phase 4 that README does not; key_commands differ in organization between
the two files). There is no mechanism to detect or correct this drift.

---

## Solution

Fragment-based single-source-of-truth pattern. Canonical content lives in one file per section.
Documents are assembled from fragments plus document-specific content via a build script.
Plain string substitution — no templating engine, no new runtime dependencies.

---

## Audit Findings (AC-1)

Audit performed 2026-04-20 across: README.md, context/PROJECT_CONTEXT.md, context/DECISIONS_LOG.md,
context/SCRIPT_INDEX.md, context/DATA_FLOW.md, context/STAGE_FILES.md, context/SCHEMA_REFERENCE.md,
context/PARKING_LOT.md, CLAUDE.md.

### Exact Duplicates

| Fragment | Section | Present in | Canonical source | Notes |
|---|---|---|---|---|
| `current_phase_status.md` | Phase table | README.md, PROJECT_CONTEXT.md | README.md | PROJECT_CONTEXT has "Competet" typo in Phase 4 |

### Near-Duplicates (drift — same concept, different wording)

| Fragment | Section | Present in | Canonical source | Notes |
|---|---|---|---|---|
| `project_split.md` | Dev vs Implementation description | README.md, PROJECT_CONTEXT.md, DECISIONS_LOG.md | README.md | README has full detail; others are shortened summaries |
| `project_structure.md` | Directory tree | README.md (full), PROJECT_CONTEXT.md (abbreviated) | README.md | PROJECT_CONTEXT abbreviated version replaced by full fragment |
| `key_commands.md` | Quick reference commands | README.md (embedded in Setup), PROJECT_CONTEXT.md (standalone section) | PROJECT_CONTEXT.md | Used in PROJECT_CONTEXT only — see decision note below |

**key_commands decision:** PROJECT_CONTEXT.md version is better organized (grouped by phase,
includes test commands). However, README.md's run scripts list is embedded inside a numbered
setup walkthrough and serves a different purpose. Including the PROJECT_CONTEXT version in
README would duplicate test commands (Setup step 6 already lists them) and conflate a
narrative walkthrough with a quick reference. Decision: `key_commands` fragment is used by
PROJECT_CONTEXT.md only. README.md keeps its run scripts section verbatim in its template.
The two lists can evolve independently without creating noise in README.

### In-Scope Documents

| Document | Reason |
|---|---|
| `README.md` | Contains 3 of 4 duplicate sections; is the canonical source for most content |
| `context/PROJECT_CONTEXT.md` | Contains all 4 duplicate sections; highest drift risk |

### Out of Scope (stays hand-maintained)

| Document | Reason |
|---|---|
| `CLAUDE.md` | Claude Code configuration file — cannot be a generated artifact |
| `context/DECISIONS_LOG.md` | Specialized technical reference; sections serve distinct purposes |
| `context/SCRIPT_INDEX.md` | Already single-source for script reference |
| `context/DATA_FLOW.md` | Already single-source for data flow |
| `context/STAGE_FILES.md` | Already single-source for stage file lifecycle |
| `context/SCHEMA_REFERENCE.md` | Already single-source for JSON schemas |
| `context/PARKING_LOT.md` | Working list; all content is unique |

Full audit detail written to: `docs/fragments/audit_report.md` (produced during implementation step 1)

---

## File Layout

```
docs/
├── fragments/
│   ├── audit_report.md             (AC-1 artifact — written first, before any build steps)
│   ├── current_phase_status.md     <!-- fragment: current_phase_status -->
│   ├── project_split.md            <!-- fragment: project_split -->
│   ├── project_structure.md        <!-- fragment: project_structure -->
│   └── key_commands.md             <!-- fragment: key_commands -->
└── templates/
    ├── README.md                   (document template with {{include: ...}} markers)
    └── PROJECT_CONTEXT.md          (document template with {{include: ...}} markers)

scripts/utils/build_docs.py         (assembler script)
.git/hooks/pre-commit               (reminder hook)
```

Assembled outputs write to their existing paths:
- `docs/templates/README.md` → `README.md`
- `docs/templates/PROJECT_CONTEXT.md` → `context/PROJECT_CONTEXT.md`

Note: `docs/templates/` is new — distinct from the existing `templates/` at the project root
(which holds script input templates such as `interview_debrief_template.yaml`).

---

## Fragment Specs

### `docs/fragments/current_phase_status.md`

Content: the phase table from README.md (lines 19–29). Includes emoji ✅ column.
No section heading — heading is in the template.

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

### `docs/fragments/project_split.md`

Content: the Development vs Implementation section from README.md (lines 33–46).
No section heading — heading is in the template.

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

### `docs/fragments/project_structure.md`

Content: the full annotated directory tree from README.md (lines 369–441).
No section heading — heading is in the template.
Opening ` ``` ` and closing ` ``` ` fence are part of the fragment content.

### `docs/fragments/key_commands.md`

Content: the Quick Reference — Key Commands section from PROJECT_CONTEXT.md (lines 105–134).
No section heading — heading is in the template.
Opening ` ``` ` and closing ` ``` ` fence blocks are part of the fragment content.

---

## Template Structure

**Rule:** Section headings (`## Heading`) are always part of the template, never part of the
fragment. Fragments contain only the section body content. This keeps heading text editable
in the template without touching the fragment.

### `docs/templates/README.md`

Sections replaced with include markers:

| Section heading | Marker |
|---|---|
| `## Project Phases` | `{{include: current_phase_status}}` |
| `## Development vs Implementation` | `{{include: project_split}}` |
| `## Project Structure` | `{{include: project_structure}}` |

All other sections preserved verbatim: Project Overview, Daily Workflow, Job Status Values,
Phase 4 Resume Generation, Phase 4 Cover Letter Generation, Phase 5 Interview Prep,
Post-Interview Debrief, Post-Interview Thank-You Letters, Interview Workshop Capture,
Tech Stack, Security & Privacy, Claude Code (Optional), Setup (including the run scripts
list — not replaced by key_commands fragment; see key_commands decision above), Way Ahead,
Skills Demonstrated, Author, License.

Assembled header (first line of assembled output):
```
<!-- assembled by build_docs.py -- edit docs/templates/ and docs/fragments/ not this file -->
```

### `docs/templates/PROJECT_CONTEXT.md`

Sections replaced with include markers:

| Section heading | Marker |
|---|---|
| `## Project Split — Development vs Implementation` | `{{include: project_split}}` |
| `## Current Phase Status` | `{{include: current_phase_status}}` |
| `## Project Structure (top level)` | `{{include: project_structure}}` |
| `## Quick Reference — Key Commands` | `{{include: key_commands}}` |

All other sections preserved verbatim: About This File, What This Project Is,
V&V Framework, Non-Negotiable Rules, Supporting Context Files.

---

## Build Script — `scripts/utils/build_docs.py`

### Target path mapping

Hardcoded dict inside the script:

```python
TARGET_PATHS = {
    "README.md": "README.md",
    "PROJECT_CONTEXT.md": "context/PROJECT_CONTEXT.md",
}
```

### Logic

1. Resolve which templates to process (all, or one via `--doc [filename]`)
2. For each template:
   a. Read template content from `docs/templates/[filename]`
   b. Find all `{{include: name}}` markers (regex scan)
   c. For each marker: read `docs/fragments/[name].md`; if missing, raise with
      message: `ERROR: Fragment '[name].md' not found (referenced in template '[filename]')`
   d. Replace each marker with fragment content (str.replace, one pass per marker)
   e. Prepend assembled header comment
   f. Write to target path (overwrite unconditionally — idempotent)
3. Print summary: documents assembled, fragments resolved, any warnings

### CLI

```bash
python scripts/utils/build_docs.py                      # assemble all (default)
python scripts/utils/build_docs.py --all                # same as default
python scripts/utils/build_docs.py --doc README.md      # single document
python scripts/utils/build_docs.py --doc PROJECT_CONTEXT.md  # single document
```

`--doc` accepts the template filename (basename only, e.g. `PROJECT_CONTEXT.md` not
`context/PROJECT_CONTEXT.md`). The script resolves the target path via `TARGET_PATHS`.

### Error behavior

- Missing fragment: prints error with clear message, skips that template, continues others,
  exits non-zero when done (so callers and pre-commit automation detect failure)
- Missing template directory: error on startup, exits non-zero immediately
- Fragment marker with no matching file: same as missing fragment above — never silently skips
- Clean run (all templates assembled successfully): exits 0

### Recursive processing

Fragments are not recursively processed. Include markers within fragment content are treated
as literal text and passed through to the assembled output unchanged.

### No new dependencies

Uses only Python stdlib: `argparse`, `pathlib`, `re`.

---

## Pre-Commit Hook — `.git/hooks/pre-commit`

Shell script, chmod +x. Non-blocking (exits 0 in all cases).

Two distinct checks:

1. **Fragment/template modified** — reminds user to rebuild before pushing.
2. **Assembled output staged without fragment/template changes** — warns user they may have
   edited an assembled file directly. These edits will be silently overwritten on the next build.

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

Hook installation: documented in README Setup section (in the template, so it appears in the
assembled README). One manual step — copy or symlink the script, then `chmod +x`.

---

## Assembled Output Header

First line of every assembled document:

```
<!-- assembled by build_docs.py -- edit docs/templates/ and docs/fragments/ not this file -->
```

This is valid HTML comment syntax; invisible in rendered Markdown. Does not break GitHub
rendering or any existing tooling.

---

## SCRIPT_INDEX Update

`context/SCRIPT_INDEX.md` — add to "One-time / utility scripts" table:

| Script | Purpose |
|---|---|
| `utils/build_docs.py` | Assemble README.md and PROJECT_CONTEXT.md from templates + fragments. Run after editing any fragment or template. `python scripts/utils/build_docs.py` or `--doc [filename]` |

---

## Implementation Order

1. Write `docs/fragments/audit_report.md` (AC-1)
2. Write 4 fragment files in `docs/fragments/` (AC-2)
3. Write 2 template files in `docs/templates/` (AC-3)
4. Write `scripts/utils/build_docs.py` (AC-4)
5. Run build script — verify assembled outputs match expected content
6. Write `.git/hooks/pre-commit` and chmod +x (AC-5)
7. Update `context/SCRIPT_INDEX.md` (AC-7)
8. Run syntax check on build_docs.py
9. Git commit: `docs/fragments/`, `docs/templates/`, `scripts/utils/build_docs.py`,
   `context/SCRIPT_INDEX.md`
   (`.git/hooks/pre-commit` is not committed — lives outside tracked tree)

---

## Out of Scope (per proposal)

- Automatic commit/push triggering
- Jinja2 or templating engine
- Conditional includes or loops
- Fragment versioning beyond git history
- Automatic drift detection on assembled outputs
- Non-Markdown documents
- candidate_profile.md (generated by phase3_build_candidate_profile.py)
