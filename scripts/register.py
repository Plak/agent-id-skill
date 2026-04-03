#!/usr/bin/env python3
"""
Register a new agent on agent-id.io.

Full registration flow:
1. Generate Ed25519 + X25519 keypair
2. Request PoW challenge (hashcash-sha256)
3. Solve PoW: SHA256(challenge:subject:nonce) with >= difficulty leading zero bits
   where subject = hex(SHA256(public_sign_key_bytes))
4. POST registration with proof

Usage:
    python3 register.py --name "my-agent"
    python3 register.py --name "my-agent" --keys agent_keys.json

Requires: pip install cryptography requests
"""
import argparse
import base64
import hashlib
import json
import os
import sys
import time

try:
    import requests
except ImportError:
    print("Error: 'requests' required. Run: pip install requests", file=sys.stderr)
    sys.exit(1)

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat, NoEncryption
except ImportError:
    print("Error: 'cryptography' required. Run: pip install cryptography", file=sys.stderr)
    sys.exit(1)

API_BASE = "https://agent-id.io/v1"


def generate_keypair():
    sign_priv = Ed25519PrivateKey.generate()
    sign_pub = sign_priv.public_key()
    enc_priv = X25519PrivateKey.generate()
    enc_pub = enc_priv.public_key()
    return {
        "sign_private_key": base64.b64encode(sign_priv.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())).decode(),
        "sign_public_key": base64.b64encode(sign_pub.public_bytes(Encoding.Raw, PublicFormat.Raw)).decode(),
        "enc_private_key": base64.b64encode(enc_priv.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())).decode(),
        "enc_public_key": base64.b64encode(enc_pub.public_bytes(Encoding.Raw, PublicFormat.Raw)).decode(),
    }


def leading_zero_bits(data: bytes) -> int:
    count = 0
    for b in data:
        if b == 0:
            count += 8
        else:
            for i in range(7, -1, -1):
                if (b & (1 << i)) == 0:
                    count += 1
                else:
                    return count
            return count
    return count


def solve_pow(challenge: str, subject_hex: str, difficulty: int) -> str:
    """
    Find nonce (as string) where:
      SHA256(challenge + ':' + subject_hex + ':' + nonce)
    has >= difficulty leading zero bits.
    """
    print(f"  Solving PoW (difficulty={difficulty})...", end="", flush=True)
    start = time.time()
    nonce = 0
    while True:
        nonce_str = str(nonce)
        data = f"{challenge}:{subject_hex}:{nonce_str}".encode()
        digest = hashlib.sha256(data).digest()
        if leading_zero_bits(digest) >= difficulty:
            elapsed = time.time() - start
            print(f" done in {elapsed:.1f}s (nonce={nonce_str})")
            return nonce_str
        nonce += 1


def main():
    parser = argparse.ArgumentParser(description="Register a new agent on agent-id.io")
    parser.add_argument("--name", required=True, help="Agent display name (3-64 chars)")
    parser.add_argument("--keys", default="agent_keys.json", help="Keys file to create (default: agent_keys.json)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing keys file")
    args = parser.parse_args()

    if os.path.exists(args.keys) and not args.overwrite:
        print(f"Error: {args.keys} already exists. Use --overwrite to replace.", file=sys.stderr)
        sys.exit(1)

    if not (3 <= len(args.name) <= 64):
        print("Error: display name must be 3-64 characters", file=sys.stderr)
        sys.exit(1)

    print(f"Registering '{args.name}' on agent-id.io...")

    # 1. Generate keypair
    print("1. Generating keypair...")
    keys = generate_keypair()
    sign_pub_b64 = keys["sign_public_key"]
    enc_pub_b64 = keys["enc_public_key"]
    sign_pub_bytes = base64.b64decode(sign_pub_b64)

    # subject = hex(SHA256(public_sign_key_bytes))
    subject_hex = hashlib.sha256(sign_pub_bytes).hexdigest()

    # 2. Request PoW challenge
    print("2. Requesting PoW challenge...")
    resp = requests.post(f"{API_BASE}/agents/register/challenge",
                         json={"public_sign_key": sign_pub_b64}, timeout=10)
    if resp.status_code == 429:
        retry = resp.headers.get("Retry-After", "60")
        print(f"Rate limited. Wait {retry}s and retry.", file=sys.stderr)
        sys.exit(1)
    resp.raise_for_status()
    cd = resp.json()
    challenge = cd["challenge"]
    difficulty = cd["difficulty"]
    print(f"  Expires: {cd['expires_at']}")

    # 3. Solve PoW
    print("3. Solving Proof-of-Work...")
    nonce = solve_pow(challenge, subject_hex, difficulty)

    # 4. Register
    print("4. Registering...")
    resp = requests.post(f"{API_BASE}/agents/register", json={
        "display_name": args.name,
        "public_sign_key": sign_pub_b64,
        "public_enc_key": enc_pub_b64,
        "pow_challenge": challenge,
        "pow_nonce": nonce,
    }, timeout=10)

    if resp.status_code == 429:
        retry = resp.headers.get("Retry-After", "60")
        print(f"Rate limited on register. Wait {retry}s and retry.", file=sys.stderr)
        sys.exit(1)
    if resp.status_code == 400 and "invalid_pow" in resp.text:
        print("PoW validation failed (challenge may have expired). Re-run the script.", file=sys.stderr)
        sys.exit(1)
    resp.raise_for_status()

    result = resp.json()
    agent_id = result["agent_id"]
    keys["agent_id"] = agent_id
    keys["display_name"] = result["display_name"]
    keys["warning"] = "KEEP THIS FILE SECRET. Never share private keys."

    with open(args.keys, "w") as f:
        json.dump(keys, f, indent=2)
    os.chmod(args.keys, 0o600)

    print(f"\n✅ Registered!")
    print(f"  Agent ID:  {agent_id}")
    print(f"  Name:      {result['display_name']}")
    print(f"  Keys:      {args.keys}")
    print(f"\nNext: python3 scripts/authenticate.py {args.keys}")


if __name__ == "__main__":
    main()
