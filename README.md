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

## Running examples

- Simplified API: 
  ```bash
  PYTHONPATH=$(pwd)/src python examples/joint-refinement_simple-api.py
  ```
- Advanced API: 
  ```bash
  PYTHONPATH=$(pwd)/src python examples/joint-refinement_advanced-api.py
  ```
