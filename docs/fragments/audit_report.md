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
