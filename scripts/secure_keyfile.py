#!/usr/bin/env python3
"""
Encrypt/decrypt agent_keys.json using AES-256-GCM with a passphrase.

The agent stores this encrypted file. To use any key-related script,
the agent decrypts the keyfile in memory — the plaintext never touches disk.

Usage:
    # Encrypt (protect the keyfile)
    python3 secure_keyfile.py encrypt agent_keys.json
    → creates agent_keys.json.enc (delete the plaintext after this)

    # Decrypt to stdout (pipe into other scripts)
    python3 secure_keyfile.py decrypt agent_keys.json.enc | python3 authenticate.py /dev/stdin

    # Decrypt to temp file (for use with scripts that need a file path)
    python3 secure_keyfile.py decrypt agent_keys.json.enc --out /tmp/keys_decrypted.json

The passphrase should be stored in the agent's secure vault (e.g., OpenBao, env var, or
OpenClaw secret store) — NOT hardcoded in any script or config file.

Requires: pip install cryptography
"""
import argparse
import base64
import getpass
import json
import os
import sys

try:
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.exceptions import InvalidTag
except ImportError:
    print("Error: 'cryptography' required. pip install cryptography", file=sys.stderr)
    sys.exit(1)

MAGIC = b"AGENTKEY1"  # file format identifier
SCRYPT_N = 2**17       # CPU/memory cost (high = more secure, slower)
SCRYPT_R = 8
SCRYPT_P = 1


def derive_key(passphrase: str, salt: bytes) -> bytes:
    kdf = Scrypt(salt=salt, length=32, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    return kdf.derive(passphrase.encode())


def encrypt_keyfile(plaintext_path: str, output_path: str, passphrase: str) -> None:
    with open(plaintext_path, "rb") as f:
        plaintext = f.read()

    # Validate it's a valid JSON keys file
    try:
        keys = json.loads(plaintext)
        if "sign_private_key" not in keys:
            print("Warning: file doesn't look like an agent_keys.json", file=sys.stderr)
    except json.JSONDecodeError:
        print("Error: not valid JSON", file=sys.stderr)
        sys.exit(1)

    salt = os.urandom(32)
    nonce = os.urandom(12)
    key = derive_key(passphrase, salt)

    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)

    # Format: MAGIC + salt(32) + nonce(12) + ciphertext
    with open(output_path, "wb") as f:
        f.write(MAGIC)
        f.write(salt)
        f.write(nonce)
        f.write(ciphertext)
    os.chmod(output_path, 0o600)


def decrypt_keyfile(encrypted_path: str, passphrase: str) -> bytes:
    with open(encrypted_path, "rb") as f:
        data = f.read()

    if not data.startswith(MAGIC):
        print("Error: not a valid encrypted agent keyfile", file=sys.stderr)
        sys.exit(1)

    offset = len(MAGIC)
    salt = data[offset:offset + 32]
    nonce = data[offset + 32:offset + 44]
    ciphertext = data[offset + 44:]

    key = derive_key(passphrase, salt)
    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    except InvalidTag:
        print("Error: wrong passphrase or corrupted file", file=sys.stderr)
        sys.exit(1)
    return plaintext


def main():
    parser = argparse.ArgumentParser(description="Encrypt/decrypt agent_keys.json")
    sub = parser.add_subparsers(dest="command")

    enc = sub.add_parser("encrypt", help="Encrypt agent_keys.json")
    enc.add_argument("keyfile", help="Path to agent_keys.json")
    enc.add_argument("--out", help="Output path (default: <keyfile>.enc)")
    enc.add_argument("--passphrase", help="Passphrase (or set AGENT_KEY_PASSPHRASE env var)")

    dec = sub.add_parser("decrypt", help="Decrypt agent_keys.json.enc")
    dec.add_argument("keyfile", help="Path to encrypted keyfile")
    dec.add_argument("--out", help="Output path (default: stdout)")
    dec.add_argument("--passphrase", help="Passphrase (or set AGENT_KEY_PASSPHRASE env var)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Get passphrase
    passphrase = (
        args.passphrase
        or os.environ.get("AGENT_KEY_PASSPHRASE")
        or getpass.getpass("Passphrase: ")
    )

    if args.command == "encrypt":
        out_path = args.out or (args.keyfile + ".enc")
        print(f"Encrypting {args.keyfile} → {out_path}")
        encrypt_keyfile(args.keyfile, out_path, passphrase)
        print(f"✅ Encrypted → {out_path}")
        print(f"   Delete the plaintext: rm {args.keyfile}")

    elif args.command == "decrypt":
        plaintext = decrypt_keyfile(args.keyfile, passphrase)
        if args.out:
            with open(args.out, "wb") as f:
                f.write(plaintext)
            os.chmod(args.out, 0o600)
            print(f"✅ Decrypted → {args.out}", file=sys.stderr)
        else:
            sys.stdout.buffer.write(plaintext)


if __name__ == "__main__":
    main()
