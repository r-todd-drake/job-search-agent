# ==============================================
# phase5_debrief.py
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
#   python scripts/phase5_debrief.py --role Viasat_SE_IS --stage hiring_manager --init
#   python scripts/phase5_debrief.py --role Viasat_SE_IS --stage hiring_manager --convert
#   python scripts/phase5_debrief.py --role Viasat_SE_IS --stage hiring_manager --interactive
# ==============================================

import os
import sys
import json
import argparse
from datetime import date

import yaml
from dotenv import load_dotenv
from anthropic import Anthropic

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.utils.pii_filter import strip_pii

load_dotenv()

# ==============================================
# CONFIGURATION
# ==============================================

TEMPLATE_PATH = "templates/interview_debrief_template.yaml"
DEBRIEFS_DIR = "data/debriefs"
MODEL = "claude-haiku-4-5-20251001"

VALID_STAGES = ["recruiter_screen", "hiring_manager", "panel", "final"]
VALID_FORMATS = ["phone", "video", "onsite"]
VALID_ASSESSMENTS = ["for_sure", "maybe", "doubt_it", "definitely_not"]
VALID_LANDED = ["yes", "partially", "no"]
VALID_RESPONSE_FELT = ["strong", "adequate", "weak"]
SALARY_FIELDS = ["range_given_min", "range_given_max", "candidate_anchor", "candidate_floor"]

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


def _normalize_yaml_booleans(data: dict) -> None:
    """Fix YAML boolean coercion for enum fields. PyYAML parses `yes`/`no` as True/False.
    Mutates data in place."""
    bool_map = {True: 'yes', False: 'no'}
    for story in data.get('stories_used', []) or []:
        if story.get('landed') in bool_map:
            story['landed'] = bool_map[story['landed']]


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


def run_interactive(role, stage, debriefs_dir, client=None):
    try:
        draft_path = os.path.join(debriefs_dir, role, f"debrief_{stage}_draft.yaml")
        if os.path.exists(draft_path):
            print(
                f"A draft already exists for {role}/{stage}. "
                f"--interactive will create a separate JSON output and will not use the draft."
            )
            response = input("Continue? (y/n): ").strip().lower()
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
        client = Anthropic()
        run_interactive(args.role, args.stage, DEBRIEFS_DIR, client=client)


if __name__ == "__main__":
    main()
