# Post-Interview Debrief Capture — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `phase_debrief.py` with `--init`, `--convert`, and `--interactive` modes that capture post-interview debriefs as YAML and write structured JSON to `data/debriefs/[role]/`.

**Architecture:** A1 (MVP) is a two-step workflow -- user fills a YAML draft created by `--init`, then `--convert` validates it and writes JSON. A2 adds `--interactive` which walks through a guided questionnaire, calls Claude for optional follow-up questions, and writes JSON directly. All three modes share the same validation helpers and JSON output schema. Pure business logic is separated from I/O for clean unit testing.

**Tech Stack:** Python 3, PyYAML (`pyyaml`), Anthropic Python SDK (already in requirements), python-dotenv, pytest

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `docs/features/post-interview-debrief/interview_debrief_template.yaml` | Create | Reference YAML template -- source of truth for field structure and inline comments |
| `scripts/phase_debrief.py` | Create | All three modes, validation helpers, AI follow-up integration |
| `tests/test_phase_debrief.py` | Create | Unit tests for validators; integration tests for each mode |
| `requirements.txt` | Modify | Add `pyyaml` |

---

## Task 1: YAML Template + Dependency

**Files:**
- Create: `docs/features/post-interview-debrief/interview_debrief_template.yaml`
- Modify: `requirements.txt`

- [ ] **Step 1: Add pyyaml to requirements.txt**

Add `PyYAML==6.0.2` to `requirements.txt`, then run:

```bash
pip install pyyaml
```

- [ ] **Step 2: Create the reference YAML template**

Create `docs/features/post-interview-debrief/interview_debrief_template.yaml`:

```yaml
# Post-Interview Debrief
# Fill in all fields. Leave optional fields as null if not applicable.

metadata:
  role: null                     # pre-filled by --init
  stage: null                    # pre-filled by --init
  company: null                  # e.g. "Viasat"
  interviewer_name: null         # e.g. "Jane Smith"
  interviewer_title: null        # e.g. "Director of Systems Engineering"
  interview_date: null           # YYYY-MM-DD -- drives output filename
  format: null                   # phone | video | onsite
  produced_date: null            # pre-filled by --init

advancement_read:
  assessment: null               # for_sure | maybe | doubt_it | definitely_not
  notes: null

stories_used:
  - tags: []                     # e.g. [leadership, cross-functional]
    framing: null                # brief description of how it was told
    landed: null                 # yes | partially | no
    library_id: null             # optional -- link to interview_library.json entry once in library

gaps_surfaced:
  - gap_label: null              # e.g. "no cleared SCIF experience"
    response_given: null
    response_felt: null          # strong | adequate | weak

salary_exchange:                 # all fields optional
  range_given_min: null          # numeric -- e.g. 145000
  range_given_max: null          # numeric
  candidate_anchor: null         # numeric
  candidate_floor: null          # numeric
  notes: null

what_i_said: null                # free text -- claims, commitments, framings to stay consistent on

open_notes: null                 # anything else worth capturing
```

- [ ] **Step 3: Commit**

```bash
git add docs/features/post-interview-debrief/interview_debrief_template.yaml requirements.txt
git commit -m "Add debrief YAML template and pyyaml dependency"
```

---

## Task 2: Script Skeleton + Argparse

**Files:**
- Create: `scripts/phase_debrief.py`
- Create: `tests/test_phase_debrief.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_phase_debrief.py`:

```python
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scripts.phase_debrief as pd


def test_argparse_init():
    args = pd.build_parser().parse_args(
        ['--role', 'TestRole', '--stage', 'hiring_manager', '--init']
    )
    assert args.role == 'TestRole'
    assert args.stage == 'hiring_manager'
    assert args.init is True
    assert args.convert is False
    assert args.interactive is False


def test_argparse_convert():
    args = pd.build_parser().parse_args(
        ['--role', 'TestRole', '--stage', 'hiring_manager', '--convert']
    )
    assert args.convert is True
    assert args.init is False


def test_argparse_interactive():
    args = pd.build_parser().parse_args(
        ['--role', 'TestRole', '--stage', 'hiring_manager', '--interactive']
    )
    assert args.interactive is True
    assert args.init is False


def test_argparse_mutually_exclusive():
    with pytest.raises(SystemExit):
        pd.build_parser().parse_args(
            ['--role', 'R', '--stage', 'hiring_manager', '--init', '--convert']
        )


def test_argparse_invalid_stage():
    with pytest.raises(SystemExit):
        pd.build_parser().parse_args(
            ['--role', 'R', '--stage', 'bad_stage', '--init']
        )
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_phase_debrief.py -v
```

Expected: ERROR -- `No module named 'scripts.phase_debrief'`

- [ ] **Step 3: Create the script skeleton**

Create `scripts/phase_debrief.py`:

