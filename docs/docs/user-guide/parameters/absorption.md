[easydiffractionCIF][0]{:.label-cif}

# \_absorption

**Sample-absorption** correction for powder samples. A sample in a
cylindrical (Debye–Scherrer) holder absorbs the incident and diffracted
beams by an amount that depends on scattering angle, attenuating
low-angle reflections more than high-angle ones. Correcting for it
removes an angle-dependent distortion of the measured intensities.

The correction is a switchable category: `type = 'none'` (the default)
applies no correction, while `type = 'cylinder-hewat'` applies the
cylindrical Hewat model. It is applied identically on the **CrysPy** and
**CrysFML** engines for constant-wavelength Bragg powder experiments.

The absorption coefficient `mu_r` is normally entered as a known,
**fixed** value (it is strongly correlated with the atomic displacement
parameters and the scale). There is no IUCr standard data name for
`mu_r`, so it is serialised under the EasyDiffraction custom dictionary.

## \_absorption.type

Active absorption correction type. One of `none` (no correction) or
`cylinder-hewat` (cylindrical Debye–Scherrer, Hewat model). Use
`experiment.absorption.show_supported()` to list the types available for
the current experiment.

## \_absorption.mu_r

Linear absorption coefficient times the sample radius, `μR`
(dimensionless). Only present for `type = 'cylinder-hewat'`. The Hewat
expansion is validated to four decimals for `μR ≲ 1.5`; larger values
are still computed but emit a warning, as a Lobanov-type form is
preferable in that range.

<!-- prettier-ignore-start -->
[0]: #
[1]: https://www.iucr.org/resources/cif/dictionaries/browse/cif_core
[2]: https://www.iucr.org/resources/cif/dictionaries/browse/cif_pd
<!-- prettier-ignore-end -->
