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


# ==============================================
# DOCX EXTRACTION
# ==============================================

def _extract_docx_paragraphs(docx_path):
    """
    Extract paragraphs from docx as list of (text, style_name, is_italic) tuples.
    Blank paragraphs are skipped.
    is_italic is True when all non-blank runs in the paragraph are italic.
    """
    from docx import Document
    doc = Document(docx_path)
    result = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        style = para.style.name
        non_blank_runs = [r for r in para.runs if r.text.strip()]
        is_italic = bool(non_blank_runs) and all(r.italic for r in non_blank_runs)
        result.append((text, style, is_italic))
    return result


def _split_sections(paragraphs):
    """
    Divide paragraph list into story_bank, gap_prep, questions buckets.
    Detection uses case-insensitive substring match on paragraph text.
    Paragraphs in other sections (Company Brief, Introduce Yourself, etc.)
    are assigned to no bucket and discarded.

    For "other" markers, only apply when the paragraph has a heading style.
    Primary bucket markers (story_bank, gap_prep, questions) match any paragraph.
    """
    SECTION_MARKERS = {
        "story_bank":  ["STORY BANK"],
        "gap_prep":    ["GAP PREPARATION"],
        "questions":   ["QUESTIONS TO ASK"],
        "other":       ["COMPANY", "ROLE BRIEF", "INTRODUCE YOURSELF",
                        "SALARY", "END OF", "INTERVIEW PREP PACKAGE",
                        "CONTINUITY"],
    }
    sections = {"story_bank": [], "gap_prep": [], "questions": []}
    current = None

    for text, style, is_italic in paragraphs:
        upper = text.upper()
        is_heading = "heading" in style.lower()
        matched_section = False
        for key, markers in SECTION_MARKERS.items():
            if any(m in upper for m in markers):
                if key == "other" and not is_heading:
                    # "other" markers only apply to heading-style paragraphs
                    continue
                current = None if key == "other" else key
                matched_section = True
                break
        if not matched_section and current in sections:
            sections[current].append((text, style, is_italic))

    return sections


# ==============================================
# STORY PARSER
# ==============================================

def _parse_stories(paragraphs):
    """
    Parse story bank paragraphs into a list of story dicts.
    Each dict has: employer, title_held, dates, situation, task,
                   action, result, if_probed, _header (raw story heading).
    Italic paragraphs are skipped (coaching / delivery notes).
    """
    STORY_FIELDS = {
        "Situation:": "situation",
        "Task:":      "task",
        "Action:":    "action",
        "Result:":    "result",
        "If probed:": "if_probed",
    }
    stories = []
    current = None
    current_field = None

    for text, style, is_italic in paragraphs:
        if is_italic:
            continue

        if re.match(r'^STORY\s+\d+\s*[-\u2013]', text, re.IGNORECASE):
            if current:
                stories.append(current)
            current = {
                "employer": "", "title_held": "", "dates": "",
                "situation": "", "task": "", "action": "", "result": "",
                "if_probed": None, "_header": text
            }
            current_field = None
            continue

        if current is None:
            continue

        if text.startswith("Employer:"):
            value = text[len("Employer:"):].strip()
            parts = [p.strip() for p in value.split("|")]
            current["employer"]   = parts[0] if len(parts) > 0 else ""
            current["title_held"] = parts[1] if len(parts) > 1 else ""
            current["dates"]      = parts[2] if len(parts) > 2 else ""
            current_field = None
            continue

        matched = False
        for label, field in STORY_FIELDS.items():
            if text.startswith(label):
                current[field] = text[len(label):].strip()
                current_field = field
                matched = True
                break

        if not matched and current_field:
            # Continuation line for the current field
            if current[current_field] is None:
                current[current_field] = text
            elif current[current_field] == "":
                current[current_field] = text
            else:
                current[current_field] += " " + text

    if current:
        stories.append(current)
    return stories


# ==============================================
# GAP PARSER
# ==============================================

def _parse_gaps(paragraphs):
    """
    Parse gap prep paragraphs into a list of gap response dicts.
    Each dict has: gap_label, severity, honest_answer, bridge, redirect.
    Skips: italic paragraphs, SHORT TENURE section.
    Stops at: HARD QUESTIONS section.
    """
    GAP_FIELDS = {
        "Honest answer:": "honest_answer",
        "Bridge:":        "bridge",
        "Redirect:":      "redirect",
    }
    gaps = []
    current = None
    current_field = None
    in_short_tenure = False

    for text, style, is_italic in paragraphs:
        if is_italic:
            continue
        upper = text.upper()
        if "SHORT TENURE" in upper:
            in_short_tenure = True
            current = None
            continue
        if "HARD QUESTIONS" in upper:
            break
        if re.match(r'^GAP\s+\d+\s*(?:--|\u2013)', text, re.IGNORECASE):
            in_short_tenure = False
            if current:
                gaps.append(current)
            severity = "preferred" if "[PREFERRED]" in upper else "required"
            label_match = re.match(
                r'^GAP\s+\d+\s*(?:--|\u2013)\s+(.+?)\s*(?:\[(?:REQUIRED|PREFERRED)\])?:?\s*$',
                text, re.IGNORECASE
            )
            gap_label = label_match.group(1).strip() if label_match else text
            current = {
                "gap_label": gap_label, "severity": severity,
                "honest_answer": "", "bridge": "", "redirect": "",
            }
            current_field = None
            continue

        if in_short_tenure or current is None:
            continue
        if text.startswith("Gap:"):
            current_field = None  # Skip the Gap: line itself
            continue

        matched = False
        for label, field in GAP_FIELDS.items():
            if text.startswith(label):
                current[field] = text[len(label):].strip()
                current_field = field
                matched = True
                break
        if not matched and current_field:
            if current[current_field]:
                current[current_field] += " " + text
            else:
                current[current_field] = text

    if current:
        gaps.append(current)
    return gaps