```python
# ==============================================
# phase_debrief.py
# Post-interview debrief capture.
#
# Modes:
#   --init        Create a YAML draft pre-filled with role, stage, and date
#   --convert     Validate the YAML draft and write JSON output
#   --interactive Guided questionnaire with AI follow-up questions (A2)
#
# Output: data/debriefs/[role]/debrief_[stage]_[interview-date]_filed-[produced-date].json
#
# Usage:
#   python scripts/phase_debrief.py --role Viasat_SE_IS --stage hiring_manager --init
#   python scripts/phase_debrief.py --role Viasat_SE_IS --stage hiring_manager --convert
#   python scripts/phase_debrief.py --role Viasat_SE_IS --stage hiring_manager --interactive
# ==============================================

import os
import sys
import json
import argparse
from datetime import date

import yaml
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.utils.pii_filter import strip_pii

load_dotenv()

# ==============================================
# CONFIGURATION
# ==============================================

TEMPLATE_PATH = "docs/features/post-interview-debrief/interview_debrief_template.yaml"
DEBRIEFS_DIR = "data/debriefs"
MODEL = "claude-haiku-4-5-20251001"

VALID_STAGES = ["recruiter_screen", "hiring_manager", "panel", "final"]
VALID_FORMATS = ["phone", "video", "onsite"]
VALID_ASSESSMENTS = ["for_sure", "maybe", "doubt_it", "definitely_not"]
VALID_LANDED = ["yes", "partially", "no"]
VALID_RESPONSE_FELT = ["strong", "adequate", "weak"]
SALARY_FIELDS = ["range_given_min", "range_given_max", "candidate_anchor", "candidate_floor"]

# ==============================================
# ARGPARSE
# ==============================================

def build_parser():
    parser = argparse.ArgumentParser(description="Post-interview debrief capture")
    parser.add_argument("--role", required=True, help="Role slug (e.g. Viasat_SE_IS)")
    parser.add_argument(
        "--stage", required=True, choices=VALID_STAGES, help="Interview stage"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--init", action="store_true", default=False,
                      help="Create YAML draft")
    mode.add_argument("--convert", action="store_true", default=False,
                      help="Convert YAML draft to JSON")
    mode.add_argument("--interactive", action="store_true", default=False,
                      help="Guided questionnaire (A2)")
    return parser


# ==============================================
# MODE STUBS (implemented in later tasks)
# ==============================================

def run_init(role, stage, template_path, debriefs_dir):
    pass


def run_convert(role, stage, debriefs_dir):
    pass


def run_interactive(role, stage, debriefs_dir, client=None):
    pass


# ==============================================
# MAIN
# ==============================================

def main():
    args = build_parser().parse_args()
    if args.init:
        run_init(args.role, args.stage, TEMPLATE_PATH, DEBRIEFS_DIR)
    elif args.convert:
        run_convert(args.role, args.stage, DEBRIEFS_DIR)
    elif args.interactive:
        run_interactive(args.role, args.stage, DEBRIEFS_DIR)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_phase_debrief.py -v
```

Expected: 5 PASSED

- [ ] **Step 5: Commit**

```bash
git add scripts/phase_debrief.py tests/test_phase_debrief.py
git commit -m "Add phase_debrief.py skeleton with argparse"
```

---

## Task 3: Validation Helpers

**Files:**
- Modify: `scripts/phase_debrief.py`
- Modify: `tests/test_phase_debrief.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_phase_debrief.py`:

```python
import json

# ---- validate_required ----

def test_validate_required_all_present():
    data = {
        'metadata': {'interview_date': '2026-04-10', 'format': 'video'},
        'advancement_read': {'assessment': 'maybe'}
    }
    assert pd.validate_required(data) == []


def test_validate_required_missing_interview_date():
    data = {
        'metadata': {'interview_date': None, 'format': 'video'},
        'advancement_read': {'assessment': 'maybe'}
    }
    errors = pd.validate_required(data)
    assert 'interview_date: missing required value' in errors


def test_validate_required_missing_format():
    data = {
        'metadata': {'interview_date': '2026-04-10', 'format': None},
        'advancement_read': {'assessment': 'maybe'}
    }
    errors = pd.validate_required(data)
    assert 'format: missing required value' in errors


def test_validate_required_missing_assessment():
    data = {
        'metadata': {'interview_date': '2026-04-10', 'format': 'video'},
        'advancement_read': {'assessment': None}
    }
    errors = pd.validate_required(data)
    assert 'assessment: missing required value' in errors


def test_validate_required_all_missing():
    data = {
        'metadata': {'interview_date': None, 'format': None},
        'advancement_read': {'assessment': None}
    }
    assert len(pd.validate_required(data)) == 3


# ---- validate_enums ----

def test_validate_enums_all_valid():
    data = {
        'metadata': {'format': 'video'},
        'advancement_read': {'assessment': 'maybe'},
        'stories_used': [{'landed': 'yes'}, {'landed': 'partially'}],
        'gaps_surfaced': [{'response_felt': 'strong'}]
    }
    assert pd.validate_enums(data) == []


def test_validate_enums_invalid_format():
    data = {
        'metadata': {'format': 'zoom'},
        'advancement_read': {'assessment': 'maybe'},
        'stories_used': [],
        'gaps_surfaced': []
    }
    errors = pd.validate_enums(data)
    assert any("format" in e and "zoom" in e for e in errors)


def test_validate_enums_invalid_assessment():
    data = {
        'metadata': {'format': 'video'},
        'advancement_read': {'assessment': 'unsure'},
        'stories_used': [],
        'gaps_surfaced': []
    }
    errors = pd.validate_enums(data)
    assert any("assessment" in e and "unsure" in e for e in errors)


def test_validate_enums_invalid_landed():
    data = {
        'metadata': {'format': 'video'},
        'advancement_read': {'assessment': 'maybe'},
        'stories_used': [{'landed': 'kinda'}],
        'gaps_surfaced': []
    }
    errors = pd.validate_enums(data)
    assert any("landed" in e and "kinda" in e for e in errors)


def test_validate_enums_invalid_response_felt():
    data = {
        'metadata': {'format': 'video'},
        'advancement_read': {'assessment': 'maybe'},
        'stories_used': [],
        'gaps_surfaced': [{'response_felt': 'ok'}]
    }
    errors = pd.validate_enums(data)
    assert any("response_felt" in e and "ok" in e for e in errors)


def test_validate_enums_skips_null_values():
    # None values are handled by validate_required, not validate_enums
    data = {
        'metadata': {'format': None},
        'advancement_read': {'assessment': None},
        'stories_used': [{'landed': None}],
        'gaps_surfaced': [{'response_felt': None}]
    }
    assert pd.validate_enums(data) == []


# ---- cast_salary_fields ----

def test_cast_salary_fields_all_null():
    data = {'salary_exchange': {
        'range_given_min': None, 'range_given_max': None,
        'candidate_anchor': None, 'candidate_floor': None, 'notes': None
    }}
    result, errors = pd.cast_salary_fields(data)
    assert errors == []
    assert result['salary_exchange']['range_given_min'] is None


def test_cast_salary_fields_numeric_string():
    data = {'salary_exchange': {
        'range_given_min': '145000', 'range_given_max': None,
        'candidate_anchor': None, 'candidate_floor': None, 'notes': None
    }}
    result, errors = pd.cast_salary_fields(data)
    assert errors == []
    assert result['salary_exchange']['range_given_min'] == 145000
    assert isinstance(result['salary_exchange']['range_given_min'], int)


def test_cast_salary_fields_integer_passthrough():
    data = {'salary_exchange': {
        'range_given_min': 145000, 'range_given_max': None,
        'candidate_anchor': None, 'candidate_floor': None, 'notes': None
    }}
    result, errors = pd.cast_salary_fields(data)
    assert errors == []
    assert result['salary_exchange']['range_given_min'] == 145000


def test_cast_salary_fields_non_numeric():
    data = {'salary_exchange': {
        'range_given_min': 'competitive', 'range_given_max': None,
        'candidate_anchor': None, 'candidate_floor': None, 'notes': None
    }}
    result, errors = pd.cast_salary_fields(data)
    assert any("range_given_min" in e for e in errors)


# ---- build_output_filename ----

def test_build_output_filename():
    result = pd.build_output_filename('hiring_manager', '2026-04-10', '2026-04-13')
    assert result == 'debrief_hiring_manager_2026-04-10_filed-2026-04-13.json'


# ---- build_json_output ----

def _base_data():
    return {
        'metadata': {
            'role': 'TestRole', 'stage': 'hiring_manager', 'company': 'Viasat',
            'interviewer_name': None, 'interviewer_title': None,
            'interview_date': '2026-04-10', 'format': 'video',
            'produced_date': '2026-04-13'
        },
        'advancement_read': {'assessment': 'maybe', 'notes': None},
        'stories_used': [],
        'gaps_surfaced': [],
        'salary_exchange': {
            'range_given_min': None, 'range_given_max': None,
            'candidate_anchor': None, 'candidate_floor': None, 'notes': None
        },
        'what_i_said': None,
        'open_notes': None
    }


def test_build_json_output_all_top_level_keys_present():
    result = pd.build_json_output(_base_data())
    for key in ['metadata', 'advancement_read', 'stories_used',
                'gaps_surfaced', 'salary_exchange', 'what_i_said', 'open_notes']:
        assert key in result


def test_build_json_output_empty_lists():
    result = pd.build_json_output(_base_data())
    assert result['stories_used'] == []
    assert result['gaps_surfaced'] == []


def test_build_json_output_story_has_library_id():
    data = _base_data()
    data['stories_used'] = [
        {'tags': ['leadership'], 'framing': 'Led EO rewrite', 'landed': 'yes', 'library_id': None}
    ]
    result = pd.build_json_output(data)
    assert 'library_id' in result['stories_used'][0]
    assert result['stories_used'][0]['library_id'] is None


def test_build_json_output_salary_null_fields_present():
    result = pd.build_json_output(_base_data())
    for field in ['range_given_min', 'range_given_max', 'candidate_anchor',
                  'candidate_floor', 'notes']:
        assert field in result['salary_exchange']
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_phase_debrief.py -k "validate or cast or build" -v
```

