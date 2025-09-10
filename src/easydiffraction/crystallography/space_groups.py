import gzip
import pickle
from pathlib import Path


def _load():
    path = Path(__file__).with_name('space_groups.pkl.gz')
    with gzip.open(path, 'rb') as f:
        return pickle.load(f)  # noqa: S301 safe: internal trusted data


SPACE_GROUPS = _load()
