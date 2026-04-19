# agent-id-skill

Public source repository for agent-id workflows across multiple agent runtimes.

## Goals

- keep the public OpenClaw skill publishable from this repo
- ship dedicated Claude and OpenAI runtime variants without private coupling
- keep each runtime package self-contained and publishable on its own

## Layout

```text
openclaw/
  agent-id-io/      # publishable OpenClaw skill
claude/
  agent-id-io/      # Claude-oriented runtime package
openai/
  agent-id-io/      # Codex and ChatGPT runtime package
```

## Runtime entrypoints

- `openclaw/agent-id-io/SKILL.md`
- `claude/agent-id-io/CLAUDE.md`
- `openai/agent-id-io/AGENTS.md`
- `openai/agent-id-io/CHATGPT.md`

`CHATGPT.md` is a plain repository artifact for reusable ChatGPT project/custom-instruction text, not a native OpenAI packaging format.

## Publishing model

- OpenClaw release source: `openclaw/agent-id-io`
- Claude release source: `claude/agent-id-io`
- OpenAI release source: `openai/agent-id-io`
- Shared ideas may exist across runtimes, but published artifacts must not depend on private infrastructure or files outside their own release folder.

## Source of truth

- **Git is the leading system.**
- Public text, metadata, version bumps, and release structure are changed in this repository first.
- Runtime-specific publish steps should always be derived from the Git state.

## Current status

- `openclaw/agent-id-io` is the active public OpenClaw skill source
- `claude/agent-id-io` is now scaffolded for Claude-specific instruction loading
- `openai/agent-id-io` is now scaffolded for Codex and ChatGPT usage
