import base64
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_derive(keys_path: Path, out_dir: Path, optimize: bool = False) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable]
    if optimize:
        cmd.append("-O")
    cmd.extend(["scripts/derive_keys.py", str(keys_path), "--out-dir", str(out_dir)])
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)


def _write_keys(keys_path: Path, seed_bytes: bytes) -> None:
    keys_path.write_text(
        json.dumps(
            {
                "agent_id": "test-agent",
                "sign_private_key": base64.b64encode(seed_bytes).decode(),
            }
        )
    )


def _assert_invalid_seed_rejected(result: subprocess.CompletedProcess[str], out_dir: Path) -> None:
    assert result.returncode == 1
    assert "sign_private_key must decode to exactly 32 bytes" in result.stderr
    assert not (out_dir / "id_agent_ed25519").exists()
    assert not (out_dir / "agent_pgp_private.asc").exists()


def test_derive_keys_rejects_invalid_seed_length(tmp_path):
    keys_path = tmp_path / "agent_keys.json"
    out_dir = tmp_path / "out"
    _write_keys(keys_path, b"\x01" * 31)

    result = _run_derive(keys_path, out_dir, optimize=False)

    _assert_invalid_seed_rejected(result, out_dir)


def test_derive_keys_rejects_invalid_seed_length_under_optimized_python(tmp_path):
    keys_path = tmp_path / "agent_keys.json"
    out_dir = tmp_path / "out"
    _write_keys(keys_path, b"\x01" * 31)

    result = _run_derive(keys_path, out_dir, optimize=True)

    _assert_invalid_seed_rejected(result, out_dir)
