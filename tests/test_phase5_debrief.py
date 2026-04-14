import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scripts.phase5_debrief as pd


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


# ---- run_init ----

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


# ---- run_convert ----

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

UNQUOTED_DATES_YAML = """
metadata:
  role: TestRole
  stage: hiring_manager
  company: Viasat
  interviewer_name: Jane Smith
  interviewer_title: Director
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


def test_run_convert_unquoted_dates(tmp_path):
    """PyYAML parses unquoted dates as datetime.date -- run_convert must cast to str."""
    _write_draft(tmp_path, 'TestRole', 'hiring_manager', UNQUOTED_DATES_YAML)
    pd.run_convert('TestRole', 'hiring_manager', str(tmp_path))
    output = tmp_path / 'TestRole' / 'debrief_hiring_manager_2026-04-10_filed-2026-04-13.json'
    assert output.exists()
    with open(output) as f:
        data = json.load(f)
    assert data['metadata']['interview_date'] == '2026-04-10'
    assert data['metadata']['produced_date'] == '2026-04-13'


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


# ---- run_interactive ----

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
        'leadership', 'Led EO rewrite', 'yes',
        'y',                              # add another story
        'cross-functional', 'Built stakeholder map', 'partially',
        'n',
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
    """Asserts: (a) warning message printed, (b) session proceeds when user confirms y."""
    (tmp_path / 'TestRole').mkdir()
    (tmp_path / 'TestRole' / 'debrief_hiring_manager_draft.yaml').write_text('existing')
    monkeypatch.setattr('builtins.input', _make_inputs(
        'y',            # confirm conflict warning -- session must proceed after this
        'Viasat', 'Jane', 'Dir', '2026-04-10', 'video', 'maybe', '',
        'leadership', 'framing', 'yes', 'n',
        'gap', 'response', 'adequate', 'n',
        '', '', '', '', '',
        '',
        '',
    ))
    pd.run_interactive('TestRole', 'hiring_manager', str(tmp_path), client=None)
    captured = capsys.readouterr()
    # (a) warning message printed
    assert 'draft already exists' in captured.out.lower()
    # (b) session proceeded -- JSON output was written
    assert len(list((tmp_path / 'TestRole').glob('*.json'))) == 1


# ---- get_followup_question / AI integration ----

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
