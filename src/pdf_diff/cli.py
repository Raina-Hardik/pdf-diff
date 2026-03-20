from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from pdf_diff.diff import diff_markdown_files
from pdf_diff.logging import configure_logging, get_logger
from pdf_diff.parser import convert_pdf_to_markdown, convert_pdf_with_ocr

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Convert PDFs into persisted Markdown files.",
)

logger = get_logger()

PdfArgument = Annotated[
    Path,
    typer.Argument(..., exists=True, dir_okay=False, readable=True, help="Path to the source PDF."),
]
MarkdownArgument = Annotated[
    Path,
    typer.Argument(
        ..., exists=True, dir_okay=False, readable=True, help="Path to a Markdown file."
    ),
]
OutputOption = Annotated[
    Path | None,
    typer.Option(
        "--output",
        "-o",
        dir_okay=False,
        help="Markdown output path. Defaults to the PDF path with an .md suffix.",
    ),
]


@app.command()
def convert(
    input_pdf: PdfArgument,
    output: OutputOption = None,
    keep_pages: Annotated[
        bool,
        typer.Option(
            "--keep-pages/--no-keep-pages",
            help="Preserve page boundaries in the generated Markdown.",
        ),
    ] = True,
    ocr: Annotated[
        bool,
        typer.Option("--ocr", help="Use the future OCR-backed conversion path."),
    ] = False,
    backend: Annotated[
        str | None,
        typer.Option(
            "--backend",
            "-b",
            help="pdfsmith backend to use for conversion. Auto-selects best available when omitted.",
        ),
    ] = None,
) -> None:
    configure_logging()

    target_path = output or input_pdf.with_suffix(".md")
    markdown = (
        convert_pdf_with_ocr(input_pdf)
        if ocr
        else convert_pdf_to_markdown(input_pdf, keep_pages=keep_pages, backend=backend)
    )

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(markdown, encoding="utf-8")

    logger.info(
        "markdown_written",
        engine="pdfsmith",
        backend=backend or "auto",
        input_pdf=str(input_pdf),
        output_markdown=str(target_path),
        keep_pages=keep_pages,
        ocr=ocr,
    )
    typer.echo(str(target_path))


@app.command()
def diff(left: MarkdownArgument, right: MarkdownArgument) -> None:
    configure_logging()
    typer.echo(diff_markdown_files(left, right))


def main() -> None:
    app()
