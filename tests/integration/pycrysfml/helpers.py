# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import json
import inspect
import os
import numpy as np
import re
from io import StringIO
import pathlib


def set_crysfml_db():
    os.environ['CRYSFML_DB'] = str(pathlib.Path.cwd() / 'repo' / 'CFML' / 'Src' / 'Databases')


def path_to_progs(file_name: str = ''):
    abspath = pathlib.Path.cwd() / 'dist' / 'CFML' / 'progs' / file_name
    return os.path.relpath(abspath)


def path_to_actual(file_name: str = ''):
    caller = inspect.stack()[1].filename
    abspath = pathlib.Path(caller).parent / 'actual' / file_name
    return os.path.relpath(abspath)


def path_to_desired(file_name: str = ''):
    caller = inspect.stack()[1].filename
    abspath = pathlib.Path(caller).parent / 'desired' / file_name
    return os.path.relpath(abspath)


def path_to_input(file_name: str = ''):
    caller = inspect.stack()[1].filename
    abspath = pathlib.Path(caller).parent / 'input' / file_name
    return os.path.relpath(abspath)


def dat_to_ndarray(file_name: str, skip_begin: int = 0, skip_end: int = 0, usecols=(0)):
    """Parses the file to extract an array of data and converts it to a numpy array."""
    with pathlib.Path(file_name).open('r') as file:
        lines = file.readlines()  # reads into list
    del lines[:skip_begin]  # deletes requested number of first lines
    del lines[len(lines) - skip_end :]  # deletes requested number of last lines
    lines = [l.replace('(', ' ').replace(')', ' ') for l in lines]  # replace brackets with spaces
    joined = '\n'.join(lines)  # joins into single string
    return np.genfromtxt(
        StringIO(joined), usecols=usecols, unpack=True
    )  # converts string to ndarray


def sub_to_ndarray(file_name: str):
    """Parses the FullProf .SUB file to extract an array of data and converts it to a numpy array."""
    with pathlib.Path(file_name).open('r') as file:
        lines = file.readlines()  # reads into list
    # Extracts the first three numbers from the first line
    numbers = re.findall(r'\d+\.\d+|\d+', lines[0])[:3]
    min, inc, max = list(map(float, numbers))
    x_array = np.arange(
        start=min, stop=max + inc - (1e-5), step=inc
    )  # 1e-5 is to avoid extra point at the end
    # Extracts the data from the rest of the file
    skip_begin = 1
    del lines[:skip_begin]  # deletes requested number of first lines
    joined = ''.join(lines)  # joins into single string
    joined = joined.replace('\n', ' ')  # replaces newlines with spaces
    y_array = np.genfromtxt(StringIO(joined))  # converts string to ndarray
    return x_array, y_array


def load_from_json(file_name: str):
    """Loads a JSON file."""
    with pathlib.Path(file_name).open('r') as file:
        return json.load(file)


def chi_squared(calc: np.ndarray, meas: np.ndarray, skip_last: int = 0):
    """Calculates the chi-squared value between two arrays."""
    if skip_last:
        calc = calc[:-skip_last]
        meas = meas[:-skip_last]
    return np.sum((meas - calc) ** 2)
