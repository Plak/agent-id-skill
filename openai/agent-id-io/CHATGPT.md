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
- Use `references/api.md` for endpoint behavior and errors.
- After a mutating step, recommend a verification step.

## Preferred approach

1. Identify the exact flow.
2. Use or recommend the matching script from `scripts/`.
3. Show the minimum exact API payload needed.
4. Verify the resulting server-side state where possible.
