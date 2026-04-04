"""Integration tests with mocked HTTP - no real API calls."""
import base64
import hashlib
import json
import stat
import sys
from pathlib import Path

import pytest
import requests
import responses
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.authenticate import ORIGIN, RP_ID, b64url_encode
from scripts.register import API_BASE, generate_keypair, solve_pow
from scripts import authenticate, keygen, register, rotate_keys


@responses.activate
def test_register_flow_success():
    """Exercise the registration primitives against mocked HTTP endpoints."""
    responses.post(
        f"{API_BASE}/agents/register/challenge",
        json={
            "challenge": "abc",
            "difficulty": 1,
            "expires_at": "2099-01-01T00:00:00Z",
        },
        status=200,
    )
    responses.post(
        f"{API_BASE}/agents/register",
        json={"agent_id": "test-uuid", "display_name": "test"},
        status=200,
    )

    keys = generate_keypair()
    assert "sign_public_key" in keys
    assert "enc_public_key" in keys

    sign_pub_bytes = base64.b64decode(keys["sign_public_key"])
    subject_hex = hashlib.sha256(sign_pub_bytes).hexdigest()
    nonce = solve_pow("abc", subject_hex, 1)
    assert nonce.isdigit()

    challenge_resp = requests.post(
        f"{API_BASE}/agents/register/challenge",
        json={"public_sign_key": keys["sign_public_key"]},
        timeout=10,
    )
    assert challenge_resp.status_code == 200
    assert challenge_resp.json()["challenge"] == "abc"

    register_resp = requests.post(
        f"{API_BASE}/agents/register",
        json={
            "display_name": "test",
            "public_sign_key": keys["sign_public_key"],
            "public_enc_key": keys["enc_public_key"],
            "pow_challenge": "abc",
            "pow_nonce": nonce,
        },
        timeout=10,
    )
    assert register_resp.status_code == 200
    assert register_resp.json()["agent_id"] == "test-uuid"

    assert len(responses.calls) == 2
    assert responses.calls[0].request.url == f"{API_BASE}/agents/register/challenge"
    assert json.loads(responses.calls[0].request.body) == {
        "public_sign_key": keys["sign_public_key"]
    }
    assert responses.calls[1].request.url == f"{API_BASE}/agents/register"
    assert json.loads(responses.calls[1].request.body)["pow_nonce"] == nonce


def test_authenticate_challenge_signing():
    """Build and verify an authentication signature without HTTP."""
    keys = generate_keypair()
    private_key = Ed25519PrivateKey.from_private_bytes(
        base64.b64decode(keys["sign_private_key"])
    )
    public_key = private_key.public_key()

    rp_id_hash = hashlib.sha256(RP_ID.encode()).digest()
    flags = bytes([0x01])
    sign_count = (0).to_bytes(4, "big")
    authenticator_data = rp_id_hash + flags + sign_count

    client_data = json.dumps(
        {
            "type": "webauthn.get",
            "challenge": "test-challenge",
            "origin": ORIGIN,
        },
        separators=(",", ":"),
    ).encode()
    client_data_hash = hashlib.sha256(client_data).digest()
    signed_data = authenticator_data + client_data_hash
    signature = private_key.sign(signed_data)

    public_key.verify(signature, signed_data)
    credential_id = b64url_encode(
        public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
    )
    assert credential_id
    assert b64url_encode(authenticator_data)
    assert b64url_encode(client_data)
    assert b64url_encode(signature)


@responses.activate
def test_register_rate_limit_handling():
    """Return a mocked 429 challenge response and verify the caller sees it."""
    responses.post(
        f"{API_BASE}/agents/register/challenge",
        status=429,
        headers={"Retry-After": "60"},
    )

    response = requests.post(
        f"{API_BASE}/agents/register/challenge",
        json={"public_sign_key": "dummy"},
        timeout=10,
    )

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"


