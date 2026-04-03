# agent-id-skill

OpenClaw Skill: Register, authenticate, and manage AI agent identities on [agent-id.io](https://agent-id.io).

## What it does

- Register new agent identities with Ed25519 keypairs
- Authenticate via passkey challenge/response
- Add/remove passkeys, rotate keys
- Verify identity via domain or code-repo
- Request/manage sponsorships
- Look up other agents in the directory

## Usage

This skill is loaded automatically by OpenClaw when tasks match its description. See `SKILL.md` for the full skill specification.

## Structure

```
SKILL.md          — Skill specification (loaded by OpenClaw)
scripts/          — Helper scripts
references/       — Reference docs and API specs
```

## CI

- `python-lint`: pylint on all scripts
- `python-security`: bandit security scan on all scripts
