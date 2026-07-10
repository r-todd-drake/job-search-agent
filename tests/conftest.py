import pytest
from pathlib import Path
from unittest.mock import MagicMock


def pytest_sessionfinish(session, exitstatus):
    """Exit with code 0 when no tests are collected (empty suite is valid)."""
    if exitstatus == 5:
        session.exitstatus = 0


@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def mock_anthropic(mocker):
    """Shared mock factory. Patch path is set per-test to match the script's import."""
    return mocker


@pytest.fixture
def pii_values():
    return {
        "name": "Jane Q. Applicant",
        "phone": "(555) 867-5309",
        "email": "applicant@example.com",
        "linkedin": "linkedin.com/in/applicant",
        "github": "github.com/applicant",
    }


def make_mock_response(text):
    """Build a minimal Anthropic API response mock for a given text string."""
    mock = MagicMock()
    mock.content = [MagicMock(text=text)]
    return mock
