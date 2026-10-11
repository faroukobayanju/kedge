# How to add a failing PR as a target

Let Kedge work on a new failing dependency PR by adding it to the `targets.json` allowlist.

## Prerequisites

- A failing Dependabot or Renovate PR on a public GitHub repo
- A fork of that repo that you (and `gh`) can push to

## Steps

1. Fork the repo:

   ```bash
   gh repo fork <owner>/<repo> --clone=false
   ```

2. Find a command that installs dependencies and runs the unit tests in one go, and prints a Jest or pytest summary. Try it on the PR branch locally:

   ```bash
   gh repo clone <owner>/<repo> /tmp/try && cd /tmp/try && gh pr checkout <n>
   npm ci && npx vitest run      # example: should fail on this branch
   ```

   Put the install inside `test_cmd`, not `setup_cmd`, so every test run picks up the agent's dependency change. Keep it under 600 s.

3. Add an entry to `targets.json`:

   ```json
   {
     "pr_url": "https://github.com/<owner>/<repo>/pull/<n>",
     "test_cmd": "npm ci && npx vitest run",
     "fork": "<you>/<repo>"
   }
   ```

   Add `"setup_cmd": "..."` only for one-time setup that the agent's change can't affect.

## Verification

```bash
uv run python -m kedge run https://github.com/<owner>/<repo>/pull/<n>
```

The second log line should give a real count, for example `🧪 base branch has 240 tests`. `unknown` means Kedge couldn't parse the base branch's test output.

## Troubleshooting

| Error | Fix |
|---|---|
| `error: PR not in targets.json allowlist` | The `pr_url` must match exactly, with no trailing slash or `/files`. |
| `error: expected https://github.com/<owner>/<repo>/pull/<n>` | Use the PR URL, not a branch or compare URL. |
| `🧪 base branch has unknown tests` | The test command fails on the base branch too, or prints no summary. Fix `test_cmd` first. |
| Push fails at the end of a green run | `gh` has no push access to `fork`. |

## Related

- [CLI reference: targets.json](../reference/cli.md#targetsjson)
