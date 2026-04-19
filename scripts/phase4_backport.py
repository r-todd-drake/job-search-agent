# ==============================================
# phase4_backport.py
# Identifies net-new and variant resume bullets from
# stage files and stages them for backport into
# experience_library.md.
#
# Usage:
#   python scripts/phase4_backport.py --role Viasat_SE_IS
#   python scripts/phase4_backport.py --role Viasat_SE_IS --dry-run
# ==============================================

import os
import re
import json
import argparse
from datetime import date
from rapidfuzz import fuzz as _fuzz

JOBS_PACKAGES_DIR = "data/job_packages"
LIBRARY_MD_PATH = "data/experience_library/experience_library.md"
REGISTRY_PATH = "data/backport_registry.json"

SKIP_SECTION_HEADERS = {"## PROFESSIONAL SUMMARY", "## CORE COMPETENCIES"}
UNKNOWN_THEME = "UNKNOWN -- assign before committing"


def parse_stage_file(content: str) -> list:
    """Parse stage4_final.txt or stage2_approved.txt content.

    Returns list of {employer, bullets: [{text, theme}]}.
    """
    sections = []
    current_employer = None
    current_bullets = []
    current_bullet_text = None
    in_skip_section = False

    for line in content.splitlines():
        stripped = line.strip()

        # Section headers
        if stripped.startswith("## "):
            # Save previous employer
            if current_employer is not None:
                if current_bullet_text is not None:
                    current_bullets.append({"text": current_bullet_text, "theme": UNKNOWN_THEME})
                    current_bullet_text = None
                sections.append({"employer": current_employer, "bullets": current_bullets})
                current_bullets = []

            if stripped in SKIP_SECTION_HEADERS:
                in_skip_section = True
                current_employer = None
            else:
                in_skip_section = False
                current_employer = stripped[3:].strip()
            continue

        if in_skip_section:
            continue

        if current_employer is None:
            continue

        # Theme annotation for preceding bullet
        theme_match = re.match(r'^\s+\[Theme:\s*(.+?)\]\s*$', line)
        if theme_match and current_bullet_text is not None:
            theme = theme_match.group(1).strip()
            current_bullets.append({"text": current_bullet_text, "theme": theme})
            current_bullet_text = None
            continue

        # Skip metadata lines
        if stripped.startswith("[") or stripped.startswith("=") or \
           stripped.startswith("Title:") or stripped.startswith("Dates:") or \
           stripped.startswith("STAGE") or stripped.startswith("END OF") or \
           not stripped:
            # Flush pending bullet (no theme found before next content)
            if current_bullet_text is not None and stripped:
                current_bullets.append({"text": current_bullet_text, "theme": UNKNOWN_THEME})
                current_bullet_text = None
            continue

        # Bullet lines
        if stripped.startswith("- ") and not stripped.startswith("- ["):
            if current_bullet_text is not None:
                current_bullets.append({"text": current_bullet_text, "theme": UNKNOWN_THEME})
            current_bullet_text = stripped[2:].strip()
            continue

    # Flush final employer
    if current_employer is not None:
        if current_bullet_text is not None:
            current_bullets.append({"text": current_bullet_text, "theme": UNKNOWN_THEME})
        sections.append({"employer": current_employer, "bullets": current_bullets})

    return sections


def extract_library_bullets(library_md_path: str) -> list:
    """Read experience_library.md and return all employer bullets with metadata.

    Returns list of {text, theme, employer, line_number, sources}.
    Stops at PROFESSIONAL SUMMARIES section.
    """
    bullets = []
    current_employer = None
    current_theme = None
    current_bullet = None

    with open(library_md_path, encoding="utf-8") as f:
        lines = f.readlines()

    ANNOTATION_PREFIXES = ("*NOTE:", "*PRIORITY:", "*VERIFY:", "[CANONICAL", "[VERIFY", "[FLAGGED")
    for i, raw_line in enumerate(lines, start=1):
        line = raw_line.rstrip("\n")
        stripped = line.strip()

        if stripped.startswith("## PROFESSIONAL SUMMARIES"):
            if current_bullet:
                bullets.append(current_bullet)
                current_bullet = None
            break

        if stripped.startswith("## ") and not stripped.startswith("## PROFESSIONAL"):
            if current_bullet:
                bullets.append(current_bullet)
                current_bullet = None
            current_employer = stripped[3:].strip()
            current_theme = None
            continue

        if stripped.startswith("### "):
            if current_bullet:
                bullets.append(current_bullet)
                current_bullet = None
            raw_theme = stripped[4:].strip()
            if raw_theme.startswith("Theme:"):
                raw_theme = raw_theme[6:].strip()
            current_theme = raw_theme
            continue

        if stripped.startswith("- ") and not stripped.startswith("- [") and current_employer and current_theme:
            if current_bullet:
                bullets.append(current_bullet)
            bullet_text = stripped[2:].strip()
            bullet_text = bullet_text.replace("[FLAGGED]", "").replace("[VERIFY]", "").strip()
            current_bullet = {
                "text": bullet_text,
                "theme": current_theme,
                "employer": current_employer,
                "line_number": i,
                "sources": [],
            }
            continue

        if stripped.startswith("*Used in:") and current_bullet:
            src_text = stripped.replace("*Used in:", "").replace("*", "").strip()
            current_bullet["sources"] = [s.strip() for s in src_text.split(",")]
            continue

        # Annotation lines – skip explicitly; never flush current_bullet.
        # Handles: *NOTE:*, *PRIORITY:*, [CANONICAL...], [VERIFY...], [FLAGGED...]
        # These may appear between a bullet line and its *Used in:* tag.
        if any(stripped.startswith(p) for p in ANNOTATION_PREFIXES):
            continue

    if current_bullet:
        bullets.append(current_bullet)

    return bullets


