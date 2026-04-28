import csv
import os
import pytest
from datetime import date
from unittest.mock import patch, MagicMock, call
from scripts.init_job_package import (
    validate_role,
    validate_req,
    load_csv_rows,
    check_conflicts,
    create_job_folder,
    create_job_description,
    append_csv_row,
    open_file_in_editor,
    collect_optional_fields,
    main,
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


def test_append_csv_row_full_row_completeness(tmp_path):
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "company,title,location,salary_range,url,req_number,date_found,status,package_folder\n"
    )
    extra_fields = {
        "company": "Acme Corp",
        "title": "Software Engineer",
        "location": "Austin TX",
        "salary_range": "$120k-$150k",
        "url": "https://jobs.acme.com/123",
    }
    append_csv_row(str(csv_file), "Acme_SE", "REQ-1", extra_fields)
    rows = list(csv.DictReader(open(str(csv_file))))
    assert rows[0]["company"] == "Acme Corp"
    assert rows[0]["title"] == "Software Engineer"
    assert rows[0]["location"] == "Austin TX"
    assert rows[0]["salary_range"] == "$120k-$150k"
    assert rows[0]["url"] == "https://jobs.acme.com/123"
    assert rows[0]["req_number"] == "REQ-1"
    assert rows[0]["package_folder"] == "Acme_SE"
    assert rows[0]["date_found"] == str(date.today())


def test_append_csv_row_extra_fields_none_becomes_empty_string(tmp_path):
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "company,title,location,salary_range,url,req_number,date_found,status,package_folder\n"
    )
    extra_fields = {"company": None, "title": "Engineer", "location": None, "salary_range": None, "url": None}
    append_csv_row(str(csv_file), "Acme_SE", "REQ-1", extra_fields)
    rows = list(csv.DictReader(open(str(csv_file))))
    assert rows[0]["company"] == ""
    assert rows[0]["title"] == "Engineer"
    assert rows[0]["location"] == ""
    assert rows[0]["salary_range"] == ""
    assert rows[0]["url"] == ""


def test_collect_optional_fields_all_provided():
    responses = iter(["Acme Corp", "Software Engineer", "Austin TX", "$120k-$150k", "https://jobs.acme.com/123"])
    result = collect_optional_fields(input_fn=lambda _: next(responses))
    assert result == {
        "company": "Acme Corp",
        "title": "Software Engineer",
        "location": "Austin TX",
        "salary_range": "$120k-$150k",
        "url": "https://jobs.acme.com/123",
    }


def test_collect_optional_fields_all_skipped():
    result = collect_optional_fields(input_fn=lambda _: "")
    assert result == {
        "company": None,
        "title": None,
        "location": None,
        "salary_range": None,
        "url": None,
    }


def test_collect_optional_fields_mixed():
    responses = iter(["Acme Corp", "", "Austin TX", "", ""])
    result = collect_optional_fields(input_fn=lambda _: next(responses))
    assert result["company"] == "Acme Corp"
    assert result["title"] is None
    assert result["location"] == "Austin TX"
    assert result["salary_range"] is None
    assert result["url"] is None


def test_collect_optional_fields_strips_whitespace():
    result = collect_optional_fields(input_fn=lambda _: "  Acme Corp  ")
    assert result["company"] == "Acme Corp"
    result2 = collect_optional_fields(input_fn=lambda _: "   ")
    assert result2["company"] is None


def test_collect_optional_fields_prompt_labels():
    prompts_seen = []

    def capture_input(prompt):
        prompts_seen.append(prompt)
        return ""

    collect_optional_fields(input_fn=capture_input)
    assert len(prompts_seen) == 5
    assert any("Company" in p for p in prompts_seen)
    assert any("Title" in p for p in prompts_seen)
    assert any("Location" in p for p in prompts_seen)
    assert any("Salary" in p for p in prompts_seen)
    assert any("URL" in p for p in prompts_seen)


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


def test_main_happy_path_calls_all_side_effects(tmp_path, capsys):
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "package_folder,status,req_number,date_found,company,title,location,salary_range,url\n"
    )
    mock_folder_creator = MagicMock(return_value=str(tmp_path / "Anduril_SE"))
    mock_file_creator = MagicMock(
        return_value=str(tmp_path / "Anduril_SE" / "job_description.txt")
    )
    mock_csv_appender = MagicMock()
    mock_file_opener = MagicMock()

    exit_code = main(
        role="Anduril_SE",
        req="REQ-1",
        packages_dir=str(tmp_path),
        jobs_csv=str(csv_file),
        folder_creator=mock_folder_creator,
        file_creator=mock_file_creator,
        csv_appender=mock_csv_appender,
        file_opener=mock_file_opener,
        folder_exists=lambda p: False,
        input_fn=lambda _: "",
    )

    assert exit_code == 0
    mock_folder_creator.assert_called_once_with(str(tmp_path), "Anduril_SE")
    mock_file_creator.assert_called_once_with(str(tmp_path / "Anduril_SE"))
    mock_csv_appender.assert_called_once_with(
        str(csv_file),
        "Anduril_SE",
        "REQ-1",
        {"company": None, "title": None, "location": None, "salary_range": None, "url": None},
    )
    mock_file_opener.assert_called_once()
    captured = capsys.readouterr()
    assert "job_description.txt" in captured.out


