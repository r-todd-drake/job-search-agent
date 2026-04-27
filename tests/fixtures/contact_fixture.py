# tests/fixtures/contact_fixture.py
"""
Fictional fixture contacts for Phase 6 tests.
Jane Q. Applicant at Acme Defense Systems -- four warmth variants.
"""

BASE = {
    "contact_name": "Jane Q. Applicant",
    "company": "Acme Defense Systems",
    "title": "Systems Engineering Director",
    "linkedin_url": "https://linkedin.com/in/janequapplicant",
    "source": "LinkedIn search",
    "first_contact": None,
    "response_date": None,
    "stage": 1,
    "status": "Active",
    "role_activated": None,
    "referral_bonus": None,
    "notes": "",
}

COLD = {**BASE, "warmth": "Cold", "notes": ""}

ACQUAINTANCE = {
    **BASE,
    "warmth": "Acquaintance",
    "notes": "Met at AUSA Annual Meeting 2024, discussed LTAMDS program sustainment",
}

FORMER_COLLEAGUE = {
    **BASE,
    "warmth": "Former Colleague",
    "notes": "Worked together at Raytheon, Advanced Concepts group, 2019-2022",
}

STRONG = {
    **BASE,
    "warmth": "Strong",
    "notes": "Close colleague from Raytheon; collaborated on multiple capture efforts",
}

ALL_VARIANTS = [COLD, ACQUAINTANCE, FORMER_COLLEAGUE, STRONG]
