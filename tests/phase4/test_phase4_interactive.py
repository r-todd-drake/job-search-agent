# tests/phase4/test_phase4_interactive.py

import sys
import os
import pytest
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch


def test_list_eligible_roles_finds_valid_roles(tmp_path):
    (tmp_path / "Alpha_Corp_PM").mkdir()
    (tmp_path / "Alpha_Corp_PM" / "job_description.txt").write_text("JD text")
    (tmp_path / "Beta_Inc_SE").mkdir()
    (tmp_path / "Beta_Inc_SE" / "job_description.txt").write_text("JD text")

    from scripts.phase4_interactive import list_eligible_roles
    roles = list_eligible_roles(jobs_dir=str(tmp_path))
    assert roles == ["Alpha_Corp_PM", "Beta_Inc_SE"]


def test_list_eligible_roles_skips_folder_without_jd(tmp_path):
    (tmp_path / "EmptyRole").mkdir()  # no job_description.txt
    (tmp_path / "ValidRole").mkdir()
    (tmp_path / "ValidRole" / "job_description.txt").write_text("JD")

    from scripts.phase4_interactive import list_eligible_roles
    roles = list_eligible_roles(jobs_dir=str(tmp_path))
    assert roles == ["ValidRole"]


def test_list_eligible_roles_excludes_inactive(tmp_path):
    inactive = tmp_path / "inactive"
    inactive.mkdir()
    (inactive / "job_description.txt").write_text("JD")  # should be excluded
    (tmp_path / "ActiveRole").mkdir()
    (tmp_path / "ActiveRole" / "job_description.txt").write_text("JD")

    from scripts.phase4_interactive import list_eligible_roles
    roles = list_eligible_roles(jobs_dir=str(tmp_path))
    assert roles == ["ActiveRole"]
    assert "inactive" not in roles


def test_list_eligible_roles_returns_empty_when_jobs_dir_missing(tmp_path):
    nonexistent = tmp_path / "does_not_exist"
    from scripts.phase4_interactive import list_eligible_roles
    assert list_eligible_roles(jobs_dir=str(nonexistent)) == []


def test_open_file_linux(monkeypatch):
    mock_popen = MagicMock()
    monkeypatch.setattr(sys, "platform", "linux")
    import subprocess as _sub
    monkeypatch.setattr(_sub, "Popen", mock_popen)

    from scripts.phase4_interactive import open_file
    open_file("/tmp/test.txt")

    mock_popen.assert_called_once_with(["xdg-open", "/tmp/test.txt"])


def test_open_file_macos(monkeypatch):
    mock_popen = MagicMock()
    monkeypatch.setattr(sys, "platform", "darwin")
    import subprocess as _sub
    monkeypatch.setattr(_sub, "Popen", mock_popen)

    from scripts.phase4_interactive import open_file
    open_file("/tmp/test.txt")

    mock_popen.assert_called_once_with(["open", "/tmp/test.txt"])


def test_open_file_win32(monkeypatch):
    mock_startfile = MagicMock()
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(os, "startfile", mock_startfile, raising=False)

    from scripts.phase4_interactive import open_file
    open_file("C:/tmp/test.txt")

    mock_startfile.assert_called_once_with("C:/tmp/test.txt")


def test_main_exits_when_library_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.phase4_interactive.EXPERIENCE_LIBRARY_JSON",
                        str(tmp_path / "missing.json"))
    monkeypatch.setattr("scripts.phase4_interactive.JOBS_PACKAGES_DIR", str(tmp_path))

    from scripts.phase4_interactive import main
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1


def test_main_exits_when_no_eligible_roles(tmp_path, monkeypatch):
    lib_path = tmp_path / "exp_lib.json"
    lib_path.write_text("{}")
    monkeypatch.setattr("scripts.phase4_interactive.EXPERIENCE_LIBRARY_JSON", str(lib_path))
    monkeypatch.setattr("scripts.phase4_interactive.JOBS_PACKAGES_DIR", str(tmp_path))
    # tmp_path has no role subfolders

    from scripts.phase4_interactive import main
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1


def _setup_role(tmp_path, role_name="TestRole"):
    """Helper: create a minimal job package and return (lib_path, role_dir)."""
    role_dir = tmp_path / role_name
    role_dir.mkdir()
    (role_dir / "job_description.txt").write_text("JD content")
    lib_path = tmp_path / "exp_lib.json"
    lib_path.write_text('{"employers": [], "summaries": []}')
    return lib_path, role_dir


