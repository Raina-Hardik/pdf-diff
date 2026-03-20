from __future__ import annotations

import difflib
import shutil
import subprocess
from pathlib import Path


def resolve_diff_renderer(renderer: str) -> str:
    normalized = renderer.strip().lower()
    if normalized not in {"auto", "unified", "delta"}:
        raise ValueError(f"Unsupported renderer '{renderer}'. Use auto, unified, or delta.")

    if normalized == "auto":
        return "delta" if _delta_available() else "unified"

    if normalized == "delta" and not _delta_available():
        return "unified"

    return normalized


def diff_markdown_files(
    left: Path,
    right: Path,
    *,
    renderer: str = "auto",
    context_lines: int = 3,
) -> str:
    left_text = left.read_text(encoding="utf-8")
    right_text = right.read_text(encoding="utf-8")

    unified = _unified_diff(
        left_text,
        right_text,
        from_path=str(left),
        to_path=str(right),
        context_lines=context_lines,
    )
    chosen = resolve_diff_renderer(renderer)

    if chosen == "delta":
        return _render_with_delta(unified)

    return unified


def _unified_diff(
    left_text: str,
    right_text: str,
    *,
    from_path: str,
    to_path: str,
    context_lines: int,
) -> str:
    diff_lines = difflib.unified_diff(
        left_text.splitlines(keepends=True),
        right_text.splitlines(keepends=True),
        fromfile=from_path,
        tofile=to_path,
        n=context_lines,
        lineterm="",
    )
    return "\n".join(diff_lines)


def _render_with_delta(unified_diff_text: str) -> str:
    delta = shutil.which("delta")
    if delta is None:
        return unified_diff_text

    result = subprocess.run(
        [delta, "--no-gitconfig", "--paging=never"],
        input=unified_diff_text,
        text=True,
        capture_output=True,
    )
    if result.returncode not in (0, 1):
        return unified_diff_text

    return result.stdout or unified_diff_text


def _delta_available() -> bool:
    return shutil.which("delta") is not None
