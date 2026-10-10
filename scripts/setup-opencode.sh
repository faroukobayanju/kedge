#!/usr/bin/env bash
# Install the OpenCode version whose plugin API matches Entire's generated plugin.
# OpenCode v2 rejects Entire's v1-style plugin ("Plugin must export a default definition"),
# so Entire never sees the session. Pin v1 locally; kedge puts it first on PATH.
set -euo pipefail
cd "$(dirname "$0")/.."
npm install --prefix .tools/opencode opencode-ai@1.18.35 --no-audit --no-fund
.tools/opencode/node_modules/.bin/opencode --version
