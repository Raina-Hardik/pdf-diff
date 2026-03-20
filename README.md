## pdf-diff

pdf-diff converts PDFs into persisted Markdown files.

The conversion engine of choice is pdfsmith.

The current scope is intentionally narrow:

- Convert a PDF into a Markdown file next to the source document.
- Use pdfsmith as the PDF-to-Markdown engine.
- Preserve page boundaries where possible.
- Keep the generated Markdown as the long-term source of truth.

Diff rendering is not part of v0.0.1. The planned model is PDF -> Markdown vs PDF -> Markdown, with the end user choosing their preferred diff viewer.

## Status

Current version: 0.0.1

Implemented now:

- `pdf-diff convert`
- Markdown persistence to disk
- pdfsmith-backed conversion
- Structured logging
- Smoke-test coverage for the convert workflow

Intentionally deferred:

- PDF-to-PDF diff workflow
- delta integration
- OCR support

## Design Notes

- Markdown is the source of truth.
- pdfsmith is the conversion abstraction layer.
- Original PDFs are never overwritten.
- Generated Markdown defaults to a 1:1 filename mapping.
- Optional features are scaffolded early, but raise `NotImplementedError` until their dependency groups are populated.

## Quick Start

Initialize and install dependencies with uv:

```powershell
uv sync
```

Run the CLI:

```powershell
uv run pdf-diff convert path\to\document.pdf
```

Write to a specific output path:

```powershell
uv run pdf-diff convert path\to\document.pdf --output out\document.md
```

Disable page boundary markers:

```powershell
uv run pdf-diff convert path\to\document.pdf --no-keep-pages
```

## Command Surface

### convert

Converts a single PDF into Markdown.

Behavior:

- Default output path: `input.pdf` -> `input.md`
- Page boundaries are preserved by default with HTML comments in the Markdown output.
- Conversion is routed through pdfsmith.

Example:

```powershell
uv run pdf-diff convert docs\sample.pdf
```

## Optional Feature Groups

The extras exist now so the public shape is stable, but they are placeholders for later work.

- `pdf-diff[delta]`
- `pdf-diff[ocr]`

At the moment, code paths that rely on these features raise `NotImplementedError` by design.

Planned OCR support is expected to build on pdfsmith's docling backend, but it is not declared as an installable extra yet because its current dependency constraints conflict with this project's Typer version.

## Development

Run tests:

```powershell
uv run pytest
```

Run lint checks:

```powershell
uv run ruff check .
uv run ruff format .
```

## Smoke Test

The repository includes a smoke-style CLI test that:

- creates a tiny PDF fixture on the fly
- runs `pdf-diff convert`
- verifies that Markdown is written to disk
- checks that extracted text and page markers are present

Run it with:

```powershell
uv run pytest tests/test_smoke_convert.py
```

## Roadmap

- Add PDF -> Markdown vs PDF -> Markdown diff workflow
- Add optional delta integration for terminal-friendly output
- Add OCR support behind the `ocr` extra
- Improve Markdown structure retention beyond text extraction
