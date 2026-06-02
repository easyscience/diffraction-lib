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
`space_groups.pkl.gz`, is the single source the crystallography
submodule uses for symmetry constraints (cell, atom-site coordinate, and
ADP) and that the proposed Wyckoff-detection feature will use for
letters, multiplicities, and site symmetries. An audit of the current
pickle found it substantially incomplete and irregular:

- **613 entries covering only 188 of 230** International Tables groups.
- **42 groups have no entries at all** — and they are mostly the
  _simplest primitive_ ones: tetragonal P4, P4₁, P4₂, P4₃, P-4, I-4,
  P4/m, P4₂/m, P4/n, P4₂/n; almost the entire primitive trigonal set P3
  … P-3c1; the whole hexagonal P6 set P6 … P6₃/m; and cubic P23, P2₁3,
  Pm-3, Pn-3, Pa-3.
- **18 groups are missing settings** — monoclinic IT 3–15 carry only
  cell-choice-1; five orthorhombic groups (48, 50, 59, 68, 70) miss the
  `1a-cb` setting; cubic 228 misses origin choice 2.

Having I4 but not P4, and dropping nearly all primitive
trigonal/hexagonal groups, is not a principled subset — it points to a
bug in whatever generated the original pickle. The provenance and
generation of that file are unknown and unreproducible. As a result,
both the existing symmetry-constraint code and the planned Wyckoff
feature silently do nothing for very common groups.

Several authoritative reference sources are already gathered under
`tmp/space-groups/`:

- `data/cryspy/wyckoff.dat` — **byte-identical to cryspy's** Wyckoff
  table (verified); complete for all 230 groups (representatives,
  multiplicities, site symmetries).
- `data/avogadro/spacegroupdata.h` and `data/sginfo/sginfo.dat` —
  independently gathered setting and multiplicity references.
- `data/cctbx/bricks.cpp` and `data/cctbx/symbols.cpp` — cctbx/sgtbx
  source snapshots kept for provenance; installed cctbx/sgtbx is used
  for extraction.
- `data/raspa/raspa-space-group-information.csv` — a settings table
  extracted from the RASPA manual appendix (IT № → Hermann-Mauguin /
  Hall → cell choice → centring → crystal system); no Wyckoff data.
- `data/international-tables/International-Tables-for-crystallography.pdf`
  (Vol A) and `data/international-tables/ITC-Vol.C.pdf` — authoritative
  manual curation sources (PDF).
- `data/iucr/cif_core.dic` — CIF Core dictionary.

One-time source-extraction and generation helpers live under
`tmp/space-groups/helper-tools/`. They are local, ignored curation
tooling rather than branch deliverables; the durable record is the final
generated database, the checked-in ADR companion curation overrides, and
the provenance recorded in this ADR.

`gemmi 0.7.5` is in the environment; `cctbx` is not installed (only its
source snippets are present).

The goal: a **complete, self-owned** `space_groups.json.gz` covering all
230 groups × all standard settings plus every coordinate-code alias the
current `SpaceGroup` category can produce × full Wyckoff orbits, built
**once** with its software provenance recorded (§Build provenance).

## Decision

### 1. Scope and schema

Cover **all 230 IT groups × every standard setting and public
coordinate-code alias × every Wyckoff position**, where each position
stores its `multiplicity`, `site_symmetry`, and the full `coords_xyz`
orbit.

The schema **extends the existing one additively**: every current key is
preserved so consumers (`crystallography.py`, the calculators, CIF code)
keep working, and a few **symmetry-core** metadata keys are added
alongside. Each space-group setting carries:

- the existing keys — `IT_number`, `setting`,
  `IT_coordinate_system_code`, `name_H-M_alt`, `crystal_system`, and
  `Wyckoff_positions`
  (`{letter: {multiplicity, site_symmetry, coords_xyz}}`);
- added per-setting metadata — `hall_symbol`, the full general-position
  `symop` list, `generators`, `point_group`, `laue_class`, and
  `centring`.

Per the maintainer's scope choice this is the **symmetry core only**;
further fields cctbx exposes are listed in Deferred Work for the future.

