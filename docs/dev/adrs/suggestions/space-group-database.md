# ADR: Complete Space-Group Reference Database

**Status:** Proposed **Date:** 2026-06-01

## Group

Structure model.

> This ADR follows [`AGENTS.md`](../../../../AGENTS.md). It is a
> prerequisite for
> [`wyckoff-letter-detection.md`](wyckoff-letter-detection.md): Wyckoff
> detection can only resolve letters for space groups present in the
> bundled table, and that table is currently incomplete.

## Context

The packaged space-group reference data,
`src/easydiffraction/crystallography/space_groups.py` →
`space_groups.pkl.gz`, is the single source the crystallography submodule
uses for symmetry constraints (cell, atom-site coordinate, and ADP) and
that the proposed Wyckoff-detection feature will use for letters,
multiplicities, and site symmetries. An audit of the current pickle found
it substantially incomplete and irregular:

- **613 entries covering only 188 of 230** International Tables groups.
- **42 groups have no entries at all** — and they are mostly the *simplest
  primitive* ones: tetragonal P4, P4₁, P4₂, P4₃, P-4, I-4, P4/m, P4₂/m,
  P4/n, P4₂/n; almost the entire primitive trigonal set P3 … P-3c1;
  the whole hexagonal P6 set P6 … P6₃/m; and cubic P23, P2₁3, Pm-3, Pn-3,
  Pa-3.
- **18 groups are missing settings** — monoclinic IT 3–15 carry only
  cell-choice-1; five orthorhombic groups (48, 50, 59, 68, 70) miss the
  `1a-cb` setting; cubic 228 misses origin choice 2.

Having I4 but not P4, and dropping nearly all primitive trigonal/hexagonal
groups, is not a principled subset — it points to a bug in whatever
generated the original pickle. The provenance and generation of that file
are unknown and unreproducible. As a result, both the existing
symmetry-constraint code and the planned Wyckoff feature silently do
nothing for very common groups.

Several authoritative reference sources are already gathered under
`tmp/third-party-resources/`:

- `wyckoff.dat` — **byte-identical to cryspy's** Wyckoff table (verified);
  complete for all 230 groups (representatives, multiplicities, site
  symmetries).
- `spacegroupdata.h`, `sginfo.dat` — SgInfo space-group data.
- `bricks.cpp`, `symbols.cpp` — cctbx/sgtbx sources (Hall symbols,
  settings, Wyckoff "bricks"), per `links.txt`.
- `raspa-page_55_reference.csv` — a settings table (IT № → Hermann-Mauguin
  / Hall → cell choice → centring → crystal system); no Wyckoff data.
- `International-Tables-for-crystallography.pdf` (Vol A) and `ITC-Vol.C.pdf`
  — the authoritative ground truth (PDF).
- `cif_core.dic` — CIF Core dictionary.

`gemmi 0.7.5` is in the environment; `cctbx` is not installed (only its
source snippets are present).

The goal: a **complete, self-owned** `space_groups.json.gz` covering all
230 groups × all standard settings × full Wyckoff orbits, built **once**
with its software provenance recorded (§Build provenance) and any source
disagreements resolved by human curation.

## Decision

### 1. Scope and schema

Cover **all 230 IT groups × every standard setting (coordinate-system
code) × every Wyckoff position**, where each position stores its
`multiplicity`, `site_symmetry`, and the full `coords_xyz` orbit.

The schema **extends the existing one additively**: every current key is
preserved so consumers (`crystallography.py`, the calculators, CIF code)
keep working, and a few **symmetry-core** metadata keys are added alongside.
Each space-group setting carries:

- the existing keys — `IT_number`, `setting`, `IT_coordinate_system_code`,
  `name_H-M_alt`, `crystal_system`, and `Wyckoff_positions`
  (`{letter: {multiplicity, site_symmetry, coords_xyz}}`);
- added per-setting metadata — `hall_symbol`, the full general-position
  `symop` list, `generators`, `point_group`, `laue_class`, and `centring`.

Per the maintainer's scope choice this is the **symmetry core only**;
further fields cctbx exposes are listed in Deferred Work for the future.

