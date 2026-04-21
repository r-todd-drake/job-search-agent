import csv
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


def test_load_csv_rows_returns_list_of_dicts(tmp_path):
    from scripts.init_job_package import load_csv_rows
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text("package_folder,status,req_number\nAnduril_SE,PURSUE,REQ-1\n")
    rows = load_csv_rows(str(csv_file))
    assert len(rows) == 1
    assert rows[0]["package_folder"] == "Anduril_SE"
    assert rows[0]["req_number"] == "REQ-1"


def test_check_conflicts_true_duplicate_active_status():
    from scripts.init_job_package import check_conflicts
    rows = [{"package_folder": "Anduril_SE", "status": "PURSUE", "req_number": "REQ-1"}]
    assert check_conflicts(rows, "Anduril_SE", "REQ-1") == "true_duplicate"


def test_check_conflicts_true_duplicate_blank_status():
    from scripts.init_job_package import check_conflicts
    rows = [{"package_folder": "Anduril_SE", "status": "", "req_number": "REQ-1"}]
    assert check_conflicts(rows, "Anduril_SE", "REQ-1") == "true_duplicate"


def test_check_conflicts_true_duplicate_applied_same_role():
    # APPLIED is an active status — same role + same req# is still a hard duplicate
    from scripts.init_job_package import check_conflicts
    rows = [{"package_folder": "Anduril_SE", "status": "APPLIED", "req_number": "REQ-1"}]
    assert check_conflicts(rows, "Anduril_SE", "REQ-1") == "true_duplicate"


def test_check_conflicts_inactive_skip():
    from scripts.init_job_package import check_conflicts
    rows = [{"package_folder": "Anduril_SE", "status": "SKIP", "req_number": "REQ-1"}]
    assert check_conflicts(rows, "Anduril_SE", "REQ-1") == "inactive_reactivation"


def test_check_conflicts_inactive_ghosted():
    from scripts.init_job_package import check_conflicts
    rows = [{"package_folder": "Anduril_SE", "status": "GHOSTED", "req_number": "REQ-1"}]
    assert check_conflicts(rows, "Anduril_SE", "REQ-1") == "inactive_reactivation"


def test_check_conflicts_same_req_different_employer_no_conflict():
    # Same req# but different package_folder = different employer — allow creation
    from scripts.init_job_package import check_conflicts
    rows = [{"package_folder": "Anduril_SE", "status": "PURSUE", "req_number": "REQ-1"}]
    assert check_conflicts(rows, "Boeing_SE", "REQ-1") is None


def test_check_conflicts_no_conflict():
    from scripts.init_job_package import check_conflicts
    rows = [{"package_folder": "Anduril_SE", "status": "PURSUE", "req_number": "REQ-1"}]
    assert check_conflicts(rows, "Boeing_SE", "REQ-999") is None
