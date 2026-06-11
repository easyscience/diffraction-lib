[pdCIF][2]{:.label-cif}

# \_pref_orient

Per-phase **preferred-orientation** (texture) correction using the
March–Dollase model. Powder samples whose crystallites pack with a
preferred orientation (platy crystals lying flat, needles aligning) show
Bragg intensities that deviate from the ideal random-powder average;
this correction restores them.

Each row corrects one linked phase along one crystallographic direction.
The defaults (`march_r = 1`, `march_random_fract = 0`) are a
mathematical no-op, so a freshly added row applies no texture until you
change them. Supported on the **CrysPy** engine for constant-wavelength
Bragg powder experiments.

See the
[IUCr powder dictionary](https://www.iucr.org/resources/cif/dictionaries/browse/cif_pd)
(`pd_pref_orient_March_Dollase`) for the standard data names.

## \_pref_orient.phase_id

Identifier of the linked phase corrected by this row.

## \_pref_orient.march_r

March coefficient `r`. `r = 1` means no preferred orientation; `r < 1`
describes disk-/plate-like crystallites and `r > 1` needle-like ones.
This is the standard IUCr/FullProf/GSAS coefficient (serialised as
`_pd_pref_orient_March_Dollase.r`); the CrysPy backend stores its
reciprocal internally.

## \_pref_orient.index_h

Texture-axis Miller index _h_.

## \_pref_orient.index_k

Texture-axis Miller index _k_.

## \_pref_orient.index_l

Texture-axis Miller index _l_.

## \_pref_orient.march_random_fract

Random (untextured) fraction of crystallites; `0` is pure March–Dollase.
There is no IUCr standard name for this quantity, so it is serialised
under the EasyDiffraction custom dictionary.

<!-- prettier-ignore-start -->
[0]: #
[1]: https://www.iucr.org/resources/cif/dictionaries/browse/cif_core
[2]: https://www.iucr.org/resources/cif/dictionaries/browse/cif_pd
<!-- prettier-ignore-end -->