Coordinates and operators stay **strings** (e.g. `'(x,1/2,0)'`,
`'-x,y,-z'`) to match the existing parser (`_parse_rotation_matrix`,
`sympify`) in `crystallography.py` and to keep the file JSON-native
(§2). Triclinic no-setting groups keep the `None` coordinate code, as
today (see the `''`→`None` normalisation in
[`wyckoff-letter-detection.md`](wyckoff-letter-detection.md) §2).

**Query surface preserved.** On disk the JSON is a list of setting
records, each carrying the canonical `IT_number` and
`IT_coordinate_system_code` fields — there is no separate `coord_code`
storage field; that name is only the runtime variable for the tuple key.
On load the module reconstructs the same in-memory `SPACE_GROUPS` dict
keyed by `(IT_number, IT_coordinate_system_code)`, so every current
lookup keeps working unchanged. Because each record also carries
`name_H-M_alt` and `hall_symbol`, the database can rebuild an
**H-M-short-symbol → IT_number** index equivalent to cryspy's
`get_it_number_by_name_hm_short` (1:1 — each of the 230 groups has a
single short symbol), with the setting selected separately per IT number
exactly as the `SpaceGroup` category does today. A fuller "H-M symbol
_with_ setting → specific `(IT_number, IT_coordinate_system_code)`"
lookup is a multimap (one symbol can map to several settings/origins)
and is out of committed scope; actually dropping the cryspy dependency
is left to Deferred Work. The point here is only that the new database
is **at least as queryable as today**, by both IT number +
coordinate-system code and by Hermann-Mauguin symbol. The generated
database therefore includes 816 records: 530 cctbx-tabulated settings,
226 cryspy reference-settings aliases, and 60 runtime coordinate-code
aliases, so every coordinate code the `SpaceGroup` category can produce
— i.e. every `get_it_coordinate_system_codes_by_it_number` value — is a
valid `SPACE_GROUPS` key.

### 2. JSON storage removes the unpickle workaround

The database is stored as **gzip-compressed JSON**
(`space_groups.json.gz`), not a pickle. `space_groups.py` today loads a
pickle through a bespoke `_RestrictedUnpickler` that permits only
built-in types — a security workaround for a file that holds nothing but
dicts, lists, strings, ints, and `None`. Switching to JSON **deletes
that workaround**: the loader decompresses and `json.load`s the stream,
then rebuilds the `(IT_number, coord_code)`-keyed dict (§1). JSON cannot
execute code, is human-readable, diffable, and language-agnostic; the
only constraint on the generator is to emit JSON-native types, which the
string-based schema already satisfies.

### 3. Generation sources: cryspy first, cctbx for setting metadata

Build the Wyckoff-facing part of the database from **cryspy
`wyckoff.dat`** first. It is complete for all 230 IT groups, carries the
letters and representative coordinate orbits, and stores the dotted
International-Tables-style site-symmetry strings that
`wyckoff-letter-detection.md` needs. This keeps the minimum
implementation close to the source already used by the calculator while
moving ownership of the data into EasyDiffraction.

Use **cctbx/sgtbx** for the setting-level metadata that cryspy's Wyckoff
table does not provide in the same form: full symmetry operators,
generators, point group, Laue class, Hall symbol candidates, and
operation/orbit-closure checks. cctbx is a **generation-only**
dependency: it is installed into the pixi environment **only for the
generation run** and removed afterwards — it is never added to the
runtime dependencies and never imported at runtime, which loads only the
bundled JSON. Building the database is a **one-time effort**, not a
recurring pipeline: cctbx is installed once for that build, the exact
software versions used are recorded in §Build provenance, and the
install is then removed. A pinned GitHub data download was the
considered alternative; the temporary install was chosen for the
authoritative API and the least parsing risk.

### 4. One-time local generation helper

Keep the one-time generator at
`tmp/space-groups/helper-tools/generate_space_groups.py` and run it
**once** to emit `space_groups.json.gz`. It is intentionally not kept in
the branch after implementation, because it is local curation tooling
rather than runtime or routine development tooling. The future rebuild
path is preserved by keeping the helper in the ignored
`tmp/space-groups/` workspace and by recording its SHA-256, input
sources, command line, software versions, and ADR companion curation
overrides in §Build provenance. The generated JSON is the committed
artifact; the ADR and overrides explain how it was produced.

### 5. Multi-source verification

The generator verifies its output against **every** gathered source, not
just the primary one:

