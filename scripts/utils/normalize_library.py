# ==============================================
# normalize_library.py
# One-time cleanup script to consolidate the
# experience_library.md file.
#
# Merges all tranche-suffixed employer sections
# (e.g. "## SHIELD AI – Tranche 4 Additions")
# into clean single employer sections
# (e.g. "## SHIELD AI").
#
# Also merges all PROFESSIONAL SUMMARIES sections
# and removes non-bullet structural sections
# (FLAGS SUMMARY, MASTER FLAGS, etc.)
#
# Input:  data/experience_library/experience_library.md
# Output: data/experience_library/experience_library_normalized.md
#
# After verifying output is correct, replace the
# original with the normalized version.
# ==============================================

import re
import os
from datetime import datetime

INPUT_PATH = "data/experience_library/experience_library.md"
OUTPUT_PATH = "data/experience_library/experience_library_normalized.md"

# ==============================================
# KNOWN EMPLOYER CANONICAL NAMES
# Maps any variant of an employer name to its
# canonical form used as the ## header.
# Add entries here if new variants are found.
# ==============================================

EMPLOYER_CANONICAL = {
    "SARONIC TECHNOLOGIES": "SARONIC TECHNOLOGIES",
    "KFORCE": "KFORCE (Supporting Leidos / NIWC PAC)",
    "KFORCE (SUPPORTING LEIDOS / NIWC PAC)": "KFORCE (Supporting Leidos / NIWC PAC)",
    "SHIELD AI": "SHIELD AI",
    "G2 OPS": "G2 OPS",
    "SAIC": "SAIC",
    "L3 COMMUNICATIONS": "L3 COMMUNICATIONS",
    "U.S. ARMY": "U.S. ARMY",
    "EARLIER CAREER": "U.S. ARMY",
    "EARLIER CAREER – U.S. ARMY": "U.S. ARMY",
    "BATTELLE TECHNICAL HIGHLIGHTS": "BATTELLE TECHNICAL HIGHLIGHTS",
}

# Sections to skip entirely (not employer bullet sections)
SKIP_SECTIONS = [
    "FLAGS SUMMARY",
    "MASTER FLAGS",
    "ITEMS REQUIRING",
    "VERIFICATION SESSION",
    "TRANCHE NOTES",
    "PROCESSING NOTES",
    "BATTELLE TECHNICAL HIGHLIGHTS",
]

def get_canonical_employer(raw_name):
    """
    Given a raw ## header name, return the canonical employer name
    or None if this section should be skipped.
    """
    # Strip tranche suffixes
    # e.g. "SHIELD AI – Tranche 4 Additions" -> "SHIELD AI"
    # e.g. "SHIELD AI – Tranche 5 Additions" -> "SHIELD AI"
    cleaned = re.sub(
        r'\s*[–—-]+\s*Tranche\s+\d+.*$',
        '',
        raw_name,
        flags=re.IGNORECASE
    ).strip()

    # Strip "Additions" suffix if somehow remaining
    cleaned = re.sub(r'\s+Additions$', '', cleaned, flags=re.IGNORECASE).strip()

    # Check skip list
    for skip in SKIP_SECTIONS:
        if skip.upper() in cleaned.upper():
            return None

    # Check canonical map (case insensitive)
    upper = cleaned.upper()
    for key, canonical in EMPLOYER_CANONICAL.items():
        if key.upper() == upper or upper.startswith(key.upper()):
            return canonical

    # If not in map, return cleaned name as-is (will be treated as new employer)
    return cleaned

def is_summaries_header(stripped):
    """Check if this line is any variant of the PROFESSIONAL SUMMARIES header."""
    return 'PROFESSIONAL SUMMARIES' in stripped.upper()

def is_employer_header(stripped):
    """Check if this line is a ## employer section header."""
    return (stripped.startswith('## ')
            and not stripped.startswith('### ')
            and not is_summaries_header(stripped))

# ==============================================
# PARSE INTO SECTIONS
# ==============================================

