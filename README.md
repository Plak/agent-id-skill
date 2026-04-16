# agent-id-skill

Public source repository for agent-id skills across multiple agent runtimes.

## Goals

- keep the public OpenClaw skill publishable from this repo
- prepare a clean home for a future Claude-oriented variant
- avoid coupling published skills to private infrastructure or internal repos

## Layout

```text
openclaw/
  agent-id-io/      # publishable OpenClaw skill
claude/
  # next iteration lives here
```

## Publishing model

- OpenClaw release source: `openclaw/agent-id-io`
- Future Claude release source: a dedicated folder under `claude/`
- Each runtime folder should stay self-contained and publishable on its own.
- Shared ideas may exist across runtimes, but published artifacts must not depend on private infrastructure or files outside their own release folder.

## Source of truth

- **Git is the leading system.**
- Public text, metadata, version bumps, and release structure are changed in this repository first.
- ClawHub publishes are derived from the Git state, not edited ad hoc in a separate workflow.

## Current status

- `openclaw/agent-id-io` is the active public OpenClaw skill source
- ClawHub slug: `agent-id-io`
- Claude variant is intentionally not scaffolded yet beyond the repo slot
