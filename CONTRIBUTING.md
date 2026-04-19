# Contributing

## Repo roles

This project is developed **GitLab-first**.

- **Internal GitLab** is the canonical development repository.
- **Public GitHub** is an export and publication target.
- Development, review, security checks, and test verification happen on GitLab first.
- Only the verified, public-safe result is pushed to GitHub.

## Remote convention

Recommended local remote layout:

```bash
git remote rename origin gitlab           # only if the clone started differently
git remote add github https://github.com/Plak/agent-id-skill.git
```

For the maintained internal clone used by K:

- `origin` already points to internal GitLab
- `github` may be added as a second remote when public export is needed

Expected state:

```bash
git remote -v
origin  ssh://git@192.168.6.202:2222/agents-stack/agent-id-skill.git (fetch)
origin  ssh://git@192.168.6.202:2222/agents-stack/agent-id-skill.git (push)
github  https://github.com/Plak/agent-id-skill.git (fetch)
github  https://github.com/Plak/agent-id-skill.git (push)
```

## Branch and review flow

1. Start from internal GitLab main:

   ```bash
   git fetch origin
   git switch -c <branch-name> origin/main
   ```

2. Do the actual work only in the GitLab clone.

3. Verify before review:

   ```bash
   python3 -m pytest tests/ -v
   ```

4. Push branch to GitLab and review there first:

   ```bash
   git push -u origin <branch-name>
   ```

5. Merge on GitLab only after review, QA, and security checks are green.

6. Export the verified result to GitHub:

   ```bash
   git fetch origin
   git switch main
   git pull --ff-only origin main
   git push github main
   ```

## Public export rule

Before pushing anything to GitHub, check that the exported commit range is safe to publish:

- no private infrastructure details
- no internal hostnames, IPs, or tokens
- no internal-only notes or operational shortcuts
- no half-tested work-in-progress branches

If GitHub needs a PR instead of a direct fast-forward, create that PR **from the already verified GitLab result**, not from fresh unreviewed work.

## Short version

- Build here on GitLab
- Test here on GitLab
- Review here on GitLab
- Publish only the verified result to GitHub
