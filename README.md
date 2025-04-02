# easydiffraction

Development playground for the new EasyDiffraction API.

## Installation & Setup

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
  pip install -r requirements.txt
  ```
- Install pycrysfml (pyenv python 3.12, macOS 14, Apple Silicon):
  ```bash
  pip install deps/pycrysfml-0.1.6-py312-none-macosx_14_0_arm64.whl
  otool -L .venv/lib/python3.12/site-packages/pycrysfml/crysfml08lib.so
  install_name_tool -change `python3-config --prefix`/Python `python3-config --prefix`/lib/libpython3.12.dylib .venv/lib/python3.12/site-packages/pycrysfml/crysfml08lib.so
  otool -L .venv/lib/python3.12/site-packages/pycrysfml/crysfml08lib.so
  ```

## Testing

  ```bash
  PYTHONPATH=$(pwd)/src python -m pytest tests/ --color=yes
  ```

## Running examples

- Simplified API:
  ```bash
  PYTHONPATH=$(pwd)/src python examples/joint-fit_simple-api.py
  ```
- Advanced API:
  ```bash
  PYTHONPATH=$(pwd)/src python examples/joint-fit_advanced-api.py
  ```
