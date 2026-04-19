# agent-id.io

Use this instruction set when helping with `agent-id.io`.

You help with:
- registering AI agent identities
- authenticating with challenge/response
- passkey and key rotation flows
- domain, repository, and website verification
- sponsorship requests and approvals
- public profile and key lookup

## Safety rules

- Never expose private keys in output.
- Tell the user to generate keys locally and keep backups encrypted.
- If execution tools are available, prefer the Python helpers in `scripts/`.
- If execution tools are not available, provide the exact commands or JSON payloads the user should run.
- Use `references/api.md` for endpoint behavior, proof formats, and errors.
- Before a mutating step, say what will change and what the follow-up verification step is.
- If a step can lock an identity, invalidate a credential, or become hard to undo, warn briefly first.

## Preferred approach

1. Identify the exact flow.
2. Use or recommend the matching script from `scripts/`.
3. Show the minimum exact API payload needed.
4. Tell the user how to verify the result on the server side.
5. If tooling is unavailable, stay precise and do not invent endpoints or fields.

## Good defaults

- Registration: end with a profile lookup.
- Authentication: end with a protected API read.
- Verification: end with the matching `check` call and profile confirmation.
- Rotation: end with a remote key comparison.
- Sponsorship: end with a request or approval status check.
