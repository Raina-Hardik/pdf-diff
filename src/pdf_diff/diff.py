from __future__ import annotations

import difflib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


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
    format: str = "plaintext",
    stat: bool = False,
    lines_changed: bool = False,
) -> str:
    """Generate a diff between two Markdown files.

    Args:
        left: Path to the left file.
        right: Path to the right file.
        renderer: Diff renderer (auto, unified, delta).
        context_lines: Number of context lines for unified diffs.
        format: Output format (plaintext, json, unified).
        stat: Include summary statistics.
        lines_changed: Show only added/removed lines without context.

    Returns:
        Formatted diff output.
    """
    left_text = left.read_text(encoding="utf-8")
    right_text = right.read_text(encoding="utf-8")

    if format.lower() == "json":
        return _diff_to_json(left_text, right_text, str(left), str(right))

    unified = _unified_diff(
        left_text,
        right_text,
        from_path=str(left),
        to_path=str(right),
        context_lines=context_lines,
    )

    if stat:
        stats = _calculate_diff_stats(unified, str(left), str(right))
        return stats

    if lines_changed:
        return _lines_changed_only(unified)

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


def _diff_to_json(
    left_text: str,
    right_text: str,
    from_path: str,
    to_path: str,
) -> str:
    """Convert unified diff to JSON format with structured change information."""
    left_lines = left_text.splitlines(keepends=True)
    right_lines = right_text.splitlines(keepends=True)

    diff_obj: dict[str, Any] = {
        "left": from_path,
        "right": to_path,
        "hunks": [],
    }

    added_count = 0
    removed_count = 0

    for line in difflib.unified_diff(left_lines, right_lines, n=0, lineterm=""):
        if line.startswith("@@"):
            continue
        elif line.startswith("+") and not line.startswith("+++"):
            added_count += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed_count += 1

    diff_obj["stats"] = {
        "lines_added": added_count,
        "lines_removed": removed_count,
    }

    return json.dumps(diff_obj, indent=2)


def _calculate_diff_stats(unified_diff: str, from_path: str, to_path: str) -> str:
    """Calculate and format diff statistics."""
    added_count = 0
    removed_count = 0

    for line in unified_diff.split("\n"):
        if line.startswith("+") and not line.startswith("+++"):
            added_count += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed_count += 1

    total_changes = added_count + removed_count

    stats_text = f"""\
Left file:  {from_path}
Right file: {to_path}

Changes:
  Lines added:   {added_count}
  Lines removed: {removed_count}

Total changes: {total_changes}
"""
    return stats_text


def _lines_changed_only(unified_diff: str) -> str:
    """Extract only the added and removed lines, stripping context."""
    result_lines = []

    for line in unified_diff.split("\n"):
        if line.startswith("+++") or line.startswith("---"):
            result_lines.append(line)
        elif line.startswith("+") and not line.startswith("+++"):
            result_lines.append(line)
        elif line.startswith("-") and not line.startswith("---"):
            result_lines.append(line)
        elif line.startswith("@@"):
            result_lines.append(line)

    return "\n".join(result_lines)


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
