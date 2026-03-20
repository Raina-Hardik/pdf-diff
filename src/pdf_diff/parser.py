from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from pdfsmith import parse_async as pdfsmith_parse_async
from pdfsmith import parse as pdfsmith_parse
from pypdf import PdfReader, PdfWriter


def convert_pdf_to_markdown(
    input_pdf: Path, *, keep_pages: bool = True, backend: str | None = None
) -> str:
    if not keep_pages:
        markdown = pdfsmith_parse(input_pdf, backend=backend)
        return _normalize_document_markdown(markdown)

    sections = _parse_pages_with_pdfsmith(input_pdf, backend=backend)
    markdown = "\n\n".join(section for section in sections if section)
    return f"{markdown}\n" if markdown else ""


async def convert_pdf_to_markdown_async(
    input_pdf: Path, *, keep_pages: bool = True, backend: str | None = None
) -> str:
    if keep_pages:
        return await asyncio.to_thread(
            convert_pdf_to_markdown,
            input_pdf,
            keep_pages=keep_pages,
            backend=backend,
        )

    markdown = await pdfsmith_parse_async(input_pdf, backend=backend)
    return _normalize_document_markdown(markdown)


async def convert_pdfs_to_markdown_batch(
    input_pdfs: list[Path],
    *,
    keep_pages: bool = True,
    backend: str | None = None,
    max_concurrency: int = 4,
) -> dict[Path, str]:
    semaphore = asyncio.Semaphore(max(1, max_concurrency))

    async def _convert_one(pdf_path: Path) -> tuple[Path, str]:
        async with semaphore:
            markdown = await convert_pdf_to_markdown_async(
                pdf_path,
                keep_pages=keep_pages,
                backend=backend,
            )
            return pdf_path, markdown

    tasks = [_convert_one(pdf_path) for pdf_path in input_pdfs]
    converted = await asyncio.gather(*tasks)
    return {pdf_path: markdown for pdf_path, markdown in converted}


def convert_pdf_with_ocr(input_pdf: Path) -> str:
    """TODO: implement OCR conversion via pdfsmith's docling-backed OCR path."""
    raise NotImplementedError(
        f"OCR conversion is not implemented yet for {input_pdf}. Install support later via pdf-diff[ocr]."
    )


def _parse_pages_with_pdfsmith(input_pdf: Path, backend: str | None = None) -> list[str]:
    reader = PdfReader(str(input_pdf))
    sections: list[str] = []

    with TemporaryDirectory(prefix="pdf_diff_pages_") as temp_dir:
        temp_root = Path(temp_dir)

        for page_number, page in enumerate(reader.pages, start=1):
            page_pdf = temp_root / f"page_{page_number}.pdf"
            writer = PdfWriter()
            writer.add_page(page)

            with page_pdf.open("wb") as handle:
                writer.write(handle)

            markdown = _normalize_document_markdown(pdfsmith_parse(page_pdf, backend=backend))
            page_header = f"<!-- page: {page_number} -->"
            sections.append(f"{page_header}\n\n{markdown}" if markdown else page_header)

    return sections


def _normalize_document_markdown(text: str) -> str:
    stripped_lines: list[str] = []
    blank_run = 0

    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.rstrip()
        if line:
            stripped_lines.append(line)
            blank_run = 0
            continue

        blank_run += 1
        if blank_run <= 2:
            stripped_lines.append("")

    return "\n".join(stripped_lines).strip()
