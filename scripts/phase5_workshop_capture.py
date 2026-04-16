# ==============================================
# phase5_workshop_capture.py
# Parses a workshopped interview prep .docx and
# writes durable content into interview_library.json.
#
# Reads:  data/job_packages/[role]/interview_prep_[stage].docx
# Writes: data/interview_library.json (appends / updates)
#
# Usage:
#   python scripts/phase5_workshop_capture.py \
#     --role Viasat_SE_IS --stage hiring_manager
# ==============================================

import os
import sys
import json
import re
import argparse
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.interview_library_parser import (
    LIBRARY_PATH, TAGS_PATH, init_library, load_tags, _load_library
)

JOBS_PACKAGES_DIR = "data/job_packages"

# ── Tag keyword map for auto-suggestion ──────────────────────────────────────
# Keys match controlled vocabulary in interview_library_tags.json.
# Values are substrings to search in lower-cased content text.

TAG_KEYWORDS = {
    "leadership":            ["led ", "lead ", "managed", "directed", "ownership"],
    "cross-functional":      ["cross-functional", "cross functional", "multi-team", "cross-org"],
    "technical-credibility": ["architecture", "designed", "implemented", "technical review"],
    "ambiguity":             ["ambiguous", "ambiguity", "unclear", "undefined", "pivoted"],
    "stakeholder-management":["stakeholder", "customer", "sponsor", "executive brief"],
    "program-delivery":      ["milestone", "schedule", "delivery", "deadline", "cdrl"],
    "systems-engineering":   ["systems engineering", "se process", "v&v", "verification"],
    "communication":         ["briefed", "presented", "communicated", "weekly report"],
    "conflict-resolution":   ["conflict", "disagreement", "resolved tension", "mediated"],
    "domain-gap":            ["gap in", "limited experience", "new to", "hadn't used"],
    "tools-gap":             ["tool gap", "no experience with", "haven't used"],
    "clearance":             ["clearance", "ts/sci", "secret", "cleared"],
    "salary":                ["salary", "compensation", "offer range"],
    "culture-fit":           ["culture", "team environment", "values alignment"],
    "mbse":                  ["mbse", "model-based", "sysml", "cameo", "doors", "magic draw"],
    "requirements-analysis": ["requirements", "srs", "conops", "specification"],
    "integration":           ["integration", "interface", "icd", "ato"],
    "v-and-v":               ["v&v", "verification", "validation", "qualification"],
    "architecture":          ["architecture", "design pattern", "system design", "framework"],
    "domain-translation":    ["domain translation", "bridging", "translat"],
}


# ==============================================
# ARGPARSE
# ==============================================

def build_parser():
    parser = argparse.ArgumentParser(description="Phase 5 Workshop Capture")
    parser.add_argument("--role", required=True,
                        help="Role package folder name (e.g. Viasat_SE_IS)")
    parser.add_argument("--stage", required=True,
                        help="Interview stage (e.g. hiring_manager, team_panel)")
    return parser


# ==============================================
# DOCX LOCATION
# ==============================================

def _locate_docx(role, stage):
    """Return path to workshopped .docx, or sys.exit with clear error."""
    path = os.path.join(JOBS_PACKAGES_DIR, role, f"interview_prep_{stage}.docx")
    if not os.path.exists(path):
        print(f"\nERROR: Workshopped .docx not found: {path}")
        print("Generate and workshop interview prep before running capture.")
        sys.exit(1)
    return path