@responses.activate
def test_authenticate_save_token_uses_mode_0600(tmp_path, tmp_keys, monkeypatch):
    """Saved token files must be created without group/other read bits."""
    keys_path, _ = tmp_keys
    token_path = tmp_path / "token.txt"

    responses.post(
        f"{authenticate.API_BASE}/auth/challenge",
        json={"challenge": "test-challenge"},
        status=200,
    )
    responses.post(
        f"{authenticate.API_BASE}/auth/verify",
        json={"token": "secret-jwt", "expires_at": "2099-01-01T00:00:00Z"},
        status=200,
    )

    monkeypatch.setattr(
        sys,
        "argv",
        ["authenticate.py", keys_path, "--save-token", str(token_path)],
    )

    authenticate.main()

    mode = stat.S_IMODE(token_path.stat().st_mode)
    assert mode == 0o600
    assert mode & (stat.S_IRGRP | stat.S_IROTH) == 0
    assert token_path.read_text() == "secret-jwt"


def test_rotate_keys_carries_agent_metadata(tmp_path, tmp_keys, monkeypatch):
    """Rotation output should preserve agent_id and display_name metadata."""
    keys_path, keys = tmp_keys
    new_keys_path = tmp_path / "new_agent_keys.json"
    payload_path = tmp_path / "rotation_payload.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "rotate_keys.py",
            keys_path,
            "--new-keys",
            str(new_keys_path),
            "--payload",
            str(payload_path),
        ],
    )

    rotate_keys.main()

    new_keys = json.loads(new_keys_path.read_text())
    assert new_keys["agent_id"] == keys["agent_id"]
    assert new_keys["display_name"] == keys["display_name"]


def test_rotate_keys_keeps_display_name_optional(tmp_path, tmp_keys, monkeypatch):
    """Rotation should copy agent_id and omit display_name when it was absent."""
    keys_path, keys = tmp_keys
    del keys["display_name"]
    Path(keys_path).write_text(json.dumps(keys))

    new_keys_path = tmp_path / "new_agent_keys.json"
    payload_path = tmp_path / "rotation_payload.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "rotate_keys.py",
            keys_path,
            "--new-keys",
            str(new_keys_path),
            "--payload",
            str(payload_path),
        ],
    )

    rotate_keys.main()

    new_keys = json.loads(new_keys_path.read_text())
    assert new_keys["agent_id"] == keys["agent_id"]
    assert "display_name" not in new_keys


def test_keygen_encrypt_creates_encrypted_output_only(tmp_path, monkeypatch):
    """--encrypt should write only the encrypted keyfile and no plaintext sibling."""
    output_path = tmp_path / "agent_keys.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "keygen.py",
            "--output",
            str(output_path),
            "--encrypt",
            "--passphrase",
            "test-passphrase",
        ],
    )

    keygen.main()

    assert not output_path.exists()
    assert output_path.with_suffix(output_path.suffix + ".enc").exists()


def test_keygen_plaintext_mode_warns(tmp_path, monkeypatch, capsys):
    """Plaintext key generation stays compatible but warns on stderr."""
    output_path = tmp_path / "agent_keys.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "keygen.py",
            "--output",
            str(output_path),
        ],
    )

    keygen.main()

    captured = capsys.readouterr()
    assert output_path.exists()
    assert "plaintext private keys were written" in captured.err


@responses.activate
def test_register_encrypt_creates_encrypted_output_only(tmp_path, monkeypatch):
    """--encrypt should persist only the encrypted registration keyfile."""
    output_path = tmp_path / "registered_keys.json"

    responses.post(
        f"{API_BASE}/agents/register/challenge",
        json={
            "challenge": "abc",
            "difficulty": 1,
            "expires_at": "2099-01-01T00:00:00Z",
        },
        status=200,
    )
    responses.post(
        f"{API_BASE}/agents/register",
        json={"agent_id": "test-uuid", "display_name": "test"},
        status=200,
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "register.py",
            "--name",
            "test",
            "--keys",
            str(output_path),
            "--encrypt",
            "--passphrase",
            "test-passphrase",
        ],
    )

    register.main()

    assert not output_path.exists()
    assert output_path.with_suffix(output_path.suffix + ".enc").exists()


