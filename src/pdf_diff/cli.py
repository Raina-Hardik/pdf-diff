from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import typer

from pdf_diff.diff import diff_markdown_files, resolve_diff_renderer
from pdf_diff.logging import configure_logging, get_logger
from pdf_diff.parser import (
    convert_pdf_to_markdown,
    convert_pdf_with_ocr,
    convert_pdfs_to_markdown_batch,
)

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
OutputDirOption = Annotated[
    Path | None,
    typer.Option(
        "--output-dir",
        "-d",
        file_okay=False,
        dir_okay=True,
        help="Directory for generated Markdown files. Defaults to each input PDF directory.",
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
def convert_many(
    input_pdfs: Annotated[
        list[Path],
        typer.Argument(..., help="One or more input PDF files to convert."),
    ],
    output_dir: OutputDirOption = None,
    keep_pages: Annotated[
        bool,
        typer.Option(
            "--keep-pages/--no-keep-pages",
            help="Preserve page boundaries in the generated Markdown.",
        ),
    ] = True,
    backend: Annotated[
        str | None,
        typer.Option(
            "--backend",
            "-b",
            help="pdfsmith backend to use for conversion. Auto-selects best available when omitted.",
        ),
    ] = None,
    jobs: Annotated[
        int,
        typer.Option(
            "--jobs",
            "-j",
            min=1,
            help="Maximum number of concurrent conversions.",
        ),
    ] = 4,
) -> None:
    configure_logging()

    if not input_pdfs:
        raise typer.BadParameter("At least one input PDF is required.")

    for pdf_path in input_pdfs:
        if not pdf_path.exists() or not pdf_path.is_file():
            raise typer.BadParameter(f"Input PDF not found: {pdf_path}")

    converted = asyncio.run(
        convert_pdfs_to_markdown_batch(
            input_pdfs,
            keep_pages=keep_pages,
            backend=backend,
            max_concurrency=jobs,
        )
    )

    for input_pdf in input_pdfs:
        parent_dir = output_dir or input_pdf.parent
        target_path = parent_dir / f"{input_pdf.stem}.md"
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(converted[input_pdf], encoding="utf-8")

        logger.info(
            "markdown_written",
            engine="pdfsmith",
            backend=backend or "auto",
            input_pdf=str(input_pdf),
            output_markdown=str(target_path),
            keep_pages=keep_pages,
            batch=True,
        )
        typer.echo(str(target_path))


@app.command()
def diff(
    left: MarkdownArgument,
    right: MarkdownArgument,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            dir_okay=False,
            help="Write diff output to this file instead of stdout.",
        ),
    ] = None,
    renderer: Annotated[
        str,
        typer.Option(
            "--renderer",
            "-r",
            help="Diff renderer: auto, unified, or delta.",
            case_sensitive=False,
        ),
    ] = "auto",
    context_lines: Annotated[
        int,
        typer.Option(
            "--context",
            "-c",
            min=0,
            help="Number of context lines for unified diffs.",
        ),
    ] = 3,
) -> None:
    configure_logging()
    chosen_renderer = resolve_diff_renderer(renderer)
    diff_output = diff_markdown_files(
        left,
        right,
        renderer=chosen_renderer,
        context_lines=context_lines,
    )

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(diff_output, encoding="utf-8")
        typer.echo(str(output))
        return

    typer.echo(diff_output)


def main() -> None:
    app()
