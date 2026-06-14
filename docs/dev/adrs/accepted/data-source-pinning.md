# ADR: Data Download Source Pinning

**Status:** Accepted **Date:** 2026-06-14

> This ADR follows [`AGENTS.md`](../../../../AGENTS.md). No deliberate
> exception to those instructions is taken.

## Group

Documentation.

> Placed with the documentation/tutorial-infrastructure decisions
> (notebook generation, versioned docs) because the downloaded payload
> is primarily example, tutorial, and project-archive data. The
> mechanism is reused by the public `download_data()` API.

> Sibling of [`resource-naming.md`](resource-naming.md): this ADR pins
> _which snapshot_ of the data repository to fetch and decides
> replace-in-place under stable identifiers; that ADR decides what those
> identifiers _are_ (the dash-prefixed `<category>-<slug>` scheme that replaces the
> integer ids).

## Context

EasyDiffraction does not ship its example/tutorial datasets inside the
wheel — they are large (measured patterns, project archives) — so the
library downloads them on demand from the `easyscience/diffraction`
repository via `pooch`. The library therefore has to record **which
snapshot of that repository to fetch**.

Today `src/easydiffraction/utils/utils.py` records this with **two**
hand-edited constants:

- `_DATA_INDEX_REF` — a full commit SHA, used to build the raw
  `raw.githubusercontent.com/easyscience/diffraction/<ref>/data/...`
  URLs (`_build_data_url`).
- `_DATA_INDEX_HASH` — a `sha256:` checksum of `data/index.json`, passed
  to `pooch.retrieve` as `known_hash` (`_fetch_data_index`).

Each downloadable archive additionally carries its own content checksum
inside `index.json` — stored today in the existing **`hash`** field as a
`sha256:...` string (`record.get('hash')`, passed to `pooch` as
`known_hash`) — so per-archive integrity is already data-driven and is
**not** part of this decision. Throughout this ADR, "the dataset
`sha256`" means the value of that existing `hash` field; this ADR does
**not** rename the data-index schema or introduce a new `sha256` key, so
no data-repository migration follows from it.

Problems with the current arrangement:

- **Two coupled values.** Every data change requires editing both the
  commit and the index checksum, in source, plus a release.
- **Opaque and in code.** The pin is a bare SHA embedded in logic.
- **Cache staleness coupling.** `_fetch_data_index` caches the index
  under the fixed filename `data-index.json`. The checksum is what makes
  `pooch` notice the index changed and re-download it; without it, a
  changed commit would silently reuse the stale cached index.

Constraints established for this decision:

- The data repository is **multi-purpose** (data, project metadata, and
  later umbrella site content), so it must not be tagged or
  directory-versioned for data reasons alone.
- **No new repositories** (the project already has `diffraction`,
  `diffraction-lib`, `diffraction-app`) and **no git submodules**.
- The data is **not small** — it stays a runtime download, not a
  packaged or submodule-checked-out payload.
- Which data a build uses should **track the library version** and be
  **reproducible** for any released version.
- There must be a way to **test new or updated data during
  development**.

## Decision

1. **Pin by a single git commit.** The data source is identified by one
   value: a full commit SHA of `easyscience/diffraction`. A full SHA is
   content-addressed, so it fixes the exact bytes of `index.json` and
   every archive at that snapshot, over HTTPS. This is purpose-neutral:
   it pins "the repository as it was at this commit" regardless of why
   the repository changed.

2. **Store the commit in a packaged, non-code file.** The commit lives
   in `src/easydiffraction/_data_index_ref.txt` (one line: the SHA),
   read at runtime via `importlib.resources`. It is edited by hand, like
   the current constant, but it is data rather than logic, and because
   it sits under the package directory it is included in the wheel and
   readable for both source checkouts and installed users.

   `pyproject.toml` is explicitly **not** used to hold this value:
   `pyproject.toml` is a build-time file that is not shipped in the
   wheel, and custom `[tool.*]` tables are not exposed through
   `importlib.metadata`, so an installed package could not read it at
   runtime.

3. **Drop `_DATA_INDEX_HASH`.** With the commit pinning the index bytes
   and per-archive checksums verifying downloads, the separate index
   checksum is redundant. `pooch.retrieve` for the index uses
   `known_hash=None`.

4. **Derive the cached index filename from the commit.** The index is
   cached as `data-index-<commit>.json` instead of `data-index.json`.
   Changing the commit therefore changes the cache filename, so the new
   index is downloaded fresh; old indices remain cached under their own
   names (harmless, and useful offline). This replaces the checksum as
   the cache-busting mechanism while keeping a single source of truth.

