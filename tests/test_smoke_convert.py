from __future__ import annotations

from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from typer.testing import CliRunner

from pdf_diff.cli import app


def test_convert_command_writes_markdown(tmp_path: Path) -> None:
    input_pdf = tmp_path / "sample.pdf"
    output_markdown = tmp_path / "sample.md"
    _write_test_pdf(input_pdf, text="Hello PDF Diff")

    runner = CliRunner()
    result = runner.invoke(app, ["convert", str(input_pdf), "--output", str(output_markdown)])

    assert result.exit_code == 0, result.output
    assert output_markdown.exists()

    markdown = output_markdown.read_text(encoding="utf-8")
    assert "Hello PDF Diff" in markdown
    assert "<!-- page: 1 -->" in markdown


def test_convert_many_command_writes_all_markdown_outputs(tmp_path: Path) -> None:
    input_pdf_a = tmp_path / "sample_a.pdf"
    input_pdf_b = tmp_path / "sample_b.pdf"
    output_dir = tmp_path / "batch_output"

    _write_test_pdf(input_pdf_a, text="Batch A")
    _write_test_pdf(input_pdf_b, text="Batch B")

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "convert-many",
            str(input_pdf_a),
            str(input_pdf_b),
            "--output-dir",
            str(output_dir),
            "--jobs",
            "2",
        ],
    )

    assert result.exit_code == 0, result.output

    markdown_a = output_dir / "sample_a.md"
    markdown_b = output_dir / "sample_b.md"
    assert markdown_a.exists()
    assert markdown_b.exists()
    assert "Batch A" in markdown_a.read_text(encoding="utf-8")
    assert "Batch B" in markdown_b.read_text(encoding="utf-8")


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
