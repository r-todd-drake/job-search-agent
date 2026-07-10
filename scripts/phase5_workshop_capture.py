# ==============================================
# phase5_workshop_capture.py
# Parses a workshopped interview prep .docx and
# writes durable content into interview_library.json.
#
# Reads:  data/job_packages/[role]/interview_prep_[stage].docx
# Writes: data/interview_library.json (appends / updates)
#
# Usage:
#   python -m scripts.phase5_workshop_capture \
#     --role Acme_SE_Systems --stage hiring_manager
# ==============================================

import os
import sys
import json
import re
import argparse
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.interview_library_parser import (
    LIBRARY_PATH, TAGS_PATH, init_library, load_tags, _load_library, write_library
)
from scripts.config import JOBS_PACKAGES_DIR

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
                        help="Role package folder name (e.g. Acme_SE_Systems)")
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


# ==============================================
# QUESTION PARSER
# ==============================================

def _parse_questions(paragraphs, stage):
    """
    Parse questions section paragraphs into a list of question dicts.
    Each dict has: stage, text (question only, rationale stripped), category=None.
    Extracts numbered items (1. ...) only.
    Strips rationale text after the closing "?".
    Italic paragraphs are skipped.
    """
    questions = []
    for text, style, is_italic in paragraphs:
        if is_italic:
            continue
        if not re.match(r'^\d+\.', text):
            continue
        # Strip number prefix
        text_no_num = re.sub(r'^\d+\.\s*', '', text).strip()
        # Take only up to and including the first "?"
        q_match = re.search(r'^(.*?\?)', text_no_num)
        if not q_match:
            continue
        q_text = q_match.group(1).strip()
        questions.append({"stage": stage, "text": q_text, "category": None})
    return questions


# ==============================================
# TAG SUGGESTION AND ID GENERATION
# ==============================================

def _suggest_tags(text):
    """Return list of tags from controlled vocabulary whose keywords appear in text."""
    vocabulary = load_tags()
    text_lower = text.lower()
    return [
        tag for tag, keywords in TAG_KEYWORDS.items()
        if tag in vocabulary and any(kw in text_lower for kw in keywords)
    ]


def _make_story_id(employer, tags):
    """Generate a unique slug from employer name and primary tag."""
    emp = re.sub(r'[^a-z0-9]+', '-', employer.lower()).strip('-')
    tag = tags[0] if tags else "story"
    return f"{emp}-{tag}"[:60]


def _make_gap_id(gap_label):
    """Generate a unique slug from gap label."""
    return re.sub(r'[^a-z0-9]+', '-', gap_label.lower()).strip('-')[:60]


def _make_question_id(text):
    """Generate a unique slug from first 60 chars of question text."""
    return re.sub(r'[^a-z0-9]+', '-', text.lower())[:60].strip('-')


# ==============================================
# DUPLICATE DETECTION
# ==============================================

def _find_duplicate_story(library, employer, primary_tag):
    """Return existing story entry matching employer + primary_tag, or None.
    When primary_tag is empty, matches on employer alone."""
    for s in library.get("stories", []):
        if s.get("employer", "").lower() != employer.lower():
            continue
        if not primary_tag or primary_tag in s.get("tags", []):
            return s
    return None


def _find_duplicate_gap(library, gap_label):
    """Return existing gap entry matching gap_label (case-insensitive), or None."""
    norm = gap_label.lower().strip()
    for g in library.get("gap_responses", []):
        if g.get("gap_label", "").lower().strip() == norm:
            return g
    return None


def _find_duplicate_question(library, text):
    """Return existing question entry matching first 60 chars of text, or None."""
    prefix = text[:60].lower()
    for q in library.get("questions", []):
        if q.get("text", "")[:60].lower() == prefix:
            return q
    return None


# ==============================================
# LIBRARY WRITE HELPERS
# ==============================================

