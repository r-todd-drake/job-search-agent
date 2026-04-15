# Post-Interview Debrief Amendment -- Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Amend `phase5_debrief.py` and its template to replace flat `interviewer_name`/`interviewer_title` fields with an `interviewers` array, add a `--panel_label` CLI argument, and update the output filename pattern accordingly.

**Architecture:** Three tightly coupled changes to one script, one template, and one test file. TDD order: write 6 failing tests first, implement the script changes, then update fixtures so all 57 tests pass. The 51 existing tests are the regression baseline -- all must continue to pass.

**Tech Stack:** Python 3, PyYAML, argparse, pytest, Anthropic SDK

---

## Files Modified

| File | Change |
|---|---|
| `templates/interview_debrief_template.yaml` | Replace `interviewer_name`/`interviewer_title` with `panel_label` + `interviewers` array |
| `scripts/phase5_debrief.py` | `build_parser`, `build_output_filename`, new `validate_interviewers`, `build_json_output`, `run_init`, `run_convert`, `run_interactive`, `main` |
| `tests/test_phase5_debrief.py` | 6 new tests + updated `MINIMAL_TEMPLATE`, `VALID_FILLED_YAML`, `UNQUOTED_DATES_YAML`, `_base_data()`, `_default_inputs()`, and 4 inline `_make_inputs` sequences |

---

### Task 1: Update YAML template

**Files:**
- Modify: `templates/interview_debrief_template.yaml`

- [ ] **Step 1: Overwrite template with amended content**

Replace the entire file with:

```yaml
# Post-Interview Debrief
# Fill in all fields. Leave optional fields as null if not applicable.

metadata:
  role: null                     # pre-filled by --init
  stage: null                    # pre-filled by --init
  panel_label: null              # optional -- e.g. "se_team" or "business_leaders"
  company: null                  # e.g. "Viasat"
  interviewers:
    - name: null
      title: null
      notes: null                # questions asked, background, programs mentioned, shared experiences
  interview_date: null           # YYYY-MM-DD -- drives output filename
  format: null                   # phone | video | onsite
  produced_date: null            # pre-filled by --init

advancement_read:
  assessment: null               # for_sure | maybe | doubt_it | definitely_not
  notes: null

stories_used:
  - tags: []                     # e.g. [leadership, cross-functional]
    framing: null                # brief description of how it was told
    landed: null                 # 'yes' | partially | 'no' -- quote yes/no to avoid YAML boolean parsing
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

- [ ] **Step 2: Verify the file reads correctly**

```bash
python -c "import yaml; d = yaml.safe_load(open('templates/interview_debrief_template.yaml')); print(d['metadata'].keys())"
```

Expected output includes: `dict_keys(['role', 'stage', 'panel_label', 'company', 'interviewers', 'interview_date', 'format', 'produced_date'])`

---

### Task 2: Write 6 failing tests (TDD red phase)

**Files:**
- Modify: `tests/test_phase5_debrief.py`

- [ ] **Step 1: Append the following block to the end of `tests/test_phase5_debrief.py`**

```python
# ---- Amendment tests: interviewers array, panel_label, filename pattern ----

