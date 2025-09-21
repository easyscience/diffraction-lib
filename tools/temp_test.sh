clear
PYTHONPATH=$(pwd)/src .pixi/envs/default/bin/python -m pytest -q --tb=no --disable-warnings tests/temp/short.py
