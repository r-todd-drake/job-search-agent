import json
import os

LIBRARY_PATH = "data/interview_library.json"
TAGS_PATH = "data/interview_library_tags.json"

_EMPTY_LIBRARY = {"stories": [], "gap_responses": [], "questions": []}


def init_library():
    """Create empty library file if it does not exist. Never overwrites existing content."""
    if os.path.exists(LIBRARY_PATH):
        return
    os.makedirs(os.path.dirname(LIBRARY_PATH), exist_ok=True)
    with open(LIBRARY_PATH, "w", encoding="utf-8") as f:
        json.dump(dict(_EMPTY_LIBRARY), f, indent=2)


def _load_library():
    """Load library from disk. Returns empty structure if file absent."""
    if not os.path.exists(LIBRARY_PATH):
        return {k: list(v) for k, v in _EMPTY_LIBRARY.items()}
    with open(LIBRARY_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_tags():
    """Load controlled tag vocabulary. Returns empty list if file absent."""
    if not os.path.exists(TAGS_PATH):
        return []
    with open(TAGS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("tags", [])
