# Development Documentation

This directory contains development-only project documentation. Keep it
under `docs/dev` rather than a repository-root `dev/` directory so all
documentation lives under one tree, while published user documentation
remains isolated under `docs/docs`.

## Structure

| Path                                                       | Purpose                                                                                           |
| ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| [`adrs/index.md`](adrs/index.md)                           | Architecture and decision navigation, grouped by topic.                                           |
| [`issues/index.md`](issues/index.md)                       | Issue index: open issues (ordered by priority) and closed issues, as tables linking to each file. |
| [`issues/open/`](issues/open/)                             | Open development issues, one file per issue (`<priority>_<title>.md`).                            |
| [`issues/closed/`](issues/closed/)                         | Closed development issues retained for history, one file per issue (`<title>.md`).                |
| [`package-structure/short.md`](package-structure/short.md) | Generated compact package tree.                                                                   |
| [`package-structure/full.md`](package-structure/full.md)   | Generated package tree with top-level classes.                                                    |
| [`plans/`](plans/)                                         | Implementation plans for larger migrations.                                                       |
| [`roadmap/ROADMAP.md`](roadmap/ROADMAP.md)                 | Development roadmap. This may later be copied into `docs/docs` during the published-docs build.   |

## Rules

- Put architecture and decision history in ADR files.
- Put proposed decisions in `adrs/suggestions/` until accepted.
- Move accepted suggestions to `adrs/accepted/` and update
  `adrs/index.md`.
- Do not edit generated package-structure files by hand; run
  `pixi run update-package-diagrams`.
- Keep development documentation out of `docs/docs` unless it is meant
  to become user-facing documentation.
