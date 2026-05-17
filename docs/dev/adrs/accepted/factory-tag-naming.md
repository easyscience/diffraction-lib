# ADR: Factory Tag Naming

## Status

Accepted.

## Date

2026-05-17

## Group

Naming.

## Context

Factory tags are persisted and used for public selection. Inconsistent
abbreviations or ordering would make saved files and user code harder to
read.

## Decision

Canonical factory tags are:

- lowercase
- hyphen-separated
- semantically ordered from general to specific
- unique within a factory

Use standard abbreviations:

| Concept             | Abbreviation |
| ------------------- | ------------ |
| Powder              | `pd`         |
| Single crystal      | `sc`         |
| Constant wavelength | `cwl`        |
| Time-of-flight      | `tof`        |
| Bragg scattering    | `bragg`      |
| Total scattering    | `total`      |

Context-local aliases are allowed when the owning object already
disambiguates the choice, for example `pseudo-voigt` inside a CWL
experiment.

## Consequences

Saved tags are stable and greppable, while user-facing APIs can remain
short where context makes the canonical prefix redundant.