- cryspy `wyckoff.dat` — letters, multiplicities, site symmetries, and
  representative coordinate orbits;
- gemmi (already a runtime dependency, 0.7.5) — `spacegroup_table()`
  covers all 230 groups and 564 settings with Hall symbols and full
  symmetry operations. gemmi has **no** Wyckoff API (no letters, site
  symmetries, or special-position enumeration), so its independent
  contribution is precise: it validates the **set of settings** and the
  **symmetry operations** per setting, and — given a representative
  coordinate taken from another source — it confirms that
  representative's **orbit and multiplicity** by applying its operations
  (an operation-closure check). It does **not** independently produce
  the representative coordinates, letters, or site-symmetry symbols, so
  the disagreement report labels a gemmi orbit/multiplicity check as
  _dependent_ on the cctbx/cryspy representative, not as an independent
  third source for that representative;
- Avogadro `data/avogadro/spacegroupdata.h` and SgInfo
  `data/sginfo/sginfo.dat` — settings and multiplicities;
- cctbx `data/cctbx/symbols.cpp` / `data/cctbx/bricks.cpp` — source
  provenance for Hall symbols and settings;
- RASPA `data/raspa/raspa-space-group-information.csv` — setting /
  cell-choice enumeration;
- International Tables Vol A — authoritative spot-checks.

Verification covers presence (all 230 groups, their standard settings,
and the public cryspy coordinate-code alias surface), per-position
values (letter, multiplicity, site symmetry), and orbit coordinates.

### 6. Disagreement report and human-in-the-loop curation

Where **two or more sources disagree** on any value — a multiplicity, a
site-symmetry symbol, a coordinate, a letter, the presence of a setting
— the generator emits a structured **disagreement report** entry
containing:

- the case (group / setting / Wyckoff letter / field);
- each contributing source and its value;
- an `IT` column for later International Tables comparison;
- an `Override` column for the final selected value and rationale.

The maintainer inspects the report and **selects** the authoritative
value per case. Selections are recorded in a checked-in **YAML overrides
file**,
`docs/dev/adrs/suggestions/space-group-database/space_groups_overrides.yaml`
while the ADR is proposed. If this ADR is accepted, move that companion
file with the ADR to the accepted ADR area. YAML lets each selection
carry an inline comment recording its rationale. The generator consumes
it during the build, so every non-obvious choice is explicit and
auditable rather than baked silently into the binary. The overrides are
deliberately not embedded in this ADR or in the implementation plan:
those Markdown files describe the process, while the YAML file is the
stable machine-readable input to the generator with a focused diff for
curated values. The disagreement report itself is a local curation
artifact under `tmp/space-groups/extracted-comparison/`. The Markdown
report is split into one table per field, and the comparison folder also
contains a combined CSV plus one CSV per field so each class of
disagreement can be checked independently. Cases where all sources agree
need no entry.

### 7. Current curation baseline and deferrals

The extracted comparison data is sufficient for the **minimal database
needed by `wyckoff-letter-detection.md`**. The Phase 1 build therefore
uses this source priority:

1. Use cryspy `data/cryspy/wyckoff.dat` as the initial authority for
   Wyckoff-facing fields: letters, multiplicities, site-symmetry
   symbols, and representative coordinate orbits. It is complete for all
   230 IT groups and carries the International-Tables-style
   site-symmetry strings that the detection feature needs.
2. Use cctbx/sgtbx as the source for setting-level symmetry metadata
   that cryspy does not provide in the same table, especially full
   symmetry operators, generators, point group, Laue class, Hall symbol
   candidates, and orbit-closure checks.
3. Use RASPA, Avogadro, SgInfo, and gemmi as cross-checks for setting
   presence, Hermann-Mauguin / Hall symbols, centring, multiplicities,
   and operation closure. When cryspy lacks a field or a value is
   disputed, the maintainer should prefer the source that agrees with
   the largest independent cluster and record the choice in the ADR
   companion overrides file.

