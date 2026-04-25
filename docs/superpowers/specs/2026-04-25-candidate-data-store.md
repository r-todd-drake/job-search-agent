# Candidate Data Store — Design Spec

**Status:** Design decided, ready for audit + implementation planning
**Parking lot items:** 17a (URGENT), 17b (not urgent)
**Date:** 25 Apr 2026

---

## Problem

Six production scripts are currently gitignored because they contain hardcoded personal
data. They cannot be shared on GitHub in their current state, which defeats the project's
value as a portfolio artifact and limits reuse by any other candidate.

**Scripts currently gitignored:**
- `scripts/phase3_build_candidate_profile.py` — highest PII density: `KNOWN_FACTS`,
  `INTRO_MONOLOGUE`, `SHORT_TENURE_EXPLANATION` (education, military, certs, gaps, narrative)
- `scripts/check_cover_letter.py`
- `scripts/check_resume.py`
- `scripts/phase2_job_ranking.py`
- `scripts/phase2_semantic_analyzer.py`
- `scripts/phase4_resume_generator.py`

A second, lower-priority problem: scripts like `phase5_workshop_capture.py` contain no
personal data but are tuned to defense SE (tag vocabulary, keyword assumptions). They work
on GitHub but cannot be used by someone in a different field without modifying scripts
directly.

---

## Two-Item Split

**17a — URGENT:** Remove PII from scripts; house in `context/candidate/` data store.
Scripts become PII-free framework code and can return to git tracking.

**17b — NOT URGENT:** Generalize domain-specific vocabulary and prompt language.
`context/domain/` mirrors the 17a pattern. Do not begin until 17a loader design is final.

These can proceed concurrently — they touch different parts of the codebase — but 17b
should not start until the `context/candidate/` pattern is validated in production.

---

## Decided Architecture — 17a

### Folder structure

```
context/
├── candidate/                        ← new folder, gitignored via single rule
│   ├── candidate_config.yaml         ← gitignored — personal data lives here
│   └── candidate_config.example.yaml ← tracked — blank template, ships with repo
├── CANDIDATE_BACKGROUND.md           ← move here from context/ root (gitignored)
├── PIPELINE_STATUS.md                ← move here from context/ root (gitignored)
└── [all other context files]         ← tracked project docs, unchanged
```

### .gitignore rule

```
context/candidate/*
!context/candidate/candidate_config.example.yaml
```

Single rule covers the entire folder. The example file is explicitly unignored so it
ships with the repo as a blank template for new users.

### candidate_config.yaml (gitignored)

Holds all structured career narrative — content that is too long or too structured for
`.env` variables:

```yaml
# context/candidate/candidate_config.yaml
# Your personal career data. Never commit this file.

education:
  degrees:
    - institution: ...
      degree: ...
      notes: ...
  certifications:
    - name: ...
      status: ...  # active / lapsed / not held
  not_held: [...]  # explicit list of degrees/certs candidate does NOT have

military:
  service:
    - branch: ...
      mos: ...
      dates: ...
      notes: ...

confirmed_skills:
  programming: ...
  tools: [...]
  not_held: [...]  # explicit gaps

confirmed_gaps: [...]

clearance:
  level: ...
  status: ...  # Current / Active
  granted: ...

style_rules:
  dash_style: en dash only
  metric_rule: no unverifiable metrics
  # etc.

intro_monologue: |
  [multi-line base introduction for Phase 5 to tailor per stage]

short_tenure_explanation: |
  [Saronic or other short-tenure framing — final approved wording]
```

### .env (already exists, extend as needed)

Retains scalar PII: `CANDIDATE_NAME`, `CANDIDATE_PHONE`, `CANDIDATE_EMAIL`,
`CANDIDATE_LINKEDIN`, `CANDIDATE_GITHUB`, `CANDIDATE_LOCATION`, `ANTHROPIC_API_KEY`.
No changes needed unless audit of the 5 scripts reveals additional scalars not yet
covered.

### Loader: scripts/utils/candidate_config.py (tracked)

New module. Loads `candidate_config.yaml` once and exposes all fields as accessible
attributes or a typed dict. All gitignored scripts import from here instead of defining
constants locally. Once a script is refactored to use the loader, it contains no PII
and can be restored to git tracking.

```python
# scripts/utils/candidate_config.py
import yaml, os

_CONFIG_PATH = "context/candidate/candidate_config.yaml"
_config = None

def load():
    global _config
    if _config is None:
        if not os.path.exists(_CONFIG_PATH):
            raise FileNotFoundError(
                f"{_CONFIG_PATH} not found. "
                f"Copy candidate_config.example.yaml and fill in your data."
            )
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            _config = yaml.safe_load(f)
    return _config
```

Scripts call `candidate_config.load()` and access fields by key. If the file is missing,
the error message points the user to the example template.

---

## Parallel Architecture — 17b (for reference, not yet scoped)

```
context/
└── domain/
    ├── domain_config.yaml         ← gitignored — field-specific vocab/settings
    └── domain_config.example.yaml ← tracked — blank template
```

Holds: tag vocabulary, keyword lists, role-level language, domain-specific prompt
phrases (e.g., "defense and aerospace", "TS/SCI"). Same loader pattern as 17a.

### phase2_job_ranking.py is a 17b script

`phase2_job_ranking.py` contains no personal identity data (no name, no clearance, no
narrative) and can be restored to git tracking immediately without a 17a refactor.
However, its `KEYWORDS` list — terms, weights, and aliases used to score job descriptions —
is tuned entirely to this user's background (MBSE, maritime autonomy, C4ISR, Project
Overmatch, etc.). A different candidate would need a completely different keyword profile
to get useful rankings.

The `KEYWORDS` list belongs in `domain_config.yaml`, not hardcoded in the script.

### Future design question: keyword bootstrapping for new users (not urgent)

Moving keywords to `domain_config.yaml` solves portability only if a new user has a way
to populate that file. Two approaches to resolve before 17b implementation:

- **Manual input** — example file ships with a commented keyword/weight/alias skeleton;
  user fills it in by hand.
- **Resume ingestion** — a setup script reads the user's resume(s), uses Claude to extract
  domain keywords and suggest weights, and drafts a starter `domain_config.yaml` for review.

Design this when 17a is validated in production.

---

## Refactor Sequence for 17a

1. **Audit** — read all 5 remaining gitignored scripts; inventory every hardcoded
   personal constant (not just in phase3 — some scripts may have minimal PII,
   others more)
2. **Schema design** — design `candidate_config.yaml` to cover all fields found
   in the audit; write `candidate_config.example.yaml` with placeholder values
3. **Loader** — build and test `scripts/utils/candidate_config.py`
4. **Migrate `context/CANDIDATE_BACKGROUND.md` and `PIPELINE_STATUS.md`** into
   `context/candidate/` and update `.gitignore`, `CLAUDE.md`, `PROJECT_CONTEXT.md`
   references
5. **Refactor scripts** — one at a time; restore each to git tracking once clean
6. **Update `phase3_build_candidate_profile.py`** last — it has the most constants
   and is the most complex refactor

---

## Next Step for Execution Session

**Start here:** run the audit (step 1 above). Read the 5 gitignored scripts and
produce an inventory of every hardcoded personal constant in each — field name,
current value category (scalar PII / narrative / gap / style rule), and which
`candidate_config.yaml` section it maps to.

This inventory drives the schema design in step 2 and prevents surprises mid-refactor.

**Suggested opener for execution session:**
> "Here's the design spec: [paste this file]. The next step is the audit (step 1).
> Read the 5 gitignored scripts listed in the spec and produce the inventory table."
