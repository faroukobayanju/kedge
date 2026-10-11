# How to use Claude Code or another model as the agent

Swap the worker agent: a different free OpenCode model, or headless Claude Code.

## Prerequisites

- For OpenCode models: the pinned OpenCode from `./scripts/setup-opencode.sh`
- For Claude Code: the `claude` CLI installed and logged in (`claude -p "hi"` works)

## Steps

- **A different OpenCode model:**

  ```bash
  KEDGE_MODEL=opencode/<model-id> uv run python -m kedge run <pr_url>
  ```

  List the models with `.tools/opencode/node_modules/.bin/opencode models`.

- **Claude or Nova through the neatHack LiteLLM endpoint** (OpenAI-compatible, `https://litellm.vision.aivar.app/v1`):

  ```bash
  echo 'LITELLM_API_KEY=<your key>' >> .env          # never commit .env
  KEDGE_MODEL=litellm/claude-sonnet-4.6 uv run python -m kedge run <pr_url>
  ```

  Models: `claude-sonnet-4.6`, `claude-haiku`, `claude-opus-4.6`, `nova-pro`, `nova-lite` (listed in `kedge/opencode.json`). OpenCode stays the agent, so Entire capture and step costs work the same way. Check spend with `curl -s https://litellm.vision.aivar.app/key/info -H "Authorization: Bearer $LITELLM_API_KEY"`.

- **Claude Code:**

  ```bash
  KEDGE_WORKER=claude uv run python -m kedge run <pr_url>
  ```

  Edits run `claude -p <prompt> --output-format json --permission-mode acceptEdits --max-turns 15`. Plans run with `--model haiku --max-turns 1`. Entire is enabled with `--agent claude-code`.

## Verification

The ship's log shows non-zero `cost_usd` per step with paid models. `result.json`'s `entire_explain` names the agent session.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Every step is `worker_error` with Claude | `claude -p` isn't logged in (`Invalid API key · Please run /login`). Run `claude` once and log in. |
| `💸 out of budget` early | Paid models cost real money. Raise `--budget` (default $0.50). |

## Related

- [CLI reference: environment](../reference/cli.md#environment)
