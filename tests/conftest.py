import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nexaworks.data.loader import load_dataset

@pytest.fixture
def raw():
    path = ROOT / "data" / "candidate_dataset.json"
    if not path.exists():
        pytest.skip("candidate_dataset.json not present")
    return load_dataset(path)
