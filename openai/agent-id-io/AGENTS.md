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
- Read `references/api.md` when endpoint behavior, status codes, or proof formats matter.
- For state-changing actions, call out irreversible risk briefly before executing.
- Never print secrets unless the user explicitly requests them.

## Workflow

1. Clarify whether this is register, auth, verify, sponsorship, or lookup.
2. Use the helper scripts for deterministic cryptographic steps.
3. Use the API reference for exact payloads and failure cases.
4. Verify the resulting remote state after each mutation.

## Key commands

- `python3 scripts/keygen.py`
- `python3 scripts/register.py --help`
- `python3 scripts/authenticate.py --help`
- `python3 scripts/rotate_keys.py --help`
- `python3 scripts/sign_challenge.py --help`
- `python3 scripts/sign_sponsorship.py --help`
- `python3 scripts/derive_keys.py --help`
- `python3 scripts/secure_keyfile.py --help`
