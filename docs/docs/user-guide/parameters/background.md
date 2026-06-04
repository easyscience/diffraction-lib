[pdCIF][2]{:.label-cif}

# \_pd_background

This category defines various background functions that could be used
when calculating diffractograms. Please see the
[IUCr page](https://www.iucr.org/resources/cif/dictionaries/browse/cif_pd)
for further details.

!!! tip "Automatic background estimation"

    Line-segment background points can be detected automatically from the
    measured pattern with
    [`background.auto_estimate()`](../analysis-workflow/experiment.md#background-category),
    instead of entering them by hand.

## [\_pd_background.line_segment_X](https://www.iucr.org/resources/cif/dictionaries/browse/cif_pd)

List of X-coordinates used to create many straight-line segments
representing the background in a calculated diffractogram.

Supported values: `2theta` and `time-of-flight`

## [\_pd_background.line_segment_intensity](https://www.iucr.org/resources/cif/dictionaries/browse/cif_pd)

List of intensities used to create many straight-line segments
representing the background in a calculated diffractogram.

## [\_pd_background.X_coordinate](https://www.iucr.org/resources/cif/dictionaries/browse/cif_pd)

The type of X-coordinate against which the pd_background values were
calculated.

<!-- prettier-ignore-start -->
[0]: #
[1]: https://www.iucr.org/resources/cif/dictionaries/browse/cif_core
[2]: https://www.iucr.org/resources/cif/dictionaries/browse/cif_pd
<!-- prettier-ignore-end -->
