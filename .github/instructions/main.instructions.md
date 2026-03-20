---
description: Starting a new project. Adding dependencies, setting up tooling, and establishing coding guidelines.

---

# pdf-diff — AI Agent Instructions

## Core Principles

* Simplicity > cleverness
* Deterministic outputs > magic
* Prefer plain text (Markdown) over complex structures
* Minimize dependencies

---

## Tooling

### Package Management

* Use `uv` (Astral) exclusively
* Initialize project:

  ```bash
  uv init
  ```
* Add dependencies:

  ```bash
  uv add <package>
  ```
* Never use:

  * `pip install`
  * `uv pip install`

---

### Build System

* Use `hatch` as backend
* Keep configuration minimal inside `pyproject.toml`

---

### Linting & Formatting

* Use `ruff` for both linting and formatting
* Commands:

  ```bash
  ruff check .
  ruff format .
  ```

---

## Project Structure

```
pdf-diff/
│
├── src/pdf_diff/
│   ├── __init__.py
│   ├── cli.py          # Typer entrypoint
│   ├── parser.py       # PDF → Markdown (pdfsmith)
│   ├── diff.py         # Markdown diff (delta)
│   └── logging.py      # structlog config
│
├── scratch/            # one-off scripts (gitignored)
├── tests/
├── pyproject.toml
└── README.md
```

---

## CLI

* Use `typer` for CLI
* Keep commands small and composable

Example:

```python
import typer

app = typer.Typer()

@app.command()
def diff(file_a: str, file_b: str):
    ...
```

---

## Logging

* Use `structlog`
* Prefer structured logs over print
* Default to INFO level

---

## PDF Processing Flow

1. Input: `XYZ.pdf`
2. Convert using `pdfsmith` → `XYZ.md`
3. Store both:

   ```
   XYZ.pdf
   XYZ.md
   ```
4. Diff operates only on `.md` files using `delta`

---

## File Handling Rules

* Never overwrite original PDFs
* Always persist generated Markdown
* File naming must be 1:1:

  ```
  file.pdf → file.md
  ```

---

## Scratch Scripts

* Place all one-off experiments in:

  ```
  scratch/
  ```
* Must be gitignored
* No production logic here

---

## Dependency Guidelines

* Add only if absolutely necessary
* Prefer stdlib where possible
* Keep startup time fast

---

## Code Style

* Small functions
* Explicit > implicit
* No hidden side effects
* Type hints required

---

## Testing

* Focus on:

  * PDF → MD conversion correctness
  * Stable diffs
* Avoid over-mocking

---

## Anti-Patterns

* No global state
* No magic file paths
* No hidden caching
* No unnecessary abstractions

---

## Philosophy

* Markdown is the source of truth
* Diff should be human-readable
* Optimize for clarity over performance (until needed)
