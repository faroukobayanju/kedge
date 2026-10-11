// Real, public run data from runs/ (kedge-demo#1, packaging 21.3 -> 24.2, --storm delete-test). No keys, no private accounts.
export type Frame = { kind: "plan" | "step" | "final"; fs: string; fa: string; lost?: boolean; won?: boolean; x?: boolean; label: string };
export const NOGUARD: Frame[] = [
  { kind: "plan", fs: "Plan", fa: "make the failing tests pass", label: "plan" },
  { kind: "step", fs: "2/5", fa: "Edited tests/test_sorting.py, versions.py", lost: true, label: "step 1" },
  { kind: "final", fs: "Shipped", fa: "PR opened without 3 tests. Nobody checked.", lost: true, x: true, label: "final" },
];
export const KEDGE: Frame[] = [
  { kind: "plan", fs: "Plan", fa: "Remove LegacyVersion from the import in versions.py, keeping Version and parse.", label: "plan" },
  { kind: "step", fs: "2/5", fa: "Edited tests/test_sorting.py, versions.py", lost: true, x: true, label: "step 1" },
  { kind: "step", fs: "0/5", fa: "Edited versions.py", label: "step 2" },
  { kind: "step", fs: "5/5", fa: "Edited versions.py", label: "step 3" },
  { kind: "final", fs: "Green", fa: "All tests pass. Draft PR opened.", won: true, label: "final" },
];
export const SHA = "33a6358";
// ship's log lines exactly as `kedge run` prints them (kedge/shiplog.py)
export const SHIPLOG = [
  "⚓ kedge  dependabot/pip/packaging-24.2  ·  budget $0.50",
  "🧪 base branch has 5 tests",
  "🌊 DRIFT  out_of_plan · tests 2/2 · tests/test_sorting.py, versions.py",
  "⚓ hauled back to 33a6358",
  "⛵ step 2  edited 1 files · tests 0/5",
  "⛵ step 3  edited 1 files · tests 5/5",
  "🏁 green · $0.00 · github.com/faroukobayanju/kedge-demo/pull/11",
];
export const CMD = "kedge run https://github.com/faroukobayanju/kedge-demo/pull/1 --storm delete-test";

// neatlogs: `neatlogs traces spans list dd17b437ccb5defbbd23974697cc7c48` (run 20261010-2159-1d8a, guard on).
// Offsets are span start minus the WORKFLOW span start; tokens are the kedge.tokens attribute on each step span.
export const TRACE = {
  id: "dd17b437ccb5defbbd23974697cc7c48",
  root: "kedge run 20261010-2159-1d8a",
  total: 161.4,
  steps: [[20.9, 23372], [51.6, 50428], [73.2, 24329], [99.0, 23813], [125.5, 24790], [161.4, 31740]] as [number, number][],
};
// Entire: `entire checkpoint explain 01M4M45DRP0JWA8GR1NPWGTT84` (run 20261011-0035-3b13, kedge-demo#1).
// Author, session and local paths are left out on purpose.
export const ENTIRE_CMD = "entire checkpoint explain 01M4M45DRP0JWA8GR1NPWGTT84";
export const ENTIRE = [
  "● Checkpoint 01M4M45DRP0JWA8GR1NPWGTT84",
  "  created  2026-10-11 00:00:24",
  "  tokens   97k",
  "  commits  bdfc56c kedge 20261011-0035-3b13 step 5",
  "────────────────────────────────────────────",
  "## Intent",
  "\"You are fixing a failing dependency-bump PR.",
  " PR: build(deps): bump packaging from 21.3 to 24.2",
  "## Files (1)",
  "- versions.py",
];
// cfo.ai unit economics (docs/business-plan.md, exported from cfo.ai). $0.45 is a modelled token price, not a bill.
export const UNIT = { price: "$10.00", model: "−$0.45", pay: "−$0.30", infra: "$0.00", margin: 92.5 };
// Real batch over public failing Dependabot/Renovate PRs (runs/batch-*.jsonl). Repo names only, no owners.
export const BATCH: Frame[] = [
  { kind: "step", fs: "Green", fa: "cimd #7", won: true, label: "6.3 min" },
  { kind: "step", fs: "Green", fa: "create-pull-request #402", won: true, label: "3.4 min" },
  { kind: "step", fs: "Gave up", fa: "prompt-optimizer #4", label: "3.4 min" },
  { kind: "step", fs: "Gave up", fa: "crypto-idea #125", label: "19.2 min" },
  { kind: "step", fs: "Green", fa: "numpy-flint-arb #179", won: true, label: "5.2 min" },
  { kind: "step", fs: "Gave up", fa: "finrem-citizen-ui #608", label: "31.1 min" },
  { kind: "step", fs: "Timeout", fa: "periplus #18 (tests ran 10 min)", label: "10.2 min" },
  { kind: "step", fs: "Gave up", fa: "dbt-snowflake-iceberg-sync #83", label: "33.7 min" },
  { kind: "step", fs: "Green", fa: "kokoro-extension #31", won: true, label: "28.0 min" },
];