Expected: FAILED -- functions not defined

- [ ] **Step 3: Implement the validation helpers**

Add to `scripts/phase_debrief.py` before the `run_init` stub:

```python
# ==============================================
# VALIDATION AND OUTPUT HELPERS
# ==============================================

def validate_required(data: dict) -> list:
    """Check that required fields are non-null. Returns list of error strings."""
    errors = []
    if not data.get('metadata', {}).get('interview_date'):
        errors.append('interview_date: missing required value')
    if not data.get('metadata', {}).get('format'):
        errors.append('format: missing required value')
    if not data.get('advancement_read', {}).get('assessment'):
        errors.append('assessment: missing required value')
    return errors


def validate_enums(data: dict) -> list:
    """Check that enum fields contain valid values. Skips null. Returns list of error strings."""
    errors = []
    fmt = data.get('metadata', {}).get('format')
    if fmt is not None and fmt not in VALID_FORMATS:
        errors.append(
            f"format: '{fmt}' is not valid. Accepted: {', '.join(VALID_FORMATS)}"
        )
    assessment = data.get('advancement_read', {}).get('assessment')
    if assessment is not None and assessment not in VALID_ASSESSMENTS:
        errors.append(
            f"assessment: '{assessment}' is not valid. Accepted: {', '.join(VALID_ASSESSMENTS)}"
        )
    for i, story in enumerate(data.get('stories_used', []) or []):
        landed = story.get('landed')
        if landed is not None and landed not in VALID_LANDED:
            errors.append(
                f"landed (story {i + 1}): '{landed}' is not valid. Accepted: {', '.join(VALID_LANDED)}"
            )
    for i, gap in enumerate(data.get('gaps_surfaced', []) or []):
        rf = gap.get('response_felt')
        if rf is not None and rf not in VALID_RESPONSE_FELT:
            errors.append(
                f"response_felt (gap {i + 1}): '{rf}' is not valid. Accepted: {', '.join(VALID_RESPONSE_FELT)}"
            )
    return errors


def cast_salary_fields(data: dict) -> tuple:
    """Cast salary fields to int. Returns (updated_data, list of error strings)."""
    errors = []
    salary = data.get('salary_exchange', {}) or {}
    updated = dict(salary)
    for field in SALARY_FIELDS:
        val = salary.get(field)
        if val is None:
            continue
        try:
            updated[field] = int(val)
        except (ValueError, TypeError):
            errors.append(f"{field}: expected a number, got '{val}'")
    result = dict(data)
    result['salary_exchange'] = updated
    return result, errors


def build_output_filename(stage: str, interview_date: str, produced_date: str) -> str:
    return f"debrief_{stage}_{interview_date}_filed-{produced_date}.json"


def build_json_output(data: dict) -> dict:
    """Build the canonical JSON output dict from validated data."""
    return {
        'metadata': {
            'role': data['metadata'].get('role'),
            'stage': data['metadata'].get('stage'),
            'company': data['metadata'].get('company'),
            'interviewer_name': data['metadata'].get('interviewer_name'),
            'interviewer_title': data['metadata'].get('interviewer_title'),
            'interview_date': data['metadata'].get('interview_date'),
            'format': data['metadata'].get('format'),
            'produced_date': data['metadata'].get('produced_date'),
        },
        'advancement_read': {
            'assessment': data['advancement_read'].get('assessment'),
            'notes': data['advancement_read'].get('notes'),
        },
        'stories_used': [
            {
                'tags': s.get('tags') or [],
                'framing': s.get('framing'),
                'landed': s.get('landed'),
                'library_id': s.get('library_id'),
            }
            for s in (data.get('stories_used') or [])
        ],
        'gaps_surfaced': [
            {
                'gap_label': g.get('gap_label'),
                'response_given': g.get('response_given'),
                'response_felt': g.get('response_felt'),
            }
            for g in (data.get('gaps_surfaced') or [])
        ],
        'salary_exchange': {
            'range_given_min': data.get('salary_exchange', {}).get('range_given_min'),
            'range_given_max': data.get('salary_exchange', {}).get('range_given_max'),
            'candidate_anchor': data.get('salary_exchange', {}).get('candidate_anchor'),
            'candidate_floor': data.get('salary_exchange', {}).get('candidate_floor'),
            'notes': data.get('salary_exchange', {}).get('notes'),
        },
        'what_i_said': data.get('what_i_said'),
        'open_notes': data.get('open_notes'),
    }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_phase_debrief.py -k "validate or cast or build" -v
```

