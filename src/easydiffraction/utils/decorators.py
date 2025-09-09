# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction Python Library contributors <https://github.com/easyscience/diffraction-lib>
# SPDX-License-Identifier: BSD-3-Clause

import inspect
import typing

import numpy as np


def enforce_type(func):
    sig = inspect.signature(func)

    def wrapper(self, *args, **kwargs):
        bound_args = sig.bind(self, *args, **kwargs)
        bound_args.apply_defaults()

        for name, value in list(bound_args.arguments.items())[1:]:  # skip 'self'
            expected_type = sig.parameters[name].annotation
            if expected_type is inspect._empty:
                continue  # no annotation, skip

            origin = typing.get_origin(expected_type)
            if origin is not None:
                args_types = typing.get_args(expected_type)
                valid_types = tuple(t for t in args_types if isinstance(t, type))
                if not any(isinstance(value, t) for t in valid_types):
                    raise TypeError(f"Parameter '{name}': expected {expected_type}, got {type(value).__name__}.")
            else:
                if isinstance(expected_type, type):
                    if not isinstance(value, expected_type):
                        raise TypeError(f"Parameter '{name}': expected {expected_type.__name__}, got {type(value).__name__}.")
                elif isinstance(expected_type, str) and expected_type == 'np.ndarray':
                    if not isinstance(value, np.ndarray):
                        raise TypeError(f"Parameter '{name}': expected np.ndarray, got {type(value).__name__}.")
                else:
                    if hasattr(expected_type, '__name__'):
                        if type(value).__name__ != expected_type.__name__:
                            raise TypeError(f"Parameter '{name}': expected {expected_type}, got {type(value).__name__}.")
                    else:
                        if type(value).__name__ != str(expected_type):
                            raise TypeError(f"Parameter '{name}': expected {expected_type}, got {type(value).__name__}.")

        return func(self, *args, **kwargs)

    return wrapper
