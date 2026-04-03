#!/usr/bin/env python3
"""
Sign a sponsorship approval: sponsor signs the requester's public_sign_key
with the sponsor's Ed25519 private key.

Usage:
    python3 sign_sponsorship.py <requester_public_sign_key_base64> sponsor_keys.json

Output: JSON with "sponsor_signature" ready for POST /sponsorship/requests/{id}/approve

Requires: pip install cryptography
"""
import argparse
import base64
import json
import sys

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
except ImportError:
    print("Error: 'cryptography' package required. Run: pip install cryptography", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Sign sponsorship approval")
    parser.add_argument("requester_public_sign_key", help="Requester's public_sign_key (base64, from /sponsorship/requests)")
    parser.add_argument("sponsor_keys_file", help="Sponsor's agent_keys.json")
    args = parser.parse_args()

    with open(args.sponsor_keys_file) as f:
        keys = json.load(f)

    priv_bytes = base64.b64decode(keys["sign_private_key"])
    private_key = Ed25519PrivateKey.from_private_bytes(priv_bytes)

    requester_pub_bytes = base64.b64decode(args.requester_public_sign_key)
    signature = private_key.sign(requester_pub_bytes)

    payload = {
        "sponsor_signature": base64.b64encode(signature).decode()
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
