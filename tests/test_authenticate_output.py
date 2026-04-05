"""Authenticate CLI output safety tests."""

import sys

import pytest
import responses

from scripts import authenticate


@responses.activate
def test_authenticate_requires_explicit_output_flag(tmp_keys, monkeypatch, capsys):
    """authenticate should fail closed unless token output intent is explicit."""
    keys_path, _ = tmp_keys

    responses.post(
        f"{authenticate.API_BASE}/auth/challenge",
        json={"challenge": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"},
        status=200,
    )
    responses.post(
        f"{authenticate.API_BASE}/auth/verify",
        json={"token": "secret-jwt", "expires_at": "2099-01-01T00:00:00Z"},
        status=200,
    )

    monkeypatch.setattr(sys, "argv", ["authenticate.py", keys_path])

    with pytest.raises(SystemExit) as exc:
        authenticate.main()

    captured = capsys.readouterr()
    assert exc.value.code == 1
    assert "token output is disabled by default" in captured.err
    assert "secret-jwt" not in captured.out
    assert "secret-jwt" not in captured.err
    assert len(responses.calls) == 0


@responses.activate
def test_authenticate_print_token_explicit_opt_in(tmp_keys, monkeypatch, capsys):
    """--print-token should emit JWT on stdout and expiry metadata on stderr."""
    keys_path, _ = tmp_keys

    responses.post(
        f"{authenticate.API_BASE}/auth/challenge",
        json={"challenge": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"},
        status=200,
    )
    responses.post(
        f"{authenticate.API_BASE}/auth/verify",
        json={"token": "secret-jwt", "expires_at": "2099-01-01T00:00:00Z"},
        status=200,
    )

    monkeypatch.setattr(sys, "argv", ["authenticate.py", keys_path, "--print-token"])

    authenticate.main()

    captured = capsys.readouterr()
    assert captured.out.strip() == "secret-jwt"
    assert "# Expires: 2099-01-01T00:00:00Z" in captured.err
