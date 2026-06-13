[pdCIF][2]{:.label-cif}

# `_background`

EdSTAR stores line-segment and polynomial background rows under
`_background`. Report CIF maps these rows to the corresponding pdCIF
background names where pdCIF has equivalents.

!!! tip "Automatic background estimation"

    Line-segment background points can be detected automatically with
    [`background.auto_estimate()`](../analysis-workflow/experiment.md#background-category).

## `_background.id` { #background-id }

Stable row identifier for a line-segment background point.

## `_background.position` { #background-position }

X-axis position of the background point.

## `_background.intensity` { #background-intensity }

Background intensity at the stored position.

## `_background.order` { #background-order }

Chebyshev polynomial term order.

## `_background.coef` { #background-coef }

Chebyshev polynomial coefficient.

## `_background.type` { #background-type }

Background model type.

<!-- prettier-ignore-start -->
[0]: #
[1]: https://www.iucr.org/resources/cif/dictionaries/browse/cif_core
[2]: https://www.iucr.org/resources/cif/dictionaries/browse/cif_pd
<!-- prettier-ignore-end -->
