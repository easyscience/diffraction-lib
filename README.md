# easydiffraction

Development playground for the new EasyDiffraction API.

## User Installation & Setup

- Create a new virtual environment:
  ```bash
  python3 -m venv .venv
  ```
- Activate the environment:
  ```bash
  . .venv/bin/activate
  ```
- Install the package from GitHub:
  ```bash
  pip install git+https://github.com/easyscience/diffraction-lib@develop#egg=easydiffraction
  ```

## Developer Installation & Setup

- Create a new virtual environment:
  ```bash
  python3 -m venv .venv
  ```
- Activate the environment:
  ```bash
  . .venv/bin/activate
  ```
- Install dependencies:
  ```bash
  pip install --upgrade pip
  pip python -m pip install . '[visualization]'
  ```
- Install pycrysfml (pyenv python 3.12, macOS 14, Apple Silicon):

  ```bash
  # Install from local wheel
  pip install deps/pycrysfml-0.1.6-py312-none-macosx_14_0_arm64.whl
  # Try to import the module
  python -c "from pycrysfml import cfml_py_utilities"
  # If previous step failed, check the linked libraries
  otool -L .venv/lib/python3.12/site-packages/pycrysfml/crysfml08lib.so
  # If the library is linked to the wrong Python version, you can fix it with:
  install_name_tool -change `python3-config --prefix`/Python `python3-config --prefix`/lib/libpython3.12.dylib .venv/lib/python3.12/site-packages/pycrysfml/crysfml08lib.so
  # Check again the linked Python library
  otool -L .venv/lib/python3.12/site-packages/pycrysfml/crysfml08lib.so
  # Try to import the module again
  python -c "from pycrysfml import cfml_py_utilities"
  ```

- Install CBLAS library, required for using the Pair Distribution Function
  feature. This step is required only on Windows.

  ```bash
  # Install from the conda-forge channel
  conda install libcblas -c conda-forge

  # Try to import the module
  python -c "import diffpy.pdffit2"
  ```

## Testing

- Unit tests:
  ```bash
  PYTHONPATH=$(pwd)/src python -m pytest tests/unit_tests/ --color=yes -n auto
  ```
- Functional tests:
  ```bash
  PYTHONPATH=$(pwd)/src python -m pytest tests/functional_tests/ --color=yes -n auto
  ```

## Running examples

- Simplified API:
  ```bash
  PYTHONPATH=$(pwd)/src python examples/joint-fit_basic-usage.py
  ```
- Advanced API:
  ```bash
  PYTHONPATH=$(pwd)/src python examples/joint-fit_advanced-usage.py
  ```
