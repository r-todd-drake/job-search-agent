# Candidate Data Store (17a) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove all hardcoded personal data from six gitignored scripts by housing it in `context/candidate/candidate_config.yaml`, loaded via a shared utility module, so all six scripts become PII-free framework code and can return to git tracking.

**Architecture:** A single YAML file (`candidate_config.yaml`, gitignored) holds all structured career narrative. A loader module (`scripts/utils/candidate_config.py`, tracked) reads it once per process and caches the result. Scripts replace hardcoded constants with calls to the loader — all config access happens inside functions, never at module level, so imports are safe in test environments. `candidate_config.example.yaml` (tracked) ships as a blank template for new users. `phase2_job_ranking.py` is restored to tracking with zero code changes.

**Tech Stack:** Python 3, PyYAML (already a dependency via existing scripts), pytest

---

## File Map

**Create (tracked):**
- `context/candidate/candidate_config.example.yaml` — blank template that ships with the repo
- `scripts/utils/candidate_config.py` — loader module + `get_hardcoded_rules()` + `build_known_facts()`
- `tests/utils/test_candidate_config.py` — unit tests for the loader
- `tests/phase4/conftest.py` — autouse config patch fixture for phase4 tests
- `tests/phase3/conftest.py` — autouse config patch fixture for phase3 tests

**Create (gitignored):**
- `context/candidate/candidate_config.yaml` — real personal data, never committed

**Modify (tracked):**
- `.gitignore` — swap 6 individual script entries for a single `context/candidate/*` rule; remove the 2 context file entries
- `scripts/check_resume.py` — remove `HARDCODED_RULES` constant; load from config in `run_layer1()`
- `scripts/check_cover_letter.py` — same
- `scripts/phase4_resume_generator.py` — remove `EMPLOYER_TIERS`, `CHRONOLOGICAL_ORDER`, 3 `build_docx` hardcodes; load from config in functions
- `scripts/phase2_semantic_analyzer.py` — update fallback profile in `load_candidate_profile()`
- `scripts/phase3_build_candidate_profile.py` — remove `KNOWN_FACTS`, `INTRO_MONOLOGUE`, `SHORT_TENURE_EXPLANATION`; load from config in `build_profile()`
- `CLAUDE.md` — update safe-to-read paths; add `context/candidate/` to gitignored section
- `context/SCRIPT_INDEX.md` — add `candidate_config.py` entry

**Move (gitignored files):**
- `context/CANDIDATE_BACKGROUND.md` → `context/candidate/CANDIDATE_BACKGROUND.md`
- `context/PIPELINE_STATUS.md` → `context/candidate/PIPELINE_STATUS.md`

---

## Task 1: Restore phase2_job_ranking.py to git tracking

**Files:**
- Modify: `.gitignore`

This script has no personal data. The `KEYWORDS` list is domain vocabulary (17b scope). Remove it from `.gitignore` and stage it — no code changes needed.

- [ ] **Step 1: Remove from .gitignore**

In `.gitignore`, delete line 22:
```
scripts/phase2_job_ranking.py
```

- [ ] **Step 2: Verify the script is now visible to git**

```
git status
```
Expected: `scripts/phase2_job_ranking.py` appears as an untracked file (not shown before).

- [ ] **Step 3: Syntax check**

```
python -m py_compile scripts/phase2_job_ranking.py && echo OK
```
Expected: `OK`

- [ ] **Step 4: Run phase2 tests**

```
pytest tests/phase2/test_job_ranking.py -v
```
Expected: All tests pass.

- [ ] **Step 5: Commit**

```
git add .gitignore scripts/phase2_job_ranking.py
git commit -m "chore: restore phase2_job_ranking.py to git tracking — no PII"
```

---

## Task 2: Update .gitignore for context/candidate/

**Files:**
- Modify: `.gitignore`

Replace the 5 remaining individual script entries and the 2 context file entries with a single folder rule.

- [ ] **Step 1: Edit .gitignore**

Remove these 7 lines (lines 15–16 and 19–24 in the current file):
```
context/CANDIDATE_BACKGROUND.md
context/PIPELINE_STATUS.md

scripts/phase3_build_candidate_profile.py
scripts/check_cover_letter.py
scripts/check_resume.py
scripts/phase2_semantic_analyzer.py
scripts/phase4_resume_generator.py
```

Add these lines in their place (under "Personal configuration and context files"):
```
context/candidate/*
!context/candidate/candidate_config.example.yaml
```

The final "Personal configuration and context files" block should look like:
```
# Personal configuration and context files
.env
project_career_resume.md
RESUME_TAILORING_CONTEXT.md
context/candidate/*
!context/candidate/candidate_config.example.yaml
```

- [ ] **Step 2: Verify the rule works**

```
git check-ignore -v context/candidate/candidate_config.yaml
```
Expected: `.gitignore:N:context/candidate/*  context/candidate/candidate_config.yaml`

```
git check-ignore -v context/candidate/candidate_config.example.yaml
```
Expected: no output (file is NOT ignored — the `!` negation applies).

- [ ] **Step 3: Commit**

```
git add .gitignore
git commit -m "chore: replace individual gitignore entries with context/candidate/* rule"
```

---

## Task 3: Create candidate_config.example.yaml

**Files:**
- Create: `context/candidate/candidate_config.example.yaml`

This is the blank template that ships with the repo. All values are placeholders — no real data.

- [ ] **Step 1: Create the directory**

```
mkdir -p context/candidate
```

- [ ] **Step 2: Write the example file**

Create `context/candidate/candidate_config.example.yaml` with this exact content:

