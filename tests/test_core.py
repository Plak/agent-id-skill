"""
Core tests for agent-id-skill scripts.
No real API calls — all crypto operations tested locally.
"""
import base64
import hashlib
import json
import os

import pytest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat, NoEncryption

from scripts.crypto_utils import atomic_write, atomic_write_new, secure_zero, to_secure_buffer
from scripts.register import generate_keypair, solve_pow
from scripts.secure_keyfile import encrypt_keyfile, decrypt_keyfile


# ---------- Test 1: Keygen ----------

def test_keygen_generates_valid_keypair():
    """generate_keypair returns 32-byte Ed25519 + X25519 keys, base64-decodable."""
    keys = generate_keypair()

    # Must have all four key fields
    for field in ("sign_private_key", "sign_public_key", "enc_private_key", "enc_public_key"):
        assert field in keys, f"Missing field: {field}"

    # All keys must be valid base64, 32 bytes raw
    for field in ("sign_private_key", "sign_public_key", "enc_private_key", "enc_public_key"):
        raw = base64.b64decode(keys[field])
        assert len(raw) == 32, f"{field} should be 32 bytes, got {len(raw)}"

    # Ed25519 private key must be loadable
    priv_bytes = base64.b64decode(keys["sign_private_key"])
    priv_key = Ed25519PrivateKey.from_private_bytes(priv_bytes)
    pub_bytes = priv_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    assert pub_bytes == base64.b64decode(keys["sign_public_key"])


# ---------- Test 2: Challenge signing ----------

def test_sign_challenge_produces_valid_signature():
    """Sign a challenge with Ed25519, verify with public key."""
    keys = generate_keypair()
    priv_bytes = base64.b64decode(keys["sign_private_key"])
    private_key = Ed25519PrivateKey.from_private_bytes(priv_bytes)
    pub_key = private_key.public_key()

    # Simulate the WebAuthn assertion signing from sign_challenge.py / authenticate.py
    rp_id_hash = hashlib.sha256(b"agent-id.io").digest()
    flags = bytes([0x01])
    sign_count = (0).to_bytes(4, "big")
    authenticator_data = rp_id_hash + flags + sign_count

    challenge = "dGVzdC1jaGFsbGVuZ2U"  # base64url of "test-challenge"
    client_data = json.dumps({
        "type": "webauthn.get",
        "challenge": challenge,
        "origin": "https://agent-id.io",
    }, separators=(",", ":")).encode()

    client_data_hash = hashlib.sha256(client_data).digest()
    signed_data = authenticator_data + client_data_hash
    signature = private_key.sign(signed_data)

    # Verify — raises InvalidSignature if wrong
    pub_key.verify(signature, signed_data)


# ---------- Test 3: Encrypt/Decrypt roundtrip ----------

def test_secure_keyfile_encrypt_decrypt_roundtrip(tmp_path, tmp_keys, fast_scrypt):
    """Encrypt agent_keys.json, decrypt with same passphrase, verify identical content."""
    keys_path, keys = tmp_keys
    enc_path = str(tmp_path / "agent_keys.json.enc")
    passphrase = "test-passphrase-7291"

    encrypt_keyfile(keys_path, enc_path, passphrase, scrypt_n=fast_scrypt)

    # Encrypted file must exist and differ from plaintext
    assert os.path.exists(enc_path)
    with open(enc_path, "rb") as f:
        enc_data = f.read()
    assert enc_data[:9] == b"AGENTKEY1"  # magic header

    # Decrypt and compare
    decrypted = decrypt_keyfile(enc_path, passphrase, scrypt_n=fast_scrypt)
    decrypted_keys = json.loads(decrypted)
    assert decrypted_keys["sign_private_key"] == keys["sign_private_key"]
    assert decrypted_keys["sign_public_key"] == keys["sign_public_key"]
    assert decrypted_keys["agent_id"] == keys["agent_id"]


# ---------- Test 4: Wrong passphrase fails ----------

def test_secure_keyfile_wrong_passphrase_fails(tmp_path, tmp_keys, fast_scrypt):
    """Decrypting with wrong passphrase must raise SystemExit (via sys.exit)."""
    keys_path, _ = tmp_keys
    enc_path = str(tmp_path / "agent_keys.json.enc")

    encrypt_keyfile(keys_path, enc_path, "correct-passphrase", scrypt_n=fast_scrypt)

    with pytest.raises(SystemExit):
        decrypt_keyfile(enc_path, "wrong-passphrase", scrypt_n=fast_scrypt)


def test_secure_zero_and_to_secure_buffer():
    """Secure buffers should be mutable and zeroable for best-effort cleanup."""
    from_bytes = to_secure_buffer(b"secret")
    from_text = to_secure_buffer("secret")

    assert isinstance(from_bytes, bytearray)
    assert isinstance(from_text, bytearray)
    assert bytes(from_bytes) == b"secret"
    assert bytes(from_text) == b"secret"

    secure_zero(from_bytes)
    secure_zero(from_text)

    assert bytes(from_bytes) == b"\x00" * 6
    assert bytes(from_text) == b"\x00" * 6