This is intentionally a **curated seed database**, not the final
International Tables audit. The `IT` and `Override` columns in the
comparison reports are left for future human verification. Future
curation should check flagged rows against International Tables Vol A
first, and may also consult the IUCr International Tables Symmetry
Database (`https://symmdb.iucr.org/`), Bilbao Crystallographic Server,
and ISODISTORT as independent online references for Wyckoff-position
data. The IUCr Symmetry Database is especially relevant where subscriber
access is available because its Wyckoff-position program exposes
multiplicities, letters, site-symmetry symbols, and coordinate triplets.
Those checks are deferred so the database can unblock Wyckoff detection
now while keeping every non-obvious choice visible for later correction.

The triclinic groups do not require a special-case database model. P1
(IT 1) has one Wyckoff position, `a`, with multiplicity 1. P-1 (IT 2)
has the expected inversion-centre special positions plus the general
position. The only awkwardness is representation of "no
coordinate-system code": EasyDiffraction's `SpaceGroup` category uses
the empty string `''`, while the table key uses `None`. The database
keeps `(1, None)` and `(2, None)`; callers normalise `''` to `None` at
lookup boundaries, as specified in
[`wyckoff-letter-detection.md`](wyckoff-letter-detection.md). This is
the least surprising solution because it keeps "no setting" distinct
from any real coordinate-code string without inventing a sentinel value.

### 8. The database file is generated, not hand-edited

`space_groups.json.gz` is never edited by hand. Any correction flows
through the curation overrides and a regeneration run, keeping the file
and the documented decisions in sync.

## Consequences

### Positive

- Complete coverage of the **data**: every one of the 230 groups and
  their standard settings is present, including the currently-broken P4
  / P3 / P6 / Pm-3 and the monoclinic alternative settings. For settings
  with a non-`None` coordinate code the existing `(IT_number, code)`
  lookups find the new entries immediately, with no consumer change; the
  two triclinic `None`-code groups additionally need the companion
  consumer-side fix (see Compatibility).
- Documented, auditable provenance: the local generator helper SHA-256,
  curation overrides, local disagreement report, and recorded build
  versions show exactly how the seed database was produced and which
  value checks remain deferred.
- The Wyckoff-detection "unsupported group" path shrinks from "common
  groups" to genuinely-exotic settings, simplifying that feature.
- The 42-group gap and the missing settings become permanent regression
  guards.

### Trade-offs

- A temporary, generation-only cctbx install is needed for the one-time
  build (never a runtime dependency).
- Deferred human curation over the disagreement report before the seed
  is promoted from cross-checked package data to a final International
  Tables audit.
- `space_groups.json.gz` is larger than today's partial pickle (gzipped
  JSON is less compact than gzipped pickle), though still well under
  ~1.5 MB.

### Compatibility Outcomes

- The in-memory `SPACE_GROUPS` dict is unchanged (same
  `(IT_number, coord_code)` keys; existing value keys preserved, new
  ones added), so `crystallography.py`, the calculators, and CIF code
  need no changes — they see complete data and ignore the new keys.
- Only the on-disk format changes (pickle → gzipped JSON); the
  `_RestrictedUnpickler` and the pickle dependency are **removed**, a
  net simplification.
- Existing projects load identically. Previously-unsupported groups with
  a real coordinate code (P4, P3, P6, Pm-3, the monoclinic alternative
  settings, …) gain correct symmetry behaviour immediately — the
  existing `(IT_number, code)` lookups simply find the now-present
  entries. The two triclinic `None`-code groups remain skipped until the
  companion consumer-side fix lands: `_get_wyckoff_exprs()` returns
  early when `coord_code is None` and `_get_general_position_ops()`
  indexes the raw key, so they need the `''`→`None` normalisation
  defined in
  [`wyckoff-letter-detection.md`](wyckoff-letter-detection.md) §2 (which
  also updates these call sites). This ADR delivers the data; that ADR
  delivers the `None`-code consumer handling.

## Alternatives Considered

- **cryspy as the sole source.** Fastest (already present, verified
  complete, zero new deps), but it does not provide every setting-level
  metadata field needed for the new database and its provenance is the
  calculator the database is meant to outgrow. Accepted as the initial
  authority for Wyckoff-facing fields, but not as the sole authority for
  the whole database.
- **Parse SgInfo / cctbx C sources directly.** Most "self-owned", but
  the highest parsing and verification burden. Used as cross-checks
  instead of the primary generator.
- **Generate Wyckoff orbits at runtime from symmetry operators** (no
  bundled table). Rejected: heavy runtime cost on a hot path, and it
  discards the established, cache-friendly table design.
