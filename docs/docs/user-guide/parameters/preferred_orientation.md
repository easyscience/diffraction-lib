[pdCIF][2]{:.label-cif}

# `_preferred_orientation`

EdSTAR stores per-structure preferred-orientation rows under
`_preferred_orientation`. The correction uses the March-Dollase model.

!!! tip "No-op defaults"

    The defaults (`march_r = 1`, `march_random_fract = 0`) leave the
    calculated intensities unchanged.

## `_preferred_orientation.structure_id` { #preferred-orientation-structure-id }

Identifier of the linked structure corrected by this row.

## `_preferred_orientation.march_r` { #preferred-orientation-march-r }

March coefficient `r`. `r = 1` means no preferred orientation, `r < 1`
describes plate-like crystallites, and `r > 1` describes needle-like
crystallites.

## `_preferred_orientation.index_h` { #preferred-orientation-index-h }

Texture-axis Miller index _h_.

## `_preferred_orientation.index_k` { #preferred-orientation-index-k }

Texture-axis Miller index _k_.

## `_preferred_orientation.index_l` { #preferred-orientation-index-l }

Texture-axis Miller index _l_.

## `_preferred_orientation.march_random_fract` { #preferred-orientation-march-random-fract }

Random, untextured fraction of crystallites.

<!-- prettier-ignore-start -->
[0]: #
[1]: https://www.iucr.org/resources/cif/dictionaries/browse/cif_core
[2]: https://www.iucr.org/resources/cif/dictionaries/browse/cif_pd
<!-- prettier-ignore-end -->
