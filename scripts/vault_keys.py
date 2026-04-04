#!/usr/bin/env python3
"""Store, load, and delete agent key material in OpenBao/Vault KV v2."""
import argparse
import json
import os
import sys

import requests

try:
    from .crypto_utils import atomic_write, secure_zero, to_secure_buffer
except ImportError:
    from crypto_utils import atomic_write, secure_zero, to_secure_buffer


DEFAULT_VAULT_ADDR = "https://127.0.0.1:8200"


def fail(message: str) -> None:
    """Print a user-facing error and exit with status 1."""
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(1)


def require_token() -> str:
    """Return VAULT_TOKEN or exit if it is not configured."""
    token = os.environ.get("VAULT_TOKEN")
    if not token:
        fail("VAULT_TOKEN is required")
    return token


def get_vault_addr() -> str:
    """Resolve the Vault address from the environment or default."""
    return os.environ.get("VAULT_ADDR", DEFAULT_VAULT_ADDR).rstrip("/")


def kv_data_endpoint(vault_addr: str, agent_id: str) -> str:
    """Build the KV v2 data endpoint for the given agent."""
    return f"{vault_addr}/v1/kv/data/agent-id/{agent_id}/keys"


def kv_delete_endpoint(vault_addr: str, agent_id: str) -> str:
    """Build the KV v2 soft-delete endpoint for the given agent."""
    return f"{vault_addr}/v1/kv/delete/agent-id/{agent_id}/keys"


def request_headers(token: str) -> dict[str, str]:
    """Build headers for Vault API requests."""
    return {
        "X-Vault-Token": token,
        "Content-Type": "application/json",
    }


def write_json_file(path: str, payload: dict) -> None:
    """Write JSON with restrictive permissions."""
    serialized = to_secure_buffer(json.dumps(payload, indent=2) + "\n")
    try:
        atomic_write(path, bytes(serialized), mode=0o600)
    finally:
        secure_zero(serialized)


def store_keys(vault_addr: str, token: str, input_path: str, agent_id_override: str | None) -> None:
    """Store a local agent_keys.json in KV v2."""
    with open(input_path, "rb") as handle:
        serialized = to_secure_buffer(handle.read())
    try:
        keys = json.loads(bytes(serialized))

        agent_id = agent_id_override or keys.get("agent_id")
        if not agent_id:
            fail("store requires agent_id in the input file or via --agent-id")

        response = requests.post(
            kv_data_endpoint(vault_addr, agent_id),
            headers=request_headers(token),
            json={"data": keys},
            timeout=10,
        )
        response.raise_for_status()
        print(f"Stored key material for agent_id {agent_id}", file=sys.stderr)
    finally:
        # Best-effort only: Python/requests may retain copies internally.
        secure_zero(serialized)


def load_keys(vault_addr: str, token: str, agent_id: str, output_path: str | None) -> None:
    """Load agent key material from KV v2."""
    response = requests.get(
        kv_data_endpoint(vault_addr, agent_id),
        headers=request_headers(token),
        timeout=10,
    )
    response.raise_for_status()

    payload = response.json()
    try:
        keys = payload["data"]["data"]
    except KeyError as exc:
        fail(f"unexpected Vault response shape: missing {exc}")

    if output_path:
        write_json_file(output_path, keys)
        print(f"Wrote key material for agent_id {agent_id} to {output_path}", file=sys.stderr)
        return

    serialized = to_secure_buffer(json.dumps(keys, indent=2) + "\n")
    try:
        sys.stdout.write(bytes(serialized).decode())
    finally:
        secure_zero(serialized)


def delete_keys(vault_addr: str, token: str, agent_id: str) -> None:
    """Soft-delete the latest KV v2 version for an agent."""
    response = requests.post(
        kv_delete_endpoint(vault_addr, agent_id),
        headers=request_headers(token),
        timeout=10,
    )
    response.raise_for_status()
    print(f"Deleted latest Vault key version for agent_id {agent_id}", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(description="Manage agent key material in OpenBao/Vault KV v2")
    subparsers = parser.add_subparsers(dest="command")

    store = subparsers.add_parser("store", help="Store agent_keys.json in Vault")
    store.add_argument("--in", dest="input_path", default="agent_keys.json", help="Input path")
    store.add_argument("--agent-id", help="Override agent_id from the key file")

    load = subparsers.add_parser("load", help="Load agent_keys.json from Vault")
    load.add_argument("--agent-id", help="Agent identifier")
    load.add_argument("--out", help="Write JSON to a file instead of stdout")

    delete = subparsers.add_parser("delete", help="Soft-delete the latest Vault key version")
    delete.add_argument("--agent-id", help="Agent identifier")

    return parser


def main(argv: list[str] | None = None) -> None:
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help(sys.stderr)
        raise SystemExit(1)

    token = require_token()
    vault_addr = get_vault_addr()

    try:
        if args.command == "store":
            store_keys(vault_addr, token, args.input_path, args.agent_id)
        elif args.command == "load":
            if not args.agent_id:
                fail("load requires --agent-id")
            load_keys(vault_addr, token, args.agent_id, args.out)
        elif args.command == "delete":
            if not args.agent_id:
                fail("delete requires --agent-id")
            delete_keys(vault_addr, token, args.agent_id)
    except requests.RequestException as exc:
        fail(f"Vault request failed: {exc}")


if __name__ == "__main__":
    main()
