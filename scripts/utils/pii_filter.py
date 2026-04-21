# ==============================================
# pii_filter.py
# Strips direct PII from text before sending
# to external APIs (Anthropic, web search, etc.)
#
# PII values are loaded from .env – never
# hardcoded in this file.
#
# Add to .env:
#   CANDIDATE_NAME=Your Full Name
#   CANDIDATE_PHONE=(xxx) xxx-xxxx
#   CANDIDATE_EMAIL=your@email.com
#   CANDIDATE_LINKEDIN=linkedin.com/in/yourprofile
#   CANDIDATE_GITHUB=github.com/yourusername
#
# Usage:
#   from scripts.utils.pii_filter import strip_pii
#   safe_text = strip_pii(candidate_profile)
# ==============================================

import os
import re
from dotenv import load_dotenv

load_dotenv()

def get_pii_replacements():
    """
    Build PII replacement pairs from environment variables.
    Each tuple is (pattern_to_find, replacement_string).
    Empty values are skipped safely.
    """
    replacements = []

    # Candidate name – also handle common variants
    name = os.getenv('CANDIDATE_NAME', '')
    if name:
        replacements.append((re.escape(name), '[CANDIDATE]'))
        # Also catch last name only if name has multiple parts
        parts = name.strip().split()
        if len(parts) >= 2:
            last_name = parts[-1]
            # Only replace standalone last name (word boundary)
            replacements.append((r'\b' + re.escape(last_name) + r'\b', '[CANDIDATE]'))

    # Phone number
    phone = os.getenv('CANDIDATE_PHONE', '')
    if phone:
        replacements.append((re.escape(phone), '[PHONE]'))
        # Also catch common format variants (dashes, dots, spaces)
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 10:
            pattern = (r'\(?' + digits[:3] + r'\)?[\s.\-]?' +
                      digits[3:6] + r'[\s.\-]?' + digits[6:])
            replacements.append((pattern, '[PHONE]'))

    # Email
    email = os.getenv('CANDIDATE_EMAIL', '')
    if email:
        replacements.append((re.escape(email), '[EMAIL]'))

    # LinkedIn URL – handle with and without https://www.
    linkedin = os.getenv('CANDIDATE_LINKEDIN', '')
    if linkedin:
        # Strip protocol prefix for matching
        clean = re.sub(r'^https?://(www\.)?', '', linkedin)
        replacements.append((re.escape(clean), '[LINKEDIN]'))
        replacements.append((re.escape('https://www.' + clean), '[LINKEDIN]'))
        replacements.append((re.escape('https://' + clean), '[LINKEDIN]'))

    # GitHub URL – handle with and without https://
    github = os.getenv('CANDIDATE_GITHUB', '')
    if github:
        clean = re.sub(r'^https?://', '', github)
        replacements.append((re.escape(clean), '[GITHUB]'))
        replacements.append((re.escape('https://' + clean), '[GITHUB]'))

    return replacements


def strip_pii(text):
    """
    Remove direct PII from text before sending to external API.
    Career content and background details are preserved.
    Only contact identifiers are replaced with placeholders.

    Args:
        text: String that may contain PII

    Returns:
        String with PII replaced by safe placeholders
    """
    if not text:
        return text

    replacements = get_pii_replacements()

    for pattern, replacement in replacements:
        if pattern:
            try:
                text = re.sub(pattern, replacement,
                             text, flags=re.IGNORECASE)
            except re.error:
                # If pattern is invalid, skip silently
                pass

    return text


def verify_strip(text):
    """
    Check if any known PII remains in text after stripping.
    Returns list of detected PII types – empty list means clean.
    Use for testing and validation.
    """
    detected = []

    checks = [
        ('CANDIDATE_NAME',     'name'),
        ('CANDIDATE_PHONE',    'phone'),
        ('CANDIDATE_EMAIL',    'email'),
        ('CANDIDATE_LINKEDIN', 'linkedin'),
        ('CANDIDATE_GITHUB',   'github'),
    ]

    for env_key, label in checks:
        value = os.getenv(env_key, '')
        if value and value.lower() in text.lower():
            detected.append(label)

    return detected


# ==============================================
# STANDALONE TEST
# Run: python -m scripts.utils.pii_filter
# ==============================================

if __name__ == '__main__':
    print("PII Filter – Standalone Test")
    print("=" * 40)

    # Check env vars are loaded
    checks = [
        ('CANDIDATE_NAME',     'Name'),
        ('CANDIDATE_PHONE',    'Phone'),
        ('CANDIDATE_EMAIL',    'Email'),
        ('CANDIDATE_LINKEDIN', 'LinkedIn'),
        ('CANDIDATE_GITHUB',   'GitHub'),
    ]

    print("Environment variables loaded:")
    all_loaded = True
    for key, label in checks:
        val = os.getenv(key, '')
        if val:
            print(f"  {label}: ✓ ({val[:20]}...)" if len(val) > 20
                  else f"  {label}: ✓ ({val})")
        else:
            print(f"  {label}: ✗ NOT SET – add {key} to .env")
            all_loaded = False

    if not all_loaded:
        print("\nWARNING: Some PII values not configured.")
        print("Add missing values to .env before using pii_filter.")
    else:
        # Run a quick test
        name = os.getenv('CANDIDATE_NAME', '')
        email = os.getenv('CANDIDATE_EMAIL', '')
        phone = os.getenv('CANDIDATE_PHONE', '')

        test_text = f"""
CANDIDATE: {name}
Contact: {email} | {phone}
Background: Senior Systems Engineer with 20+ years experience.
Clearance: Current TS/SCI
"""
        filtered = strip_pii(test_text)
        remaining = verify_strip(filtered)

        print("\nTest input:")
        print(test_text)
        print("After strip_pii():")
        print(filtered)

        if remaining:
            print(f"WARNING: PII still detected: {remaining}")
        else:
            print("✓ All PII successfully stripped")
