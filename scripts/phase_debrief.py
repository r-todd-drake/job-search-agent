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