Expected: All PASSED

- [ ] **Step 5: Commit**

```bash
git add scripts/phase_debrief.py tests/test_phase_debrief.py
git commit -m "Add validation helpers and JSON builder for phase_debrief"
```

---

## Task 4: `--init` Mode

**Files:**
- Modify: `scripts/phase_debrief.py`
- Modify: `tests/test_phase_debrief.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_phase_debrief.py`:

```python
import yaml
from datetime import date as date_type

MINIMAL_TEMPLATE = """
metadata:
  role: null
  stage: null
  company: null
  interviewer_name: null
  interviewer_title: null
  interview_date: null
  format: null
  produced_date: null
advancement_read:
  assessment: null
  notes: null
stories_used:
  - tags: []
    framing: null
    landed: null
    library_id: null
gaps_surfaced:
  - gap_label: null
    response_given: null
    response_felt: null
salary_exchange:
  range_given_min: null
  range_given_max: null
  candidate_anchor: null
  candidate_floor: null
  notes: null
what_i_said: null
open_notes: null
"""


def _make_template(tmp_path):
    t = tmp_path / "template.yaml"
    t.write_text(MINIMAL_TEMPLATE)
    return str(t)


def test_run_init_creates_role_directory(tmp_path):
    pd.run_init('TestRole', 'hiring_manager', _make_template(tmp_path), str(tmp_path))
    assert (tmp_path / 'TestRole').is_dir()


def test_run_init_creates_draft_file(tmp_path):
    pd.run_init('TestRole', 'hiring_manager', _make_template(tmp_path), str(tmp_path))
    assert (tmp_path / 'TestRole' / 'debrief_hiring_manager_draft.yaml').exists()


def test_run_init_prefills_role_stage_date(tmp_path):
    pd.run_init('TestRole', 'hiring_manager', _make_template(tmp_path), str(tmp_path))
    draft = tmp_path / 'TestRole' / 'debrief_hiring_manager_draft.yaml'
    with open(draft) as f:
        data = yaml.safe_load(f)
    assert data['metadata']['role'] == 'TestRole'
    assert data['metadata']['stage'] == 'hiring_manager'
    assert data['metadata']['produced_date'] == str(date_type.today())


def test_run_init_overwrite_confirmed(tmp_path, monkeypatch):
    template = _make_template(tmp_path)
    pd.run_init('TestRole', 'hiring_manager', template, str(tmp_path))
    monkeypatch.setattr('builtins.input', lambda _: 'y')
    pd.run_init('TestRole', 'hiring_manager', template, str(tmp_path))
    assert (tmp_path / 'TestRole' / 'debrief_hiring_manager_draft.yaml').exists()


def test_run_init_overwrite_cancelled_preserves_content(tmp_path, monkeypatch):
    template = _make_template(tmp_path)
    pd.run_init('TestRole', 'hiring_manager', template, str(tmp_path))
    draft = tmp_path / 'TestRole' / 'debrief_hiring_manager_draft.yaml'
    draft.write_text("sentinel content")
    monkeypatch.setattr('builtins.input', lambda _: 'n')
    pd.run_init('TestRole', 'hiring_manager', template, str(tmp_path))
    assert draft.read_text() == "sentinel content"


def test_run_init_prints_draft_path(tmp_path, capsys):
    pd.run_init('TestRole', 'hiring_manager', _make_template(tmp_path), str(tmp_path))
    captured = capsys.readouterr()
    assert 'debrief_hiring_manager_draft.yaml' in captured.out
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_phase_debrief.py -k "run_init" -v
```

Expected: FAILED -- `run_init` is a stub returning None

- [ ] **Step 3: Implement `run_init`**

Replace the `run_init` stub in `scripts/phase_debrief.py`:

```python
def run_init(role, stage, template_path, debriefs_dir):
    role_dir = os.path.join(debriefs_dir, role)
    os.makedirs(role_dir, exist_ok=True)
    draft_path = os.path.join(role_dir, f"debrief_{stage}_draft.yaml")
    if os.path.exists(draft_path):
        response = input(
            f"Draft already exists at {draft_path}. Overwrite? (y/n): "
        ).strip().lower()
        if response != 'y':
            print("Cancelled. Existing draft preserved.")
            return
    with open(template_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    data['metadata']['role'] = role
    data['metadata']['stage'] = stage
    data['metadata']['produced_date'] = str(date.today())
    with open(draft_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    print(f"Draft created at {draft_path}")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_phase_debrief.py -k "run_init" -v
```

Expected: 6 PASSED

- [ ] **Step 5: Commit**

```bash
git add scripts/phase_debrief.py tests/test_phase_debrief.py
git commit -m "Implement --init mode for phase_debrief"
```

---

## Task 5: `--convert` Mode

**Files:**
- Modify: `scripts/phase_debrief.py`
- Modify: `tests/test_phase_debrief.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_phase_debrief.py`:

