from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
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


def test_diff_command_accepts_pdf_vs_pdf(tmp_path: Path) -> None:
    left_pdf = tmp_path / "left.pdf"
    right_pdf = tmp_path / "right.pdf"
    output = tmp_path / "pdf_diff.txt"

    _write_test_pdf(left_pdf, text="PDF left text")
    _write_test_pdf(right_pdf, text="PDF right text")

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "diff",
            str(left_pdf),
            str(right_pdf),
            "--renderer",
            "unified",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert output.exists()

    diff_text = output.read_text(encoding="utf-8")
    assert "PDF left text" in diff_text
    assert "PDF right text" in diff_text


def test_diff_command_accepts_markdown_vs_pdf(tmp_path: Path) -> None:
    left_md = tmp_path / "left.md"
    right_pdf = tmp_path / "right.pdf"
    output = tmp_path / "mixed_diff.txt"

    left_md.write_text("# Mixed Input\n\n- source is markdown\n", encoding="utf-8")
    _write_test_pdf(right_pdf, text="source is pdf")

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "diff",
            str(left_md),
            str(right_pdf),
            "--renderer",
            "unified",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert output.exists()

    diff_text = output.read_text(encoding="utf-8")
    assert "source is markdown" in diff_text
    assert "source is pdf" in diff_text


def _write_test_pdf(path: Path, *, text: str) -> None:
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=144)

    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    font_reference = writer._add_object(font)

    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_reference})}
    )

    content_stream = DecodedStreamObject()
    escaped_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content_stream.set_data(f"BT /F1 12 Tf 36 100 Td ({escaped_text}) Tj ET".encode("utf-8"))
    page[NameObject("/Contents")] = writer._add_object(content_stream)

    with path.open("wb") as handle:
        writer.write(handle)


def test_diff_command_json_format(tmp_path: Path) -> None:
    left = tmp_path / "left.md"
    right = tmp_path / "right.md"

    left.write_text("# Title\n\n- apples\n- oranges\n", encoding="utf-8")
    right.write_text("# Title\n\n- apples\n- bananas\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "diff",
            str(left),
            str(right),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0, result.output
    output_json = json.loads(result.output)

    assert "left" in output_json
    assert "right" in output_json
    assert "stats" in output_json
    assert "lines_added" in output_json["stats"]
    assert "lines_removed" in output_json["stats"]
    assert output_json["stats"]["lines_added"] > 0
    assert output_json["stats"]["lines_removed"] > 0


def test_diff_command_stat_output(tmp_path: Path) -> None:
    left = tmp_path / "left.md"
    right = tmp_path / "right.md"

    left.write_text("# Title\n\n- apples\n- oranges\n- grapes\n", encoding="utf-8")
    right.write_text("# Title\n\n- apples\n- bananas\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "diff",
            str(left),
            str(right),
            "--stat",
        ],
    )

    assert result.exit_code == 0, result.output
    stat_output = result.output

    assert "Left file:" in stat_output
    assert "Right file:" in stat_output
    assert "Lines added:" in stat_output
    assert "Lines removed:" in stat_output
    assert "Total changes:" in stat_output


def test_diff_command_lines_changed_only(tmp_path: Path) -> None:
    left = tmp_path / "left.md"
    right = tmp_path / "right.md"

    left.write_text(
        "# Title\n\nContext line\n- apples\n- oranges\nMore context\n",
        encoding="utf-8",
    )
    right.write_text(
        "# Title\n\nContext line\n- bananas\nMore context\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "diff",
            str(left),
            str(right),
            "--lines-changed",
        ],
    )

    assert result.exit_code == 0, result.output
    diff_output = result.output

    assert "-" in diff_output
    assert "+" in diff_output
    assert "Context line" not in diff_output or diff_output.count("Context line") <= 1


def test_diff_command_renderer_ndiff(tmp_path: Path) -> None:
    left = tmp_path / "left.md"
    right = tmp_path / "right.md"

    left.write_text("alpha\nbeta\n", encoding="utf-8")
    right.write_text("alpha\ngamma\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "diff",
            str(left),
            str(right),
            "--renderer",
            "ndiff",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "- beta" in result.output
    assert "+ gamma" in result.output


def test_diff_command_renderer_html(tmp_path: Path) -> None:
    left = tmp_path / "left.md"
    right = tmp_path / "right.md"

    left.write_text("alpha\nbeta\n", encoding="utf-8")
    right.write_text("alpha\ngamma\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "diff",
            str(left),
            str(right),
            "--renderer",
            "html",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "<!DOCTYPE html" in result.output
    assert "gamma" in result.output


def test_diff_command_renderer_delta_alias_maps_to_unified(tmp_path: Path) -> None:
    left = tmp_path / "left.md"
    right = tmp_path / "right.md"

    left.write_text("alpha\nbeta\n", encoding="utf-8")
    right.write_text("alpha\ngamma\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "diff",
            str(left),
            str(right),
            "--renderer",
            "delta",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "---" in result.output
    assert "+++" in result.output
