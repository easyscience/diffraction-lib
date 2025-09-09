import pickle
import gzip
from pathlib import Path

def _load():
    path = Path(__file__).with_name("space_groups.pkl.gz")
    with gzip.open(path, "rb") as f:
        return pickle.load(f)

SPACE_GROUP_LOOKUP_DICT = _load()