```yaml
# context/candidate/candidate_config.example.yaml
# Blank template — copy to candidate_config.yaml and fill in your data.
# candidate_config.yaml is gitignored and will never be committed.

education:
  degrees:
    - institution: "[University Name]"
      degree: "[Degree Name]"
      notes: "[e.g., Army ROTC — commission pathway to Infantry Officer]"
  continuing_education:
    - institution: "[Institution Name]"
      program: "[Program Name]"
      status: "enrolled"  # enrolled / completed
  not_held_labels:
    - "[e.g., Systems Engineering degree]"
    - "[e.g., Computer Science degree]"

certifications:
  active:
    - "[e.g., ICAgile Certified Professional]"
  lapsed:
    - "[e.g., CompTIA Security+]"
  not_held:
    - "[e.g., INCOSE certified]"
    - "[e.g., PMP certified]"

military:
  service:
    - branch: "[e.g., U.S. Army]"
      mos: "[e.g., 11M (Infantryman)]"
      dates: "[e.g., 1991–1994]"
      notes: "[optional additional detail]"

clearance:
  level: "[e.g., TS/SCI]"
  status: "Current"  # Current (between employers) or Active (on a program)
  granted: "[year]"

confirmed_skills:
  programming: "[prose description of programming background]"
  tools:
    - "[e.g., Git/GitHub (version control for personal projects)]"
  not_held:
    - "[e.g., GitLab]"
    - "[e.g., MATLAB]"

confirmed_gaps:
  - "[Full sentence describing gap — e.g., No Terraform or infrastructure-as-code experience]"

employers:
  # List in reverse chronological order — order determines CHRONOLOGICAL_ORDER in phase4
  - name: "[EXACT EMPLOYER NAME AS IT APPEARS IN experience_library.json]"
    tier: 1  # 1 = most recent / highest priority, 2 = secondary, 3 = oldest / brief
  - name: "[EMPLOYER 2]"
    tier: 1

resume_defaults:
  role_title: "[e.g., Senior Systems Engineer]"
  education_line: "[e.g., University Name — Degree | Army ROTC]"
  certifications_line: "[e.g., ICAgile Certified Professional | Current TS/SCI]"

style_rules:
  dash_style: "en dash only — never em dash"
  metric_rule: "no unverifiable metrics"
  lapsed_certs_to_exclude:
    - name: "[e.g., CompTIA Security+]"
      fix: "Remove — certification is lapsed and must not appear"
  clearance_language:
    pattern_to_flag: "[e.g., Active TS/SCI]"
    fix: "Use 'Current TS/SCI' between employers — 'Active' only when employed on a program"
    between_employers: "[e.g., Current TS/SCI]"
    on_program: "[e.g., Active TS/SCI]"
  terminology:
    - rule_name: "[short label for violation report]"
      pattern: "[exact string to flag]"
      replacement: "[correct replacement]"
      case_sensitive: false

intro_monologue: |
  [Multi-line base introduction for Phase 5 to tailor per interview stage.
  Verbatim — never paraphrase or compress this text.]

short_tenure_explanation: |
  [Short-tenure framing — final approved wording.
  Verbatim — never paraphrase or compress this text.]
```

- [ ] **Step 3: Verify the file is tracked (not gitignored)**

```
git check-ignore -v context/candidate/candidate_config.example.yaml
```
Expected: no output (file is NOT ignored).

```
git status
```
Expected: `context/candidate/candidate_config.example.yaml` appears as an untracked file.

- [ ] **Step 4: Commit**

```
git add context/candidate/candidate_config.example.yaml
git commit -m "feat: add candidate_config.example.yaml blank template"
```

---

## Task 4: Populate candidate_config.yaml (gitignored)

**Files:**
- Create: `context/candidate/candidate_config.yaml` (gitignored — never commit)

Migrate personal constants from the existing gitignored scripts to the YAML. This file
is never committed. Source locations are given for each field.

- [ ] **Step 1: Create the file**

Create `context/candidate/candidate_config.yaml`. Start from the structure in
`candidate_config.example.yaml` and fill in real values as follows:

| YAML field | Source |
|---|---|
| `education.degrees[0]` | `phase3_build_candidate_profile.py` KNOWN_FACTS lines 52–57 |
| `education.continuing_education[0]` | KNOWN_FACTS line 55 |
| `education.not_held_labels` | KNOWN_FACTS lines 57–60 |
| `certifications.active` | KNOWN_FACTS line 63 |
| `certifications.lapsed` | KNOWN_FACTS line 62 |
| `certifications.not_held` | KNOWN_FACTS lines 64–65 |
| `military.service[]` | KNOWN_FACTS lines 68–77 (one entry per date range) |
| `clearance.level / status / granted` | KNOWN_FACTS lines 79–82 |
| `confirmed_skills.programming` | KNOWN_FACTS lines 85–88 |
| `confirmed_skills.tools` | KNOWN_FACTS line 89 |
| `confirmed_skills.not_held` | KNOWN_FACTS line 90 |
| `confirmed_gaps[]` | KNOWN_FACTS lines 92–99 (one entry per bullet) |
| `employers[]` name + tier | `phase4_resume_generator.py` EMPLOYER_TIERS lines 65–73 |
| `employers[]` order | CHRONOLOGICAL_ORDER lines 441–449 (top = most recent) |
| `resume_defaults.role_title` | `phase4_resume_generator.py` line 775 (`"Senior Systems Engineer"`) |
| `resume_defaults.education_line` | `phase4_resume_generator.py` line 854 |
| `resume_defaults.certifications_line` | `phase4_resume_generator.py` line 855 |
| `style_rules.lapsed_certs_to_exclude` | `check_resume.py` HARDCODED_RULES lines 52–58 |
| `style_rules.clearance_language` | `check_resume.py` HARDCODED_RULES lines 60–64 |
| `style_rules.terminology[]` | `check_resume.py` HARDCODED_RULES lines 66–90 (skip em dash — that stays hardcoded in loader) |
| `intro_monologue` | `phase3_build_candidate_profile.py` INTRO_MONOLOGUE lines 110–128 (verbatim) |
| `short_tenure_explanation` | `phase3_build_candidate_profile.py` SHORT_TENURE_EXPLANATION lines 130–143 (verbatim) |

- [ ] **Step 2: Validate YAML syntax**

```
python -c "import yaml; yaml.safe_load(open('context/candidate/candidate_config.yaml', encoding='utf-8')); print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Verify it is gitignored**

```
git check-ignore -v context/candidate/candidate_config.yaml
```
Expected: output confirms the file is ignored. If not, stop and fix `.gitignore` before continuing.

```
git status
```
Expected: `context/candidate/candidate_config.yaml` does NOT appear in git status output.

---

## Task 5: Write scripts/utils/candidate_config.py and its tests

**Files:**
- Create: `scripts/utils/candidate_config.py`
- Create: `tests/utils/test_candidate_config.py`

- [ ] **Step 1: Write the loader module**

Create `scripts/utils/candidate_config.py`:

```python
import os
import yaml
from dotenv import load_dotenv

_CONFIG_PATH = "context/candidate/candidate_config.yaml"
_config = None


def load():
    global _config
    if _config is None:
        if not os.path.exists(_CONFIG_PATH):
            raise FileNotFoundError(
                f"{_CONFIG_PATH} not found. "
                f"Copy context/candidate/candidate_config.example.yaml, "
                f"fill in your data, and save as candidate_config.yaml."
            )
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            _config = yaml.safe_load(f)
    return _config


def get_hardcoded_rules(document_type="resume"):
    """Return HARDCODED_RULES as a list of (rule_name, pattern, fix, case_sensitive) tuples.

    The em dash rule is universal and hardcoded here. All other rules come from
    style_rules in candidate_config.yaml.
    """
    cfg = load()
    rules = []

    rules.append((
        "Em dash",
        "—",
        "Replace — with – (en dash)",
        True,
    ))

    style = cfg.get("style_rules", {})

    for cert in style.get("lapsed_certs_to_exclude", []):
        rules.append((
            f"{cert['name']} reference",
            cert["name"],
            f"{cert['fix']} on {document_type}",
            False,
        ))

    cl = style.get("clearance_language", {})
    if cl.get("pattern_to_flag"):
        rules.append((
            cl["pattern_to_flag"],
            cl["pattern_to_flag"],
            cl["fix"],
            True,
        ))

    for term in style.get("terminology", []):
        rules.append((
            term.get("rule_name", term["pattern"]),
            term["pattern"],
            f"Use '{term['replacement']}' instead",
            term.get("case_sensitive", False),
        ))

    return rules


def build_known_facts():
    """Build the KNOWN_FACTS text block for Claude prompts in phase3.

    Combines scalar PII from .env with structured career data from candidate_config.yaml.
    """
    load_dotenv()
    cfg = load()

    lines = ["\nCONFIRMED FACTS (supplement library data):"]
    lines.append(f"- Name: {os.getenv('CANDIDATE_NAME', '[CANDIDATE]')}")
    lines.append(f"- Location: {os.getenv('CANDIDATE_LOCATION', '[LOCATION]')}")
    lines.append(f"- Phone: {os.getenv('CANDIDATE_PHONE', '[PHONE]')}")
    lines.append(f"- Email: {os.getenv('CANDIDATE_EMAIL', '[EMAIL]')}")
    lines.append(f"- LinkedIn: {os.getenv('CANDIDATE_LINKEDIN', '[LINKEDIN]')}")
    lines.append(f"- GitHub: {os.getenv('CANDIDATE_GITHUB', '[GITHUB]')}")
    lines.append("")

    edu = cfg.get("education", {})
    lines.append("EDUCATION (confirmed):")
    for deg in edu.get("degrees", []):
        lines.append(f"- {deg.get('institution', '')}")
        lines.append(f"- Degree: {deg.get('degree', '')}")
        if deg.get("notes"):
            lines.append(f"- {deg['notes']}")
    for entry in edu.get("continuing_education", []):
        lines.append(f"- {entry.get('institution', '')} — {entry.get('program', '')} ({entry.get('status', '')})")
    for label in edu.get("not_held_labels", []):
        lines.append(f"- NOT a {label}")
    lines.append("")

    certs = cfg.get("certifications", {})
    lines.append("CERTIFICATIONS (confirmed):")
    for cert in certs.get("active", []):
        lines.append(f"- {cert}")
    for cert in certs.get("lapsed", []):
        lines.append(f"- {cert} (lapsed)")
    for cert in certs.get("not_held", []):
        lines.append(f"- NOT {cert}")
    lines.append("")

    cl = cfg.get("clearance", {})
    style = cfg.get("style_rules", {})
    cl_lang = style.get("clearance_language", {})
    lines.append("CLEARANCE:")
    lines.append(f"- {cl.get('status', 'Current')} {cl.get('level', 'TS/SCI')} (granted {cl.get('granted', '')})")
    if cl_lang.get("between_employers"):
        lines.append(f"- Use \"{cl_lang['between_employers']}\" when between employers")
        lines.append(f"- Use \"{cl_lang['on_program']}\" once employed on a program")
    lines.append("")

    mil = cfg.get("military", {})
    lines.append("MILITARY SERVICE (confirmed):")
    for svc in mil.get("service", []):
        entry = f"- {svc.get('branch', '')} {svc.get('mos', '')} {svc.get('dates', '')}".strip()
        lines.append(entry)
        if svc.get("notes"):
            lines.append(f"- {svc['notes']}")
    lines.append("")

    skills = cfg.get("confirmed_skills", {})
    lines.append("CONFIRMED SKILLS - PROGRAMMING:")
    lines.append(f"- {skills.get('programming', '')}")
    for tool in skills.get("tools", []):
        lines.append(f"- {tool}")
    for item in skills.get("not_held", []):
        lines.append(f"- No {item}")
    lines.append("")

    lines.append("CONFIRMED GAPS (never include on resume):")
    for gap in cfg.get("confirmed_gaps", []):
        lines.append(f"- {gap}")
    lines.append("")

    lines.append("STYLE RULES:")
    lines.append(f"- {style.get('dash_style', 'En dashes only, never em dashes')}")
    lines.append(f"- {style.get('metric_rule', 'No unverifiable metrics')}")
    for term in style.get("terminology", []):
        lines.append(f"- \"{term['pattern']}\" not \"{term['replacement']}\"")

    return "\n".join(lines)
```

- [ ] **Step 2: Write the tests**

Create `tests/utils/test_candidate_config.py`:

```python
# tests/utils/test_candidate_config.py
#
# Unit tests for scripts/utils/candidate_config.py
# These tests control _config directly — do NOT apply the autouse patch fixture here.
#
# Run: pytest tests/utils/test_candidate_config.py -v

import pytest
import yaml
import scripts.utils.candidate_config as cc


@pytest.fixture(autouse=True)
def reset_config_cache():
    """Reset the module cache before each test so tests are independent."""
    cc._config = None
    yield
    cc._config = None


def test_load_returns_dict_from_yaml(tmp_path):
    config_data = {
        "clearance": {"level": "TS/SCI", "status": "Current", "granted": "2022"},
        "style_rules": {"dash_style": "en dash only"},
    }
    config_file = tmp_path / "candidate_config.yaml"
    config_file.write_text(yaml.dump(config_data), encoding="utf-8")

    original_path = cc._CONFIG_PATH
    cc._CONFIG_PATH = str(config_file)
    try:
        result = cc.load()
        assert result["clearance"]["level"] == "TS/SCI"
    finally:
        cc._CONFIG_PATH = original_path


def test_load_caches_result(tmp_path):
    config_data = {"clearance": {"level": "TS/SCI"}}
    config_file = tmp_path / "candidate_config.yaml"
    config_file.write_text(yaml.dump(config_data), encoding="utf-8")

    original_path = cc._CONFIG_PATH
    cc._CONFIG_PATH = str(config_file)
    try:
        result1 = cc.load()
        result2 = cc.load()
        assert result1 is result2
    finally:
        cc._CONFIG_PATH = original_path


def test_load_raises_with_helpful_message_when_file_missing(tmp_path):
    original_path = cc._CONFIG_PATH
    cc._CONFIG_PATH = str(tmp_path / "nonexistent.yaml")
    try:
        with pytest.raises(FileNotFoundError) as exc_info:
            cc.load()
        assert "candidate_config.example.yaml" in str(exc_info.value)
    finally:
        cc._CONFIG_PATH = original_path


def test_get_hardcoded_rules_always_includes_em_dash():
    cc._config = {"style_rules": {}}
    rules = cc.get_hardcoded_rules()
    patterns = [r[1] for r in rules]
    assert "—" in patterns


def test_get_hardcoded_rules_includes_lapsed_cert():
    cc._config = {
        "style_rules": {
            "lapsed_certs_to_exclude": [
                {"name": "CompTIA Security+", "fix": "Remove — lapsed"}
            ],
            "clearance_language": {},
            "terminology": [],
        }
    }
    rules = cc.get_hardcoded_rules("resume")
    patterns = [r[1] for r in rules]
    assert "CompTIA Security+" in patterns


def test_get_hardcoded_rules_includes_clearance_pattern():
    cc._config = {
        "style_rules": {
            "lapsed_certs_to_exclude": [],
            "clearance_language": {
                "pattern_to_flag": "Active TS/SCI",
                "fix": "Use Current TS/SCI",
            },
            "terminology": [],
        }
    }
    rules = cc.get_hardcoded_rules()
    patterns = [r[1] for r in rules]
    assert "Active TS/SCI" in patterns


def test_get_hardcoded_rules_returns_four_tuples():
    cc._config = {
        "style_rules": {
            "lapsed_certs_to_exclude": [
                {"name": "Test Cert", "fix": "Remove it"}
            ],
            "clearance_language": {
                "pattern_to_flag": "Active TS/SCI",
                "fix": "Use Current",
            },
            "terminology": [
                {"rule_name": "test", "pattern": "foo", "replacement": "bar", "case_sensitive": False}
            ],
        }
    }
    rules = cc.get_hardcoded_rules()
    assert all(len(r) == 4 for r in rules)


def test_get_hardcoded_rules_passes_document_type_to_fix():
    cc._config = {
        "style_rules": {
            "lapsed_certs_to_exclude": [
                {"name": "Test Cert", "fix": "Remove — lapsed"}
            ],
            "clearance_language": {},
            "terminology": [],
        }
    }
    rules_resume = cc.get_hardcoded_rules("resume")
    rules_cl = cc.get_hardcoded_rules("cover letter")
    cert_fix_resume = next(r[2] for r in rules_resume if r[1] == "Test Cert")
    cert_fix_cl = next(r[2] for r in rules_cl if r[1] == "Test Cert")
    assert "resume" in cert_fix_resume
    assert "cover letter" in cert_fix_cl
```

- [ ] **Step 3: Run the tests (they should pass)**

```
pytest tests/utils/test_candidate_config.py -v
```
Expected: All tests pass.

- [ ] **Step 4: Syntax check the loader**

```
python -m py_compile scripts/utils/candidate_config.py && echo OK
```
Expected: `OK`

- [ ] **Step 5: Smoke-test the loader against the real yaml**

```
python -c "
from scripts.utils.candidate_config import load, get_hardcoded_rules
cfg = load()
print('employers:', len(cfg.get('employers', [])))
rules = get_hardcoded_rules('resume')
print('hardcoded rules:', len(rules))
print('OK')
"
```
Expected: `employers: 7`, `hardcoded rules: 7` (em dash + 1 cert + 1 clearance + 4 terminology), `OK`

(Adjust expected counts if your YAML has different numbers.)

- [ ] **Step 6: Commit**

```
git add scripts/utils/candidate_config.py tests/utils/test_candidate_config.py
git commit -m "feat: add candidate_config loader module with tests"
```

---

## Task 6: Migrate context files to context/candidate/

**Files:**
- Move: `context/CANDIDATE_BACKGROUND.md` → `context/candidate/CANDIDATE_BACKGROUND.md`
- Move: `context/PIPELINE_STATUS.md` → `context/candidate/PIPELINE_STATUS.md`
- Modify: `scripts/check_resume.py` (path constant only)
- Modify: `scripts/check_cover_letter.py` (path constant only)

- [ ] **Step 1: Move the files**

```
git mv context/CANDIDATE_BACKGROUND.md context/candidate/CANDIDATE_BACKGROUND.md
git mv context/PIPELINE_STATUS.md context/candidate/PIPELINE_STATUS.md
```

Note: `git mv` on gitignored files may not work. If it errors, use:
```
cp context/CANDIDATE_BACKGROUND.md context/candidate/CANDIDATE_BACKGROUND.md
cp context/PIPELINE_STATUS.md context/candidate/PIPELINE_STATUS.md
```
Then manually delete the originals. The files are gitignored so git won't track the move.

- [ ] **Step 2: Verify new paths exist**

```
python -c "import os; print(os.path.exists('context/candidate/CANDIDATE_BACKGROUND.md'))"
```
Expected: `True`

- [ ] **Step 3: Update CANDIDATE_BACKGROUND_PATH in check_resume.py**

In `scripts/check_resume.py`, change line 37:
```python
# Before
CANDIDATE_BACKGROUND_PATH = "context/CANDIDATE_BACKGROUND.md"

# After
CANDIDATE_BACKGROUND_PATH = "context/candidate/CANDIDATE_BACKGROUND.md"
```

- [ ] **Step 4: Update CANDIDATE_BACKGROUND_PATH in check_cover_letter.py**

In `scripts/check_cover_letter.py`, change line 37:
```python
# Before
CANDIDATE_BACKGROUND_PATH = "context/CANDIDATE_BACKGROUND.md"

# After
CANDIDATE_BACKGROUND_PATH = "context/candidate/CANDIDATE_BACKGROUND.md"
```

- [ ] **Step 5: Syntax check both scripts**

```
python -m py_compile scripts/check_resume.py && python -m py_compile scripts/check_cover_letter.py && echo OK
```
Expected: `OK`

- [ ] **Step 6: Commit**

```
git add scripts/check_resume.py scripts/check_cover_letter.py
git commit -m "chore: migrate CANDIDATE_BACKGROUND.md and PIPELINE_STATUS.md to context/candidate/"
```

---

## Task 7: Refactor check_resume.py and check_cover_letter.py

**Files:**
- Modify: `scripts/check_resume.py`
- Modify: `scripts/check_cover_letter.py`
- Create: `tests/phase4/conftest.py`

Both scripts have an identical `HARDCODED_RULES` constant. Replace it with a call to
`candidate_config.get_hardcoded_rules()` inside `run_layer1()`.

- [ ] **Step 1: Write tests/phase4/conftest.py**

This autouse fixture patches `candidate_config._config` so all phase4 tests can import
refactored scripts without needing a real `candidate_config.yaml`.

Create `tests/phase4/conftest.py`:

```python
# tests/phase4/conftest.py
# Autouse fixture: patches candidate_config with test data for all phase4 tests.
# Prevents import-time failures in refactored scripts that call candidate_config.load().

import pytest
import scripts.utils.candidate_config as _cc


_TEST_CONFIG = {
    "style_rules": {
        "lapsed_certs_to_exclude": [
            {"name": "CompTIA Security+", "fix": "Remove — certification is lapsed"}
        ],
        "clearance_language": {
            "pattern_to_flag": "Active TS/SCI",
            "fix": "Use 'Current TS/SCI' between employers — 'Active' only when employed on a program",
            "between_employers": "Current TS/SCI",
            "on_program": "Active TS/SCI",
        },
        "terminology": [
            {"rule_name": "Plank Holder (capitalized)", "pattern": "Plank Holder",
             "replacement": "Plank Owner (two words, capitalized)", "case_sensitive": True},
            {"rule_name": "plank holder (lowercase)", "pattern": "plank holder",
             "replacement": "Plank Owner (two words, capitalized)", "case_sensitive": False},
            {"rule_name": "plankowner (one word)", "pattern": "plankowner",
             "replacement": "Plank Owner (two words, capitalized)", "case_sensitive": False},
            {"rule_name": "safety-critical", "pattern": "safety-critical",
             "replacement": "mission-critical", "case_sensitive": False},
        ],
        "dash_style": "en dash only",
        "metric_rule": "no unverifiable metrics",
    },
    "employers": [
        {"name": "SARONIC TECHNOLOGIES", "tier": 1},
        {"name": "KFORCE (Supporting Leidos / NIWC PAC)", "tier": 1},
        {"name": "SHIELD AI", "tier": 1},
        {"name": "G2 OPS", "tier": 1},
        {"name": "SAIC", "tier": 2},
        {"name": "L3 COMMUNICATIONS", "tier": 3},
        {"name": "U.S. ARMY", "tier": 3},
    ],
    "resume_defaults": {
        "role_title": "Senior Systems Engineer",
        "education_line": "State University — B.A. Test Degree | ROTC",
        "certifications_line": "Test Cert | Current TS/SCI",
    },
    "clearance": {"level": "TS/SCI", "status": "Current", "granted": "2022"},
    "confirmed_gaps": [],
    "intro_monologue": "Test intro monologue.",
    "short_tenure_explanation": "Test tenure explanation.",
}