print("=" * 60)
print("NORMALIZE EXPERIENCE LIBRARY")
print("=" * 60)
print(f"\nInput:  {INPUT_PATH}")
print(f"Output: {OUTPUT_PATH}")

with open(INPUT_PATH, encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

# Data structures
file_header_lines = []      # Lines before first ## section
employer_sections = {}      # canonical_name -> list of content lines
summaries_lines = []        # All summaries content
current_section = None      # Current canonical employer name or "SUMMARIES"
current_lines = []          # Lines accumulated for current section
in_file_header = True
skip_current = False

for line in lines:
    stripped = line.strip()

    # Accumulate file header (everything before first ## section)
    if in_file_header:
        if is_employer_header(stripped) or is_summaries_header(stripped):
            in_file_header = False
            # Fall through to section handling below
        else:
            file_header_lines.append(line)
            continue

    # Detect new section
    if stripped.startswith('## ') and not stripped.startswith('### '):

        # Save previous section
        if current_section and not skip_current and current_lines:
            if current_section == "SUMMARIES":
                summaries_lines.extend(current_lines)
            else:
                if current_section not in employer_sections:
                    employer_sections[current_section] = []
                employer_sections[current_section].extend(current_lines)

        # Determine new section type
        if is_summaries_header(stripped):
            current_section = "SUMMARIES"
            skip_current = False
            current_lines = []
        else:
            raw_name = stripped[3:].strip()
            canonical = get_canonical_employer(raw_name)
            if canonical is None:
                skip_current = True
                current_section = None
                current_lines = []
            else:
                skip_current = False
                current_section = canonical
                current_lines = []
        continue

    # Accumulate content for current section
    if not skip_current and current_section:
        current_lines.append(line)

# Save final section
if current_section and not skip_current and current_lines:
    if current_section == "SUMMARIES":
        summaries_lines.extend(current_lines)
    else:
        if current_section not in employer_sections:
            employer_sections[current_section] = []
        employer_sections[current_section].extend(current_lines)

# ==============================================
# REPORT WHAT WAS FOUND
# ==============================================

print(f"\nSections found:")
for name, content in employer_sections.items():
    bullet_count = sum(1 for l in content if l.strip().startswith('- '))
    print(f"  {name}: {bullet_count} bullets ({len(content)} lines)")
print(f"  SUMMARIES: {len(summaries_lines)} lines")

# ==============================================
# WRITE NORMALIZED OUTPUT
# ==============================================

# Define output order
EMPLOYER_ORDER = [
    "SARONIC TECHNOLOGIES",
    "KFORCE (Supporting Leidos / NIWC PAC)",
    "SHIELD AI",
    "G2 OPS",
    "SAIC",
    "L3 COMMUNICATIONS",
    "U.S. ARMY",
    "BATTELLE TECHNICAL HIGHLIGHTS",
]

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    # Write updated file header
    for line in file_header_lines:
        # Update the "Last built" line
        if '# Last built:' in line:
            f.write(f"# Last built: {datetime.now().strftime('%d %b %Y')} (normalized)\n")
        else:
            f.write(line)

    # Write employer sections in order
    for emp_name in EMPLOYER_ORDER:
        if emp_name in employer_sections:
            f.write(f"\n## {emp_name}\n")
            for line in employer_sections[emp_name]:
                f.write(line)

    # Write any employers not in the predefined order
    for emp_name, content in employer_sections.items():
        if emp_name not in EMPLOYER_ORDER:
            f.write(f"\n## {emp_name}\n")
            for line in content:
                f.write(line)

    # Write summaries
    if summaries_lines:
        f.write("\n## PROFESSIONAL SUMMARIES (Archived by Role Target)\n")
        for line in summaries_lines:
            f.write(line)

output_size = os.path.getsize(OUTPUT_PATH) / 1024

print(f"\nNormalized file written: {OUTPUT_PATH}")
print(f"File size: {output_size:.1f} KB")
print(f"\nNext steps:")
print(f"  1. Review {OUTPUT_PATH} in VS Code to verify structure")
print(f"  2. If correct, replace experience_library.md with normalized version")
print(f"  3. Run phase3_parse_library.py to confirm clean parse")
