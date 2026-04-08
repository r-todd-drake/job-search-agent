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


# ==============================================
# LAYER 2 – API ASSESSMENT
# ==============================================

def run_layer2(client, cl_text, gaps_section, banned_section):
    """
    Single API call for nuanced gap and claims assessment.
    Primary purpose: detect implied gap fulfillment – language that conveys experience
    in a confirmed gap area without naming the gap term directly.
    Returns list of finding dicts. Falls back to raw output on JSON parse failure.
    """
    prompt = f"""Review this cover letter text for violations against the confirmed gaps and banned language rules below.

CONFIRMED GAPS (candidate has no professional experience with these – do not claim or imply):
{gaps_section}

BANNED / CORRECTED LANGUAGE (specific terms and their correct replacements):
{banned_section}

COVER LETTER TEXT:
{cl_text}

Assess the cover letter for:
- IMPLIED GAP FULFILLMENT: Language that conveys experience, ownership, or authority in a confirmed
  gap area without naming the gap term directly. This is the primary concern – cover letter prose
  can imply gap fulfillment more subtly than resume bullets. Example: "hands-on experience deploying
  cloud infrastructure" implies AWS/Azure/GCP experience even if those terms do not appear.
- Claims that explicitly reference confirmed gap tools, credentials, or domains
- Use of banned terms or language that should be corrected
- GENERIC OPENER PHRASES: Flag sentences that open with "I am excited to apply", "I am writing to
  express", "I am writing to apply", "I am pleased to apply", or similar filler opener patterns
- Fabricated or unverifiable metrics, outcomes, or experience not grounded in confirmed background

IMPORTANT – EM DASH CLARIFICATION:
The em dash is the specific character \u2014 (U+2014). Only flag this character as a violation.
Hyphens (-) in compound words such as "end-to-end", "mission-critical", "real-time" are correct
usage and must NOT be flagged as em dash violations.

IMPORTANT – ONLY FLAG ACTUAL VIOLATIONS:
Only flag language that is actually wrong in the cover letter text. Do NOT flag language that already
conforms to the rules. Examples of correct language that must NOT be flagged:
- "mission-critical" – already the correct term, do not flag
- "Current TS/SCI" – already the correct form, do not flag
- "Plank Owner" – already the correct form, do not flag
Flag only what is actually present and actually wrong, not what demonstrates compliance.

Return ONLY a raw JSON array. No markdown fences. No explanation. No preamble.
If no violations found, return an empty array: []

Each finding must follow this exact structure:
{{
  "violation_type": "short label",
  "line_reference": "line N" or "N/A",
  "flagged_text": "exact quoted text from cover letter (keep short)",
  "suggested_fix": "specific correction"
}}"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()

    try:
        findings_raw = json.loads(raw)
        findings = []
        for f in findings_raw:
            findings.append({
                "layer": 2,
                "rule": f.get("violation_type", "Unknown"),
                "line": f.get("line_reference", "N/A"),
                "flagged_text": f.get("flagged_text", ""),
                "fix": f.get("suggested_fix", ""),
            })
        return findings
    except json.JSONDecodeError:
        print("\n  WARNING: Layer 2 response was not valid JSON. Raw output:")
        print("  " + raw[:500])
        return [{
            "layer": 2,
            "rule": "JSON parse failure",
            "line": "N/A",
            "flagged_text": raw[:200],
            "fix": "Review raw API output above manually",
        }]
