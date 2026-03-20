from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
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
DiffInputArgument = Annotated[
    Path,
    typer.Argument(
        ...,
        exists=True,
        dir_okay=False,
        readable=True,
        help="Path to an input file (.md or .pdf).",
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
    left: DiffInputArgument,
    right: DiffInputArgument,
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
    backend: Annotated[
        str | None,
        typer.Option(
            "--backend",
            "-b",
            help="pdfsmith backend to use when converting PDF inputs for diff.",
        ),
    ] = None,
    format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format: plaintext, unified, or json.",
            case_sensitive=False,
        ),
    ] = "plaintext",
    stat: Annotated[
        bool,
        typer.Option(
            "--stat",
            help="Show summary statistics instead of full diff.",
        ),
    ] = False,
    lines_changed: Annotated[
        bool,
        typer.Option(
            "--lines-changed",
            help="Show only changed lines without context.",
        ),
    ] = False,
) -> None:
    configure_logging()
    chosen_renderer = resolve_diff_renderer(renderer)

    with TemporaryDirectory(prefix="pdf_diff_inputs_") as temp_dir:
        temp_root = Path(temp_dir)
        left_markdown_path = _materialize_diff_input_as_markdown(left, temp_root, backend=backend)
        right_markdown_path = _materialize_diff_input_as_markdown(right, temp_root, backend=backend)

        diff_output = diff_markdown_files(
            left_markdown_path,
            right_markdown_path,
            renderer=chosen_renderer,
            context_lines=context_lines,
            format=format.lower(),
            stat=stat,
            lines_changed=lines_changed,
        )

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(diff_output, encoding="utf-8")
        typer.echo(str(output))
        return

    typer.echo(diff_output)


def _materialize_diff_input_as_markdown(
    input_path: Path,
    temp_root: Path,
    *,
    backend: str | None,
) -> Path:
    if input_path.suffix.lower() == ".pdf":
        markdown = convert_pdf_to_markdown(input_path, backend=backend)
        temp_markdown_path = temp_root / f"{input_path.stem}.md"
        temp_markdown_path.write_text(markdown, encoding="utf-8")
        return temp_markdown_path

    return input_path


def main() -> None:
    app()
