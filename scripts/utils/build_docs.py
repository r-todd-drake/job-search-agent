"""Assemble project documents from templates and fragments.

Usage:
    python scripts/utils/build_docs.py           # assemble all documents
    python scripts/utils/build_docs.py --all     # same as above
    python scripts/utils/build_docs.py --doc README.md   # single document
"""

import argparse
import re
import sys
from pathlib import Path

FRAGMENTS_DIR = Path("docs/fragments")
TEMPLATES_DIR = Path("docs/templates")

ASSEMBLED_HEADER = (
    "<!-- assembled by build_docs.py"
    " -- edit docs/templates/ and docs/fragments/ not this file -->"
)

TARGET_PATHS: dict[str, Path] = {
    "README.md": Path("README.md"),
    "PROJECT_CONTEXT.md": Path("context/PROJECT_CONTEXT.md"),
}

_MARKER_RE = re.compile(r"\{\{include:\s*(\w+)\s*\}\}")


def find_markers(content: str) -> list[str]:
    return _MARKER_RE.findall(content)


def assemble_document(
    template_content: str,
    fragments_dir: Path,
    template_name: str = "unknown",
) -> str:
    missing: list[str] = []

    def _replace(match: re.Match) -> str:
        name = match.group(1)
        fragment_path = fragments_dir / f"{name}.md"
        if not fragment_path.exists():
            missing.append(
                f"ERROR: Fragment '{name}.md' not found"
                f" (referenced in template '{template_name}')"
            )
            return match.group(0)
        return fragment_path.read_text(encoding="utf-8")

    assembled = _MARKER_RE.sub(_replace, template_content)

    if missing:
        raise FileNotFoundError("\n".join(missing))

    return ASSEMBLED_HEADER + "\n" + assembled


def _run(templates: list[str]) -> int:
    assembled_count = 0
    fragment_count = 0
    errors = 0

    for template_name in templates:
        template_path = TEMPLATES_DIR / template_name
        target_path = TARGET_PATHS[template_name]

        try:
            content = template_path.read_text(encoding="utf-8")
            n_fragments = len(find_markers(content))
            output = assemble_document(content, FRAGMENTS_DIR, template_name)
            target_path.write_text(output, encoding="utf-8")
            print(f"  assembled: {template_name} -> {target_path} ({n_fragments} fragment(s))")
            assembled_count += 1
            fragment_count += n_fragments
        except FileNotFoundError as exc:
            print(str(exc))
            errors += 1

    print(
        f"\nDone: {assembled_count} document(s) assembled,"
        f" {fragment_count} fragment(s) resolved",
        end="",
    )
    if errors:
        print(f", {errors} error(s)")
    else:
        print()

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Assemble project documents from templates and fragments."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Assemble all documents (default)")
    group.add_argument(
        "--doc",
        metavar="FILENAME",
        help="Assemble one document by template filename (e.g. README.md)",
    )
    args = parser.parse_args()

    if not TEMPLATES_DIR.exists():
        print(f"ERROR: Templates directory not found: {TEMPLATES_DIR}")
        sys.exit(1)

    if args.doc:
        if args.doc not in TARGET_PATHS:
            known = ", ".join(TARGET_PATHS)
            print(f"ERROR: Unknown document '{args.doc}'. Known: {known}")
            sys.exit(1)
        templates = [args.doc]
    else:
        templates = list(TARGET_PATHS.keys())

    errors = _run(templates)
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
