# ==============================================
# phase4_backport.py
# Identifies net-new and variant resume bullets from
# stage files and stages them for backport into
# experience_library.md.
#
# Usage:
#   python -m scripts.phase4_backport --role Viasat_SE_IS
#   python -m scripts.phase4_backport --role Viasat_SE_IS --dry-run
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


def normalize_role_source_name(role: str) -> str:
    """Append _Resume suffix to role if not already present."""
    if role.endswith("_Resume"):
        return role
    return f"{role}_Resume"


def resolve_input_file(package_dir: str) -> tuple:
    """Return (absolute_path, filename) for the best available stage input file.

    Prefers stage4_final.txt; falls back to stage2_approved.txt.
    Raises FileNotFoundError with a clear message if neither exists.
    """
    stage4 = os.path.join(package_dir, "stage4_final.txt")
    stage2 = os.path.join(package_dir, "stage2_approved.txt")
    if os.path.exists(stage4):
        return stage4, "stage4_final.txt"
    if os.path.exists(stage2):
        return stage2, "stage2_approved.txt"
    raise FileNotFoundError(
        f"Neither stage4_final.txt nor stage2_approved.txt found in {package_dir}.\n"
        "Complete Stage 2 or Stage 4 before running backport."
    )


def main(
    role: str,
    package_dir: str,
    library_md_path: str,
    registry_path: str,
    dry_run: bool = False,
    net_new_threshold: float = 85.0,
    variant_floor: float = 60.0,
) -> None:
    print("=" * 60)
    print("PHASE 4 \u2013 EXPERIENCE LIBRARY BACKPORT")
    print("=" * 60)

    # Registry duplicate check
    registry = load_registry(registry_path)
    existing = check_registry(registry, role)
    if existing:
        print(f"WARNING: {role} has already been processed on {existing['date_processed']}.")
        print("  Re-running will append a duplicate registry entry.")
        print("  Proceeding anyway \u2013 review backport_staged.md before committing.\n")

    # Resolve input file
    input_path, input_filename = resolve_input_file(package_dir)
    print(f"  Input file: {input_filename}")

    # Parse stage file
    content = open(input_path, encoding="utf-8").read()
    stage_sections = parse_stage_file(content)
    total_stage_bullets = sum(len(s["bullets"]) for s in stage_sections)
    print(f"  Stage bullets parsed: {total_stage_bullets}")

    # Extract library bullets
    library_bullets = extract_library_bullets(library_md_path)
    print(f"  Library bullets loaded: {len(library_bullets)}")

    role_source_name = normalize_role_source_name(role)

    net_new_entries = []
    variant_entries = []
    source_gap_entries = []
    present_count = 0

    for section in stage_sections:
        stage_employer = section["employer"]
        matched_employer = match_employer(stage_employer, library_bullets)

        if matched_employer is None:
            print(f"  WARNING: Employer '{stage_employer}' not found in library \u2013 skipping section.")
            continue

        employer_lib_bullets = [b for b in library_bullets if b["employer"] == matched_employer]

        for bullet in section["bullets"]:
            result = classify_bullet(
                bullet["text"],
                employer_lib_bullets,
                net_new_threshold=net_new_threshold,
                variant_floor=variant_floor,
            )

            if result["classification"] == "net_new":
                net_new_entries.append({
                    "employer": stage_employer,
                    "text": bullet["text"],
                    "theme": bullet["theme"],
                })
            elif result["classification"] == "variant":
                variant_entries.append({
                    "employer": stage_employer,
                    "text": bullet["text"],
                    "theme": bullet["theme"],
                    "matched_text": result["match"]["text"],
                    "score": result["score"],
                })
            else:  # present
                present_count += 1
                lib_bullet = result["match"]
                if not check_source_attribution(lib_bullet, role_source_name):
                    source_gap_entries.append({
                        "text": lib_bullet["text"],
                        "employer": matched_employer,
                        "theme": lib_bullet["theme"],
                        "line_number": lib_bullet["line_number"],
                        "matched_sources": lib_bullet["sources"],
                    })

    # Summary
    print(f"\n  Results:")
    print(f"    Net-new bullets:  {len(net_new_entries)}")
    print(f"    Variant bullets:  {len(variant_entries)}")
    print(f"    Present bullets:  {present_count}")
    print(f"    Source gaps:      {len(source_gap_entries)}")

    if dry_run:
        print("\n  Dry run \u2013 no files written.")
        return

    # Write backport_staged.md
    output_path = os.path.join(package_dir, "backport_staged.md")
    staged_content = generate_staged_output(
        net_new_entries, variant_entries, source_gap_entries, role_source_name
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(staged_content)
    print(f"\n  Written: {output_path}")

    # Update registry
    registry = update_registry(registry, role, len(net_new_entries), len(source_gap_entries))
    save_registry(registry_path, registry)
    print(f"  Registry updated: {registry_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Stage net-new resume bullets for backport into experience_library.md"
    )
    parser.add_argument("--role", required=True, help="Role slug (e.g. Viasat_SE_IS)")
    parser.add_argument("--dry-run", action="store_true", help="Print findings without writing files")
    parser.add_argument("--net-new-threshold", type=float, default=85.0,
                        help="Fuzzy match threshold for 'present' classification (default: 85)")
    parser.add_argument("--variant-floor", type=float, default=60.0,
                        help="Fuzzy match floor for 'variant' classification (default: 60)")
    args = parser.parse_args()

    package_dir = os.path.join(JOBS_PACKAGES_DIR, args.role)
    if not os.path.isdir(package_dir):
        print(f"ERROR: Job package directory not found: {package_dir}")
        raise SystemExit(1)

    main(
        role=args.role,
        package_dir=package_dir,
        library_md_path=LIBRARY_MD_PATH,
        registry_path=REGISTRY_PATH,
        dry_run=args.dry_run,
        net_new_threshold=args.net_new_threshold,
        variant_floor=args.variant_floor,
    )
