import pytest
from nexaworks.persistence import reproducibility_check

def test_reproducible(raw):
    out=reproducibility_check(raw,seed=42); assert out["run_1_status"]==out["run_2_status"]