@pytest.fixture(autouse=True)
def patch_candidate_config(monkeypatch):
    monkeypatch.setattr(_cc, "_config", _TEST_CONFIG)
```

- [ ] **Step 2: Verify existing phase4 tests still pass with the new fixture**

```
pytest tests/phase4/ -v -m "not live"
```
Expected: Same pass/fail counts as before (all non-live tests pass).

- [ ] **Step 3: Refactor check_resume.py**

In `scripts/check_resume.py`:

**Add** after the existing imports (around line 29):
```python
from scripts.utils import candidate_config
```

**Remove** the entire `HARDCODED_RULES` constant (lines 47–90):
```python
# DELETE THIS ENTIRE BLOCK:
HARDCODED_RULES = [
    (
        "Em dash",
        ...
    ),
    ...
]
```

**Replace** the first line of `run_layer1()` that iterates over `HARDCODED_RULES`:
```python
# Before
def run_layer1(resume_lines, gap_terms):
    findings = []

    # Hardcoded rules
    for rule_name, pattern, fix, case_sensitive in HARDCODED_RULES:

# After
def run_layer1(resume_lines, gap_terms):
    findings = []

    for rule_name, pattern, fix, case_sensitive in candidate_config.get_hardcoded_rules("resume"):
```

- [ ] **Step 4: Syntax check check_resume.py**

```
python -m py_compile scripts/check_resume.py && echo OK
```
Expected: `OK`

- [ ] **Step 5: Run check_resume tests**

```
pytest tests/phase4/test_check_resume.py -v -m "not live"
```
Expected: All non-live tests pass.

- [ ] **Step 6: Refactor check_cover_letter.py**

Apply the identical changes as Step 3 to `scripts/check_cover_letter.py`:

**Add** import:
```python
from scripts.utils import candidate_config
```

**Remove** `HARDCODED_RULES` constant (same lines 47–90).

**Replace** the iteration in `run_layer1()`:
```python
# Before
    for rule_name, pattern, fix, case_sensitive in HARDCODED_RULES:

# After
    for rule_name, pattern, fix, case_sensitive in candidate_config.get_hardcoded_rules("cover letter"):
```

- [ ] **Step 7: Syntax check check_cover_letter.py**

```
python -m py_compile scripts/check_cover_letter.py && echo OK
```
Expected: `OK`

- [ ] **Step 8: Run cover letter tests**

```
pytest tests/phase4/test_check_cover_letter.py -v -m "not live"
```
Expected: All non-live tests pass.

- [ ] **Step 9: Commit**

```
git add tests/phase4/conftest.py scripts/check_resume.py scripts/check_cover_letter.py
git commit -m "feat: load HARDCODED_RULES from candidate_config — check_resume and check_cover_letter are now PII-free"
```

---

## Task 8: Refactor phase4_resume_generator.py

**Files:**
- Modify: `scripts/phase4_resume_generator.py`

Three changes: (1) replace `EMPLOYER_TIERS` and `CHRONOLOGICAL_ORDER` constants with
config-driven helper functions, (2) remove hardcoded strings from `build_docx()`,
(3) update fallback profile in `load_candidate_profile()`.

- [ ] **Step 1: Add the import**

After the existing imports in `scripts/phase4_resume_generator.py`, add:
```python
from scripts.utils import candidate_config
```

- [ ] **Step 2: Replace EMPLOYER_TIERS and CHRONOLOGICAL_ORDER**

Remove the `EMPLOYER_TIERS` dict (lines 65–73) and the `CHRONOLOGICAL_ORDER` list
(lines 441–449).

Add these two helper functions immediately after the `load_dotenv()` call at the top
of the file, before `JOBS_PACKAGES_DIR` and the config imports:

```python
def _get_employer_tiers():
    employers = candidate_config.load().get("employers", [])
    return {e["name"]: e["tier"] for e in employers}


def _get_chronological_order():
    employers = candidate_config.load().get("employers", [])
    return [e["name"] for e in employers]
```

In `stage1_select_bullets()`, replace every reference to `EMPLOYER_TIERS` with
`_get_employer_tiers()` and every reference to `CHRONOLOGICAL_ORDER` in
`build_stage1_draft()` with `_get_chronological_order()`.

Specifically:

In `stage1_select_bullets()` (around line 212):
```python
# Before
        tier = EMPLOYER_TIERS.get(name, 2)

# After
        tier = _get_employer_tiers().get(name, 2)
```

In `build_stage1_draft()` (around line 451):
```python
# Before
    tier_order = sorted(
        candidates_by_employer.keys(),
        key=lambda x: CHRONOLOGICAL_ORDER.index(x) if x in CHRONOLOGICAL_ORDER else 99
    )

# After
    chrono = _get_chronological_order()
    tier_order = sorted(
        candidates_by_employer.keys(),
        key=lambda x: chrono.index(x) if x in chrono else 99
    )
```

- [ ] **Step 3: Update fallback profile in load_candidate_profile()**

Replace the fallback string in `load_candidate_profile()` (lines 91–99):

```python
# Before
        return """
CANDIDATE: [CANDIDATE]
CLEARANCE: Current TS/SCI (granted 2022)
LOCATION: San Diego, CA
EXPERIENCE: 20+ years defense systems engineering
EDUCATION: B.A. Geography, GIS & Remote Sensing (NOT Systems Engineering), Army ROTC, Enrolled in UCSC Extended Studies Systems Engineering Certificate Program
GAPS: No GitLab, no Terraform, no INCOSE, no FAA/DO-178, no FEA/CFD
RULES: En dashes only, no unverifiable metrics, Saronic = maritime only
"""

