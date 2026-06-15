---
title: absorption
---

# :material-blur: absorption

[pd-neut-cwl][3]{:.label-experiment} [pd-xray][3]{:.label-experiment}

## :material-tag: mu_r { #absorption-mu-r }

| Access                            | Source                    |
| --------------------------------- | ------------------------- |
| absorption.mu_r                   | [code][0]{:.label-cif}    |
| \_absorption.mu_r                 | [Edi][0]{:.label-cif}     |
| \_easydiffraction_absorption.mu_r | [coreCIF][0]{:.label-cif} |

Linear absorption coefficient times the sample radius, `μR`
(dimensionless). Only present for `type = 'cylinder-hewat'`. It is
normally entered as a known, fixed value, since it is strongly
correlated with the displacement parameters and the scale. The Hewat
expansion is validated to four decimals for `μR ≲ 1.5`; larger values
are still computed but emit a warning.

## :material-shape: type { #absorption-type }

| Access                            | Source                    |
| --------------------------------- | ------------------------- |
| absorption.type                   | [code][0]{:.label-cif}    |
| \_absorption.type                 | [Edi][0]{:.label-cif}     |
| \_easydiffraction_absorption.type | [coreCIF][0]{:.label-cif} |

Active absorption correction type. One of `none` (no correction) or
`cylinder-hewat` (cylindrical Debye–Scherrer, Hewat model). Use
`experiment.absorption.show_supported()` to list the types available for
the current experiment. This category is available for
constant-wavelength Bragg powder experiments.

<!-- prettier-ignore-start -->
[0]: #
[3]: ../../glossary.md#experiment-type-labels
<!-- prettier-ignore-end -->