# New YAML constant with amended schema -- used for validation rejection tests
# before VALID_FILLED_YAML is updated.
AMENDED_VALID_YAML = """
metadata:
  role: TestRole
  stage: hiring_manager
  panel_label: null
  company: Viasat
  interviewers:
    - name: Jane Smith
      title: Director
      notes: null
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


def test_single_interviewer_in_output():
    data = _base_data()
    result = pd.build_json_output(data)
    assert len(result['metadata']['interviewers']) == 1
    assert result['metadata']['interviewers'][0]['name'] == 'Jane Smith'
    assert result['metadata']['interviewers'][0]['title'] == 'Director'
    assert result['metadata']['interviewers'][0]['notes'] is None


def test_multiple_interviewers_in_output():
    data = _base_data()
    data['metadata']['interviewers'] = [
        {'name': 'Jane Smith', 'title': 'Director', 'notes': 'Asked about MBSE'},
        {'name': 'Bob Jones', 'title': 'Senior SE', 'notes': 'Mentioned interface pain points'},
    ]
    result = pd.build_json_output(data)
    assert len(result['metadata']['interviewers']) == 2
    assert result['metadata']['interviewers'][0]['name'] == 'Jane Smith'
    assert result['metadata']['interviewers'][1]['name'] == 'Bob Jones'
    assert result['metadata']['interviewers'][1]['notes'] == 'Mentioned interface pain points'


def test_panel_label_present_in_metadata_and_filename():
    filename = pd.build_output_filename('panel', '2026-04-20', '2026-04-20', panel_label='se_team')
    assert filename == 'debrief_panel_se_team_2026-04-20_filed-2026-04-20.json'
    data = _base_data()
    data['metadata']['panel_label'] = 'se_team'
    output = pd.build_json_output(data)
    assert output['metadata']['panel_label'] == 'se_team'


def test_panel_label_absent_in_metadata_and_filename():
    filename = pd.build_output_filename('panel', '2026-04-20', '2026-04-20')
    assert filename == 'debrief_panel_2026-04-20_filed-2026-04-20.json'
    data = _base_data()
    output = pd.build_json_output(data)
    assert output['metadata']['panel_label'] is None


def test_run_convert_rejects_empty_interviewers(tmp_path, capsys):
    content = AMENDED_VALID_YAML.replace(
        '  interviewers:\n    - name: Jane Smith\n      title: Director\n      notes: null',
        '  interviewers: []'
    )
    _write_draft(tmp_path, 'TestRole', 'hiring_manager', content)
    with pytest.raises(SystemExit):
        pd.run_convert('TestRole', 'hiring_manager', str(tmp_path))
    assert 'interviewers' in capsys.readouterr().out


def test_run_convert_rejects_all_null_interviewer_names(tmp_path, capsys):
    content = AMENDED_VALID_YAML.replace(
        '    - name: Jane Smith',
        '    - name: null'
    )
    _write_draft(tmp_path, 'TestRole', 'hiring_manager', content)
    with pytest.raises(SystemExit):
        pd.run_convert('TestRole', 'hiring_manager', str(tmp_path))
    assert 'interviewers' in capsys.readouterr().out
```

- [ ] **Step 2: Run the new tests to confirm they fail**

```bash
cd /c/Users/r_tod/Documents/Projects/Job_search_agent && python -m pytest tests/test_phase5_debrief.py -k "test_single_interviewer or test_multiple_interviewers or test_panel_label or test_run_convert_rejects" -v 2>&1 | tail -20
```

Expected: all 6 fail (FAILED or ERROR) -- this confirms the red phase is working.

---

### Task 3: Update `build_parser` and `build_output_filename`

**Files:**
- Modify: `scripts/phase5_debrief.py`

- [ ] **Step 1: Add `--panel_label` argument to `build_parser`**

In `build_parser()`, add this line after the `--stage` argument and before `mode = parser.add_mutually_exclusive_group(...)`:

```python
    parser.add_argument(
        "--panel_label", default=None,
        help="Panel label for multi-panel sessions (e.g. se_team)"
    )
```

- [ ] **Step 2: Update `build_output_filename` to accept `panel_label`**

Replace:

```python
def build_output_filename(stage: str, interview_date: str, produced_date: str) -> str:
    return f"debrief_{stage}_{interview_date}_filed-{produced_date}.json"
```

With:

```python
def build_output_filename(stage: str, interview_date: str, produced_date: str, panel_label: str = None) -> str:
    if panel_label:
        return f"debrief_{stage}_{panel_label}_{interview_date}_filed-{produced_date}.json"
    return f"debrief_{stage}_{interview_date}_filed-{produced_date}.json"
```

- [ ] **Step 3: Run `test_build_output_filename` and the two panel_label filename tests**

```bash
cd /c/Users/r_tod/Documents/Projects/Job_search_agent && python -m pytest tests/test_phase5_debrief.py -k "test_build_output_filename or test_panel_label" -v 2>&1 | tail -15
```

Expected: `test_build_output_filename` (existing) passes. `test_panel_label_present_in_metadata_and_filename` and `test_panel_label_absent_in_metadata_and_filename` still fail (build_json_output not updated yet) -- that is expected.

---

### Task 4: Add `validate_interviewers` and update `build_json_output`

**Files:**
- Modify: `scripts/phase5_debrief.py`

- [ ] **Step 1: Add `validate_interviewers` after `validate_enums`**

Insert this function after the `validate_enums` function (around line 129):

```python
def validate_interviewers(data: dict) -> list:
    """Check that interviewers array has at least one entry with a non-null name. Returns list of error strings."""
    interviewers = data.get('metadata', {}).get('interviewers') or []
    if not interviewers or not any(i.get('name') for i in interviewers):
        return ['interviewers: at least one interviewer with a non-null name is required']
    return []
```

- [ ] **Step 2: Update `build_json_output` to use `interviewers` array and `panel_label`**

Replace the entire `build_json_output` function with:

```python
def build_json_output(data: dict) -> dict:
    """Build the canonical JSON output dict from validated data."""
    interviewers = data.get('metadata', {}).get('interviewers') or []
    return {
        'metadata': {
            'role': data['metadata'].get('role'),
            'stage': data['metadata'].get('stage'),
            'panel_label': data['metadata'].get('panel_label'),
            'company': data['metadata'].get('company'),
            'interviewers': [
                {
                    'name': i.get('name'),
                    'title': i.get('title'),
                    'notes': i.get('notes'),
                }
                for i in interviewers
            ],
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

- [ ] **Step 3: Update `_base_data()` in the test file to use the new schema**

Replace the existing `_base_data` function in `tests/test_phase5_debrief.py` with:

```python
def _base_data():
    return {
        'metadata': {
            'role': 'TestRole', 'stage': 'hiring_manager', 'panel_label': None,
            'company': 'Viasat',
            'interviewers': [{'name': 'Jane Smith', 'title': 'Director', 'notes': None}],
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
```

- [ ] **Step 4: Run `build_json_output` tests and the new interviewer/panel_label tests**

```bash
cd /c/Users/r_tod/Documents/Projects/Job_search_agent && python -m pytest tests/test_phase5_debrief.py -k "build_json_output or test_single_interviewer or test_multiple_interviewers or test_panel_label" -v 2>&1 | tail -20
```

Expected: `test_single_interviewer_in_output`, `test_multiple_interviewers_in_output`, `test_panel_label_present_in_metadata_and_filename`, `test_panel_label_absent_in_metadata_and_filename` all pass. `build_json_output` existing tests pass.

---

### Task 5: Update `run_convert` and its test fixtures

**Files:**
- Modify: `scripts/phase5_debrief.py` (run_convert)
- Modify: `tests/test_phase5_debrief.py` (VALID_FILLED_YAML, UNQUOTED_DATES_YAML)

- [ ] **Step 1: Update `VALID_FILLED_YAML` in `tests/test_phase5_debrief.py`**

Replace the existing `VALID_FILLED_YAML` constant with:

```python
VALID_FILLED_YAML = """
metadata:
  role: TestRole
  stage: hiring_manager
  panel_label: null
  company: Viasat
  interviewers:
    - name: Jane Smith
      title: Director
      notes: null
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
```

- [ ] **Step 2: Update `UNQUOTED_DATES_YAML` in `tests/test_phase5_debrief.py`**

Replace the existing `UNQUOTED_DATES_YAML` constant with:

```python
UNQUOTED_DATES_YAML = """
metadata:
  role: TestRole
  stage: hiring_manager
  panel_label: null
  company: Viasat
  interviewers:
    - name: Jane Smith
      title: Director
      notes: null
  interview_date: 2026-04-10
  format: video
  produced_date: 2026-04-13
advancement_read:
  assessment: maybe
  notes: null
stories_used: []
gaps_surfaced: []
salary_exchange:
  range_given_min: null
  range_given_max: null
  candidate_anchor: null
  candidate_floor: null
  notes: null
what_i_said: null
open_notes: null
"""
```

- [ ] **Step 3: Update `run_convert` to call `validate_interviewers` and use `panel_label` in filename**

Replace the `run_convert` function body (the lines after reading the YAML and normalizing booleans) to add the interviewers validation call and pass `panel_label` to `build_output_filename`. The full updated function:

```python
def run_convert(role, stage, debriefs_dir):
    draft_path = os.path.join(debriefs_dir, role, f"debrief_{stage}_draft.yaml")
    if not os.path.exists(draft_path):
        print(f"No draft found at {draft_path}. Run --init first.")
        sys.exit(1)
    with open(draft_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    # Cast date fields to str -- PyYAML parses unquoted dates as datetime.date objects
    if data['metadata'].get('interview_date') is not None:
        data['metadata']['interview_date'] = str(data['metadata']['interview_date'])
    if data['metadata'].get('produced_date') is not None:
        data['metadata']['produced_date'] = str(data['metadata']['produced_date'])
    # Normalize YAML boolean coercion -- `yes`/`no` parse as True/False in PyYAML
    _normalize_yaml_booleans(data)
    errors = []
    errors.extend(validate_required(data))
    errors.extend(validate_enums(data))
    errors.extend(validate_interviewers(data))
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
    panel_label = data['metadata'].get('panel_label')
    filename = build_output_filename(stage, interview_date, produced_date, panel_label=panel_label)
    output_path = os.path.join(debriefs_dir, role, filename)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Debrief saved to {output_path}")
```

- [ ] **Step 4: Run all `run_convert` tests**

```bash
cd /c/Users/r_tod/Documents/Projects/Job_search_agent && python -m pytest tests/test_phase5_debrief.py -k "run_convert" -v 2>&1 | tail -20
```

Expected: all `run_convert` tests pass, including the two new rejection tests.

---

### Task 6: Update `run_interactive` and its test fixtures

**Files:**
- Modify: `scripts/phase5_debrief.py` (run_interactive)
- Modify: `tests/test_phase5_debrief.py` (`_default_inputs`, 4 inline `_make_inputs` sequences)

- [ ] **Step 1: Replace the interviewer section in `run_interactive` with the capture loop**

In `run_interactive`, replace these lines in the `# -- metadata --` block:

```python
        interviewer_name = _prompt_optional("Interviewer name")
        interviewer_title = _prompt_optional("Interviewer title")
```

With the full interviewers capture loop:

```python
        # -- interviewers --
        print("\n-- Interviewers --")
        interviewers = []
        while True:
            print(f"  Interviewer {len(interviewers) + 1}:")
            name = _prompt_optional("    Name")
            title = _prompt_optional("    Title")
            notes = _prompt_optional(
                "    Notes (questions asked, background, programs mentioned, anything for personalized follow-up)"
            )
            interviewers.append({'name': name, 'title': title, 'notes': notes})
            if not any(i.get('name') for i in interviewers):
                print("  At least one interviewer name is required.")
                interviewers.clear()
                continue
            if input("  Add another interviewer? (y/n): ").strip().lower() != 'y':
                break
```

- [ ] **Step 2: Add `panel_label` parameter to `run_interactive` and thread it through**

Change the function signature from:

```python
def run_interactive(role, stage, debriefs_dir, client=None):
```

To:

```python
def run_interactive(role, stage, debriefs_dir, client=None, panel_label=None):
```

- [ ] **Step 3: Update the `data` dict in `run_interactive` to use `interviewers` and `panel_label`**

In `run_interactive`, replace the existing `data` assignment (which references `interviewer_name`, `interviewer_title`) with:

```python
        data = {
            'metadata': {
                'role': role, 'stage': stage, 'panel_label': panel_label,
                'company': company,
                'interviewers': interviewers,
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
```

- [ ] **Step 4: Update `build_output_filename` call in `run_interactive` to pass `panel_label`**

In `run_interactive`, replace:

```python
        filename = build_output_filename(stage, interview_date, produced_date)
```

With:

```python
        filename = build_output_filename(stage, interview_date, produced_date, panel_label=panel_label)
```

- [ ] **Step 5: Update `_default_inputs()` in `tests/test_phase5_debrief.py`**

Replace the existing `_default_inputs` function with:

```python
def _default_inputs():
    """Full valid input sequence for a single-story, single-gap session."""
    return _make_inputs(
        'Viasat',           # company
        'Jane Smith',        # interviewer name
        'Director',          # interviewer title
        '',                  # interviewer notes (skip)
        'n',                 # add another interviewer?
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
```

- [ ] **Step 6: Update 4 inline `_make_inputs` sequences in existing interactive tests**

**`test_run_interactive_enum_reprompt`** -- insert interviewer prompts after `'Viasat'`:

```python
    monkeypatch.setattr('builtins.input', _make_inputs(
        'Viasat',
        'Jane', 'Dir', '',  # interviewer: name, title, notes
        'n',                # add another interviewer?
        '2026-04-10',
        'zoom',    # invalid format -- should reprompt
        'video',   # valid
        'maybe', 'Notes.',
        'leadership', 'framing', 'yes', 'n',
        'no SCIF', 'response', 'adequate', 'n',
        '', '', '', '', '',
        'Said something.',
        '',
    ))
```

**`test_run_interactive_multiple_stories`** -- insert interviewer prompts after `'Viasat'`:

```python
    monkeypatch.setattr('builtins.input', _make_inputs(
        'Viasat',
        'Jane', 'Dir', '',  # interviewer
        'n',                # add another interviewer?
        '2026-04-10', 'video', 'maybe', '',
        'leadership', 'Led EO rewrite', 'yes',
        'y',                              # add another story
        'cross-functional', 'Built stakeholder map', 'partially',
        'n',
        'gap', 'response', 'strong', 'n',
        '', '', '', '', '',
        '',
        '',
    ))
```

**`test_run_interactive_draft_conflict_warning`** -- insert interviewer prompts after `'y'` (conflict confirm) and `'Viasat'`:

```python
    monkeypatch.setattr('builtins.input', _make_inputs(
        'y',            # confirm conflict warning -- session must proceed after this
        'Viasat',
        'Jane', 'Dir', '',  # interviewer
        'n',                # add another interviewer?
        '2026-04-10', 'video', 'maybe', '',
        'leadership', 'framing', 'yes', 'n',
        'gap', 'response', 'adequate', 'n',
        '', '', '', '', '',
        '',
        '',
    ))
```

**`test_run_interactive_with_client_calls_followup`** -- insert interviewer prompts after `'Viasat'`:

```python
    monkeypatch.setattr('builtins.input', _make_inputs(
        'Viasat',
        'Jane', 'Dir', '',  # interviewer
        'n',                # add another interviewer?
        '2026-04-10', 'video',
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
```

- [ ] **Step 7: Run all `run_interactive` tests**

```bash
cd /c/Users/r_tod/Documents/Projects/Job_search_agent && python -m pytest tests/test_phase5_debrief.py -k "interactive" -v 2>&1 | tail -20
```

Expected: all interactive tests pass.

---

### Task 7: Update `run_init`, `main`, and init test fixtures

**Files:**
- Modify: `scripts/phase5_debrief.py` (run_init, main)
- Modify: `tests/test_phase5_debrief.py` (MINIMAL_TEMPLATE)

- [ ] **Step 1: Add `panel_label` parameter to `run_init` and pre-fill it in the draft**

Change the function signature from:

```python
def run_init(role, stage, template_path, debriefs_dir):
```

To:

```python
def run_init(role, stage, template_path, debriefs_dir, panel_label=None):
```

After the existing line `data['metadata']['produced_date'] = str(date.today())`, add:

```python
    data['metadata']['panel_label'] = panel_label
```

- [ ] **Step 2: Update `main` to pass `args.panel_label` to `run_init` and `run_interactive`**

Replace the `main` function body with:

```python
def main():
    args = build_parser().parse_args()
    if args.init:
        run_init(args.role, args.stage, TEMPLATE_PATH, DEBRIEFS_DIR, panel_label=args.panel_label)
    elif args.convert:
        run_convert(args.role, args.stage, DEBRIEFS_DIR)
    elif args.interactive:
        client = Anthropic()
        run_interactive(args.role, args.stage, DEBRIEFS_DIR, client=client, panel_label=args.panel_label)
```

- [ ] **Step 3: Update `MINIMAL_TEMPLATE` in `tests/test_phase5_debrief.py`**

Replace the existing `MINIMAL_TEMPLATE` constant with:

```python
MINIMAL_TEMPLATE = """
metadata:
  role: null
  stage: null
  panel_label: null
  company: null
  interviewers:
    - name: null
      title: null
      notes: null
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
```

- [ ] **Step 4: Run all `run_init` tests**

```bash
cd /c/Users/r_tod/Documents/Projects/Job_search_agent && python -m pytest tests/test_phase5_debrief.py -k "run_init" -v 2>&1 | tail -15
```

Expected: all `run_init` tests pass.

---

### Task 8: Full verification and commit

**Files:** none -- verification only

- [ ] **Step 1: Run the full test suite**

```bash
cd /c/Users/r_tod/Documents/Projects/Job_search_agent && python -m pytest tests/test_phase5_debrief.py -v 2>&1 | tail -30
```

Expected: 57 tests collected, 57 passed. If any fail, diagnose before proceeding.

- [ ] **Step 2: Syntax check**

```bash
cd /c/Users/r_tod/Documents/Projects/Job_search_agent && python -m py_compile scripts/phase5_debrief.py && echo "OK"
```

Expected: `OK` with no output.

- [ ] **Step 3: Git status check**

```bash
cd /c/Users/r_tod/Documents/Projects/Job_search_agent && git status
```

Confirm only these three files are modified: `scripts/phase5_debrief.py`, `templates/interview_debrief_template.yaml`, `tests/test_phase5_debrief.py`. Also confirm `docs/superpowers/plans/2026-04-15-post-interview-debrief-amendment.md` is new.

- [ ] **Step 4: Stage and commit**

```bash
cd /c/Users/r_tod/Documents/Projects/Job_search_agent && git add scripts/phase5_debrief.py templates/interview_debrief_template.yaml tests/test_phase5_debrief.py docs/superpowers/plans/2026-04-15-post-interview-debrief-amendment.md && git commit -m "$(cat <<'EOF'
Amend debrief script: interviewers array, panel_label, updated filename

Replace flat interviewer_name/interviewer_title fields with an interviewers
array (name, title, notes per person). Add --panel_label optional CLI argument
stored in metadata and included in output filename when provided. 57 tests pass.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Self-Review Notes

- **Spec coverage:** All 8 Definition of Done items are covered across Tasks 1-8.
- **Regression baseline:** The 51 existing tests are preserved by updating fixtures (not assertions) in Tasks 4-7.
- **Type consistency:** `build_output_filename(stage, interview_date, produced_date, panel_label=None)` signature is consistent across all call sites in Tasks 5, 6, and 7.
- **Placeholder scan:** No TBD or TODO items -- all steps include exact code.
- **`_base_data()` dependency:** Tests 1-4 (new) and the existing `build_json_output` tests all use `_base_data()`. The fixture is updated in Task 4 Step 3, before any test that depends on the new schema is run in isolation.
- **`AMENDED_VALID_YAML`:** This temporary constant in the test file (Task 2) becomes redundant after `VALID_FILLED_YAML` is updated in Task 5. It can be removed or left -- the tests that use it still work correctly after VALID_FILLED_YAML is updated since they reference AMENDED_VALID_YAML directly.
