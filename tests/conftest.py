import json
import sys
from pathlib import Path

import pytest

# sys.path fix
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.register import generate_keypair


@pytest.fixture
def tmp_keys(tmp_path):
    """Generate a temporary agent_keys.json for tests."""
    keys = generate_keypair()
    keys["agent_id"] = "00000000-0000-0000-0000-000000000001"
    keys["display_name"] = "test-agent"
    path = tmp_path / "agent_keys.json"
    path.write_text(json.dumps(keys))
    return str(path), keys


@pytest.fixture
def fast_scrypt():
    """Return a low N value for fast scrypt in tests (N=2**14)."""
    return 2**14