- **Keep the partial table and degrade gracefully.** Rejected: it leaves
  common groups (P4, P3, P6) silently without symmetry information.

## Verification

- A regression test asserts that **all 230 groups, their standard
  settings, and every public cryspy coordinate-code alias are present**
  in the loaded table (guarding against the current 42-group /
  18-setting gap).
- A query-surface test asserts that every coordinate-system code exposed
  by `SpaceGroup` resolves as a `(IT_number, coord_code)` key and that
  Hermann-Mauguin symbol resolution still reaches every group.
- Spot-check tests compare representative groups against International
  Tables: a primitive tetragonal (P4), a trigonal (P3), a hexagonal
  (P6), a centrosymmetric cubic (Pm-3), a monoclinic with cell choices,
  and an origin-choice group.
- The disagreement report is itself a verification artifact, reviewed by
  the maintainer before the database is accepted.
- A packaging regression check builds the wheel and inspects it directly
  (`tools/check_packaged_db.py`), confirming the renamed
  `space_groups.json.gz` is shipped as package data, the obsolete
  `.pkl.gz` is gone, and the archive covers all 230 groups — catching
  missing package-data inclusion without coupling to the package's full
  runtime dependency tree.
- Per the document-review rule, this ADR was written without running
  tests, linters, or build commands.

## Build Provenance

The database is built once, so the exact tooling and inputs used to
produce the committed `space_groups.json.gz` are recorded here at
generation time. This section **is** the named, durable provenance
artifact that makes the one-time build auditable and reconstructable
even after cctbx is removed from the environment.

Generation run:

```bash
pixi exec --spec cctbx --spec gemmi --spec sympy --spec pyyaml \
  python tmp/space-groups/helper-tools/generate_space_groups.py \
  --output-json src/easydiffraction/crystallography/space_groups.json.gz \
  --write-comparison-folder tmp/space-groups/extracted-comparison \
  --print-summary
```

Build environment:

- **cctbx** from conda-forge:
  - `cctbx 2026.4 py314he55896b_1`
  - `cctbx-base 2026.4 py314h4545a6d_1`
- **Helper-only packages** from conda-forge:
  `gemmi 0.7.5 py314h2fd7851_0`, `sympy 1.14.0 pyh2585a3b_106`,
  `pyyaml 6.0.3 py314h6e9b3f0_1`.
- **Python and platform:** Python 3.14.5, macOS-26.2 arm64
  (`macOS-26.2-arm64-arm-64bit-Mach-O`).
- **Runtime cross-check versions:** cryspy 0.11.0, gemmi 0.7.5.

Generated and curation artifacts:

- `src/easydiffraction/crystallography/space_groups.json.gz`:
  `30f0051c669712ab34d991e60223c5e29264fc033b2ab03392cc01465ceba926`
- `tmp/space-groups/helper-tools/generate_space_groups.py`:
  `bf10dcfbcf9e60485037ddabc65425e61f746ad9649cd3ccc67376dd6aae241a`
- `docs/dev/adrs/suggestions/space-group-database/space_groups_overrides.yaml`:
  `7077eec25d0f3b852dd7096a24dc7ac438467f9cb594f91a65ce10cda0e0722a`
- `tmp/space-groups/extracted-comparison/disagreements.md`:
  `dda940fbf75862516411685c9b9bdf7170fa4a116f90eeeff93bd068b8acda4c`
- `tmp/space-groups/extracted-comparison/all-fields.csv`:
  `4c69060514c58730d905d204144364d5696af9781d5d6132966960131ccd6b3a`

Gathered input snapshots:

- cctbx `symbols.cpp`, GitHub `cctbx/cctbx_project` commit
  `9031bd719b56bc55bc5a276f407a9a64cc08c2c3`:
  `901e038d6c060a7630c4e05f85b5c2fb6940edd9c6a2421755c146e29298b81b`
- cctbx `bricks.cpp`, GitHub `cctbx/cctbx_project` commit
  `9031bd719b56bc55bc5a276f407a9a64cc08c2c3`:
  `85cfee5c215dbbfb9520730186ddc1d73b2ba93d5c94b969dc8968da6c5f2534`
