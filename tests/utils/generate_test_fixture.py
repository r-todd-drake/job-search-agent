# ==============================================
# utils/generate_test_fixture.py
# One-time dev utility. Generates tests/fixtures/library/experience_library.md
# from the real experience_library.md, preserving real format fidelity.
#
# Usage (run from project root):
#   python tests/utils/generate_test_fixture.py
#   python tests/utils/generate_test_fixture.py --employers 3 --summaries 3
# ==============================================

import argparse
import re

LIBRARY_PATH = "data/experience_library/experience_library.md"
OUTPUT_PATH = "tests/fixtures/library/experience_library.md"


def generate_fixture(library_path: str, output_path: str, employers: int, summaries: int) -> None:
    with open(library_path, encoding="utf-8") as f:
        lines = f.readlines()

    output_lines = []
    current_employer_count = 0
    current_summary_count = 0
    in_summaries = False
    in_employer = False
    employer_bullet_count = 0
    max_bullets_per_employer = 3
    skip_employer = False

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Top-level header — always include
        if stripped.startswith("# ") and not stripped.startswith("## "):
            output_lines.append(line)
            i += 1
            continue

        # PROFESSIONAL SUMMARIES section
        if stripped.startswith("## PROFESSIONAL SUMMARIES"):
            in_summaries = True
            in_employer = False
            output_lines.append(line)
            i += 1
            continue

        if in_summaries:
            if stripped.startswith("### "):
                if current_summary_count >= summaries:
                    break
                current_summary_count += 1
                output_lines.append(line)
                i += 1
                continue
            output_lines.append(line)
            i += 1
            continue

        # Employer section header
        if stripped.startswith("## "):
            if current_employer_count >= employers:
                skip_employer = True
                i += 1
                continue
            current_employer_count += 1
            employer_bullet_count = 0
            skip_employer = False
            in_employer = True
            output_lines.append(line)
            i += 1
            continue

        if skip_employer:
            i += 1
            continue

        # Inside employer section — limit bullets
        if in_employer and stripped.startswith("- ") and not stripped.startswith("- ["):
            if employer_bullet_count >= max_bullets_per_employer:
                # Skip this bullet and its annotation lines
                i += 1
                while i < len(lines):
                    next_stripped = lines[i].strip()
                    if next_stripped.startswith("- ") or next_stripped.startswith("## ") or \
                       next_stripped.startswith("### "):
                        break
                    i += 1
                continue
            employer_bullet_count += 1
            output_lines.append(line)
            i += 1
            continue

        output_lines.append(line)
        i += 1

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(output_lines)

    print(f"Fixture written to {output_path}")
    print(f"  Employers included: {current_employer_count}")
    print(f"  Summaries included: {current_summary_count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate library test fixture from real experience_library.md")
    parser.add_argument("--employers", type=int, default=3, help="Number of employer sections to include")
    parser.add_argument("--summaries", type=int, default=3, help="Number of summary entries to include")
    args = parser.parse_args()
    generate_fixture(LIBRARY_PATH, OUTPUT_PATH, args.employers, args.summaries)
