import csv
import os
import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from scripts.init_job_package import (
    validate_role,
    validate_req,
    load_csv_rows,
    check_conflicts,
    create_job_folder,
    create_job_description,
    append_csv_row,
    open_file_in_editor,
)


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
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text("package_folder,status,req_number\nAnduril_SE,PURSUE,REQ-1\n")
    rows = load_csv_rows(str(csv_file))
    assert len(rows) == 1
    assert rows[0]["package_folder"] == "Anduril_SE"
    assert rows[0]["req_number"] == "REQ-1"


def test_check_conflicts_true_duplicate_active_status():
    rows = [{"package_folder": "Anduril_SE", "status": "PURSUE", "req_number": "REQ-1"}]
    assert check_conflicts(rows, "Anduril_SE", "REQ-1") == "true_duplicate"


def test_check_conflicts_true_duplicate_blank_status():
    rows = [{"package_folder": "Anduril_SE", "status": "", "req_number": "REQ-1"}]
    assert check_conflicts(rows, "Anduril_SE", "REQ-1") == "true_duplicate"


def test_check_conflicts_true_duplicate_applied_same_role():
    rows = [{"package_folder": "Anduril_SE", "status": "APPLIED", "req_number": "REQ-1"}]
    assert check_conflicts(rows, "Anduril_SE", "REQ-1") == "true_duplicate"


def test_check_conflicts_inactive_skip():
    rows = [{"package_folder": "Anduril_SE", "status": "SKIP", "req_number": "REQ-1"}]
    assert check_conflicts(rows, "Anduril_SE", "REQ-1") == "inactive_reactivation"


def test_check_conflicts_inactive_ghosted():
    rows = [{"package_folder": "Anduril_SE", "status": "GHOSTED", "req_number": "REQ-1"}]
    assert check_conflicts(rows, "Anduril_SE", "REQ-1") == "inactive_reactivation"


def test_check_conflicts_same_req_different_employer_no_conflict():
    rows = [{"package_folder": "Anduril_SE", "status": "PURSUE", "req_number": "REQ-1"}]
    assert check_conflicts(rows, "Boeing_SE", "REQ-1") is None


def test_check_conflicts_no_conflict():
    rows = [{"package_folder": "Anduril_SE", "status": "PURSUE", "req_number": "REQ-1"}]
    assert check_conflicts(rows, "Boeing_SE", "REQ-999") is None


def test_create_job_folder_creates_directory(tmp_path):
    path = create_job_folder(str(tmp_path), "Anduril_SE")
    assert os.path.isdir(path)
    assert path.endswith("Anduril_SE")


def test_create_job_description_creates_empty_file(tmp_path):
    folder = tmp_path / "Anduril_SE"
    folder.mkdir()
    jd_path = create_job_description(str(folder))
    assert os.path.isfile(jd_path)
    with open(jd_path) as f:
        assert f.read() == ""


def test_append_csv_row_adds_row(tmp_path):
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "package_folder,status,req_number,date_found,company,title,location,salary_range,url\n"
    )
    append_csv_row(str(csv_file), "Anduril_SE", "REQ-1")
    rows = list(csv.DictReader(open(str(csv_file))))
    assert len(rows) == 1
    assert rows[0]["package_folder"] == "Anduril_SE"
    assert rows[0]["req_number"] == "REQ-1"
    assert rows[0]["status"] == ""


def test_append_csv_row_sets_date_found(tmp_path):
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "package_folder,status,req_number,date_found,company,title,location,salary_range,url\n"
    )
    append_csv_row(str(csv_file), "Anduril_SE", "REQ-1")
    rows = list(csv.DictReader(open(str(csv_file))))
    assert rows[0]["date_found"] == str(date.today())


def test_open_file_in_editor_calls_code(tmp_path):
    dummy_file = str(tmp_path / "job_description.txt")
    open(dummy_file, "w").close()
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        open_file_in_editor(dummy_file)
    call_args = mock_run.call_args[0][0]
    assert call_args[0] == "code"
    assert dummy_file in call_args


def test_open_file_in_editor_falls_back_when_code_not_found(tmp_path):
    dummy_file = str(tmp_path / "job_description.txt")
    open(dummy_file, "w").close()
    with patch("subprocess.run", side_effect=FileNotFoundError):
        with patch("sys.platform", "win32"):
            with patch("os.startfile", create=True) as mock_startfile:
                open_file_in_editor(dummy_file)
    mock_startfile.assert_called_once_with(dummy_file)


def test_open_file_in_editor_non_fatal_when_both_fail(tmp_path, capsys):
    dummy_file = str(tmp_path / "job_description.txt")
    open(dummy_file, "w").close()
    with patch("subprocess.run", side_effect=FileNotFoundError):
        with patch("sys.platform", "win32"):
            with patch("os.startfile", create=True, side_effect=Exception("fail")):
                open_file_in_editor(dummy_file)  # must not raise
    captured = capsys.readouterr()
    assert "Warning" in captured.out
