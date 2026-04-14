# Features

Requirements artifacts for new and proposed capabilities. Each feature lives in its own sub-folder and follows a consistent three-file pattern.

## Folder Structure

```
docs/features/
├── README.md                     — this file
├── user_story_template.md        — template for new proposals
├── prompt_handoff_template.md    — template for Claude Code (CC) session starters
├── [feature-name]/               — one folder per active or in-progress feature
│   ├── proposal.md               — user story, acceptance criteria, out of scope
│   └── prompt_handoff.md         — CC session starter (written after spec review is complete)
└── completed/
    └── [feature-name]/           — moved here once built and tests passing

 CC = Claude Code - agentic development environment used for build sessions.
```
## Process

### 1 — Workshop and propose (Chat)
Work with Claude Chat to define the feature. Chat uses `user_story_template.md` to produce `proposal.md` covering the user story, acceptance criteria, and out-of-scope boundaries.

### 2 — Create feature folder
Create `docs/features/[feature-name]/` using lowercase hyphenated naming (e.g., `post-interview-debrief`, `phase6-networking`). Add `proposal.md` to the folder.

### 3 — Develop spec and/or plan (CC)
CC reads `proposal.md` and relevant context documents, then develops a design spec, implementation plan, or both. CC writes output to the feature folder. User provides input during the session as needed.

### 4 — Spec review (Chat)
Pass the CC-produced spec and/or plan to Claude Chat for review. Chat identifies gaps, ambiguities, missing decisions, and any content that would force an in-session guess during development. Chat annotates the spec using the following conventions:

- `> ⚠ REVIEW: [issue description]` — gap or decision needed; must be resolved before build
- `> ✅ RESOLVED: [what was decided]` — replaces the ⚠ annotation once resolved

User and Chat resolve all open items together. Spec is updated in place. Build does not start until all `⚠ REVIEW:` annotations are resolved.

### 5 — Write prompt handoff (Chat or user)
Once the spec is clean, write `prompt_handoff.md` using `prompt_handoff_template.md`. The handoff is a lightweight CC session starter -- it lists what to load, where to begin, and any session-specific context. It does not restate or compensate for spec content.

### 6 — Build (CC)
CC loads `prompt_handoff.md` and the reviewed spec. Builds the feature per the plan.

### 7 — Complete
Once the feature is coded and all tests pass, move the folder into `completed/`.

---

## Annotation Convention

| Annotation | Meaning | Who adds it |
|---|---|---|
| `> ⚠ REVIEW: [issue]` | Gap or decision needed -- blocks build | Chat during review |
| `> ✅ RESOLVED: [decision]` | Issue resolved -- build may proceed | Chat + user together |

All `⚠ REVIEW:` items must be resolved before `prompt_handoff.md` is written.

---

## Naming Convention

Folder names use lowercase with hyphens: `post-interview-debrief`, `interview-library`, `phase6-networking`.

---

## Relationship to Other Docs

- `docs/features/` — *what* to build and how to verify it (requirements and review)
- `docs/superpowers/specs/` — *how* to build it (design)
- `docs/superpowers/plans/` — implementation steps (execution)