- Avogadro `spacegroupdata.h`, GitHub `OpenChemistry/avogadrolibs`
  commit `88ff1a7af4625824b258933715d8f112bc35453e`:
  `c5688f343ae2f37ec2e37beea2534d47f192f354bbe382bf11203c8e7b22cac9`
- cryspy `wyckoff.dat` snapshot:
  `ce6a576068610fb9a0d80a77f1c8957c3d1138a0e8f8fa9c248c62786dd3fb38`
- cryspy `function_2_space_group.py` snapshot:
  `e3cf8fd594c053068ed6f68d805ee9d216cfefa392351a2456cb3b2632bc4462`
- SgInfo `sginfo.dat` snapshot:
  `54591fd507aeb8cd24f9cb7e552a4b85cd6c5fd8f905782b489639f4cce51205`
- RASPA appendix extraction `raspa-space-group-information.csv`:
  `61258cb176cb5851efb042d0ac144f6f3ee9f730fc92564d4550acdd52dabd17`
- RASPA manual PDF `raspa.pdf`:
  `c5dfc865276667f787f793b7b4eacddcde268d5c7a1fa203a00db612ad7f79cf`
- International Tables Vol A PDF:
  `6d619f4e71754dc257cffc1fd8e92e23145e2f8511fa97ed1b5522773da3666e`
- International Tables Vol C PDF:
  `f095728556c0ebb05ab55ca2bbccac76c544f04f71da3a121b0477ba66699a0d`
- IUCr CIF Core dictionary snapshot:
  `dd7460c1ed1666adecf2f77441556920a051f076c31a6b7274d33dfbe2b6d5ad`

### P1.1 extraction observations

The first cctbx extraction pass enumerates 530 cctbx-tabulated setting
records covering all 230 IT groups, with no duplicate
`(IT_number, IT_coordinate_system_code)` keys after normalisation. This
is not identical to the wider cryspy-style coordinate-code surface used
by EasyDiffraction today: cryspy exposes additional repeated
axis/cell-choice aliases for some monoclinic, orthorhombic, and trigonal
settings. The Phase 1 database adds 226 reference-settings alias records
and a further 60 runtime coordinate-code aliases — the redundant
cell-choice-2/3 codes for the five primitive monoclinic groups IT
3/4/6/10/11, which cryspy's runtime
`get_it_coordinate_system_codes_by_it_number` exposes and which copy
cell choice 1 verbatim — producing 816 records total, so every
coordinate code the `SpaceGroup` category can return resolves.
Reference-settings alias records are generated from cctbx by parsing the
cryspy Hermann-Mauguin alias where cctbx accepts it; otherwise they copy
the closest same-IT cctbx setting and carry the cryspy alias name.
Detailed value verification for those alias records remains part of the
deferred International Tables audit.

## Open Questions

None outstanding. Build-time specifics — the exact software versions and
the candidate additional-metadata fields — are recorded in §Build
Provenance, §P1.1 extraction observations, and Deferred Work
respectively.

## Deferred Work

- Full human verification against International Tables Vol A, with the
  IUCr International Tables Symmetry Database
  (`https://symmdb.iucr.org/`), Bilbao Crystallographic Server, and
  ISODISTORT as additional independent references for flagged
  Wyckoff-position rows. Record corrections in the ADR companion
  overrides file and regenerate the database/report.
- **Additional metadata cctbx exposes**, deliberately deferred from the
  symmetry-core schema (§1): asymmetric-unit definition, reflection /
  systematic-absence conditions, centring translation vectors,
  per-Wyckoff special-position operators, and matrix-form generators.
  Add when a concrete consumer needs them.
- Dropping the remaining cryspy dependency for Hermann-Mauguin →
  IT-number resolution, using the database's own `name_H-M_alt` /
  `hall_symbol` index (§1).
- Re-evaluating the coordinate encoding (strings versus parsed matrices)
  if profiling shows the string parse is a bottleneck.

## Related ADRs

- [`wyckoff-letter-detection.md`](wyckoff-letter-detection.md) — the
  dependent feature; its `''`→`None` coordinate-code normalisation and
  its "unsupported group" handling both build on this database.
- [`iucr-cif-tag-alignment.md`](../accepted/iucr-cif-tag-alignment.md) —
  consumes space-group and Wyckoff data on export.