Coordinates and operators stay **strings** (e.g. `'(x,1/2,0)'`, `'-x,y,-z'`)
to match the existing parser (`_parse_rotation_matrix`, `sympify`) in
`crystallography.py` and to keep the file JSON-native (§2). Triclinic
no-setting groups keep the `None` coordinate code, as today (see the
`''`→`None` normalisation in
[`wyckoff-letter-detection.md`](wyckoff-letter-detection.md) §2).

**Query surface preserved.** On disk the JSON is a list of setting records,
each carrying the canonical `IT_number` and `IT_coordinate_system_code`
fields — there is no separate `coord_code` storage field; that name is only
the runtime variable for the tuple key. On load the module reconstructs the
same in-memory `SPACE_GROUPS` dict keyed by
`(IT_number, IT_coordinate_system_code)`, so every current lookup keeps
working unchanged. Because each record also carries `name_H-M_alt` and
`hall_symbol`, the database can rebuild an **H-M-short-symbol → IT_number**
index equivalent to cryspy's `get_it_number_by_name_hm_short` (1:1 — each of
the 230 groups has a single short symbol), with the setting selected
separately per IT number exactly as the `SpaceGroup` category does today. A
fuller "H-M symbol *with* setting → specific
`(IT_number, IT_coordinate_system_code)`" lookup is a multimap (one symbol
can map to several settings/origins) and is out of committed scope; actually
dropping the cryspy dependency is left to Deferred Work. The point here is
only that the new database is **at least as queryable as today**, by both
IT number + coordinate-system code and by Hermann-Mauguin symbol.

### 2. JSON storage removes the unpickle workaround

The database is stored as **gzip-compressed JSON** (`space_groups.json.gz`),
not a pickle. `space_groups.py` today loads a pickle through a bespoke
`_RestrictedUnpickler` that permits only built-in types — a security
workaround for a file that holds nothing but dicts, lists, strings, ints,
and `None`. Switching to JSON **deletes that workaround**: the loader
decompresses and `json.load`s the stream, then rebuilds the
`(IT_number, coord_code)`-keyed dict (§1). JSON cannot execute code, is
human-readable, diffable, and language-agnostic; the only constraint on the
generator is to emit JSON-native types, which the string-based schema
already satisfies.

### 3. Primary source: cctbx/sgtbx via temporary install

Build from **cctbx/sgtbx**, the reference implementation, which provides
full Wyckoff orbits, multiplicities, generators, symmetry operators, and
tabulated settings for all 230 groups directly and correctly. cctbx exposes
Wyckoff stabilizer point-group labels rather than the dotted International
Tables site-symmetry strings, so the generator treats cctbx's value as the
initial `site_symmetry` candidate and reconciles it against cryspy
`wyckoff.dat` plus maintainer curation before the database is accepted.
cctbx is a
**generation-only** dependency: it is installed into the pixi environment
**only for the generation run** and removed afterwards — it is never added
to the runtime dependencies and never imported at runtime, which loads only
the bundled JSON. Building the database is a **one-time effort**, not a
recurring pipeline: cctbx is installed once for that build, the exact
software versions used are recorded in §Build provenance, and the install
is then removed. A pinned GitHub data download was the considered
alternative; the temporary install was chosen for the authoritative API and
the least parsing risk.

### 4. One-time generation script, checked in for transparency

Add `tools/generate_space_groups.py`, run **once** to emit
`space_groups.json.gz`. It is committed (not necessarily wired to a routine
pixi task, since it is not run on every build) so that *how* the database
was built stays on the record and a future rebuild is possible. The
committed deliverables together document the database: the generator
script, the curation overrides (§6), the disagreement report (§6), and the
recorded software versions (§Build provenance). The generated JSON is the
artifact; those text files explain it.

### 5. Multi-source verification

The generator verifies its output against **every** gathered source, not
just the primary one:

- cryspy `wyckoff.dat` — letters, multiplicities, site symmetries;
- gemmi (already a runtime dependency, 0.7.5) — `spacegroup_table()` covers
  all 230 groups and 564 settings with Hall symbols and full symmetry
  operations. gemmi has **no** Wyckoff API (no letters, site symmetries, or
  special-position enumeration), so its independent contribution is precise:
  it validates the **set of settings** and the **symmetry operations** per
  setting, and — given a representative coordinate taken from another source
  — it confirms that representative's **orbit and multiplicity** by applying
  its operations (an operation-closure check). It does **not** independently
  produce the representative coordinates, letters, or site-symmetry symbols,
  so the disagreement report labels a gemmi orbit/multiplicity check as
  *dependent* on the cctbx/cryspy representative, not as an independent third
  source for that representative;
