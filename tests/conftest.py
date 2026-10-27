import json
from pathlib import Path

import pytest

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


@pytest.fixture
def load_case():
    def load(name):
        return json.loads((EXAMPLES / f"{name}.json").read_text(encoding="utf-8"))
    return load
