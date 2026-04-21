import pytest


def test_validate_role_accepts_valid_name():
    from scripts.init_job_package import validate_role
    validate_role("Anduril_EW_SE")  # should not raise


def test_validate_role_rejects_slash():
    from scripts.init_job_package import validate_role
    with pytest.raises(ValueError, match="invalid characters"):
        validate_role("Anduril/EW/SE")


def test_validate_role_rejects_backslash():
    from scripts.init_job_package import validate_role
    with pytest.raises(ValueError, match="invalid characters"):
        validate_role("Anduril\\EW")


def test_validate_role_rejects_empty():
    from scripts.init_job_package import validate_role
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_role("")


def test_validate_req_accepts_valid_req():
    from scripts.init_job_package import validate_req
    validate_req("REQ-12345")  # should not raise


def test_validate_req_rejects_empty():
    from scripts.init_job_package import validate_req
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_req("")