```python
VALID_FILLED_YAML = """
metadata:
  role: TestRole
  stage: hiring_manager
  company: Viasat
  interviewer_name: Jane Smith
  interviewer_title: Director
  interview_date: '2026-04-10'
  format: video
  produced_date: '2026-04-13'
advancement_read:
  assessment: maybe
  notes: Felt strong overall.
stories_used:
  - tags: [leadership]
    framing: Led EO rewrite
    landed: yes
    library_id: null
gaps_surfaced:
  - gap_label: no SCIF experience
    response_given: Acknowledged and redirected
    response_felt: adequate
salary_exchange:
  range_given_min: 145000
  range_given_max: 165000
  candidate_anchor: null
  candidate_floor: null
  notes: null
what_i_said: Cited 12 years experience.
open_notes: null
"""


def _write_draft(debriefs_dir, role, stage, content):
    role_dir = os.path.join(str(debriefs_dir), role)
    os.makedirs(role_dir, exist_ok=True)
    draft_path = os.path.join(role_dir, f"debrief_{stage}_draft.yaml")
    with open(draft_path, 'w') as f:
        f.write(content)


def test_run_convert_happy_path(tmp_path):
    _write_draft(tmp_path, 'TestRole', 'hiring_manager', VALID_FILLED_YAML)
    pd.run_convert('TestRole', 'hiring_manager', str(tmp_path))
    output = tmp_path / 'TestRole' / 'debrief_hiring_manager_2026-04-10_filed-2026-04-13.json'
    assert output.exists()
    with open(output) as f:
        data = json.load(f)
    assert data['metadata']['role'] == 'TestRole'
    assert data['advancement_read']['assessment'] == 'maybe'
    assert data['stories_used'][0]['landed'] == 'yes'
    assert data['salary_exchange']['range_given_min'] == 145000
    assert isinstance(data['salary_exchange']['range_given_min'], int)


def test_run_convert_missing_interview_date(tmp_path, capsys):
    content = VALID_FILLED_YAML.replace("interview_date: '2026-04-10'", "interview_date: null")
    _write_draft(tmp_path, 'TestRole', 'hiring_manager', content)
    with pytest.raises(SystemExit):
        pd.run_convert('TestRole', 'hiring_manager', str(tmp_path))
    assert 'interview_date: missing required value' in capsys.readouterr().out


def test_run_convert_invalid_format(tmp_path, capsys):
    content = VALID_FILLED_YAML.replace("format: video", "format: zoom")
    _write_draft(tmp_path, 'TestRole', 'hiring_manager', content)
    with pytest.raises(SystemExit):
        pd.run_convert('TestRole', 'hiring_manager', str(tmp_path))
    assert 'zoom' in capsys.readouterr().out


def test_run_convert_non_numeric_salary(tmp_path, capsys):
    content = VALID_FILLED_YAML.replace("range_given_min: 145000", "range_given_min: competitive")
    _write_draft(tmp_path, 'TestRole', 'hiring_manager', content)
    with pytest.raises(SystemExit):
        pd.run_convert('TestRole', 'hiring_manager', str(tmp_path))
    assert 'range_given_min' in capsys.readouterr().out


def test_run_convert_no_partial_write(tmp_path):
    content = VALID_FILLED_YAML.replace("interview_date: '2026-04-10'", "interview_date: null")
    _write_draft(tmp_path, 'TestRole', 'hiring_manager', content)
    with pytest.raises(SystemExit):
        pd.run_convert('TestRole', 'hiring_manager', str(tmp_path))
    assert list((tmp_path / 'TestRole').glob('*.json')) == []


def test_run_convert_missing_draft_message(tmp_path, capsys):
    with pytest.raises(SystemExit):
        pd.run_convert('TestRole', 'hiring_manager', str(tmp_path))
    assert '--init' in capsys.readouterr().out


def test_run_convert_validation_failed_message(tmp_path, capsys):
    content = VALID_FILLED_YAML.replace("interview_date: '2026-04-10'", "interview_date: null")
    _write_draft(tmp_path, 'TestRole', 'hiring_manager', content)
    with pytest.raises(SystemExit):
        pd.run_convert('TestRole', 'hiring_manager', str(tmp_path))
    assert 'Validation failed' in capsys.readouterr().out


def test_run_convert_success_message(tmp_path, capsys):
    _write_draft(tmp_path, 'TestRole', 'hiring_manager', VALID_FILLED_YAML)
    pd.run_convert('TestRole', 'hiring_manager', str(tmp_path))
    assert 'Debrief saved to' in capsys.readouterr().out
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_phase_debrief.py -k "run_convert" -v
```

Expected: FAILED -- `run_convert` is a stub

- [ ] **Step 3: Implement `run_convert`**

Replace the `run_convert` stub in `scripts/phase_debrief.py`:

```python
def run_convert(role, stage, debriefs_dir):
    draft_path = os.path.join(debriefs_dir, role, f"debrief_{stage}_draft.yaml")
    if not os.path.exists(draft_path):
        print(f"No draft found at {draft_path}. Run --init first.")
        sys.exit(1)
    with open(draft_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    errors = []
    errors.extend(validate_required(data))
    errors.extend(validate_enums(data))
    data, salary_errors = cast_salary_fields(data)
    errors.extend(salary_errors)
    if errors:
        for err in errors:
            print(err)
        print("Validation failed -- no file written. Fix the above and re-run --convert.")
        sys.exit(1)
    output = build_json_output(data)
    interview_date = data['metadata']['interview_date']
    produced_date = data['metadata']['produced_date']
    filename = build_output_filename(stage, interview_date, produced_date)
    output_path = os.path.join(debriefs_dir, role, filename)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Debrief saved to {output_path}")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_phase_debrief.py -k "run_convert" -v
```

Expected: All PASSED

- [ ] **Step 5: Manual smoke test of the full A1 workflow**

```bash
python scripts/phase_debrief.py --role Smoke_Test --stage hiring_manager --init
# Edit data/debriefs/Smoke_Test/debrief_hiring_manager_draft.yaml:
#   set interview_date: '2026-04-10'
#   set format: video
#   set assessment: maybe
python scripts/phase_debrief.py --role Smoke_Test --stage hiring_manager --convert
# Verify: data/debriefs/Smoke_Test/debrief_hiring_manager_2026-04-10_filed-<today>.json exists
```

