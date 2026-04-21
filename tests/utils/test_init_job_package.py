import pytest
from scripts.init_job_package import validate_role, validate_req


def test_validate_role_accepts_valid_name():
    validate_role("Anduril_EW_SE")  # should not raise


def test_validate_role_rejects_slash():
    with pytest.raises(ValueError, match="invalid characters"):
        validate_role("Anduril/EW/SE")


def test_validate_role_rejects_backslash():
    with pytest.raises(ValueError, match="invalid characters"):
        validate_role("Anduril\\EW")


def test_validate_role_rejects_empty():
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_role("")


def test_validate_req_accepts_valid_req():
    validate_req("REQ-12345")  # should not raise


def test_validate_req_rejects_empty():
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_req("")
