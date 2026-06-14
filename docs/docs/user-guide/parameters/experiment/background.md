---
title: background
---

# :material-waveform: background

[pd-neut-cwl][3]{:.label-experiment}
[pd-neut-tof][3]{:.label-experiment} [pd-xray][3]{:.label-experiment}

## :material-tag: id { #background-id }

| Access          | Source                  |
| --------------- | ----------------------- |
| \_background.id | [Edifa][0]{:.label-cif} |

Identifier for this background line segment.

## :material-arrow-collapse-right: position { #background-position }

| Access                         | Source                  |
| ------------------------------ | ----------------------- |
| background.position            | [code][0]{:.label-cif}  |
| \_background.position          | [Edifa][0]{:.label-cif} |
| \_pd_background.line_segment_X | [pdCIF][0]{:.label-cif} |

Position used to create many straight-line segments.

## :material-arrow-collapse-up: intensity { #background-intensity }

| Access                                 | Source                  |
| -------------------------------------- | ----------------------- |
| background.intensity                   | [code][0]{:.label-cif}  |
| \_background.intensity                 | [Edifa][0]{:.label-cif} |
| \_pd_background.line_segment_intensity | [pdCIF][0]{:.label-cif} |

Intensity used to create many straight-line segments.

## :material-format-superscript: order { #background-order }

| Access                          | Source                  |
| ------------------------------- | ----------------------- |
| background.order                | [code][0]{:.label-cif}  |
| \_background.order              | [Edifa][0]{:.label-cif} |
| \_pd_background.Chebyshev_order | [pdCIF][0]{:.label-cif} |

Order used in a Chebyshev polynomial background term.

## :material-arrow-collapse-up: coef { #background-coef }

| Access                         | Source                  |
| ------------------------------ | ----------------------- |
| background.coef                | [code][0]{:.label-cif}  |
| \_background.coef              | [Edifa][0]{:.label-cif} |
| \_pd_background.Chebyshev_coef | [pdCIF][0]{:.label-cif} |

Coefficient used in a Chebyshev polynomial background term.

## :material-shape: type { #background-type }

| Access            | Source                  |
| ----------------- | ----------------------- |
| \_background.type | [Edifa][0]{:.label-cif} |

Active background type tag. Supported values include `line-segment` and
`chebyshev`.

<!-- prettier-ignore-start -->
[0]: #
[3]: ../../glossary.md#experiment-type-labels
<!-- prettier-ignore-end -->