@responses.activate
def test_register_plaintext_mode_warns(tmp_path, monkeypatch, capsys):
    """Plaintext registration stays compatible but warns on stderr."""
    output_path = tmp_path / "registered_keys.json"

    responses.post(
        f"{API_BASE}/agents/register/challenge",
        json={
            "challenge": "abc",
            "difficulty": 1,
            "expires_at": "2099-01-01T00:00:00Z",
        },
        status=200,
    )
    responses.post(
        f"{API_BASE}/agents/register",
        json={"agent_id": "test-uuid", "display_name": "test"},
        status=200,
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "register.py",
            "--name",
            "test",
            "--keys",
            str(output_path),
        ],
    )

    register.main()

    captured = capsys.readouterr()
    assert output_path.exists()
    assert "plaintext private keys were written" in captured.err


@responses.activate
def test_rotate_keys_apply_replaces_original_and_writes_backup(tmp_path, tmp_keys, monkeypatch):
    """Successful --apply should preserve a backup and atomically replace the original file."""
    keys_path, keys = tmp_keys
    original_text = Path(keys_path).read_text()

    responses.post(
        f"{rotate_keys.API_BASE}/agents/{keys['agent_id']}/keys/rotate",
        json={
            "agent_id": keys["agent_id"],
            "public_sign_key": "new-sign",
            "public_enc_key": "new-enc",
            "rotated_at": "2099-01-01T00:00:00Z",
        },
        status=200,
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "rotate_keys.py",
            keys_path,
            "--apply",
            "--token",
            "test-token",
        ],
    )

    rotate_keys.main()

    backup_path = Path(f"{keys_path}.bak")
    assert backup_path.exists()
    assert backup_path.read_text() == original_text

    rotated_keys = json.loads(Path(keys_path).read_text())
    assert rotated_keys["agent_id"] == keys["agent_id"]
    assert rotated_keys["display_name"] == keys["display_name"]
    assert rotated_keys["sign_public_key"] != keys["sign_public_key"]


@responses.activate
def test_rotate_keys_apply_failure_leaves_original_untouched(tmp_path, tmp_keys, monkeypatch):
    """Failed --apply must leave the original file unchanged and skip backup creation."""
    keys_path, keys = tmp_keys
    original_text = Path(keys_path).read_text()

    responses.post(
        f"{rotate_keys.API_BASE}/agents/{keys['agent_id']}/keys/rotate",
        json={"error": "invalid_signature"},
        status=400,
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "rotate_keys.py",
            keys_path,
            "--apply",
            "--token",
            "test-token",
        ],
    )

    with pytest.raises(SystemExit):
        rotate_keys.main()

    assert Path(keys_path).read_text() == original_text
    assert not Path(f"{keys_path}.bak").exists()


@responses.activate
def test_authenticate_zeroes_private_key_buffer(tmp_path, tmp_keys, monkeypatch):
    """Authentication should zero the decoded private key buffer after use."""
    keys_path, _ = tmp_keys
    token_path = tmp_path / "token.txt"
    zeroed_buffers = []
    real_secure_zero = authenticate.secure_zero

    def spy_secure_zero(buf):
        real_secure_zero(buf)
        zeroed_buffers.append(bytes(buf))

    responses.post(
        f"{authenticate.API_BASE}/auth/challenge",
        json={"challenge": "test-challenge"},
        status=200,
    )
    responses.post(
        f"{authenticate.API_BASE}/auth/verify",
        json={"token": "secret-jwt", "expires_at": "2099-01-01T00:00:00Z"},
        status=200,
    )

    monkeypatch.setattr(authenticate, "secure_zero", spy_secure_zero)
    monkeypatch.setattr(
        sys,
        "argv",
        ["authenticate.py", keys_path, "--save-token", str(token_path)],
    )

    authenticate.main()

    assert any(buf == b"\x00" * 32 for buf in zeroed_buffers)


def test_rotate_keys_zeroes_old_private_key_buffer(tmp_keys, monkeypatch):
    """Rotation material generation should zero the decoded old private key buffer."""
    _, keys = tmp_keys
    zeroed_buffers = []
    real_secure_zero = rotate_keys.secure_zero

    def spy_secure_zero(buf):
        real_secure_zero(buf)
        zeroed_buffers.append(bytes(buf))

    monkeypatch.setattr(rotate_keys, "secure_zero", spy_secure_zero)

    rotate_keys.build_rotation_material(keys)

    assert any(buf == b"\x00" * 32 for buf in zeroed_buffers)
