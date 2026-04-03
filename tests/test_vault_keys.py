"""Tests for the OpenBao/Vault key storage workflow."""
import json

import pytest
import responses

from scripts import vault_keys


VAULT_ADDR = "https://vault.example:8200"
AGENT_ID = "00000000-0000-0000-0000-000000000001"


def test_store_builds_correct_kv_v2_request(monkeypatch, tmp_keys):
    """Store should write the input JSON under the KV v2 data envelope."""
    keys_path, keys = tmp_keys
    endpoint = f"{VAULT_ADDR}/v1/kv/data/agent-id/{AGENT_ID}/keys"

    monkeypatch.setenv("VAULT_ADDR", VAULT_ADDR)
    monkeypatch.setenv("VAULT_TOKEN", "test-token")

    with responses.RequestsMock() as rsps:
        rsps.add(responses.POST, endpoint, json={"data": {}}, status=200)

        vault_keys.main(["store", "--in", keys_path])

        request = rsps.calls[0].request
        assert request.headers["X-Vault-Token"] == "test-token"
        assert json.loads(request.body) == {"data": keys}


def test_load_outputs_expected_json(monkeypatch, capsys):
    """Load should unwrap the KV v2 response and print the stored JSON."""
    endpoint = f"{VAULT_ADDR}/v1/kv/data/agent-id/{AGENT_ID}/keys"
    stored_keys = {
        "agent_id": AGENT_ID,
        "sign_private_key": "priv",
        "sign_public_key": "pub",
    }

    monkeypatch.setenv("VAULT_ADDR", VAULT_ADDR)
    monkeypatch.setenv("VAULT_TOKEN", "test-token")

    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            endpoint,
            json={"data": {"data": stored_keys, "metadata": {"version": 3}}},
            status=200,
        )

        vault_keys.main(["load", "--agent-id", AGENT_ID])

    output = capsys.readouterr().out
    assert json.loads(output) == stored_keys


def test_delete_calls_correct_delete_endpoint(monkeypatch):
    """Delete should hit the KV v2 soft-delete endpoint."""
    endpoint = f"{VAULT_ADDR}/v1/kv/delete/agent-id/{AGENT_ID}/keys"

    monkeypatch.setenv("VAULT_ADDR", VAULT_ADDR)
    monkeypatch.setenv("VAULT_TOKEN", "test-token")

    with responses.RequestsMock() as rsps:
        rsps.add(responses.POST, endpoint, body="", status=204)

        vault_keys.main(["delete", "--agent-id", AGENT_ID])

        assert rsps.calls[0].request.body in (None, b"", "")


def test_missing_vault_token_fails_fast(monkeypatch, capsys, tmp_keys):
    """Any command should fail clearly when VAULT_TOKEN is absent."""
    keys_path, _ = tmp_keys

    monkeypatch.delenv("VAULT_TOKEN", raising=False)
    monkeypatch.setenv("VAULT_ADDR", VAULT_ADDR)

    with pytest.raises(SystemExit) as exc:
        vault_keys.main(["store", "--in", keys_path])

    assert exc.value.code == 1
    assert "VAULT_TOKEN" in capsys.readouterr().err


@pytest.mark.parametrize("command", ["load", "delete"])
def test_missing_agent_id_fails_fast(monkeypatch, capsys, command):
    """Load and delete require an explicit agent_id."""
    monkeypatch.setenv("VAULT_ADDR", VAULT_ADDR)
    monkeypatch.setenv("VAULT_TOKEN", "test-token")

    with pytest.raises(SystemExit) as exc:
        vault_keys.main([command])

    assert exc.value.code == 1
    assert "agent-id" in capsys.readouterr().err
