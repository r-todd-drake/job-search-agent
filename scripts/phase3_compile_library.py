# ==============================================
# phase3_compile_library.py
# Merges all employer JSON files and summaries
# into a single experience_library.json for
# use by the Phase 4 resume generator.
#
# Run after phase3_parse_library.py, or any
# time individual employer files are updated.
# ==============================================

import os
import json
from datetime import datetime

# ==============================================
# CONFIGURATION
# ==============================================

EMPLOYERS_DIR = "data/experience_library/employers"
SUMMARIES_PATH = "data/experience_library/summaries.json"
OUTPUT_PATH = "data/experience_library/experience_library.json"

# ==============================================
# COMPILE
# ==============================================

print("=" * 60)
print("PHASE 3 – COMPILE EXPERIENCE LIBRARY")
print("=" * 60)

# Load all employer files
if not os.path.exists(EMPLOYERS_DIR):
    print(f"ERROR: Employers directory not found: {EMPLOYERS_DIR}")
    print("Run phase3_parse_library.py first.")
    exit(1)

employer_files = [f for f in os.listdir(EMPLOYERS_DIR) if f.endswith('.json')]

if not employer_files:
    print(f"ERROR: No employer JSON files found in {EMPLOYERS_DIR}")
    print("Run phase3_parse_library.py first.")
    exit(1)

print(f"\nLoading {len(employer_files)} employer files...")

employers = []
total_bullets = 0
total_flagged = 0
total_verify = 0

for filename in sorted(employer_files):
    filepath = os.path.join(EMPLOYERS_DIR, filename)
    with open(filepath, encoding='utf-8') as f:
        emp_data = json.load(f)

    bullet_count = len(emp_data.get('bullets', []))
    flag_count = sum(1 for b in emp_data['bullets'] if b.get('flagged'))
    verify_count = sum(1 for b in emp_data['bullets'] if b.get('verify'))

    employers.append(emp_data)
    total_bullets += bullet_count
    total_flagged += flag_count
    total_verify += verify_count

    print(f"  {filename}: {bullet_count} bullets "
          f"({flag_count} flagged, {verify_count} verify)")

# Load summaries
summaries_data = {"total": 0, "summaries": []}
if os.path.exists(SUMMARIES_PATH):
    with open(SUMMARIES_PATH, encoding='utf-8') as f:
        summaries_data = json.load(f)
    print(f"\nLoaded summaries.json: {summaries_data['total']} summaries")
else:
    print(f"\nWARNING: summaries.json not found at {SUMMARIES_PATH}")
    print("Run phase3_parse_library.py to generate summaries.")

# Build compiled library
library = {
    "metadata": {
        "candidate": "R. Todd Drake",
        "last_compiled": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_employers": len(employers),
        "total_bullets": total_bullets,
        "total_flagged": total_flagged,
        "total_verify": total_verify,
        "total_summaries": summaries_data['total'],
        "employer_names": [e['name'] for e in employers]
    },
    "employers": employers,
    "summaries": summaries_data.get('summaries', [])
}

# Save compiled library
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(library, f, indent=2, ensure_ascii=False)

# Calculate file size
size_kb = os.path.getsize(OUTPUT_PATH) / 1024

print(f"\n{'=' * 60}")
print(f"COMPILE COMPLETE")
print(f"  Output: {OUTPUT_PATH}")
print(f"  File size: {size_kb:.1f} KB")
print(f"  Employers: {len(employers)}")
print(f"  Total bullets: {total_bullets}")
print(f"    Flagged (do not use): {total_flagged}")
print(f"    Verify (needs review): {total_verify}")
print(f"    Cleared for use: {total_bullets - total_flagged - total_verify}")
print(f"  Summaries: {summaries_data['total']}")
print(f"{'=' * 60}")
print(f"\nLibrary ready for Phase 4 resume generator.")
