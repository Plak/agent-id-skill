# Runtime variants for agent-id-skill

## Goal
Add two publishable, self-contained runtime variants next to the existing OpenClaw skill:
- `claude/agent-id-io`
- `openai/agent-id-io` for Codex and ChatGPT

## Constraints
- Keep `openclaw/agent-id-io` unchanged as the active OpenClaw release source.
- Each runtime folder must be self-contained and must not depend on files outside its own release folder.
- Reuse the same public API semantics and security guardrails across runtimes.
- Do not introduce private infrastructure references.

## Deliverables
1. Root README updated for the new runtime layout.
2. Claude variant with:
   - `README.md`
   - `CLAUDE.md`
   - `references/api.md`
   - `requirements.txt`
   - `scripts/`
3. OpenAI variant with:
   - `README.md`
   - `AGENTS.md` for Codex
   - `CHATGPT.md` for ChatGPT project/custom instructions
   - `references/api.md`
   - `requirements.txt`
   - `scripts/`
4. Repo tests that verify the expected runtime layout.

## Verification
- `python3 -m unittest discover -s tests -p 'test_*.py'`
- `git status --short` clean except intentional changes
