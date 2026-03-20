from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from pdf_diff.cli import app


def test_diff_command_generates_unified_diff(tmp_path: Path) -> None:
    left = tmp_path / "left.md"
    right = tmp_path / "right.md"
    output = tmp_path / "diff.txt"

    left.write_text("# Title\n\n- apples\n- oranges\n", encoding="utf-8")
    right.write_text("# Title\n\n- apples\n- bananas\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "diff",
            str(left),
            str(right),
            "--renderer",
            "unified",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert output.exists()

    diff_text = output.read_text(encoding="utf-8")
    assert "---" in diff_text
    assert "+++" in diff_text
    assert "-- oranges" in diff_text
    assert "+- bananas" in diff_text