- [ ] **Step 6: Commit**

```bash
git add scripts/phase_debrief.py tests/test_phase_debrief.py
git commit -m "Implement --convert mode for phase_debrief"
```

---

## Task 6: `--interactive` Questionnaire (A2, no AI yet)

**Note:** `run_interactive` calls `get_followup_question` (defined in Task 7). All calls are guarded by `if client:`, and Task 6 tests always pass `client=None`, so the guard prevents any call to the undefined function. Task 7 adds the implementation.

**Files:**
- Modify: `scripts/phase_debrief.py`
- Modify: `tests/test_phase_debrief.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_phase_debrief.py`:

```python
def _make_inputs(*args):
    """Return a callable that iterates through the provided input sequence."""
    it = iter(args)
    return lambda _: next(it)


def _default_inputs():
    """Full valid input sequence for a single-story, single-gap session."""
    return _make_inputs(
        'Viasat',           # company
        'Jane Smith',        # interviewer_name
        'Director',          # interviewer_title
        '2026-04-10',        # interview_date
        'video',             # format
        'maybe',             # assessment
        'Felt strong.',      # assessment notes
        # story 1
        'leadership',        # tags
        'Led EO rewrite',    # framing
        'yes',               # landed
        'n',                 # add another story?
        # gap 1
        'no SCIF exp',       # gap_label
        'acknowledged gap',  # response_given
        'adequate',          # response_felt
        'n',                 # add another gap?
        # salary (all skipped)
        '', '', '', '', '',
        # what_i_said
        'Cited 12 years.',
        # open_notes
        '',
    )


def test_run_interactive_creates_json(tmp_path, monkeypatch):
    monkeypatch.setattr('builtins.input', _default_inputs())
    pd.run_interactive('TestRole', 'hiring_manager', str(tmp_path), client=None)
    assert len(list((tmp_path / 'TestRole').glob('*.json'))) == 1


def test_run_interactive_json_content(tmp_path, monkeypatch):
    monkeypatch.setattr('builtins.input', _default_inputs())
    pd.run_interactive('TestRole', 'hiring_manager', str(tmp_path), client=None)
    output_file = list((tmp_path / 'TestRole').glob('*.json'))[0]
    with open(output_file) as f:
        data = json.load(f)
    assert data['metadata']['company'] == 'Viasat'
    assert data['advancement_read']['assessment'] == 'maybe'
    assert len(data['stories_used']) == 1
    assert data['stories_used'][0]['landed'] == 'yes'
    assert data['stories_used'][0]['library_id'] is None
    assert len(data['gaps_surfaced']) == 1
    assert data['what_i_said'] == 'Cited 12 years.'


def test_run_interactive_enum_reprompt(tmp_path, monkeypatch):
    monkeypatch.setattr('builtins.input', _make_inputs(
        'Viasat', 'Jane', 'Dir', '2026-04-10',
        'zoom',    # invalid format -- should reprompt
        'video',   # valid
        'maybe', 'Notes.',
        'leadership', 'framing', 'yes', 'n',
        'no SCIF', 'response', 'adequate', 'n',
        '', '', '', '', '',
        'Said something.',
        '',
    ))
    pd.run_interactive('TestRole', 'hiring_manager', str(tmp_path), client=None)
    output_file = list((tmp_path / 'TestRole').glob('*.json'))[0]
    with open(output_file) as f:
        data = json.load(f)
    assert data['metadata']['format'] == 'video'


def test_run_interactive_multiple_stories(tmp_path, monkeypatch):
    monkeypatch.setattr('builtins.input', _make_inputs(
        'Viasat', 'Jane', 'Dir', '2026-04-10', 'video', 'maybe', '',
        # story 1
        'leadership', 'Led EO rewrite', 'yes',
        'y',           # add another story
        # story 2
        'cross-functional', 'Built stakeholder map', 'partially',
        'n',
        # gap
        'gap', 'response', 'strong', 'n',
        '', '', '', '', '',
        '',
        '',
    ))
    pd.run_interactive('TestRole', 'hiring_manager', str(tmp_path), client=None)
    output_file = list((tmp_path / 'TestRole').glob('*.json'))[0]
    with open(output_file) as f:
        data = json.load(f)
    assert len(data['stories_used']) == 2


def test_run_interactive_ctrl_c_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr('builtins.input', lambda _: (_ for _ in ()).throw(KeyboardInterrupt()))
    with pytest.raises(SystemExit) as exc:
        pd.run_interactive('TestRole', 'hiring_manager', str(tmp_path), client=None)
    assert exc.value.code == 0
    assert list(tmp_path.glob('**/*.json')) == []


def test_run_interactive_draft_conflict_warning(tmp_path, monkeypatch, capsys):
    (tmp_path / 'TestRole').mkdir()
    (tmp_path / 'TestRole' / 'debrief_hiring_manager_draft.yaml').write_text('existing')
    monkeypatch.setattr('builtins.input', _make_inputs(
        'y',            # confirm conflict warning
        'Viasat', 'Jane', 'Dir', '2026-04-10', 'video', 'maybe', '',
        'leadership', 'framing', 'yes', 'n',
        'gap', 'response', 'adequate', 'n',
        '', '', '', '', '',
        '',
        '',
    ))
    pd.run_interactive('TestRole', 'hiring_manager', str(tmp_path), client=None)
    assert 'draft already exists' in capsys.readouterr().out.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_phase_debrief.py -k "run_interactive" -v
```

Expected: FAILED -- `run_interactive` is a stub

- [ ] **Step 3: Add input helper functions**

Add to `scripts/phase_debrief.py` before `run_interactive`:

```python
def _prompt_enum(prompt_text, valid_values):
    """Loop until user enters a valid enum value."""
    while True:
        val = input(f"{prompt_text} ({'/'.join(valid_values)}): ").strip()
        if val in valid_values:
            return val
        print(f"  Invalid -- accepted values: {', '.join(valid_values)}")


def _prompt_optional(prompt_text):
    """Return None if user enters nothing, otherwise return stripped string."""
    val = input(f"{prompt_text} (press Enter to skip): ").strip()
    return val if val else None


def _prompt_optional_int(prompt_text):
    """Return None if skipped, int if valid, loops on invalid non-empty input."""
    while True:
        raw = input(f"{prompt_text} (press Enter to skip): ").strip()
        if not raw:
            return None
        try:
            return int(raw)
        except ValueError:
            print("  Expected a number. Try again or press Enter to skip.")
```

