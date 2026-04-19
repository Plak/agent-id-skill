# agent-id.io

Use this package when the task involves `agent-id.io`, including:
- registering an AI agent identity
- authenticating with signed challenge/response
- rotating cryptographic keys or managing passkeys
- verifying ownership of a domain, repo, or website
- approving or requesting sponsorships
- inspecting public profiles and key material

## Rules

- Generate private keys locally, never on the remote service.
- Keep `agent_keys.json` secret and prefer encrypted storage.
- Prefer the provided Python helpers in `scripts/` instead of hand-rolled crypto.
- Read `references/api.md` when endpoint behavior, status codes, proof formats, or verification semantics matter.
- Before any mutating step, state what will change and how you will verify it.
- If a step could lock the identity or invalidate existing credentials, call that out briefly before execution.
- Never print secrets unless the user explicitly requests them.

## Workflow

1. Clarify whether this is register, authenticate, verify, sponsorship, rotation, derivation, or lookup.
2. Use the helper scripts for deterministic cryptographic steps.
3. Use the API reference for exact payloads, proof values, and failure cases.
4. Execute the remote step.
5. Verify the resulting remote state after each mutation.

## Verification examples

- Registration: fetch the created agent profile.
- Authentication: confirm the protected call succeeds, not just that a token string exists.
- Verification: confirm the verification status appears on the agent profile.
- Rotation: confirm the remote public keys match the newly generated local keys.
- Sponsorship: confirm the request or approval is visible through the API.

## Key commands

- `python3 scripts/keygen.py`
- `python3 scripts/register.py --help`
- `python3 scripts/authenticate.py --help`
- `python3 scripts/rotate_keys.py --help`
- `python3 scripts/sign_challenge.py --help`
- `python3 scripts/sign_sponsorship.py --help`
- `python3 scripts/derive_keys.py --help`
- `python3 scripts/secure_keyfile.py --help`
