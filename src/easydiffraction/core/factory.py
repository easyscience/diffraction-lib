# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Base factory with registration, lookup, and context-dependent defaults.

Concrete factories inherit from ``FactoryBase`` and only need to define
``_default_rules``.
"""

from __future__ import annotations

from typing import Any
from typing import ClassVar

from easydiffraction.utils.logging import console
from easydiffraction.utils.utils import render_table


class FactoryBase:
    """
    Shared base for all factories.

    Subclasses must set:

    * ``_default_rules`` -- mapping of ``frozenset`` conditions to tag
    strings.  Use ``frozenset(): 'tag'`` for a universal default.

    The ``__init_subclass__`` hook ensures every subclass gets its own
    independent ``_registry`` list.
    """

    _registry: ClassVar[list[type]] = []
    _default_rules: ClassVar[dict[frozenset[tuple[str, Any]], str]] = {}

    def __init_subclass__(cls, **kwargs: object) -> None:
        """Give each subclass its own independent registry and rules."""
        super().__init_subclass__(**kwargs)
        cls._registry = []
        if '_default_rules' not in cls.__dict__:
            cls._default_rules = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    @classmethod
    def register(cls, klass: type) -> type:
        """
        Class decorator to register a concrete class.

        Usage::

        @SomeFactory.register class MyClass(SomeBase):     type_info =
        TypeInfo(...)

        Returns the class unmodified.
        """
        cls._registry.append(klass)
        return klass

    # ------------------------------------------------------------------
    # Supported-map helpers
    # ------------------------------------------------------------------

    @classmethod
    def _supported_map(cls) -> dict[str, type]:
        """Build ``{tag: class}`` from all registered classes."""
        return {klass.type_info.tag: klass for klass in cls._registry}

    @classmethod
    def supported_tags(cls) -> list[str]:
        """Return list of all supported tags."""
        return list(cls._supported_map().keys())

    # ------------------------------------------------------------------
    # Default resolution
    # ------------------------------------------------------------------

    @classmethod
    def default_tag(cls, **conditions: object) -> str:
        """
        Resolve the default tag for a given experimental context.

        Uses *largest-subset matching*: the rule whose key is the
        biggest subset of the given conditions wins. A rule with an
        empty key (``frozenset()``) acts as a universal fallback.

        Parameters
        ----------
        **conditions : object
            Experimental-axis values, e.g.
            ``scattering_type=ScatteringTypeEnum.BRAGG``.

        Returns
        -------
        str
            The resolved default tag string.

        Raises
        ------
        ValueError
            If no rule matches the given conditions.
        """
        condition_set = frozenset(conditions.items())
        best_match_tag: str | None = None
        best_match_size = -1

        for rule_key, rule_tag in cls._default_rules.items():
            if rule_key <= condition_set and len(rule_key) > best_match_size:
                best_match_tag = rule_tag
                best_match_size = len(rule_key)

        if best_match_tag is None:
            msg = (
                f'No default rule matches conditions {dict(conditions)}. '
                f'Available rules: {cls._default_rules}'
            )
            raise ValueError(msg)
        return best_match_tag

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    @classmethod
    def create(cls, tag: str, **kwargs: object) -> object:
        """
        Instantiate a registered class by *tag*.

        Parameters
        ----------
        tag : str
            ``type_info.tag`` value.
        **kwargs : object
            Forwarded to the class constructor.

        Returns
        -------
        object
            A new instance of the registered class.

        Raises
        ------
        ValueError
            If *tag* is not in the registry.
        """
        supported = cls._supported_map()
        if tag not in supported:
            msg = f"Unsupported type: '{tag}'. Supported: {list(supported.keys())}"
            raise ValueError(msg)
        return supported[tag](**kwargs)

    @classmethod
    def create_default_for(cls, **conditions: object) -> object:
        """
        Instantiate the default class for a given context.

        Combines ``default_tag(**conditions)`` with ``create(tag)``.

        Parameters
        ----------
        **conditions : object
            Experimental-axis values.

        Returns
        -------
        object
            A new instance of the default class.
        """
        tag = cls.default_tag(**conditions)
        return cls.create(tag)

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    @classmethod
    def supported_for(
        cls,
        *,
        calculator: object = None,
        sample_form: object = None,
        scattering_type: object = None,
        beam_mode: object = None,
        radiation_probe: object = None,
    ) -> list[type]:
        """
        Return classes matching conditions and/or calculator.

        Parameters
        ----------
        calculator : object, default=None
            Optional ``CalculatorEnum`` value.
        sample_form : object, default=None
            Optional ``SampleFormEnum`` value.
        scattering_type : object, default=None
            Optional ``ScatteringTypeEnum`` value.
        beam_mode : object, default=None
            Optional ``BeamModeEnum`` value.
        radiation_probe : object, default=None
            Optional ``RadiationProbeEnum`` value.

        Returns
        -------
        list[type]
            Classes matching the given conditions.
        """
        result = []
        for klass in cls._supported_map().values():
            compat = getattr(klass, 'compatibility', None)
            if compat and not compat.supports(
                sample_form=sample_form,
                scattering_type=scattering_type,
                beam_mode=beam_mode,
                radiation_probe=radiation_probe,
            ):
                continue
            calc_support = getattr(klass, 'calculator_support', None)
            if calculator and calc_support and not calc_support.supports(calculator):
                continue
            result.append(klass)
        return result

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    @classmethod
    def show_supported(
        cls,
        *,
        calculator: object = None,
        sample_form: object = None,
        scattering_type: object = None,
        beam_mode: object = None,
        radiation_probe: object = None,
    ) -> None:
        """
        Pretty-print a table of supported types.

        Parameters
        ----------
        calculator : object, default=None
            Optional ``CalculatorEnum`` filter.
        sample_form : object, default=None
            Optional ``SampleFormEnum`` filter.
        scattering_type : object, default=None
            Optional ``ScatteringTypeEnum`` filter.
        beam_mode : object, default=None
            Optional ``BeamModeEnum`` filter.
        radiation_probe : object, default=None
            Optional ``RadiationProbeEnum`` filter.
        """
        matching = cls.supported_for(
            calculator=calculator,
            sample_form=sample_form,
            scattering_type=scattering_type,
            beam_mode=beam_mode,
            radiation_probe=radiation_probe,
        )
        columns_headers = ['Type', 'Description']
        columns_alignment = ['left', 'left']
        columns_data = [[klass.type_info.tag, klass.type_info.description] for klass in matching]
        console.paragraph('Supported types')
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )
