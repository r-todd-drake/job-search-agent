import pytest
from pathlib import Path

from scripts.utils.build_docs import (
    ASSEMBLED_HEADER,
    find_markers,
    assemble_document,
)


class TestFindMarkers:
    def test_single_marker(self):
        content = "Before\n{{include: my_fragment}}\nAfter"
        assert find_markers(content) == ["my_fragment"]

    def test_multiple_markers(self):
        content = "{{include: frag_a}}\n\n{{include: frag_b}}"
        assert find_markers(content) == ["frag_a", "frag_b"]

    def test_no_markers(self):
        content = "No markers here at all"
        assert find_markers(content) == []

    def test_marker_with_underscore_name(self):
        content = "{{include: current_phase_status}}"
        assert find_markers(content) == ["current_phase_status"]


class TestAssembleDocument:
    def test_replaces_single_marker(self, tmp_path):
        frags = tmp_path / "fragments"
        frags.mkdir()
        (frags / "my_frag.md").write_text("Fragment body")

        result = assemble_document("Before\n{{include: my_frag}}\nAfter", frags)

        assert "Fragment body" in result
        assert "{{include: my_frag}}" not in result

    def test_replaces_multiple_markers(self, tmp_path):
        frags = tmp_path / "fragments"
        frags.mkdir()
        (frags / "a.md").write_text("AAA")
        (frags / "b.md").write_text("BBB")

        result = assemble_document("{{include: a}}\n{{include: b}}", frags)

        assert "AAA" in result
        assert "BBB" in result

    def test_prepends_assembled_header(self, tmp_path):
        frags = tmp_path / "fragments"
        frags.mkdir()

        result = assemble_document("No markers", frags)

        assert result.startswith(ASSEMBLED_HEADER)

    def test_raises_on_missing_fragment(self, tmp_path):
        frags = tmp_path / "fragments"
        frags.mkdir()

        with pytest.raises(FileNotFoundError, match="missing_frag"):
            assemble_document("{{include: missing_frag}}", frags, template_name="test.md")

    def test_error_message_includes_template_name(self, tmp_path):
        frags = tmp_path / "fragments"
        frags.mkdir()

        with pytest.raises(FileNotFoundError, match="mytemplate.md"):
            assemble_document("{{include: gone}}", frags, template_name="mytemplate.md")

    def test_fragments_not_recursively_processed(self, tmp_path):
        frags = tmp_path / "fragments"
        frags.mkdir()
        (frags / "outer.md").write_text("{{include: inner}}")

        result = assemble_document("{{include: outer}}", frags)

        assert "{{include: inner}}" in result

    def test_header_prepended_once(self, tmp_path):
        frags = tmp_path / "fragments"
        frags.mkdir()
        (frags / "frag.md").write_text("content")

        result = assemble_document("{{include: frag}}", frags)

        assert result.count(ASSEMBLED_HEADER) == 1

    def test_idempotent_run_produces_identical_file(self, tmp_path):
        frags = tmp_path / "fragments"
        frags.mkdir()
        (frags / "frag.md").write_text("Fragment body")

        template_path = tmp_path / "template.md"
        target_path = tmp_path / "output.md"
        template_path.write_text("## Section\n\n{{include: frag}}\n")

        # Simulate _run: assemble and write twice
        for _ in range(2):
            content = template_path.read_text(encoding="utf-8")
            output = assemble_document(content, frags, "template.md")
            target_path.write_text(output, encoding="utf-8")

        final = target_path.read_text(encoding="utf-8")
        assert final.count(ASSEMBLED_HEADER) == 1
        assert "Fragment body" in final

    def test_no_markers_content_preserved(self, tmp_path):
        frags = tmp_path / "fragments"
        frags.mkdir()
        body = "# Title\n\nSome text\n\nMore text"

        result = assemble_document(body, frags)

        assert body in result


class TestCLI:
    def test_unknown_doc_flag_exits_nonzero(self):
        import subprocess
        result = subprocess.run(
            ["python", "scripts/utils/build_docs.py", "--doc", "NONEXISTENT.md"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "Unknown document" in result.stdout or "Unknown document" in result.stderr