- SgInfo `spacegroupdata.h` / `sginfo.dat` — settings and generators;
- cctbx `symbols.cpp` / `bricks.cpp` — Hall symbols and settings;
- RASPA `raspa-page_55_reference.csv` — setting / cell-choice enumeration;
- International Tables Vol A — authoritative spot-checks.

Verification covers presence (all 230 groups and their standard settings),
per-position values (letter, multiplicity, site symmetry), and orbit
coordinates.

### 6. Disagreement report and human-in-the-loop curation

Where **two or more sources disagree** on any value — a multiplicity, a
site-symmetry symbol, a coordinate, a letter, the presence of a setting —
the generator emits a structured **disagreement report** entry containing:

- the case (group / setting / Wyckoff letter / field);
- each contributing source and its value;
- the **comparison with International Tables**;
- the generator's **recommended resolution** (and why).

The maintainer inspects the report and **selects** the authoritative value
per case. Selections are recorded in a checked-in **YAML overrides file**,
`tools/space_groups_overrides.yaml`, next to the generator — YAML so each
selection can carry an inline comment recording its rationale. The
generator consumes it during the build, so every non-obvious choice is
explicit and auditable rather than baked silently into the binary. The
disagreement report itself
is committed as a reviewable Markdown artifact under `docs/dev/`
(e.g. `docs/dev/space-group-database/disagreements.md`), so the curation
decisions are auditable like the project's other dev docs. Cases where all
sources agree need no entry.

### 7. The database file is generated, not hand-edited

`space_groups.json.gz` is never edited by hand. Any correction flows
through the curation overrides and a regeneration run, keeping the file and
the documented decisions in sync.

## Consequences

### Positive

- Complete coverage of the **data**: every one of the 230 groups and their
  standard settings is present, including the currently-broken P4 / P3 / P6 /
  Pm-3 and the monoclinic alternative settings. For settings with a
  non-`None` coordinate code the existing `(IT_number, code)` lookups find
  the new entries immediately, with no consumer change; the two triclinic
  `None`-code groups additionally need the companion consumer-side fix (see
  Compatibility).
- Documented, auditable provenance: the committed generator, curation
  overrides, disagreement report, and recorded build versions show exactly
  how the database was produced and every contested value decided.
- The Wyckoff-detection "unsupported group" path shrinks from "common
  groups" to genuinely-exotic settings, simplifying that feature.
- The 42-group gap and the missing settings become permanent regression
  guards.

### Trade-offs

- A temporary, generation-only cctbx install is needed for the one-time
  build (never a runtime dependency).
- A one-time human curation pass over the disagreement report.
- `space_groups.json.gz` is larger than today's partial pickle (gzipped JSON
  is less compact than gzipped pickle), though still well under ~1.5 MB.

### Compatibility Outcomes

- The in-memory `SPACE_GROUPS` dict is unchanged (same `(IT_number,
  coord_code)` keys; existing value keys preserved, new ones added), so
  `crystallography.py`, the calculators, and CIF code need no changes — they
  see complete data and ignore the new keys.
- Only the on-disk format changes (pickle → gzipped JSON); the
  `_RestrictedUnpickler` and the pickle dependency are **removed**, a net
  simplification.
- Existing projects load identically. Previously-unsupported groups with a
  real coordinate code (P4, P3, P6, Pm-3, the monoclinic alternative
  settings, …) gain correct symmetry behaviour immediately — the existing
  `(IT_number, code)` lookups simply find the now-present entries. The two
  triclinic `None`-code groups remain skipped until the companion
  consumer-side fix lands: `_get_wyckoff_exprs()` returns early when
  `coord_code is None` and `_get_general_position_ops()` indexes the raw key,
  so they need the `''`→`None` normalisation defined in
  [`wyckoff-letter-detection.md`](wyckoff-letter-detection.md) §2 (which also
  updates these call sites). This ADR delivers the data; that ADR delivers
  the `None`-code consumer handling.

## Alternatives Considered

- **cryspy as the primary source.** Fastest (already present, verified
  complete, zero new deps), but its provenance is the calculator the
  database is meant to be independent of. Kept as a **verification
  cross-check**, not the authority.