5. **Update data by replacing files in place.** Datasets keep stable
   paths/identifiers (their form — the dash-prefixed `<category>-<slug>` scheme — is
   fixed by the sibling [`resource-naming.md`](resource-naming.md));
   updating a dataset overwrites the existing file and refreshes its
   `sha256` in `index.json`. Git history records the replacement and the
   pinned commit selects the snapshot. No new dataset ids are minted for
   what is conceptually the same dataset.

6. **Version tracking and reproducibility come from the release.** The
   committed `_data_index_ref.txt` is part of the library source, so it
   is frozen into every release artifact. A released library version
   therefore always resolves to the same data snapshot, and the data a
   build uses tracks the library version without any cross-repository
   tagging.

7. **Invalidate local payloads by content, including extractions.**
   Because datasets are replaced in place under stable identifiers
   (Decision 5), the local cache must not return stale bytes after a ref
   bump. Both the downloaded archive/file **and** any project ZIP
   extraction directory are keyed by that dataset's `sha256` from the
   index — the value of the existing `hash` field per the §Context note,
   not a renamed schema key (for example the cached filename and the
   extraction directory carry a short content hash). A dataset whose
   bytes changed therefore resolves to a new local path and is
   re-fetched/re-extracted, while unchanged datasets are reused — so
   only what actually changed is re-downloaded, and an existing stale
   file or extracted directory is never served. Equivalently, an
   existing payload may be verified against the current index `sha256`
   before reuse; either way the rule covers extraction directories, not
   only direct downloads. (The index itself is keyed by the commit per
   Decision 4, so it always refreshes on a ref bump.)

8. **Validate the pinned ref before use.** On read, the contents of
   `_data_index_ref.txt` are stripped of surrounding whitespace and must
   be a full 40-character hexadecimal commit SHA. Any other value —
   empty, a branch name, a short SHA, or path-like text — raises a clear
   error before any URL or cache filename is built. This turns the "must
   be a full commit SHA" requirement into an enforced contract, so a
   malformed edit fails fast instead of silently breaking
   reproducibility or the cache-busting invariant.

## Consequences

- The data pin is a **single, non-code value** that is edited the same
  way as today (paste a commit), minus the checksum.
- Integrity is preserved: full-commit content addressing over HTTPS for
  the index, plus per-archive `sha256` for every download.
- Cache invalidation is automatic and tied to the one value: the index
  by commit, and each archive/extraction by its `sha256` (Decisions 4
  and 7). A ref bump re-fetches only the datasets whose bytes changed,
  and never returns a stale file or extracted project directory.
- Reproducibility is preserved per released version, including repeated
  use on a machine that already has older local copies; the data pin is
  agnostic to non-data changes in the multi-purpose repository.
- The pinned value **must be a full commit SHA**, not a branch name: the
  cache-busting filename trick only works for immutable refs (a moving
  branch keeps the same `index.json` content address in its name). This
  is enforced at read time (Decision 8), so a bad edit fails fast.
- Retaining content-keyed local copies of superseded datasets uses some
  extra disk in the cache; this is accepted (and prunable) in exchange
  for never serving stale bytes.
- Dropping the index checksum slightly reduces index-level
  defense-in-depth; this is accepted because the commit already fixes
  the bytes and transport is HTTPS.

## Alternatives Considered

- **Keep both constants in code.** Status quo; rejected for the
  two-value coupling, opacity, and cache coupling above.
- **Version the data with git tags** (`data-vN` or per-release tags).
  Rejected: the repository is multi-purpose, so data-driven tags pollute
  its tag namespace and conflate data with site/metadata changes.
- **Append-only versioned directories** (`data/v3/...`). Rejected: it
  conflicts with the preferred replace-in-place workflow and grows the
  repository indefinitely.
- **Git submodule of the data repository.** Rejected: no submodules, and
  the data is too large to check out or ship with the library.
- **Hold the value in `pyproject.toml`.** Rejected: not present in the
  installed wheel and not exposed via `importlib.metadata`, so it is not
  runtime-readable for installed users (see Decision 2).
- **Track a moving branch (e.g. `master`) for releases.** Rejected:
  releases would retroactively see new data and lose reproducibility;
  also defeats the filename cache-busting.

## Deferred Work

- **Development data channel and override.** A future change may let
  unreleased/dev builds resolve a live channel automatically and/or
  honor an `EASYDIFFRACTION_DATA_REF` environment variable to point a
  build at a branch or commit for testing data before it is finalized.
  This ADR only fixes the released-build pin; the dev workflow today is
  to set the commit (or the override, once added) to the data snapshot
  under test.
- **Automated bump.** Optionally, release CI could write the current
  data commit into `_data_index_ref.txt` so the value is never
  hand-edited. Out of scope here; manual editing remains the baseline.
- **Dedicated data home.** If the umbrella repository grows, moving the
  data to its own released artifact could fully decouple its lifecycle.
  Out of scope: the project does not want additional repositories now.
