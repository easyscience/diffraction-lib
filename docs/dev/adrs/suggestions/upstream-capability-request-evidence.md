# ADR: Upstream Capability Request Evidence

## Status

Proposed.

## Date

2026-06-18

## Group

Quality.

## Context

EasyDiffraction depends on external calculation engines for much of its
scientific functionality. When a required feature exists in an upstream
Fortran or reference-code implementation but is missing, incomplete, or
not wired through the Python API, maintainers need to request upstream
work with enough evidence that the request is actionable.

The first CrysFML Python API request package exposed a repeatable
pattern:

- audit the upstream Fortran source, installed Python API, tutorials,
  and verification notebooks;
- identify the exact feature missing from the Python surface;
- construct a small reproducible comparison against FullProf;
- show that the current Python/CFL path agrees before the feature is
  enabled;
- show that it disagrees after the feature is enabled in FullProf and
  represented, or attempted, through the Python/CFL path;
- attach a minimal script and screenshot so upstream developers can
  reproduce the issue without running the full EasyDiffraction stack.

Without a convention, future requests risk becoming too narrative,
too broad, or too hard for upstream developers to reproduce. They may
also accumulate untracked scratch files, generated FullProf byproducts,
or unclear "known discrepancy" examples that are difficult to maintain.

This ADR complements
[Verification Example Lifecycle](verification-example-lifecycle.md). That
ADR governs public Verification pages. This ADR governs development-only
request packets prepared for upstream projects such as CrysFML, CrySPY,
FullProf-related tooling, or other calculation backends.

## Decision

### 1. Prepare one request packet per upstream project/API surface

Create development-only request packets under `docs/dev/` using this
shape:

```text
docs/dev/<upstream>-<api>-feature-requests.md
docs/dev/<upstream>-<api>-requests/
|-- common helper(s)
|-- request_01_<feature>.py
|-- request_02_<feature>.py
`-- ...
```

Use lowercase ASCII slugs. The document is the human-facing request
summary. The scripts are the executable evidence.

### 2. Start from a source/API capability audit

Before writing requests, inspect all relevant sources:

- current EasyDiffraction tutorials and verification notebooks that need
  the feature;
- installed Python package public API;
- upstream source branch or release that supposedly contains the lower
  level functionality;
- local reference fixtures, usually FullProf `.pcr`, `.prf`, `.bac`,
  `.sum`, or single-crystal integrated-intensity files.

Record the upstream repository, branch, commit, Python package name, and
Python package version in the request document.

If the feature is not present in the upstream lower-level implementation,
do not include it in this request packet. Put it in "Out of scope" or a
separate issue instead.

### 3. Phrase every item as a concrete upstream API request

Each request section begins with this shape:

```text
Please add <feature> support to <upstream Python API surface>.
```

Then include:

- a short description of why EasyDiffraction needs the feature;
- what exists in the lower-level upstream code, if known;
- what is missing from the Python API;
- the exact Python/CFL/API surface requested.

Avoid long implementation history. The section should be ready to paste
into an upstream issue.

### 4. Include the parameter evidence beside the request

Every request section includes the smallest relevant parameter snippets:

- **FullProf `.pcr` setting** or other reference-code setting that
  enables the feature;
- **CFL string**, Python dictionary fields, or desired API call shape
  that should represent the same feature through the upstream Python API.

When no CFL string can represent the feature, say that explicitly and
show the desired Python API shape instead.

Example:

```text
FullProf `.pcr`:
  Ext1 = 0.1834, Ext-Model = 1

Desired Python API:
  extinction model parameters + hkl/intensity input
  -> corrected intensities or correction factors