def test_main_true_duplicate_exits_without_side_effects(tmp_path, capsys):
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "package_folder,status,req_number,date_found\nAnduril_SE,PURSUE,REQ-1,2026-01-01\n"
    )
    mock_folder_creator = MagicMock()
    mock_csv_appender = MagicMock()

    exit_code = main(
        role="Anduril_SE",
        req="REQ-1",
        packages_dir=str(tmp_path),
        jobs_csv=str(csv_file),
        folder_creator=mock_folder_creator,
        file_creator=MagicMock(),
        csv_appender=mock_csv_appender,
        file_opener=MagicMock(),
        folder_exists=lambda p: False,
    )

    assert exit_code == 1
    mock_folder_creator.assert_not_called()
    mock_csv_appender.assert_not_called()
    captured = capsys.readouterr()
    assert "REQ-1" in captured.out


def test_main_inactive_reactivation_exits_with_instructions(tmp_path, capsys):
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "package_folder,status,req_number,date_found\nAnduril_SE,SKIP,REQ-1,2026-01-01\n"
    )
    mock_folder_creator = MagicMock()
    mock_csv_appender = MagicMock()

    exit_code = main(
        role="Anduril_SE",
        req="REQ-1",
        packages_dir=str(tmp_path),
        jobs_csv=str(csv_file),
        folder_creator=mock_folder_creator,
        file_creator=MagicMock(),
        csv_appender=mock_csv_appender,
        file_opener=MagicMock(),
        folder_exists=lambda p: False,
    )

    assert exit_code == 1
    mock_folder_creator.assert_not_called()
    mock_csv_appender.assert_not_called()
    captured = capsys.readouterr()
    assert "reactivat" in captured.out.lower()


def test_main_folder_collision_prompts_for_suffix_and_creates_with_new_name(tmp_path, capsys):
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "package_folder,status,req_number,date_found,company,title,location,salary_range,url\n"
    )

    def folder_exists(path):
        return os.path.basename(path) == "Anduril_SE"

    mock_folder_creator = MagicMock(return_value=str(tmp_path / "Anduril_SE_2"))
    mock_file_creator = MagicMock(
        return_value=str(tmp_path / "Anduril_SE_2" / "job_description.txt")
    )
    mock_csv_appender = MagicMock()
    # First call: suffix prompt returns "_2"; next 5 calls: field prompts return "" (skip all)
    input_fn = MagicMock(side_effect=["_2", "", "", "", "", ""])

    exit_code = main(
        role="Anduril_SE",
        req="REQ-99",
        packages_dir=str(tmp_path),
        jobs_csv=str(csv_file),
        folder_creator=mock_folder_creator,
        file_creator=mock_file_creator,
        csv_appender=mock_csv_appender,
        file_opener=MagicMock(),
        folder_exists=folder_exists,
        input_fn=input_fn,
    )

    assert exit_code == 0
    mock_folder_creator.assert_called_once_with(str(tmp_path), "Anduril_SE_2")
    mock_csv_appender.assert_called_once_with(
        str(csv_file),
        "Anduril_SE_2",
        "REQ-99",
        {"company": None, "title": None, "location": None, "salary_range": None, "url": None},
    )


def test_main_optional_fields_passed_to_csv_appender(tmp_path):
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "package_folder,status,req_number,date_found,company,title,location,salary_range,url\n"
    )
    mock_csv_appender = MagicMock()
    responses = iter(["Acme Corp", "Software Engineer", "", "", ""])

    main(
        role="Acme_SE",
        req="REQ-1",
        packages_dir=str(tmp_path),
        jobs_csv=str(csv_file),
        folder_creator=MagicMock(return_value=str(tmp_path / "Acme_SE")),
        file_creator=MagicMock(return_value=str(tmp_path / "Acme_SE" / "job_description.txt")),
        csv_appender=mock_csv_appender,
        file_opener=MagicMock(),
        folder_exists=lambda p: False,
        input_fn=lambda _: next(responses),
    )

    mock_csv_appender.assert_called_once_with(
        str(csv_file),
        "Acme_SE",
        "REQ-1",
        {"company": "Acme Corp", "title": "Software Engineer", "location": None, "salary_range": None, "url": None},
    )


def test_main_date_found_auto_populated_not_prompted(tmp_path):
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "package_folder,status,req_number,date_found,company,title,location,salary_range,url\n"
    )
    prompt_count = 0

    def counting_input_fn(_):
        nonlocal prompt_count
        prompt_count += 1
        return ""

    main(
        role="Acme_SE",
        req="REQ-1",
        packages_dir=str(tmp_path),
        jobs_csv=str(csv_file),
        folder_creator=MagicMock(return_value=str(tmp_path / "Acme_SE")),
        file_creator=MagicMock(return_value=str(tmp_path / "Acme_SE" / "job_description.txt")),
        csv_appender=MagicMock(),
        file_opener=MagicMock(),
        folder_exists=lambda p: False,
        input_fn=counting_input_fn,
    )

    assert prompt_count == 5  # company, title, location, salary_range, url -- not date_found


def test_main_prompts_not_shown_on_true_duplicate(tmp_path):
    csv_file = tmp_path / "jobs.csv"
    csv_file.write_text(
        "package_folder,status,req_number,date_found\nAcme_SE,PURSUE,REQ-1,2026-01-01\n"
    )
    prompt_count = 0

    def counting_input_fn(_):
        nonlocal prompt_count
        prompt_count += 1
        return ""

    exit_code = main(
        role="Acme_SE",
        req="REQ-1",
        packages_dir=str(tmp_path),
        jobs_csv=str(csv_file),
        folder_creator=MagicMock(),
        file_creator=MagicMock(),
        csv_appender=MagicMock(),
        file_opener=MagicMock(),
        folder_exists=lambda p: False,
        input_fn=counting_input_fn,
    )

    assert exit_code == 1
    assert prompt_count == 0
