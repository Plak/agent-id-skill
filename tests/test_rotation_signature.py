"""Rotation signature integrity tests."""

import base64

import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from scripts.register import generate_keypair
from scripts.rotate_keys import build_rotation_signature_message


def test_rotation_signature_message_binds_sign_and_enc_keys():
    """Rotation signatures must bind both the new signing and encryption public keys."""
    old_keys = generate_keypair()
    old_priv = Ed25519PrivateKey.from_private_bytes(base64.b64decode(old_keys["sign_private_key"]))
    old_pub = old_priv.public_key()

    new_sign_pub = Ed25519PrivateKey.generate().public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    new_enc_pub = X25519PrivateKey.generate().public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)

    signed_message = build_rotation_signature_message(new_sign_pub, new_enc_pub)
    signature = old_priv.sign(signed_message)

    # Sanity: signature verifies against the exact signed payload.
    old_pub.verify(signature, signed_message)

    # Tampering only the encryption key must invalidate verification.
    tampered_enc_pub = X25519PrivateKey.generate().public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    tampered_message = build_rotation_signature_message(new_sign_pub, tampered_enc_pub)
    with pytest.raises(InvalidSignature):
        old_pub.verify(signature, tampered_message)
