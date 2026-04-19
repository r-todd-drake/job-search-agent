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

JOBS_PACKAGES_DIR = "data/job_packages"
LIBRARY_MD_PATH = "data/experience_library/experience_library.md"
REGISTRY_PATH = "data/backport_registry.json"

SKIP_SECTION_HEADERS = {"## PROFESSIONAL SUMMARY", "## CORE COMPETENCIES"}


def parse_stage_file(content: str) -> list:
    """Parse stage4_final.txt or stage2_approved.txt content.

    Returns list of {employer, bullets: [{text, theme}]}.
    """
    sections = []
    current_employer = None
    current_bullets = []
    current_bullet_text = None
    in_skip_section = False

    UNKNOWN_THEME = "UNKNOWN -- assign before committing"

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