def test_atomic_write_replaces_existing_file(tmp_path):
    """atomic_write should replace the destination content and keep restrictive mode."""
    target = tmp_path / "secret.txt"
    target.write_text("old")

    atomic_write(str(target), "new-secret", mode=0o600)

    assert target.read_text() == "new-secret"
    assert os.stat(target).st_mode & 0o777 == 0o600


def test_atomic_write_new_fails_if_target_exists(tmp_path):
    """atomic_write_new should fail if the destination already exists."""
    target = tmp_path / "secret.txt"
    target.write_text("old")

    with pytest.raises(FileExistsError):
        atomic_write_new(str(target), "new-secret", mode=0o600)

    assert target.read_text() == "old"


# ---------- Test 5: Deterministic key derivation ----------

def test_derive_keys_deterministic(tmp_path):
    """Same master seed produces identical SSH + PGP keys on repeated derivation."""
    from scripts.derive_keys import derive_child_seed

    # Fixed seed for reproducibility
    master_seed = b'\x01' * 32

    ssh_seed_1 = derive_child_seed(master_seed, "agent-id/ssh-ed25519")
    pgp_seed_1 = derive_child_seed(master_seed, "agent-id/pgp-ed25519")

    ssh_seed_2 = derive_child_seed(master_seed, "agent-id/ssh-ed25519")
    pgp_seed_2 = derive_child_seed(master_seed, "agent-id/pgp-ed25519")

    assert ssh_seed_1 == ssh_seed_2, "SSH seed must be deterministic"
    assert pgp_seed_1 == pgp_seed_2, "PGP seed must be deterministic"
    assert ssh_seed_1 != pgp_seed_1, "SSH and PGP seeds must differ"

    # Seeds must be 32 bytes
    assert len(ssh_seed_1) == 32
    assert len(pgp_seed_1) == 32


# ---------- Test 6: PoW solver ----------

def test_pow_solver():
    """solve_pow returns a nonce that produces correct leading zero bits."""
    challenge = "test-challenge-abc"
    subject_hex = hashlib.sha256(b"test-pubkey").hexdigest()
    difficulty = 1  # very easy for test speed

    nonce = solve_pow(challenge, subject_hex, difficulty)

    # Verify the solution
    data = f"{challenge}:{subject_hex}:{nonce}".encode()
    digest = hashlib.sha256(data).digest()
    # Count leading zero bits
    zero_bits = 0
    for byte in digest:
        if byte == 0:
            zero_bits += 8
        else:
            for i in range(7, -1, -1):
                if (byte & (1 << i)) == 0:
                    zero_bits += 1
                else:
                    break
            break

    assert zero_bits >= difficulty, f"Expected >= {difficulty} leading zero bits, got {zero_bits}"


# ---------- Test: validate_challenge ----------

def test_validate_challenge_accepts_valid_base64url():
    from scripts.crypto_utils import validate_challenge
    # 32 bytes encoded as base64url (no padding)
    validate_challenge("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")


def test_validate_challenge_rejects_non_base64():
    import pytest
    from scripts.crypto_utils import validate_challenge
    with pytest.raises(SystemExit):
        validate_challenge("!!!not base64!!!")


def test_validate_challenge_rejects_too_short():
    import pytest
    import base64
    from scripts.crypto_utils import validate_challenge
    short = base64.urlsafe_b64encode(b"\x00" * 8).decode().rstrip("=")
    with pytest.raises(SystemExit):
        validate_challenge(short)


def test_validate_challenge_rejects_too_long():
    import pytest
    import base64
    from scripts.crypto_utils import validate_challenge
    long_data = base64.urlsafe_b64encode(b"\x00" * 200).decode().rstrip("=")
    with pytest.raises(SystemExit):
        validate_challenge(long_data)


# ---------- Test: resolve_api_base ----------

def test_resolve_api_base_default(monkeypatch):
    monkeypatch.delenv("AGENT_ID_API", raising=False)
    from scripts.crypto_utils import resolve_api_base
    assert resolve_api_base() == "https://agent-id.io/v1"


def test_resolve_api_base_valid_https(monkeypatch):
    monkeypatch.setenv("AGENT_ID_API", "https://test.example.com/v1")
    from scripts import crypto_utils
    import importlib
    importlib.reload(crypto_utils)  # reload to pick up env
    # Direct call is cleaner
    from scripts.crypto_utils import resolve_api_base
    assert resolve_api_base() == "https://test.example.com/v1"


def test_resolve_api_base_rejects_http(monkeypatch):
    import pytest
    monkeypatch.setenv("AGENT_ID_API", "http://evil.example.com/v1")
    from scripts.crypto_utils import resolve_api_base
    with pytest.raises(SystemExit):
        resolve_api_base()


def test_resolve_api_base_strips_trailing_slash(monkeypatch):
    monkeypatch.delenv("AGENT_ID_API", raising=False)
    from scripts.crypto_utils import resolve_api_base
    result = resolve_api_base("https://agent-id.io/v1/")
    assert result == "https://agent-id.io/v1"
