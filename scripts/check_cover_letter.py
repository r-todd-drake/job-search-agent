# ==============================================
# check_cover_letter.py
# API-based cover letter quality checker.
# Two-layer architecture:
#   Layer 1 – fast pre-flight string matching
#   Layer 2 – single API call for nuanced assessment (implied gap fulfillment)
#
# Reads cl_stage2_approved.txt (text stage file).
# Constraints loaded dynamically from CANDIDATE_BACKGROUND.md.
#
# Usage:
#   python -m scripts.check_cover_letter --role [role]
# Example:
#   python -m scripts.check_cover_letter --role BAH_LCI_MBSE
# ==============================================

import io
import os
import re
import sys
import json
import argparse

import anthropic
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.utils.pii_filter import strip_pii

load_dotenv()

# ==============================================
# CONSTANTS
# ==============================================

CANDIDATE_BACKGROUND_PATH = "context/CANDIDATE_BACKGROUND.md"
JOBS_PACKAGES_DIR = "data/job_packages"
MODEL = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = (
    "You are a cover letter quality reviewer for a defense and aerospace systems engineering candidate. "
    "You assess cover letters for accuracy, honesty, and alignment with confirmed experience. "
    "You flag overclaiming, implied gap fulfillment, and language violations. "
    "Return only valid JSON \u2013 no markdown fences, no preamble, no explanation."
)

# Hardcoded Layer 1 rules: (rule_name, pattern, fix, case_sensitive)
HARDCODED_RULES = [
    (
        "Em dash",
        "\u2014",
        "Replace \u2014 with \u2013 (en dash)",
        True,
    ),
    (
        "CompTIA Security+ reference",
        "CompTIA Security+",
        "Remove \u2013 certification is lapsed and must not appear on cover letter",
        False,
    ),
    (
        "Active TS/SCI",
        "Active TS/SCI",
        "Use 'Current TS/SCI' between employers \u2013 'Active' only when employed on a program",
        True,
    ),
    (
        "Plank Holder (capitalized)",
        "Plank Holder",
        "Use 'Plank Owner' (two words, capitalized)",
        True,
    ),
    (
        "plank holder (lowercase)",
        "plank holder",
        "Use 'Plank Owner' (two words, capitalized)",
        False,
    ),
    (
        "plankowner (one word)",
        "plankowner",
        "Use 'Plank Owner' (two words, capitalized)",
        False,
    ),
    (
        "safety-critical",
        "safety-critical",
        "Use 'mission-critical' instead",
        False,
    ),
]

GAP_STOP_WORDS = {
    'NO', 'OR', 'AND', 'THE', 'NOT', 'USE', 'VIA', 'ANY', 'ONLY', 'NEVER',
    'CLAIM', 'THESE', 'ETC', 'SE', 'DO', 'AS', 'AT', 'IN', 'OF', 'TO',
    'BE', 'BY', 'IF', 'IS', 'IT', 'AN', 'ON', 'UP',
    'AI',
}

GAP_TERM_MIN_LENGTH = 3


# ==============================================
# SECTION EXTRACTION
# ==============================================

def extract_section(text, heading):
    """Extract content between heading and next ## heading."""
    lines = text.splitlines()
    in_section = False
    result = []
    for line in lines:
        if line.startswith(heading):
            in_section = True
            continue
        if in_section and line.startswith('## '):
            break
        if in_section:
            result.append(line)
    return '\n'.join(result)


# ==============================================
# GAP TERM EXTRACTION
# ==============================================

def extract_gap_terms(background_text):
    """
    Dynamically extract tool/credential names from the Confirmed Gaps section
    of CANDIDATE_BACKGROUND.md. Returns a set of strings for matching.
    """
    gaps_section = extract_section(background_text, "## Confirmed Gaps")
    terms = set()

    for line in gaps_section.splitlines():
        if not line.strip().startswith('-'):
            continue

        paren_matches = re.findall(r'\(([^)]+)\)', line)
        for match in paren_matches:
            for part in match.split(','):
                part = part.strip().rstrip('.')
                part = re.sub(r'\s+etc\.?$', '', part).strip()
                if part and len(part) >= 2:
                    terms.add(part)

        acronyms = re.findall(
            r'\b(?:[A-Z]{2,}(?:[/-][A-Z0-9]+)*|DO-\d+|MIL-STD-\d+)\b', line
        )
        for term in acronyms:
            if term not in GAP_STOP_WORDS:
                terms.add(term)

        camel = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]*)+\b', line)
        for term in camel:
            if term not in GAP_STOP_WORDS:
                terms.add(term)

    cleaned = set()
    for t in terms:
        if len(t) >= GAP_TERM_MIN_LENGTH and t.upper() not in GAP_STOP_WORDS:
            cleaned.add(t)

    return cleaned


# ==============================================
# LAYER 1 \u2013 STRING MATCHING
# ==============================================

def run_layer1(cl_lines, gap_terms):
    """
    Run pre-flight string checks against cover letter lines.
    Returns list of finding dicts.
    """
    findings = []

    for rule_name, pattern, fix, case_sensitive in HARDCODED_RULES:
        for i, line in enumerate(cl_lines, start=1):
            if not line.strip():
                continue
            check_line = line if case_sensitive else line.lower()
            check_pattern = pattern if case_sensitive else pattern.lower()
            if check_pattern in check_line:
                snippet = line.strip()[:120] + ('...' if len(line.strip()) > 120 else '')
                findings.append({
                    "layer": 1,
                    "rule": rule_name,
                    "line": i,
                    "flagged_text": snippet,
                    "fix": fix,
                })
                break

    for term in sorted(gap_terms):
        for i, line in enumerate(cl_lines, start=1):
            if not line.strip():
                continue
            if line.strip().startswith('##'):
                continue
            try:
                pattern = r'\b' + re.escape(term) + r'\b'
                if re.search(pattern, line, re.IGNORECASE):
                    snippet = line.strip()[:120] + ('...' if len(line.strip()) > 120 else '')
                    findings.append({
                        "layer": 1,
                        "rule": f"Confirmed gap referenced: {term}",
                        "line": i,
                        "flagged_text": snippet,
                        "fix": f"Remove or rephrase \u2013 '{term}' is in the confirmed gaps list (no professional experience to claim)",
                    })
                    break
            except re.error:
                continue

    return findings