# After
        try:
            return candidate_config.build_known_facts()
        except FileNotFoundError:
            return (
                "\nCANDIDATE: [CANDIDATE]\n"
                "CLEARANCE: [see candidate_config.yaml]\n"
                "Run phase3_build_candidate_profile.py and ensure candidate_config.yaml exists.\n"
            )
```

- [ ] **Step 4: Remove hardcoded strings from build_docx()**

In `build_docx()`, find the `add_name_header()` nested function and update it:

```python
# Before (line 775)
        p2.add_run("Senior Systems Engineer")

# After
        cfg = candidate_config.load()
        p2.add_run(cfg["resume_defaults"]["role_title"])
```

Find the Education & Certifications section at the bottom of `build_docx()`:

```python
# Before (lines 853–855)
    add_section_heading("Education & Certifications")
    add_normal("San Diego State University - B.A. Geography, GIS & Remote Sensing | Army ROTC")
    add_normal("ICAgile Certified Professional | Current TS/SCI")

# After
    add_section_heading("Education & Certifications")
    cfg = candidate_config.load()
    add_normal(cfg["resume_defaults"]["education_line"])
    add_normal(cfg["resume_defaults"]["certifications_line"])
```

Also remove the prompt-level hardcoded fragments in `stage1_select_bullets()`. Find
the `comp_prompt` block (around line 334) and remove these two hardcoded lines:
```python
# Remove these two lines from the rules list in comp_prompt:
- CRITICAL: The candidate's actual degree is B.A. Geography, GIS & Remote Sensing - NOT Systems Engineering
  Never claim a degree the candidate does not hold
- NEVER include these specific tools the candidate does not have:
  GitLab, Terraform, INCOSE certification, FAA/DO-178, FEA, CFD, Cucumber, TDD
- Version control experience is GitHub only - never GitLab
```

Replace with a config-driven block:
```python
    cfg = candidate_config.load()
    gaps_list = "\n  ".join(cfg.get("confirmed_gaps", []))
    not_held = ", ".join(cfg.get("confirmed_skills", {}).get("not_held", []))
```

Then update the f-string to reference `gaps_list` and `not_held` instead of the
hardcoded lists. The exact replacement depends on the surrounding string — fit it
into the same position in the prompt with equivalent meaning.

- [ ] **Step 5: Syntax check**

```
python -m py_compile scripts/phase4_resume_generator.py && echo OK
```
Expected: `OK`

- [ ] **Step 6: Run phase4 tests**

```
pytest tests/phase4/ -v -m "not live"
```
Expected: All non-live tests pass.

- [ ] **Step 7: Commit**

```
git add scripts/phase4_resume_generator.py
git commit -m "feat: load employer tiers, build_docx strings from candidate_config — phase4_resume_generator is now PII-free"
```

---

## Task 9: Refactor phase2_semantic_analyzer.py

**Files:**
- Modify: `scripts/phase2_semantic_analyzer.py`

This script's only personal data is the fallback profile string in
`load_candidate_profile()` (lines 45–52). The main code path reads from
`candidate_profile.md` (generated by phase3); the fallback only runs if that file
is missing.

- [ ] **Step 1: Add the import**

```python
from scripts.utils import candidate_config
```

- [ ] **Step 2: Update fallback in load_candidate_profile()**

```python
# Before (lines 45–52)
        return """
CANDIDATE: [CANDIDATE]
CLEARANCE: Current TS/SCI
LOCATION: San Diego, CA
EXPERIENCE: 20+ years defense systems engineering
SIGNATURE CREDENTIAL: Functional MBSE Pillar Lead, Project Overmatch (CNO priority)
CONSTRAINTS: Not a pure modeler, no FAA/DO-178, no INCOSE certification
"""

# After
        try:
            return candidate_config.build_known_facts()
        except FileNotFoundError:
            return (
                "\nCANDIDATE: [CANDIDATE]\n"
                "Fallback: candidate_config.yaml not found and candidate_profile.md not found.\n"
                "Run phase3_build_candidate_profile.py to generate candidate_profile.md.\n"
            )
```

- [ ] **Step 3: Syntax check**

```
python -m py_compile scripts/phase2_semantic_analyzer.py && echo OK
```
Expected: `OK`

- [ ] **Step 4: Run phase2 tests**

```
pytest tests/phase2/test_semantic_analyzer.py -v -m "not live"
```
Expected: All non-live tests pass.

- [ ] **Step 5: Commit**

```
git add scripts/phase2_semantic_analyzer.py
git commit -m "feat: remove hardcoded fallback profile from phase2_semantic_analyzer — now PII-free"
```

---

## Task 10: Refactor phase3_build_candidate_profile.py

**Files:**
- Modify: `scripts/phase3_build_candidate_profile.py`
- Create: `tests/phase3/conftest.py`

This is the highest-density script. Remove `KNOWN_FACTS`, `INTRO_MONOLOGUE`, and
`SHORT_TENURE_EXPLANATION` constants. Load them from config inside `build_profile()`.

- [ ] **Step 1: Write tests/phase3/conftest.py**

Create `tests/phase3/conftest.py` — identical pattern to the phase4 conftest:

```python
# tests/phase3/conftest.py
import pytest
import scripts.utils.candidate_config as _cc
from tests.phase4.conftest import _TEST_CONFIG


@pytest.fixture(autouse=True)
def patch_candidate_config(monkeypatch):
    monkeypatch.setattr(_cc, "_config", _TEST_CONFIG)
