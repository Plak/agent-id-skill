#!/usr/bin/env python3
"""
Generate Ed25519 (signing) + X25519 (encryption) keypair for agent-id.io registration.

Usage:
    python3 keygen.py
    python3 keygen.py --output my-agent-keys.json

Output: JSON file with private + public keys (base64 encoded).
        Public keys are ready to POST to /agents/register.
"""
import argparse
import base64
import json
import os
import sys

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat, NoEncryption
except ImportError:
    print("Error: 'cryptography' package required. Run: pip install cryptography", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Generate agent-id.io keypair")
    parser.add_argument("--output", default="agent_keys.json", help="Output file (default: agent_keys.json)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing key file")
    args = parser.parse_args()

    if os.path.exists(args.output) and not args.overwrite:
        print(f"Error: {args.output} already exists. Use --overwrite to replace.", file=sys.stderr)
        sys.exit(1)

    # Generate Ed25519 signing key
    sign_private = Ed25519PrivateKey.generate()
    sign_public = sign_private.public_key()
    sign_priv_bytes = sign_private.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    sign_pub_bytes = sign_public.public_bytes(Encoding.Raw, PublicFormat.Raw)

    # Generate X25519 encryption key
    enc_private = X25519PrivateKey.generate()
    enc_public = enc_private.public_key()
    enc_priv_bytes = enc_private.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    enc_pub_bytes = enc_public.public_bytes(Encoding.Raw, PublicFormat.Raw)

    keys = {
        "warning": "KEEP THIS FILE SECRET. Never share private keys.",
        "sign_private_key": base64.b64encode(sign_priv_bytes).decode(),
        "sign_public_key": base64.b64encode(sign_pub_bytes).decode(),
        "enc_private_key": base64.b64encode(enc_priv_bytes).decode(),
        "enc_public_key": base64.b64encode(enc_pub_bytes).decode(),
    }

    with open(args.output, "w") as f:
        json.dump(keys, f, indent=2)
    os.chmod(args.output, 0o600)

    print(f"✅ Keys generated → {args.output}")
    print(f"\nFor POST /agents/register:")
    print(f'  "public_sign_key": "{keys["sign_public_key"]}"')
    print(f'  "public_enc_key":  "{keys["enc_public_key"]}"')


if __name__ == "__main__":
    main()
