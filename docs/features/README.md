# Features

Requirements artifacts for new and proposed capabilities. Each feature lives in its own sub-folder and follows a consistent two-file pattern.

## Folder Structure

```
docs/features/
├── README.md                  — this file
├── user_story_template.md     — template for new proposals
├── [feature-name]/            — one folder per active or in-progress feature
│   ├── proposal.md            — user story, acceptance criteria, out of scope
│   └── prompt_handoff.md      — structured handoff used to initiate development
└── completed/
    └── [feature-name]/        — moved here once built and tests passing
```

## Process

1. Copy `user_story_template.md` into a new folder named for the feature
2. Rename to `proposal.md` and fill in the user story and acceptance criteria
3. Add `prompt_handoff.md` when the feature is ready to hand off to a development session
4. Once the feature is coded and all tests pass, move the folder into `completed/`

## Naming Convention

Folder names use lowercase with hyphens: `interview-prep-stage-awareness`, `phase6-networking`.

## Relationship to Other Docs

- `docs/features/` — *what* to build and how to verify it (requirements)
- `docs/superpowers/specs/` — *how* to build it (design)
- `docs/superpowers/plans/` — implementation steps (execution)
