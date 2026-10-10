import html
import json
import os
from string import Template

HTML = Template("""<!doctype html><meta charset="utf-8"><title>Kedge run $run_id</title>
<style>body{font:14px system-ui;margin:2rem;max-width:960px}td,th{padding:4px 8px;border-bottom:1px solid #ddd}
.drift{background:#fde8e8}</style>
<h1>Kedge run $run_id: $status</h1>
<p>CI: $ci · PR: <a href="$pr_url">$pr_url</a> · cost $$$cost · rollbacks $rollbacks · <a href="$trace_url">neatlogs trace</a></p>
$voyage
<table><tr><th>Step</th><th>Action</th><th>Files</th><th>Tests</th><th>Cost</th><th>Drift</th></tr>$rows</table>
<h2>Entire checkpoint</h2><pre>$entire</pre>""")


def _status(r):
    return f"{r['drift']} (rolled back)" if r.get("rolled_back") else (r.get("drift") or "ok")


def voyage_svg(recs) -> str:
    w = max(1, len(recs)) * 90 + 60
    parts = [f'<svg viewBox="0 0 {w} 120" width="100%" role="img" aria-label="voyage chart">',
             f'<line x1="20" y1="60" x2="{w - 20}" y2="60" stroke="#8aa" stroke-dasharray="4 4"/>']
    for i, r in enumerate(recs):
        x = 60 + i * 90
        if r.get("drift"):
            parts.append(f'<text class="wave" x="{x}" y="50" text-anchor="middle" font-size="28">🌊</text>')
            if r.get("rolled_back"):
                parts.append(f'<text class="anchor" x="{x}" y="95" text-anchor="middle" font-size="22">⚓</text>')
        elif r["action"] == "replan":
            parts.append(f'<text class="compass" x="{x}" y="70" text-anchor="middle" font-size="26">🧭</text>')
        else:
            parts.append(f'<text class="sail" x="{x}" y="70" text-anchor="middle" font-size="26">⛵</text>')
        parts.append(f'<text x="{x}" y="115" text-anchor="middle" font-size="11" fill="#567">'
                     f'{r["action"]} {r.get("step", "")}</text>')
    parts.append(f'<text x="{w - 30}" y="70" text-anchor="middle" font-size="26">🏁</text></svg>')
    return "".join(parts)


def render(run_dir, meta) -> tuple[str, str]:
    path = os.path.join(run_dir, "steps.jsonl")
    recs = [json.loads(line) for line in open(path) if line.strip()] if os.path.exists(path) else []
    rows = "".join(
        f'<tr class="{"drift" if r.get("drift") else ""}"><td>{r["step"]}</td><td>{r["action"]}</td>'
        f'<td>{html.escape(", ".join(r["files_changed"]))}</td><td>{r["tests_passed"]}/{r["tests_total"]}</td>'
        f'<td>${r["cost_usd"]:.3f}</td><td>{_status(r)}</td></tr>' for r in recs)
    page = HTML.substitute(run_id=meta["run_id"], status=meta["status"], pr_url=meta["pr_url"],
                           cost=f'{meta["cost_usd_total"]:.3f}', rollbacks=meta["rollbacks"],
                           trace_url=meta["trace_url"], rows=rows, ci=meta.get("ci_status", "not run"), voyage=voyage_svg(recs), entire=html.escape(meta["entire_explain"]))
    md = [f"## Kedge run `{meta['run_id']}`: {meta['status']}",
          f"CI: {meta.get('ci_status', 'not run')} · Cost ${meta['cost_usd_total']:.3f} · rollbacks {meta['rollbacks']} · [neatlogs trace]({meta['trace_url']})", "",
          "| Step | Action | Files | Tests | Cost | Drift |", "|---|---|---|---|---|---|"]
    md += [f"| {r['step']} | {r['action']} | {', '.join(r['files_changed'])} | {r['tests_passed']}/{r['tests_total']} "
           f"| ${r['cost_usd']:.3f} | {_status(r).replace('(rolled back)', 'rolled back')} |" for r in recs]
    md += ["", "### Entire checkpoint", "```", meta["entire_explain"], "```"]
    hp, mp = os.path.join(run_dir, "report.html"), os.path.join(run_dir, "report.md")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(page)
    with open(mp, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    return hp, mp