def _skip_update_roles(existing_entry, role, library, section_key):
    """On skip: add role to roles_used if not already present. Mutates library in place."""
    if role not in existing_entry.get("roles_used", []):
        existing_entry.setdefault("roles_used", []).append(role)
    # Ensure the library dict reflects the mutation
    for i, entry in enumerate(library[section_key]):
        if entry.get("id") == existing_entry["id"]:
            library[section_key][i] = existing_entry
            break


def _overwrite_entry(existing_entry, new_entry, library, section_key):
    """On overwrite: replace entry; merge roles_used from both. Mutates library in place."""
    merged_roles = list(set(
        existing_entry.get("roles_used", []) + new_entry.get("roles_used", [])
    ))
    new_entry["roles_used"] = merged_roles
    for i, entry in enumerate(library[section_key]):
        if entry.get("id") == existing_entry["id"]:
            library[section_key][i] = new_entry
            break


# ==============================================
# ENTRY BUILDERS
# ==============================================

def _build_story_entry(raw, tags, role, today):
    """Convert a parsed story dict to a library-ready entry."""
    return {
        "id":          _make_story_id(raw["employer"], tags),
        "title":       raw["_header"],
        "tags":        tags,
        "employer":    raw["employer"],
        "title_held":  raw["title_held"],
        "dates":       raw["dates"],
        "situation":   raw["situation"],
        "task":        raw["task"],
        "action":      raw["action"],
        "result":      raw["result"],
        "if_probed":   raw["if_probed"],
        "notes":       None,
        "source":      "workshopped",
        "roles_used":  [role],
        "last_updated": today,
    }


def _build_gap_entry(raw, tags, role, today):
    """Convert a parsed gap dict to a library-ready entry."""
    return {
        "id":           _make_gap_id(raw["gap_label"]),
        "gap_label":    raw["gap_label"],
        "severity":     raw["severity"],
        "tags":         tags,
        "honest_answer": raw["honest_answer"],
        "bridge":       raw["bridge"],
        "redirect":     raw["redirect"],
        "notes":        None,
        "source":       "workshopped",
        "roles_used":   [role],
        "last_updated": today,
    }


def _build_question_entry(raw, tags, role, today):
    """Convert a parsed question dict to a library-ready entry."""
    category = tags[0] if tags else "general"
    return {
        "id":          _make_question_id(raw["text"]),
        "stage":       raw["stage"],
        "category":    category,
        "text":        raw["text"],
        "tags":        tags,
        "notes":       None,
        "source":      "workshopped",
        "roles_used":  [role],
        "last_updated": today,
    }


def _confirm_tags(content_text, label):
    """
    Suggest tags for an entry; prompt user to accept or override.
    Returns final confirmed list of tags.
    Unknown tags produce a warning but are accepted.
    """
    vocabulary = load_tags()
    suggested = _suggest_tags(content_text)
    if suggested:
        print(f"  Suggested tags for {label}: {', '.join(suggested)}")
    else:
        print(f"  No tags auto-suggested for {label}.")
    raw = input(
        "  Press Enter to accept, or type comma-separated tags: "
    ).strip()
    if not raw:
        tags = suggested
    else:
        tags = [t.strip() for t in raw.split(",") if t.strip()]
    unknown = [t for t in tags if t not in vocabulary]
    for t in unknown:
        print(f"  WARNING: '{t}' is not in the tag vocabulary -- accepted anyway.")
    return tags


def _handle_duplicate(existing, new_entry, library, section_key, role, label):
    """
    Handle a duplicate entry. Prompt: skip / overwrite / rename.
    Returns True if entry was written (overwrite or rename), False if skipped.
    """
    answer = input(
        f"  Entry '{existing['id']}' already exists. Skip / overwrite / rename? (s/o/r): "
    ).strip().lower()
    if answer == "s":
        _skip_update_roles(existing, role, library, section_key)
        print(f"  Skipped {label} -- roles_used updated.")
        return False
    elif answer == "o":
        _overwrite_entry(existing, new_entry, library, section_key)
        print(f"  Overwrote {label}.")
        return True
    elif answer == "r":
        new_id = input("  Enter new ID: ").strip()
        new_entry["id"] = new_id
        library[section_key].append(new_entry)
        print(f"  Added as new entry '{new_id}'.")
        return True
    else:
        print("  Invalid choice -- skipping.")
        _skip_update_roles(existing, role, library, section_key)
        return False


