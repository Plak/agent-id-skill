#!/usr/bin/env python3
"""
Generate a new Ed25519 + X25519 keypair and create a rotation signature.

The rotation signature proves ownership of the old keypair by signing
the new public_sign_key with the old private key.

Usage:
    python3 rotate_keys.py agent_keys.json
    python3 rotate_keys.py agent_keys.json --new-keys new_agent_keys.json --payload rotation_payload.json

After rotation succeeds, replace agent_keys.json with new_agent_keys.json.
Old tokens remain valid until expiry.

Requires: pip install cryptography
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
    parser = argparse.ArgumentParser(description="Rotate agent-id.io cryptographic keys")
    parser.add_argument("keys_file", help="Current agent_keys.json")
    parser.add_argument("--new-keys", default="new_agent_keys.json", help="Output file for new keys")
    parser.add_argument("--payload", default="rotation_payload.json", help="Output file for POST payload")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output files")
    args = parser.parse_args()

    for path in [args.new_keys, args.payload]:
        if os.path.exists(path) and not args.overwrite:
            print(f"Error: {path} already exists. Use --overwrite to replace.", file=sys.stderr)
            sys.exit(1)

    # Load current private key
    with open(args.keys_file) as f:
        old_keys = json.load(f)
    old_priv_bytes = base64.b64decode(old_keys["sign_private_key"])
    old_private_key = Ed25519PrivateKey.from_private_bytes(old_priv_bytes)

    # Generate new keypair
    new_sign_private = Ed25519PrivateKey.generate()
    new_sign_public = new_sign_private.public_key()
    new_sign_priv_bytes = new_sign_private.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    new_sign_pub_bytes = new_sign_public.public_bytes(Encoding.Raw, PublicFormat.Raw)

    new_enc_private = X25519PrivateKey.generate()
    new_enc_public = new_enc_private.public_key()
    new_enc_priv_bytes = new_enc_private.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    new_enc_pub_bytes = new_enc_public.public_bytes(Encoding.Raw, PublicFormat.Raw)

    # Sign new public_sign_key with old private key
    rotation_signature = old_private_key.sign(new_sign_pub_bytes)

    # Save new keys
    new_keys = {
        "warning": "KEEP THIS FILE SECRET. Never share private keys.",
        "sign_private_key": base64.b64encode(new_sign_priv_bytes).decode(),
        "sign_public_key": base64.b64encode(new_sign_pub_bytes).decode(),
        "enc_private_key": base64.b64encode(new_enc_priv_bytes).decode(),
        "enc_public_key": base64.b64encode(new_enc_pub_bytes).decode(),
    }
    with open(args.new_keys, "w") as f:
        json.dump(new_keys, f, indent=2)
    os.chmod(args.new_keys, 0o600)

    # Save rotation payload
    payload = {
        "new_public_sign_key": base64.b64encode(new_sign_pub_bytes).decode(),
        "new_public_enc_key": base64.b64encode(new_enc_pub_bytes).decode(),
        "rotation_signature": base64.b64encode(rotation_signature).decode(),
    }
    with open(args.payload, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"✅ New keys → {args.new_keys}")
    print(f"✅ Rotation payload → {args.payload}")
    print(f"\nPOST this payload to:")
    print(f"  POST https://agent-id.io/v1/agents/<agent_id>/keys/rotate")
    print(f"  Authorization: Bearer <token>")
    print(f"\nAfter successful rotation:")
    print(f"  mv {args.new_keys} {args.keys_file}")


if __name__ == "__main__":
    main()