- [ ] **Step 4: Implement `run_interactive`**

Replace the `run_interactive` stub in `scripts/phase_debrief.py`:

```python
def run_interactive(role, stage, debriefs_dir, client=None):
    try:
        draft_path = os.path.join(debriefs_dir, role, f"debrief_{stage}_draft.yaml")
        if os.path.exists(draft_path):
            response = input(
                f"A draft already exists for {role}/{stage}. "
                f"--interactive will create a separate JSON output and will not use the draft. "
                f"Continue? (y/n): "
            ).strip().lower()
            if response != 'y':
                print("Cancelled.")
                sys.exit(0)

        print(f"\n=== Post-Interview Debrief: {role} / {stage} ===\n")

        # -- metadata --
        print("-- Interview Details --")
        company = _prompt_optional("Company")
        interviewer_name = _prompt_optional("Interviewer name")
        interviewer_title = _prompt_optional("Interviewer title")
        interview_date = input("Interview date (YYYY-MM-DD): ").strip()
        fmt = _prompt_enum("Format", VALID_FORMATS)
        produced_date = str(date.today())

        # -- advancement_read --
        print("\n-- Advancement Read --")
        assessment = _prompt_enum("Assessment", VALID_ASSESSMENTS)
        assessment_notes = _prompt_optional("Notes")
        if client:
            followup = get_followup_question(
                client, 'advancement_read', f"assessment: {assessment}. notes: {assessment_notes}"
            )
            if followup:
                extra = input(f"  {followup} ").strip()
                if extra:
                    assessment_notes = f"{assessment_notes or ''}. Follow-up: {extra}".strip('. ')

        # -- stories_used --
        print("\n-- Stories Used --")
        stories = []
        while True:
            print(f"  Story {len(stories) + 1}:")
            tags_raw = input("    Tags (comma-separated, e.g. leadership,cross-functional): ").strip()
            tags = [t.strip() for t in tags_raw.split(',') if t.strip()] if tags_raw else []
            framing = input("    How was it framed? ").strip() or None
            landed = _prompt_enum("    Landed", VALID_LANDED)
            stories.append({'tags': tags, 'framing': framing, 'landed': landed, 'library_id': None})
            if input("  Add another story? (y/n): ").strip().lower() != 'y':
                break
        if client and stories:
            followup = get_followup_question(
                client, 'stories_used', '; '.join(s.get('framing') or '' for s in stories)
            )
            if followup:
                input(f"  {followup} ")

        # -- gaps_surfaced --
        print("\n-- Gaps Surfaced --")
        gaps = []
        while True:
            print(f"  Gap {len(gaps) + 1}:")
            gap_label = input("    Gap label: ").strip() or None
            response_given = input("    How did you respond? ").strip() or None
            response_felt = _prompt_enum("    Response felt", VALID_RESPONSE_FELT)
            gaps.append({
                'gap_label': gap_label,
                'response_given': response_given,
                'response_felt': response_felt
            })
            if input("  Add another gap? (y/n): ").strip().lower() != 'y':
                break
        if client and gaps:
            followup = get_followup_question(
                client, 'gaps_surfaced', '; '.join(g.get('gap_label') or '' for g in gaps)
            )
            if followup:
                input(f"  {followup} ")

        # -- salary_exchange --
        print("\n-- Salary Exchange (all optional) --")
        range_min = _prompt_optional_int("Range given -- minimum")
        range_max = _prompt_optional_int("Range given -- maximum")
        anchor = _prompt_optional_int("Your anchor (if provided)")
        floor = _prompt_optional_int("Your floor (if disclosed)")
        salary_notes = _prompt_optional("Salary notes")
        if client:
            followup = get_followup_question(
                client, 'salary_exchange',
                f"min={range_min}, max={range_max}, anchor={anchor}, floor={floor}"
            )
            if followup:
                input(f"  {followup} ")

        # -- what_i_said --
        print("\n-- Continuity: What I Said --")
        what_i_said = _prompt_optional("Claims, commitments, or framings to stay consistent on")
        if client and what_i_said:
            followup = get_followup_question(client, 'what_i_said', what_i_said)
            if followup:
                extra = input(f"  {followup} ").strip()
                if extra:
                    what_i_said = f"{what_i_said}. {extra}"

        # -- open_notes --
        print("\n-- Open Notes --")
        open_notes = _prompt_optional("Anything else worth capturing")

        data = {
            'metadata': {
                'role': role, 'stage': stage, 'company': company,
                'interviewer_name': interviewer_name, 'interviewer_title': interviewer_title,
                'interview_date': interview_date, 'format': fmt,
                'produced_date': produced_date,
            },
            'advancement_read': {'assessment': assessment, 'notes': assessment_notes},
            'stories_used': stories,
            'gaps_surfaced': gaps,
            'salary_exchange': {
                'range_given_min': range_min, 'range_given_max': range_max,
                'candidate_anchor': anchor, 'candidate_floor': floor, 'notes': salary_notes,
            },
            'what_i_said': what_i_said,
            'open_notes': open_notes,
        }

        errors = validate_required(data)
        errors.extend(validate_enums(data))
        if errors:
            for err in errors:
                print(err)
            print("Validation failed -- no file written. Fix the above and re-run --interactive.")
            sys.exit(1)

        output = build_json_output(data)
        os.makedirs(os.path.join(debriefs_dir, role), exist_ok=True)
        filename = build_output_filename(stage, interview_date, produced_date)
        output_path = os.path.join(debriefs_dir, role, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"\nDebrief saved to {output_path}")

    except KeyboardInterrupt:
        sys.exit(0)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_phase_debrief.py -k "run_interactive" -v
```

Expected: All PASSED

- [ ] **Step 6: Commit**

