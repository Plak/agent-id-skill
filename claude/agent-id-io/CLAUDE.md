# agent-id.io

Use this package when work involves the `agent-id.io` identity and trust service, especially for:
- registering a new AI agent identity
- authenticating with challenge/response
- rotating keys or managing passkeys
- verifying an agent via DNS, repo, or website proof
- handling sponsorship requests or approvals
- looking up public agent profiles or keys

## Operating rules

- Generate and keep private keys locally. Never send private keys to `agent-id.io`.
- Treat `agent_keys.json` like a production secret.
- Prefer the helper scripts in `scripts/` over rewriting crypto steps by hand.
- Use `references/api.md` for endpoint details and error semantics.
- If a task mutates identity state, explain the irreversible risk briefly before executing.
- Never paste secret values into chat output unless the human explicitly asks.

## Fast path

1. Read `references/api.md` if the endpoint or payload is unclear.
2. Use `scripts/keygen.py` for key generation.
3. Use `scripts/register.py` or `scripts/authenticate.py` for the main flows.
4. Use `scripts/rotate_keys.py`, `scripts/sign_challenge.py`, `scripts/sign_sponsorship.py`, and `scripts/derive_keys.py` for the specialized flows.
5. Use `scripts/secure_keyfile.py` when key material needs encryption at rest.

## Common workflows

### Register a new agent
- Generate local keys with `python3 scripts/keygen.py`
- Register with `python3 scripts/register.py --help`
- Store the returned `agent_id` separately from the encrypted keyfile backup

### Authenticate
- Run `python3 scripts/authenticate.py --help`
- Tokens are short-lived and must be re-issued when expired

### Verify identity
- Start the verification flow for domain, code repo, or website proof
- Apply the exact proof value
- Run the corresponding check call only after the proof is live

### Rotate keys
- Use `python3 scripts/rotate_keys.py --help`
- Confirm the new public keys on the agent profile after rotation
- Replace old local key material only after verification succeeds

## Files

- `references/api.md`: public API reference
- `scripts/`: deterministic helpers for crypto and API flows
- `requirements.txt`: pinned Python runtime dependencies
