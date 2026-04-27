# tests/phase6/test_phase6_networking_live.py
"""
Tier 2 live API tests for phase6_networking.
Calls the real Claude API. Run manually -- not in CI.

Run: pytest tests/phase6/test_phase6_networking_live.py -v -s
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import scripts.phase6_networking as pn
from tests.fixtures.contact_fixture import COLD, ACQUAINTANCE, FORMER_COLLEAGUE, STRONG

CANDIDATE_FIXTURE = {
    "clearance": {"status": "Current", "level": "TS/SCI"},
    "military": {"service": [{"branch": "US Army", "dates": "2001-2009"}]},
    "confirmed_skills": {"programming": "Python, MATLAB"},
}

JD_FIXTURE = (
    "Systems Engineering Director -- Acme Defense Systems. "
    "Lead MBSE and digital engineering initiatives across the enterprise. "
    "TS/SCI required. 10+ years SE experience in defense."
)


@pytest.mark.live
@pytest.mark.parametrize("contact,label", [
    (COLD, "Cold"),
    (ACQUAINTANCE, "Acquaintance"),
    (FORMER_COLLEAGUE, "Former Colleague"),
    (STRONG, "Strong"),
])
def test_stage1_live_all_warmth_tiers(contact, label):
    result = pn.generate_message(1, contact, CANDIDATE_FIXTURE)
    print(f"\n--- Stage 1 / {label} ---\n{result}")
    assert isinstance(result, str)
    assert len(result) > 20
    if label in ("Acquaintance",):
        assert "[HOW YOU KNOW THIS PERSON]" in result
    if label in ("Former Colleague",):
        assert "[WHERE YOU WORKED TOGETHER]" in result


@pytest.mark.live
def test_stage2_live_strong_with_referral_bonus():
    contact = {**STRONG, "referral_bonus": "$5,000"}
    result = pn.generate_message(2, contact, CANDIDATE_FIXTURE, jd_text=JD_FIXTURE)
    print(f"\n--- Stage 2 / Strong + referral bonus ---\n{result}")
    assert isinstance(result, str)
    assert len(result) > 50


@pytest.mark.live
def test_stage2_live_acquaintance_no_referral_bonus():
    contact = {**ACQUAINTANCE, "referral_bonus": None}
    result = pn.generate_message(2, contact, CANDIDATE_FIXTURE, jd_text=JD_FIXTURE)
    print(f"\n--- Stage 2 / Acquaintance, no referral bonus ---\n{result}")
    assert "referral bonus" not in result.lower()
