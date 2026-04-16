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


def get_stories(tags=None, role=None, stage=None):
    """Return story entries matching all provided filters (AND logic).

    tags:  list of tag strings -- story matches if it has ANY listed tag (OR within tags).
    role:  role slug -- story must include this slug in roles_used.
    stage: accepted for API compatibility; not applied (stories have no stage field).

    Returns empty list on no match or absent library.
    """
    library = _load_library()
    results = library.get("stories", [])
    if tags:
        results = [s for s in results if any(t in s.get("tags", []) for t in tags)]
    if role:
        results = [s for s in results if role in s.get("roles_used", [])]
    return results
