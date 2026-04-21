# Single-Source Documentation

## User Story and Acceptance Criteria

### User Story
"As a job search system maintainer, I want shared content sections stored as
individual fragment files and assembled into project documents on demand, so
that information duplicated across multiple documents stays synchronized and
can be updated in one place."

### Background
Several project documents (README, PROJECT_CONTEXT, and others identified
during the build audit) contain overlapping sections -- current phase status,
project structure, script inventory, employer list, and similar reference
content. When one document is updated, the others fall out of sync. There is
currently no mechanism to detect or correct this drift. This feature
establishes a fragment-based single-source-of-truth pattern: canonical content
lives in one file, documents are assembled from fragments plus document-specific
content via a build script.

The build process is intentionally lightweight -- plain string substitution,
no templating engine, no new runtime dependencies beyond the Python standard
library.

---

### Acceptance Criteria

#### AC-1: Document and Fragment Audit (CC-performed, build prerequisite)
- CC reads all available project documents and identifies sections that are
  duplicated or near-duplicated across two or more files
- Near-duplicates (same content, different wording) are flagged separately
  from exact duplicates -- these represent drift and are highest priority for
  consolidation
- CC produces an audit report listing:
  - Each candidate section with a proposed normalized fragment name
    ([normalized_section_name].md)
  - Which documents currently contain that section
  - Whether the copies are identical or drifted (and if drifted, which version
    is more current)
- Documents confirmed to contain duplicative sections are in scope for the
  build script; CC proposes the in-scope document list based on audit findings
- Audit report is written to docs/fragments/audit_report.md before any
  other build steps begin

#### AC-2: Fragment Files
- Each canonical section is stored as a standalone .md file in docs/fragments/
- Fragment filenames use normalized lowercase underscores:
  [normalized_section_name].md (e.g. current_phase_status.md,
  project_structure.md)
- Fragment content is the canonical version of the section -- CC selects the
  most current version where copies have drifted, noted in the audit report
- Fragments contain only the section content, no document-level headers or
  metadata
- Each fragment includes a one-line comment at the top identifying it as a
  managed fragment: <!-- fragment: [normalized_section_name] -->

#### AC-3: Document Templates
- For each in-scope document, a template file is created alongside the
  assembled output:
  - Templates live in docs/templates/ with the same filename as the target
    document (e.g. docs/templates/README.md)
  - Templates contain the document's non-shared content verbatim, with
    include markers replacing shared sections
  - Include marker format: {{include: normalized_section_name}}
  - Document-specific content (preamble, unique sections, closing notes)
    is preserved in the template as-is
- Templates are the source of truth for document structure; assembled outputs
  are generated artifacts

#### AC-4: Build Script -- scripts/utils/build_docs.py
- Script reads each template in docs/templates/, resolves all
  {{include: name}} markers by reading the corresponding fragment from
  docs/fragments/[name].md, and writes the assembled document to its
  target path
- If a fragment referenced in a template does not exist, script errors with
  a clear message identifying the missing fragment and the template that
  references it -- does not silently skip
- Script supports two modes:
  - --all: assembles all documents from all templates (default behavior
    when no arguments given)
  - --doc [filename]: assembles a single document by target filename
    (e.g. --doc README.md)
- Script prints a summary on completion: documents assembled, fragments
  resolved, any warnings
- Script is idempotent -- running it multiple times produces the same output
- Invocation: python scripts/utils/build_docs.py or
  python scripts/utils/build_docs.py --doc README.md

#### AC-5: Pre-Commit Reminder
- A pre-commit hook script is created at .git/hooks/pre-commit
- Hook detects whether any fragment file in docs/fragments/ or any template
  in docs/templates/ has been modified in the current commit
- If modified fragments or templates are detected, hook prints a reminder
  before the commit proceeds:

  REMINDER: Fragment or template files modified.
  Run: python scripts/utils/build_docs.py
  to rebuild assembled documents before pushing.

- Hook does not block the commit -- reminder only
- Hook installation is documented in README (or the relevant setup section)

#### AC-6: Assembled Output Handling
- Assembled documents (README.md, PROJECT_CONTEXT.md, etc.) retain their
  existing file paths -- no changes to where documents live
- Assembled documents include a one-line header comment identifying them as
  generated:
  <!-- assembled by build_docs.py -- edit docs/templates/ and docs/fragments/ not this file -->
- The assembled header comment does not break existing Markdown rendering

#### AC-7: SCRIPT_INDEX.md Update
- context/SCRIPT_INDEX.md is updated to include build_docs.py under the
  utilities section with invocation pattern and purpose

---

### Out of Scope

- **Automatic commit or push triggering:** The build script assembles
  documents; it does not run git commands. The pre-commit hook reminds
  only -- it does not run the build script automatically.
- **Jinja2 or templating engine:** Build uses plain Python string
  replacement. No new runtime dependencies beyond the standard library.
- **Conditional includes or loops:** Include markers resolve to a full
  fragment file only. Conditional logic within templates is deferred.
- **Fragment versioning or history:** Fragment history is managed by Git.
  No additional version tracking within the fragment system.
- **Automatic drift detection on assembled outputs:** The script assembles
  from fragments; it does not diff assembled outputs against templates to
  detect manual edits to assembled files. If someone edits an assembled
  file directly, those edits are silently overwritten on next build. This
  is intentional -- assembled files are generated artifacts.
- **Non-Markdown documents:** Only .md files are in scope. No .txt, .py,
  or other file types.
- **candidate_profile.md:** Generated by phase3_build_candidate_profile.py
  from the experience library. Not a candidate for the fragment system --
  its generation pipeline is separate.

---

## Review Annotations
*This section is populated during the Chat spec review step (README process
step 4). Do not fill in manually.*

Open items use `> ⚠ REVIEW:` and must be resolved before build starts.
Resolved items use `> ✅ RESOLVED:` and document what was decided.

---

> ✅ RESOLVED: **In-scope document list.** CC proposes the in-scope documents
based on the AC-1 audit. Documents confirmed to contain duplicative sections
are in scope. User does not pre-select.

> ✅ RESOLVED: **Build trigger.** Manual on demand
(python scripts/utils/build_docs.py) and pre-commit reminder hook. Hook
does not block commits.

> ✅ RESOLVED: **Fragment naming convention.** Lowercase underscores:
[normalized_section_name].md.
