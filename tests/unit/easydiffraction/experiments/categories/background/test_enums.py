def test_background_enum_default_and_descriptions():
    import easydiffraction.experiments.categories.background.enums as MUT

    assert MUT.BackgroundTypeEnum.default() == MUT.BackgroundTypeEnum.LINE_SEGMENT
    assert MUT.BackgroundTypeEnum.LINE_SEGMENT.description() == 'Linear interpolation between points'
    assert MUT.BackgroundTypeEnum.CHEBYSHEV.description() == 'Chebyshev polynomial background'