# ==============================================
# MAIN
# ==============================================

def main():
    args = build_parser().parse_args()
    role = args.role
    stage = args.stage
    today = str(date.today())

    print("=" * 60)
    print("PHASE 5 \u2013 WORKSHOP CAPTURE")
    print("=" * 60)
    print(f"Role:  {role}")
    print(f"Stage: {stage}")

    docx_path = _locate_docx(role, stage)
    print(f"\nReading: {docx_path}")

    paragraphs = _extract_docx_paragraphs(docx_path)
    sections = _split_sections(paragraphs)

    raw_stories   = _parse_stories(sections["story_bank"])
    raw_gaps      = _parse_gaps(sections["gap_prep"])
    raw_questions = _parse_questions(sections["questions"], stage)

    print(f"\nFound: {len(raw_stories)} stories, "
          f"{len(raw_gaps)} gap responses, "
          f"{len(raw_questions)} questions")

    # ── Tag assignment ──────────────────────────────────────────────────────
    print("\n-- Tag Assignment --")
    story_entries = []
    for i, raw in enumerate(raw_stories):
        label = f"story {i+1} ({raw['employer']})"
        content = " ".join([raw["situation"], raw["task"], raw["action"], raw["result"]])
        tags = _confirm_tags(content, label)
        story_entries.append(_build_story_entry(raw, tags, role, today))

    gap_entries = []
    for i, raw in enumerate(raw_gaps):
        label = f"gap '{raw['gap_label']}'"
        content = " ".join([raw["honest_answer"], raw["bridge"], raw["redirect"]])
        tags = _confirm_tags(content, label)
        gap_entries.append(_build_gap_entry(raw, tags, role, today))

    question_entries = []
    for i, raw in enumerate(raw_questions):
        label = f"question {i+1}"
        tags = _confirm_tags(raw["text"], label)
        question_entries.append(_build_question_entry(raw, tags, role, today))

    # ── Summary and confirmation ────────────────────────────────────────────
    total = len(story_entries) + len(gap_entries) + len(question_entries)
    print(f"\nReady to write {len(story_entries)} stories, "
          f"{len(gap_entries)} gap responses, "
          f"{len(question_entries)} questions to interview_library.json.")
    answer = input(f"Write {total} entries? (y/n): ").strip().lower()
    if answer != "y":
        print("Cancelled -- no file written.")
        sys.exit(0)

    # ── Write with duplicate handling ───────────────────────────────────────
    init_library()
    library = _load_library()
    written = skipped = 0

    for entry in story_entries:
        dup = _find_duplicate_story(library, entry["employer"], entry["tags"][0] if entry["tags"] else "")
        if dup:
            if _handle_duplicate(dup, entry, library, "stories", role, entry["id"]):
                written += 1
            else:
                skipped += 1
        else:
            library["stories"].append(entry)
            written += 1

    for entry in gap_entries:
        dup = _find_duplicate_gap(library, entry["gap_label"])
        if dup:
            if _handle_duplicate(dup, entry, library, "gap_responses", role, entry["id"]):
                written += 1
            else:
                skipped += 1
        else:
            library["gap_responses"].append(entry)
            written += 1

    for entry in question_entries:
        dup = _find_duplicate_question(library, entry["text"])
        if dup:
            if _handle_duplicate(dup, entry, library, "questions", role, entry["id"]):
                written += 1
            else:
                skipped += 1
        else:
            library["questions"].append(entry)
            written += 1

    write_library(library)

    print(f"\n{'=' * 60}")
    print(f"Written: {written} entries")
    if skipped:
        print(f"Skipped: {skipped} (existing entries; roles_used updated)")
    print(f"Library: {LIBRARY_PATH}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