def test_main_stage1_creates_stage2_copy(tmp_path, monkeypatch):
    lib_path, role_dir = _setup_role(tmp_path)

    monkeypatch.setattr("scripts.phase4_interactive.JOBS_PACKAGES_DIR", str(tmp_path))
    monkeypatch.setattr("scripts.phase4_interactive.EXPERIENCE_LIBRARY_JSON", str(lib_path))
    monkeypatch.setattr("scripts.phase4_interactive.RESUMES_DIR", str(tmp_path / "resumes"))

    # run_stage1 must actually write the file so the copy step works
    def fake_run_stage1(client, jd_text, library, candidate_profile, output_path):
        Path(output_path).write_text("stage1 draft content")

    monkeypatch.setattr("scripts.phase4_interactive.run_stage1", fake_run_stage1)
    monkeypatch.setattr("scripts.phase4_interactive.run_stage3", MagicMock())
    monkeypatch.setattr("scripts.phase4_interactive.stage4_generate_docx",
                        MagicMock(return_value=str(tmp_path / "resume.docx")))
    monkeypatch.setattr("scripts.phase4_interactive.open_file", MagicMock())
    monkeypatch.setattr("scripts.phase4_interactive.Anthropic", MagicMock())
    monkeypatch.setattr("scripts.phase4_interactive.load_library",
                        MagicMock(return_value={"employers": [], "summaries": []}))
    monkeypatch.setattr("scripts.phase4_interactive.load_candidate_profile",
                        MagicMock(return_value="profile"))

    # Sequence: role=1, s1_review_done, s3_accept, docx_done
    responses = iter(["1", "", "a", ""])
    monkeypatch.setattr("builtins.input", lambda _="": next(responses))

    from scripts.phase4_interactive import main
    main()

    stage2 = role_dir / "stage2_approved.txt"
    assert stage2.exists()
    assert stage2.read_text() == "stage1 draft content"


def test_main_stage1_preserves_user_edited_stage2(tmp_path, monkeypatch):
    """If the user Save-As's their edited stage1_draft.txt directly into
    stage2_approved.txt in their editor (the workflow documented in
    context/STAGE_FILES.md: "stage2_approved.txt | User (manual edit from
    stage1_draft.txt)"), pressing Enter to continue must NOT clobber those
    edits by copying the untouched stage1_draft.txt over them."""
    lib_path, role_dir = _setup_role(tmp_path)

    monkeypatch.setattr("scripts.phase4_interactive.JOBS_PACKAGES_DIR", str(tmp_path))
    monkeypatch.setattr("scripts.phase4_interactive.EXPERIENCE_LIBRARY_JSON", str(lib_path))
    monkeypatch.setattr("scripts.phase4_interactive.RESUMES_DIR", str(tmp_path / "resumes"))

    def fake_run_stage1(client, jd_text, library, candidate_profile, output_path):
        Path(output_path).write_text("stage1 draft content")

    monkeypatch.setattr("scripts.phase4_interactive.run_stage1", fake_run_stage1)
    monkeypatch.setattr("scripts.phase4_interactive.run_stage3", MagicMock())
    monkeypatch.setattr("scripts.phase4_interactive.stage4_generate_docx",
                        MagicMock(return_value=str(tmp_path / "resume.docx")))
    monkeypatch.setattr("scripts.phase4_interactive.open_file", MagicMock())
    monkeypatch.setattr("scripts.phase4_interactive.Anthropic", MagicMock())
    monkeypatch.setattr("scripts.phase4_interactive.load_library",
                        MagicMock(return_value={"employers": [], "summaries": []}))
    monkeypatch.setattr("scripts.phase4_interactive.load_candidate_profile",
                        MagicMock(return_value="profile"))

    stage2 = role_dir / "stage2_approved.txt"
    responses = ["1", "", "a", ""]
    call_count = {"n": 0}

    def fake_input(prompt=""):
        idx = call_count["n"]
        call_count["n"] += 1
        if idx == 1:
            # Simulate the user Save-As'ing their edits into stage2_approved.txt
            # in their editor, before pressing Enter here.
            stage2.write_text("stage1 draft content -- user edited by hand")
        return responses[idx]

    monkeypatch.setattr("builtins.input", fake_input)

    from scripts.phase4_interactive import main
    main()

    assert stage2.read_text() == "stage1 draft content -- user edited by hand"


def test_main_stage3_rerun_then_accept(tmp_path, monkeypatch):
    lib_path, role_dir = _setup_role(tmp_path)

    monkeypatch.setattr("scripts.phase4_interactive.JOBS_PACKAGES_DIR", str(tmp_path))
    monkeypatch.setattr("scripts.phase4_interactive.EXPERIENCE_LIBRARY_JSON", str(lib_path))
    monkeypatch.setattr("scripts.phase4_interactive.RESUMES_DIR", str(tmp_path / "resumes"))

    def fake_run_stage1(client, jd_text, library, candidate_profile, output_path):
        Path(output_path).write_text("stage1 content")

    mock_stage3 = MagicMock()
    monkeypatch.setattr("scripts.phase4_interactive.run_stage1", fake_run_stage1)
    monkeypatch.setattr("scripts.phase4_interactive.run_stage3", mock_stage3)
    monkeypatch.setattr("scripts.phase4_interactive.stage4_generate_docx",
                        MagicMock(return_value=str(tmp_path / "resume.docx")))
    monkeypatch.setattr("scripts.phase4_interactive.open_file", MagicMock())
    monkeypatch.setattr("scripts.phase4_interactive.Anthropic", MagicMock())
    monkeypatch.setattr("scripts.phase4_interactive.load_library",
                        MagicMock(return_value={"employers": [], "summaries": []}))
    monkeypatch.setattr("scripts.phase4_interactive.load_candidate_profile",
                        MagicMock(return_value="profile"))

    # Sequence: role=1, s1_done, s3_rerun, rerun_ready, s3_accept, docx_done
    responses = iter(["1", "", "r", "", "a", ""])
    monkeypatch.setattr("builtins.input", lambda _="": next(responses))

    from scripts.phase4_interactive import main
    main()

    # run_stage3 should have been called twice
    assert mock_stage3.call_count == 2
    stage4 = role_dir / "stage4_final.txt"
    assert stage4.exists()