```

### 5. Scripts demonstrate agreement before and disagreement after

Each request script contains two evidence blocks:

1. **Control:** current Python/CFL path versus hardcoded FullProf data
   with the requested feature disabled. This should agree, or the script
   must explain why a direct control is impossible.
2. **Feature enabled:** the same small pattern/hkl window after the
   feature is enabled in FullProf and represented, or attempted, through
   the Python/CFL path. This should show the current discrepancy.

The control and feature-enabled comparisons must use the same scale when
that is necessary to expose an intensity correction. A fresh scale fit
must not hide the requested effect.

### 6. Hardcode only small reference windows

Do not embed full profiles in request scripts. Hardcode only the
smallest FullProf output window that makes the feature visible:

- a few peaks for powder profiles;
- a small hkl/integrated-intensity table for single-crystal requests;
- enough points around a shifted or split peak to make the discrepancy
  obvious.

The script should be understandable by upstream maintainers without the
full EasyDiffraction project data tree.

### 7. Use the narrowest upstream Python entry point

Use the upstream Python API being requested wherever possible. For CFL
requests, call the CFL API directly rather than going through
EasyDiffraction objects. For dictionary requests, use the dictionary API
or describe why a direct call cannot be made yet.

When a requested feature is outside the available entry point, the
script must:

- run a nearby control that proves the current entry point works;
- print a clear diagnostic explaining the missing API surface;
- avoid pretending that an unrelated powder profile tests a
  single-crystal or in-memory structure-factor feature.

### 8. Screenshots are part of the request packet

Each script supports a simple plot mode or produces output suitable for
a screenshot. The screenshot attached upstream should have a caption
with this information:

- sample/experiment name;
- feature-off agreement statement;
- feature-on parameter values in FullProf;
- corresponding CFL/API parameter values, if representable;
- one sentence naming the missing Python API behavior.

Screenshots are not committed unless they are intentionally used as
durable documentation. For ordinary upstream issues, attach them to the
issue outside the repository.

### 9. Generated reference byproducts stay out of commits

Running FullProf may create `.new`, `.out`, `.fst`, `.sub`, `.cif`,
`fort.77`, and other byproducts. Do not commit these unless the request
document or script consumes them as evidence.

If a FullProf reference must be regenerated for a durable verification
page, follow [Verification Example Lifecycle](verification-example-lifecycle.md)
instead. Upstream request packets should prefer hardcoded minimal
windows and temporary `/tmp` generation during investigation.

### 10. Verification before publishing the packet

Before sending or committing a request packet, run at least:

```shell
pixi run python -m py_compile docs/dev/<upstream>-<api>-requests/*.py
pixi run ruff check docs/dev/<upstream>-<api>-requests
```

Also run every request script once in non-plot mode. Note any
intentional current failures in the request document and in the script
output.

## Consequences

### Positive

- Upstream developers receive reproducible, focused requests rather than
  broad feature descriptions.
- The request document stays useful even after screenshots are detached
  into upstream issue trackers.
- Future investigations produce less scratch-file churn and fewer
  ambiguous "known discrepancy" examples.
- The same process works for CFL, dictionary, single-crystal, TOF, and
  in-memory API gaps because it explicitly allows "not representable"
  cases.

### Negative / cost

- Preparing a request takes longer than writing a prose issue because it
  requires reference data and a runnable script.
- Some features need a nearby control rather than a perfect
  feature-specific control, especially when the current API cannot
  represent the feature at all.
- Hardcoded windows must be refreshed manually if the reference
  `.pcr`/FullProf setup intentionally changes.

## Alternatives Considered

| #   | Alternative                                             | Verdict                                                                                                      |
| --- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| A   | Write upstream issues directly from prose notes.        | Rejected. Too hard to reproduce and too easy to omit the exact parameter mapping.                             |
| B   | Promote every request into public Verification pages.   | Rejected. Request packets are development evidence; public Verification pages need stronger lifecycle rules. |
| C   | Commit full FullProf output profiles for every request. | Rejected. Full profiles are large and noisy; small hardcoded windows are enough for issue evidence.          |
| D   | Use one notebook for all requests.                      | Rejected. One script per request keeps attachments small and lets upstream developers run only their feature. |

## Open Questions

1. Should request packets eventually live under a dedicated
   `docs/dev/upstream-requests/` directory if more upstream projects
   accumulate?
2. Should screenshots ever be committed as durable evidence, or should
   they always remain issue attachments?
3. Should a helper generate the hardcoded FullProf windows from `.prf`
   files to reduce manual transcription errors?
