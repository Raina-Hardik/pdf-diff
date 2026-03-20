# Features Tracker

This document tracks what is already implemented, what is planned, and what is deferred.

Legend:
- implemented: Available in a released version
- planned: Committed roadmap item, not implemented yet
- deferred: Known future feature, intentionally postponed
- proposed: Idea captured but not yet scheduled

## Version Timeline

| Version | Date | Summary |
|---|---|---|
| 0.0.1 | 2026-03-20 | Initial public release: convert pipeline scaffold, backend selection flag, smoke tests, and OSS-safe project baseline |
| 0.1.0 | 2026-03-20 | Rich diff output formats: JSON, summary statistics, lines-changed-only mode for programmatic consumption and enhanced reporting |

## Feature Matrix

| Feature | Status | Type | Version Introduced | Notes |
|---|---|---|---|---|
| CLI entrypoint (`pdf-diff`) | implemented | core | 0.0.1 | Typer-based command surface |
| `convert` command | implemented | core | 0.0.1 | Converts PDF to Markdown and writes output to disk |
| `convert-many` command | implemented | core | 0.0.1 | Converts multiple PDFs in one invocation |
| Output path option (`--output`, `-o`) | implemented | core | 0.0.1 | Defaults to same path as input with `.md` suffix |
| Batch output directory option (`--output-dir`, `-d`) | implemented | core | 0.0.1 | Writes multi-file conversion outputs to a chosen directory |
| Page boundary preservation (`--keep-pages/--no-keep-pages`) | implemented | core | 0.0.1 | Inserts page markers in generated Markdown when enabled |
| pdfsmith conversion integration | implemented | core | 0.0.1 | Uses pdfsmith parse API for PDF -> Markdown |
| Backend selection (`--backend`, `-b`) | implemented | core | 0.0.1 | If omitted, pdfsmith auto-selects best available backend |
| Async batch conversion path | implemented | core | 0.0.1 | Uses async orchestration for concurrent multi-file conversion |
| Structured logging | implemented | infra | 0.0.1 | JSON logs via structlog |
| Basic convert smoke test | implemented | test | 0.0.1 | Verifies conversion writes expected Markdown output |
| Multi-file convert smoke test | implemented | test | 0.0.1 | Verifies `convert-many` writes all expected Markdown outputs |
| End-to-end pipeline smoke test (pandoc + delta) | implemented | test | 0.0.1 | Markdown -> PDF -> Markdown and diff artifact persisted to disk |
| Fixture documents for pipeline tests | implemented | test | 0.0.1 | Two Markdown fixtures with headings, lists, and table content |
| OSS-safe gitignore guardrails | implemented | infra | 0.0.1 | Ignores local secrets and local sample data paths |
| `diff` command with renderer and output options | implemented | core | 0.0.1 | Supports unified and auto/delta rendering with optional file output |
| Markdown diff engine integration | implemented | core | 0.0.1 | Unified diff is now wired and functional |
| Diff smoke test | implemented | test | 0.0.1 | Verifies CLI diff output and persisted diff artifacts |
| PDF vs PDF diff workflow (via Markdown conversion) | planned | core | TBD | Planned model: PDF -> MD vs PDF -> MD |
| Diff output format: JSON | implemented | core | 0.1.0 | Structured JSON with stats and change metadata |
| Diff output format: summary statistics | implemented | core | 0.1.0 | Show lines added/removed with --stat flag |
| Diff output format: lines-changed-only | implemented | core | 0.1.0 | Show only changed lines without context using --lines-changed |
| OCR conversion path (`--ocr`) | deferred | core | TBD | Currently raises NotImplementedError by design |
| OCR optional dependency group wiring | deferred | packaging | TBD | Deferred due to dependency constraints with current stack |
| Optional delta dependency group wiring | proposed | packaging | TBD | CLI can use external `delta`; Python optional group remains a placeholder |
| Versioned changelog automation | proposed | infra | TBD | Candidate follow-up once release cadence stabilizes |

## Immediate Next Slice

| Priority | Item | Target Version |
|---|---|---|
| high | Add PDF-vs-PDF convenience command that converts both and diffs outputs | 0.1.x |
| medium | Expand conversion tests with backend-specific smoke matrix | 0.1.x |
| medium | Add OCR implementation behind optional group once constraints are resolved | 0.2.0 |

## Notes

- Keep this file updated whenever a feature status changes.
- When implementing a feature, update both the Feature Matrix and Version Timeline.
- Use exact release version where possible; avoid vague labels once shipped.