```bash
git add scripts/phase_debrief.py tests/test_phase_debrief.py
git commit -m "Implement --interactive questionnaire for phase_debrief (A2)"
```

---

## Task 7: AI Follow-up Integration

**Files:**
- Modify: `scripts/phase_debrief.py`
- Modify: `tests/test_phase_debrief.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_phase_debrief.py`:

```python
from unittest.mock import MagicMock


def test_get_followup_question_returns_question():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="What was the most challenging moment?")]
    )
    result = pd.get_followup_question(mock_client, 'advancement_read', 'assessment: maybe')
    assert result == "What was the most challenging moment?"


def test_get_followup_question_returns_empty():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="")]
    )
    result = pd.get_followup_question(mock_client, 'stories_used', 'Led EO rewrite')
    assert result == ""


def test_get_followup_question_strips_whitespace():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="  Was salary discussed?  ")]
    )
    result = pd.get_followup_question(mock_client, 'salary_exchange', 'min=145000')
    assert result == "Was salary discussed?"


def test_run_interactive_with_client_calls_followup(tmp_path, monkeypatch):
    mock_client = MagicMock()
    # Return a question for every section
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="What would you do differently?")]
    )
    monkeypatch.setattr('builtins.input', _make_inputs(
        'Viasat', 'Jane', 'Dir', '2026-04-10', 'video',
        'maybe', 'Felt strong.',
        'follow-up answer for advancement_read',
        'leadership', 'Led EO rewrite', 'yes', 'n',
        'follow-up answer for stories_used',
        'no SCIF exp', 'acknowledged', 'adequate', 'n',
        'follow-up answer for gaps_surfaced',
        '', '', '', '', '',
        'follow-up answer for salary_exchange',
        'Cited 12 years.',
        'follow-up answer for what_i_said',
        '',
    ))
    pd.run_interactive('TestRole', 'hiring_manager', str(tmp_path), client=mock_client)
    assert mock_client.messages.create.called


def test_run_interactive_client_none_no_followup(tmp_path, monkeypatch):
    # client=None should complete with no AI calls -- default_inputs has no extra answers
    monkeypatch.setattr('builtins.input', _default_inputs())
    pd.run_interactive('TestRole', 'hiring_manager', str(tmp_path), client=None)
    assert len(list((tmp_path / 'TestRole').glob('*.json'))) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_phase_debrief.py -k "followup or with_client or client_none" -v
```

Expected: FAILED -- `get_followup_question` not defined

- [ ] **Step 3: Add the Anthropic import and follow-up function**

Add to the imports section at the top of `scripts/phase_debrief.py`:

```python
from anthropic import Anthropic
```

Add the system prompt constant and `get_followup_question` function after the CONFIGURATION block:

```python
FOLLOWUP_SYSTEM_PROMPT = (
    "You are a debrief assistant. Given a candidate's response to a post-interview "
    "debrief section, decide if one targeted follow-up question would capture something "
    "valuable. If yes, return the question only. If no, return nothing. "
    "Do not assess, score, or infer anything about the interview outcome."
)


def get_followup_question(client, section_name: str, response: str) -> str:
    """Call Claude to decide if a follow-up question is warranted. Returns question or empty string."""
    user_content = f"Section: {section_name}\nResponse: {strip_pii(response)}"
    message = client.messages.create(
        model=MODEL,
        max_tokens=256,
        system=FOLLOWUP_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}]
    )
    return message.content[0].text.strip()
```

- [ ] **Step 4: Wire Anthropic client into `main()`**

Update `main()` in `scripts/phase_debrief.py`:

```python
def main():
    args = build_parser().parse_args()
    if args.init:
        run_init(args.role, args.stage, TEMPLATE_PATH, DEBRIEFS_DIR)
    elif args.convert:
        run_convert(args.role, args.stage, DEBRIEFS_DIR)
    elif args.interactive:
        client = Anthropic()
        run_interactive(args.role, args.stage, DEBRIEFS_DIR, client=client)
```

- [ ] **Step 5: Run the full test suite**

```bash
pytest tests/test_phase_debrief.py -v
```

Expected: All PASSED

- [ ] **Step 6: Run syntax check**

```bash
python -m py_compile scripts/phase_debrief.py && echo "OK"
```

Expected: `OK`

- [ ] **Step 7: Commit**

```bash
git add scripts/phase_debrief.py tests/test_phase_debrief.py
git commit -m "Add AI follow-up integration to --interactive mode (A2)"
```

---

## Self-Review

**Spec coverage:**
- YAML template at correct path -- Task 1
- `--role` / `--stage` args, mutually exclusive modes -- Task 2
- `--init` creates pre-populated draft, overwrite warning with exact message, prints path -- Task 4
- `--convert` validates required fields, enum fields, salary casting, no partial writes, missing draft message, success message -- Tasks 3 + 5
- All verbatim terminal messages -- Tasks 4 + 5
- `--interactive` questionnaire with enum re-prompting, multi-entry list sections -- Task 6
- Draft conflict warning on `--interactive` launch -- Task 6
- Ctrl-C discards silently, no file written, exit code 0 -- Task 6
- AI follow-up one per section, returns question or empty, never chained -- Task 7
- `strip_pii()` called before Claude API call -- Task 7
- JSON schema: all fields present when null, salary as int, `stories_used`/`gaps_surfaced` always arrays, `library_id` on every story -- Tasks 3 + 5

**Placeholder scan:** No TBD, TODO, or vague steps. All code blocks contain complete implementation. All terminal messages match the spec verbatim.

**Type consistency:**
- `build_json_output(data)` defined in Task 3, called in Tasks 5 and 6 with same signature
- `get_followup_question(client, section_name, response)` defined in Task 7, called in Task 6 guarded by `if client:` -- no call occurs when `client=None`, so all Task 6 tests pass before Task 7 is implemented
- `_prompt_enum`, `_prompt_optional`, `_prompt_optional_int` defined in Task 6 Step 3, called in Task 6 Step 4 `run_interactive`
- `VALID_STAGES`, `VALID_FORMATS`, etc. defined in Task 2 skeleton, referenced consistently in Tasks 3, 6, 7
