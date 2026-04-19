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
- Use `references/api.md` for endpoint details, proof formats, and error semantics.
- For state-changing actions, say what will change and name the verification step before executing.
- If a step is irreversible or can lock the identity, call that out briefly before continuing.
- Never paste secret values or private key material into chat output unless the human explicitly asks.

## Default workflow

1. Classify the task as register, authenticate, verify, sponsor, rotate, derive, or inspect.
2. Read `references/api.md` if the endpoint or payload is unclear.
3. Use the matching script from `scripts/` for deterministic cryptographic work.
4. Execute the remote API step.
5. Verify the resulting remote state, for example by reading the profile, keys, or verification status.

## Common workflows

### Register a new agent
- Generate local keys with `python3 scripts/keygen.py`
- Register with `python3 scripts/register.py --help`
- Store the returned `agent_id` separately from the encrypted keyfile backup
- Confirm the new profile exists after registration

### Authenticate
- Run `python3 scripts/authenticate.py --help`
- Tokens are short-lived and must be re-issued when expired
- Do not assume an old token is still valid, re-authenticate on 401

### Verify identity
- Start the verification flow for domain, code repo, or website proof
- Apply the exact proof value, byte for byte
- Run the corresponding check call only after the proof is live
- Confirm the verification shows up on the agent profile

### Rotate keys
- Use `python3 scripts/rotate_keys.py --help`
- Confirm the new public keys on the agent profile after rotation
- Replace old local key material only after verification succeeds

### Secure local key material
- Use `python3 scripts/secure_keyfile.py --help` when key material needs encryption at rest
- Keep the encrypted keyfile and the passphrase in separate places

## Files

- `references/api.md`: public API reference
- `scripts/`: deterministic helpers for crypto and API flows
- `requirements.txt`: pinned Python runtime dependencies
