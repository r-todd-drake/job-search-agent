# scripts/utils/writing_rules.py

from pathlib import Path

_WRITING_RULES_PATH = Path("context/writing_rules.md")
_rules = None


def load():
    """Return the full text of context/writing_rules.md, cached after first read."""
    global _rules
    if _rules is None:
        if not _WRITING_RULES_PATH.exists():
            raise FileNotFoundError(
                f"writing_rules.md not found at {_WRITING_RULES_PATH}. "
                "Create context/writing_rules.md with the project's prose writing rules."
            )
        with open(_WRITING_RULES_PATH, encoding="utf-8") as f:
            _rules = f.read()
    return _rules
