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

## Repository boundary

This repository contains the **skill/client side** of agent-id:

- `SKILL.md`, helper scripts, references, tests, and packaging for the OpenClaw skill
- agent-facing workflows for registration, authentication, rotation, verification, and sponsorship
- distribution path to ClawHub

This repository does **not** contain the `agent-id` backend service:

- no Go API server
- no database schema or migrations for the live service
- no k8s manifests or service deployment logic

The backend lives in the separate internal repository `agents-stack/agent-id`.

## Structure

```
SKILL.md          — Skill specification (loaded by OpenClaw)
scripts/          — Helper scripts
references/       — Reference docs and API specs
```

## CI

- `python-lint`: pylint on all scripts
- `python-security`: bandit security scan on all scripts
