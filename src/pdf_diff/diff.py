from __future__ import annotations

import difflib
import json
from pathlib import Path
from typing import Any


def resolve_diff_renderer(renderer: str) -> str:
    normalized = renderer.strip().lower()
    if normalized not in {"auto", "unified", "ndiff", "html", "delta"}:
        raise ValueError(
            f"Unsupported renderer '{renderer}'. Use auto, unified, ndiff, html, or delta."
        )

    if normalized == "auto":
        return "unified"

    # Keep backward compatibility for prior CLI values while avoiding shell calls.
    if normalized == "delta":
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
    chosen = resolve_diff_renderer(renderer)

    if format.lower() == "json":
        return _diff_to_json(left_text, right_text, str(left), str(right))

    if chosen == "html":
        return _html_diff(left_text, right_text, from_path=str(left), to_path=str(right))

    if chosen == "ndiff":
        return _ndiff(left_text, right_text)

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


def _ndiff(left_text: str, right_text: str) -> str:
    diff_lines = difflib.ndiff(left_text.splitlines(), right_text.splitlines())
    return "\n".join(diff_lines)


def _html_diff(left_text: str, right_text: str, *, from_path: str, to_path: str) -> str:
    html = difflib.HtmlDiff(wrapcolumn=100)
    return html.make_file(
        fromlines=left_text.splitlines(),
        tolines=right_text.splitlines(),
        fromdesc=from_path,
        todesc=to_path,
        context=True,
        numlines=3,
        charset="utf-8",
    )


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