def test_main_stage1_api_failure_exits(tmp_path, monkeypatch):
    lib_path, role_dir = _setup_role(tmp_path)

    monkeypatch.setattr("scripts.phase4_interactive.JOBS_PACKAGES_DIR", str(tmp_path))
    monkeypatch.setattr("scripts.phase4_interactive.EXPERIENCE_LIBRARY_JSON", str(lib_path))

    monkeypatch.setattr("scripts.phase4_interactive.run_stage1",
                        MagicMock(side_effect=Exception("API error")))
    monkeypatch.setattr("scripts.phase4_interactive.Anthropic", MagicMock())
    monkeypatch.setattr("scripts.phase4_interactive.load_library",
                        MagicMock(return_value={"employers": [], "summaries": []}))
    monkeypatch.setattr("scripts.phase4_interactive.load_candidate_profile",
                        MagicMock(return_value="profile"))

    responses = iter(["1"])
    monkeypatch.setattr("builtins.input", lambda _="": next(responses))

    from scripts.phase4_interactive import main
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1


def test_main_stage3_api_failure_exits(tmp_path, monkeypatch):
    lib_path, role_dir = _setup_role(tmp_path)

    monkeypatch.setattr("scripts.phase4_interactive.JOBS_PACKAGES_DIR", str(tmp_path))
    monkeypatch.setattr("scripts.phase4_interactive.EXPERIENCE_LIBRARY_JSON", str(lib_path))
    monkeypatch.setattr("scripts.phase4_interactive.RESUMES_DIR", str(tmp_path / "resumes"))

    def fake_run_stage1(client, jd_text, library, candidate_profile, output_path):
        Path(output_path).write_text("stage1 content")

    monkeypatch.setattr("scripts.phase4_interactive.run_stage1", fake_run_stage1)
    monkeypatch.setattr("scripts.phase4_interactive.run_stage3",
                        MagicMock(side_effect=Exception("Stage 3 API error")))
    monkeypatch.setattr("scripts.phase4_interactive.open_file", MagicMock())
    monkeypatch.setattr("scripts.phase4_interactive.Anthropic", MagicMock())
    monkeypatch.setattr("scripts.phase4_interactive.load_library",
                        MagicMock(return_value={"employers": [], "summaries": []}))
    monkeypatch.setattr("scripts.phase4_interactive.load_candidate_profile",
                        MagicMock(return_value="profile"))

    responses = iter(["1", ""])
    monkeypatch.setattr("builtins.input", lambda _="": next(responses))

    from scripts.phase4_interactive import main
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1


def test_main_open_file_oserror_continues(tmp_path, monkeypatch, capsys):
    lib_path, role_dir = _setup_role(tmp_path)

    monkeypatch.setattr("scripts.phase4_interactive.JOBS_PACKAGES_DIR", str(tmp_path))
    monkeypatch.setattr("scripts.phase4_interactive.EXPERIENCE_LIBRARY_JSON", str(lib_path))
    monkeypatch.setattr("scripts.phase4_interactive.RESUMES_DIR", str(tmp_path / "resumes"))

    def fake_run_stage1(client, jd_text, library, candidate_profile, output_path):
        Path(output_path).write_text("stage1 content")

    monkeypatch.setattr("scripts.phase4_interactive.run_stage1", fake_run_stage1)
    monkeypatch.setattr("scripts.phase4_interactive.run_stage3", MagicMock())
    monkeypatch.setattr("scripts.phase4_interactive.stage4_generate_docx",
                        MagicMock(return_value=str(tmp_path / "resume.docx")))
    monkeypatch.setattr("scripts.phase4_interactive.Anthropic", MagicMock())
    monkeypatch.setattr("scripts.phase4_interactive.load_library",
                        MagicMock(return_value={"employers": [], "summaries": []}))
    monkeypatch.setattr("scripts.phase4_interactive.load_candidate_profile",
                        MagicMock(return_value="profile"))
    # open_file raises OSError every time
    monkeypatch.setattr("scripts.phase4_interactive.open_file",
                        MagicMock(side_effect=OSError("no default app")))

    responses = iter(["1", "", "a", ""])
    monkeypatch.setattr("builtins.input", lambda _="": next(responses))

    from scripts.phase4_interactive import main
    main()  # Should NOT raise — OSError is caught and handled

    captured = capsys.readouterr()
    assert "Could not open the file automatically" in captured.out