def classify_bullet(
    bullet_text: str,
    library_bullets: list,
    net_new_threshold: float = 85.0,
    variant_floor: float = 60.0,
) -> dict:
    """Classify a stage file bullet against library bullets.

    Returns {classification: 'net_new'|'variant'|'present', match: dict|None, score: float}.
    """
    best_score = 0.0
    best_match = None

    for lib_bullet in library_bullets:
        score = _fuzz.token_sort_ratio(bullet_text, lib_bullet["text"])
        if score > best_score:
            best_score = score
            best_match = lib_bullet

    if best_score >= net_new_threshold:
        return {"classification": "present", "match": best_match, "score": best_score}
    elif best_score >= variant_floor:
        return {"classification": "variant", "match": best_match, "score": best_score}
    else:
        return {"classification": "net_new", "match": None, "score": best_score}


def match_employer(stage_employer: str, library_bullets: list, threshold: float = 80.0):
    """Find the best-matching employer name in library_bullets for a stage file employer.

    Returns employer name string or None if no match at or above threshold.
    """
    employer_names = list({b["employer"] for b in library_bullets})
    best_score = 0.0
    best_name = None

    for name in employer_names:
        score = _fuzz.token_sort_ratio(stage_employer, name)
        if score > best_score:
            best_score = score
            best_name = name

    return best_name if best_score >= threshold else None


def check_source_attribution(library_bullet: dict, role_source_name: str) -> bool:
    """Return True if role_source_name appears in library_bullet sources (case-insensitive)."""
    role_lower = role_source_name.lower()
    return any(role_lower == s.lower() for s in library_bullet.get("sources", []))


def generate_staged_output(
    net_new_entries: list,
    variant_entries: list,
    source_gap_entries: list,
    role_source_name: str,
) -> str:
    """Generate formatted backport staged output with net-new, variant, and source gap sections."""
    today = date.today().isoformat()
    lines = [
        f"# Backport Staged \u2013 {role_source_name}",
        f"Generated: {today}",
        "",
        "---",
        "",
        "## Net-New Bullets",
        "",
    ]

    if not net_new_entries:
        lines.append("No net-new bullets found.")
    else:
        for entry in net_new_entries:
            lines += [
                f"### {entry['employer']}",
                "",
                f"**Theme:** {entry['theme']}",
                f"- {entry['text']}",
                f"*Used in: {role_source_name}*",
                "*NOTE: [BACKPORT -- review before reuse. Outcome: recruiter callback | HM interview | panel | offer | no outcome]*",
                "",
                "---",
                "",
            ]

    lines += [
        "## Variant Bullets (Review Required)",
        "",
    ]

    if not variant_entries:
        lines.append("No variant bullets found.")
    else:
        for entry in variant_entries:
            lines += [
                f"### {entry['employer']}",
                "",
                f"**Theme:** {entry['theme']}",
                f"- {entry['text']}",
                f"*Fuzzy match score: {entry['score']:.0f}% \u2013 matched: \"{entry['matched_text']}\"*",
                "",
                "---",
                "",
            ]

    lines += [
        "## Source Gaps",
        "",
    ]

    if not source_gap_entries:
        lines.append("No source gaps found.")
    else:
        for entry in source_gap_entries:
            lines += [
                f"### {entry['employer']} (line {entry['line_number']})",
                "",
                f"- {entry['text']}",
                f"*Missing source:* `{role_source_name}` \u2013 add to `*Used in:*` at line {entry['line_number']}",
                "",
                "---",
                "",
            ]

    return "\n".join(lines)


def load_registry(path: str) -> dict:
    """Load backport_registry.json; return empty registry if file does not exist."""
    if not os.path.exists(path):
        return {"processed": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_registry(path: str, data: dict) -> None:
    """Save registry dict to JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def check_registry(registry: dict, role: str):
    """Return existing registry entry for role, or None if not found."""
    for entry in registry.get("processed", []):
        if entry.get("role") == role:
            return entry
    return None


def update_registry(registry: dict, role: str, net_new_count: int, source_gap_count: int) -> dict:
    """Append a new entry for role to registry and return the updated registry."""
    registry["processed"].append({
        "role": role,
        "date_processed": date.today().isoformat(),
        "net_new_count": net_new_count,
        "source_gap_count": source_gap_count,
        "outcome": "pending",
    })
    return registry
