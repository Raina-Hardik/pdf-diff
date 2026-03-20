"""
Pipeline smoke test: Markdown -> PDF (pandoc) -> Markdown (pdf-diff convert) -> diff (delta).

Requires pandoc and delta to be installed on the system PATH.
Both are skipped gracefully when unavailable.

The test outputs (converted Markdown files and the delta diff) are written to
tests/output/ for manual inspection. That directory is gitignored.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pdf_diff.cli import app

FIXTURES = Path(__file__).parent / "fixtures"
OUTPUT = Path(__file__).parent / "output"

DOCUMENT_A = FIXTURES / "document_a.md"
DOCUMENT_B = FIXTURES / "document_b.md"


def _require(tool: str) -> str:
    path = shutil.which(tool)
    if path is None:
        pytest.skip(f"{tool} not found on PATH")
    return path


def _pandoc_to_pdf(src_md: Path, dest_pdf: Path) -> None:
    pandoc = _require("pandoc")
    result = subprocess.run(
        [pandoc, str(src_md), "-o", str(dest_pdf)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"pandoc failed:\n{result.stderr}"


def _pdf_diff_convert(src_pdf: Path, dest_md: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["convert", str(src_pdf), "--output", str(dest_md)])
    assert result.exit_code == 0, f"pdf-diff convert failed:\n{result.output}"
    assert dest_md.exists(), "pdf-diff convert did not create output file"
    assert dest_md.stat().st_size > 0, "pdf-diff convert produced an empty file"


def _run_delta(left_md: Path, right_md: Path, output_file: Path) -> None:
    delta = _require("delta")
    result = subprocess.run(
        [delta, str(left_md), str(right_md), "--no-gitconfig"],
        capture_output=True,
    )
    # delta exits 0 for identical files and 1 for files with differences; both are valid.
    assert result.returncode in (0, 1), f"delta exited unexpectedly:\n{result.stderr.decode()}"
    output_file.write_bytes(result.stdout)


@pytest.fixture(scope="module")
def pipeline_output(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    tmp = tmp_path_factory.mktemp("pipeline")
    OUTPUT.mkdir(parents=True, exist_ok=True)

    pdf_a = tmp / "document_a.pdf"
    pdf_b = tmp / "document_b.pdf"
    _pandoc_to_pdf(DOCUMENT_A, pdf_a)
    _pandoc_to_pdf(DOCUMENT_B, pdf_b)

    md_a = OUTPUT / "document_a_converted.md"
    md_b = OUTPUT / "document_b_converted.md"
    _pdf_diff_convert(pdf_a, md_a)
    _pdf_diff_convert(pdf_b, md_b)

    return {"md_a": md_a, "md_b": md_b, "pdf_a": pdf_a, "pdf_b": pdf_b}


def test_converted_markdown_files_exist(pipeline_output: dict[str, Path]) -> None:
    assert pipeline_output["md_a"].exists()
    assert pipeline_output["md_b"].exists()


def test_converted_markdown_contains_expected_content(pipeline_output: dict[str, Path]) -> None:
    text_a = pipeline_output["md_a"].read_text(encoding="utf-8")
    text_b = pipeline_output["md_b"].read_text(encoding="utf-8")

    # Core content from the source documents should survive the PDF->MD round-trip.
    assert "Q1 2025" in text_a, "document_a conversion missing expected heading"
    assert "Q2 2025" in text_b, "document_b conversion missing expected heading"

    # Table data should be present as raw text (exact Markdown table syntax is not guaranteed).
    assert "12,400" in text_a or "12400" in text_a, "document_a missing January active users"
    assert "19,000" in text_b or "19000" in text_b, "document_b missing June active users"


def test_converted_documents_are_distinguishable(pipeline_output: dict[str, Path]) -> None:
    text_a = pipeline_output["md_a"].read_text(encoding="utf-8")
    text_b = pipeline_output["md_b"].read_text(encoding="utf-8")
    assert text_a != text_b, "Converted Markdown files are identical — pipeline may have failed"


def test_delta_diff_stored_to_disk(pipeline_output: dict[str, Path]) -> None:
    diff_output = OUTPUT / "pipeline_diff.txt"
    _run_delta(pipeline_output["md_a"], pipeline_output["md_b"], diff_output)
    assert diff_output.exists()
    assert diff_output.stat().st_size > 0, "delta produced no output"
