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


# ==============================================
# MODE STUBS (implemented in later tasks)
# ==============================================

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