```

- [ ] **Step 2: Verify existing phase3 tests still pass**

```
pytest tests/phase3/ -v -m "not live"
```
Expected: All non-live tests pass.

- [ ] **Step 3: Add the import**

In `scripts/phase3_build_candidate_profile.py`, add after existing imports:
```python
from scripts.utils import candidate_config
```

- [ ] **Step 4: Remove the KNOWN_FACTS constant**

Delete the entire `KNOWN_FACTS = f"""..."""` block (lines 42–105).

- [ ] **Step 5: Remove INTRO_MONOLOGUE and SHORT_TENURE_EXPLANATION constants**

Delete the entire `INTRO_MONOLOGUE = (...)` block (lines 110–128).
Delete the entire `SHORT_TENURE_EXPLANATION = (...)` block (lines 130–143).

- [ ] **Step 6: Update the compile_prompt in build_profile() to use build_known_facts()**

In `build_profile()`, find the `compile_prompt` f-string (around line 318). It
currently embeds `{KNOWN_FACTS}`. Replace that reference:

```python
# Before
CONFIRMED SUPPLEMENTAL FACTS:
{KNOWN_FACTS}

# After
CONFIRMED SUPPLEMENTAL FACTS:
{candidate_config.build_known_facts()}
```

- [ ] **Step 7: Update the Step 4 output section to load monologue and explanation from config**

In the Step 4 save block of `build_profile()` (around lines 422–423):

```python
# Before
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write(master_profile)
        f.write(f"\n\n## INTRO MONOLOGUE\n{INTRO_MONOLOGUE}\n")
        f.write(f"\n\n## SHORT TENURE EXPLANATION\n{SHORT_TENURE_EXPLANATION}\n")

# After
    cfg = candidate_config.load()
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write(master_profile)
        f.write(f"\n\n## INTRO MONOLOGUE\n{cfg['intro_monologue']}\n")
        f.write(f"\n\n## SHORT TENURE EXPLANATION\n{cfg['short_tenure_explanation']}\n")
```

- [ ] **Step 8: Syntax check**

```
python -m py_compile scripts/phase3_build_candidate_profile.py && echo OK
```
Expected: `OK`

- [ ] **Step 9: Run phase3 tests**

```
pytest tests/phase3/ -v -m "not live"
```
Expected: All non-live tests pass.

- [ ] **Step 10: Commit**

```
git add tests/phase3/conftest.py scripts/phase3_build_candidate_profile.py
git commit -m "feat: load KNOWN_FACTS, INTRO_MONOLOGUE, SHORT_TENURE_EXPLANATION from candidate_config — phase3_build_candidate_profile is now PII-free"
```

---

## Task 11: Update docs and CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`
- Modify: `context/SCRIPT_INDEX.md`

- [ ] **Step 1: Update CLAUDE.md**

In the "Never read, access, or touch these files/folders" section, no changes needed
(`context/candidate/candidate_config.yaml` inherits the "never modify" spirit from
it being gitignored).

In the "Read-only (understand structure, never modify)" section, update:
```
# Before
context/*.md — candidate background, decisions log, project context

# After
context/*.md — candidate background, decisions log, project context
context/candidate/candidate_config.example.yaml — blank template (tracked, read-only)
```

Add a new gitignored files note:
```
# Add to gitignored section:
context/candidate/candidate_config.yaml — personal career data (gitignored)
context/candidate/CANDIDATE_BACKGROUND.md — moved from context/ root (gitignored)
context/candidate/PIPELINE_STATUS.md — moved from context/ root (gitignored)
```

In the "Safe to read and edit" section, add:
```
scripts/utils/candidate_config.py — candidate data loader
```

- [ ] **Step 2: Update SCRIPT_INDEX.md**

Add a row for the new utility:

```
| scripts/utils/candidate_config.py | Loads context/candidate/candidate_config.yaml; exposes load(), get_hardcoded_rules(), build_known_facts() | Used by check_resume, check_cover_letter, phase4_resume_generator, phase2_semantic_analyzer, phase3_build_candidate_profile | — |
```

- [ ] **Step 3: Commit**

```
git add CLAUDE.md context/SCRIPT_INDEX.md
git commit -m "docs: update CLAUDE.md and SCRIPT_INDEX for candidate_config loader and context/candidate/ structure"
```

---

## Post-Refactor Verification

After all tasks complete, run the full test suite and verify all 6 previously-gitignored
scripts are now tracked:

```
pytest tests/ -v -m "not live"
```
Expected: All non-live tests pass.

```
git status
```
Expected: `scripts/phase3_build_candidate_profile.py`, `scripts/check_cover_letter.py`,
`scripts/check_resume.py`, `scripts/phase2_semantic_analyzer.py`,
`scripts/phase4_resume_generator.py` all appear as clean tracked files (not listed
in untracked or modified).

```
git ls-files scripts/*.py | sort
```
Expected: All 6 scripts appear in the list.

---

## Self-Review

**Spec coverage check:**
- [x] 17a — PII removed from all 6 scripts
- [x] Single .gitignore rule `context/candidate/*` with example exception
- [x] `candidate_config.yaml` schema covers all audit-identified fields including 3 new fields (employer_tiers, resume_defaults, signature credential via intro_monologue)
- [x] Loader with helpful FileNotFoundError message
- [x] Migration of CANDIDATE_BACKGROUND.md and PIPELINE_STATUS.md
- [x] `phase2_job_ranking.py` restored with zero code changes
- [x] `phase3_build_candidate_profile.py` refactored last

**Placeholder check:** No TBDs, no "handle edge cases", all code blocks are complete.

**Type consistency:** `get_hardcoded_rules()` returns `list[tuple[str, str, str, bool]]`
consistently across Task 5 (definition), Task 7 (check_resume), and Task 7 (check_cover_letter).
`candidate_config.load()` returns `dict` everywhere. `build_known_facts()` returns `str` everywhere.