- **Parse SgInfo / cctbx C sources directly.** Most "self-owned", but the
  highest parsing and verification burden. Used as cross-checks instead of
  the primary generator.
- **Generate Wyckoff orbits at runtime from symmetry operators** (no
  bundled table). Rejected: heavy runtime cost on a hot path, and it
  discards the established, cache-friendly table design.
- **Keep the partial table and degrade gracefully.** Rejected: it leaves
  common groups (P4, P3, P6) silently without symmetry information.

## Verification

- A regression test asserts that **all 230 groups and their standard
  settings are present** in the loaded table (guarding against the current
  42-group / 18-setting gap).
- A query-surface test asserts that lookups by `(IT_number, coord_code)` and
  by Hermann-Mauguin symbol still resolve every group — at least matching
  today's capability.
- Spot-check tests compare representative groups against International
  Tables: a primitive tetragonal (P4), a trigonal (P3), a hexagonal (P6),
  a centrosymmetric cubic (Pm-3), a monoclinic with cell choices, and an
  origin-choice group.
- The disagreement report is itself a verification artifact, reviewed by
  the maintainer before the database is accepted.
- A packaging regression check builds or installs the wheel and confirms
  `easydiffraction.crystallography.space_groups` imports and loads the
  renamed `space_groups.json.gz` — catching missing package-data inclusion
  for the new file, not just source-tree correctness. (The packaging config
  must ship `*.json.gz` in place of `*.pkl.gz`.)
- Per the document-review rule, this ADR was written without running tests,
  linters, or build commands.

## Build Provenance

The database is built once, so the exact tooling and inputs used to produce
the committed `space_groups.json.gz` are recorded here at generation time.
This section **is** the named, durable provenance artifact that makes the
one-time build auditable and reconstructable even after cctbx is removed
from the environment:

- **cctbx** — conda-forge channel, version, and build string, plus the exact
  install command used (e.g. the `pixi add` / `conda install` line);
- **Python and platform** — Python version and OS/architecture of the build;
- **gemmi** version (cross-check);
- **cryspy** version and the `wyckoff.dat` SHA-256 (cross-check);
- **gathered inputs** — origin URL/commit and SHA-256 of each source used
  from `tmp/third-party-resources/` (SgInfo, cctbx `symbols.cpp` /
  `bricks.cpp`, the RASPA CSV, the International Tables edition);
- **generator** — the `tools/generate_space_groups.py` commit and the exact
  command line (with arguments) that produced the file;
- **output** — the SHA-256 of the committed `space_groups.json.gz`.

*(Filled in when the generation is run; until then this section is the
checklist the build must populate.)*

### P1.1 extraction observations

The first cctbx extraction pass enumerates 530 cctbx-tabulated setting
records covering all 230 IT groups, with no duplicate
`(IT_number, IT_coordinate_system_code)` keys after normalisation. This is
not identical to the wider cryspy-style coordinate-code surface used by
EasyDiffraction today: cryspy exposes additional repeated axis/cell-choice
aliases for some monoclinic and orthorhombic groups. The generator therefore
treats those aliases as a Phase 1 cross-check/curation concern rather than
silently inventing values during the initial cctbx extraction.

## Open Questions

None outstanding. Build-time specifics — the exact software versions and the
candidate additional-metadata fields — are recorded in §Build Provenance,
§P1.1 extraction observations, and Deferred Work respectively.

## Deferred Work

- **Additional metadata cctbx exposes**, deliberately deferred from the
  symmetry-core schema (§1): asymmetric-unit definition, reflection /
  systematic-absence conditions, centring translation vectors, per-Wyckoff
  special-position operators, and matrix-form generators. Add when a concrete
  consumer needs them.
- Dropping the remaining cryspy dependency for Hermann-Mauguin → IT-number
  resolution, using the database's own `name_H-M_alt` / `hall_symbol` index
  (§1).
- Re-evaluating the coordinate encoding (strings versus parsed matrices) if
  profiling shows the string parse is a bottleneck.

## Related ADRs

- [`wyckoff-letter-detection.md`](wyckoff-letter-detection.md) — the
  dependent feature; its `''`→`None` coordinate-code normalisation and its
  "unsupported group" handling both build on this database.
- [`iucr-cif-tag-alignment.md`](../accepted/iucr-cif-tag-alignment.md) —
  consumes space-group and Wyckoff data on export.
