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
