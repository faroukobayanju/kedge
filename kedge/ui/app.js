const $ = (s, el = document) => el.querySelector(s);
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const icon = (id) => `<svg aria-hidden="true"><use href="#i-${id}"/></svg>`;

const DRIFT = {
  tests_regressed: { call: "Disallowed: tests lost", why: "The agent's change reduced the passing or total test count. Usually a deleted or skipped test." },
  out_of_plan: { call: "Disallowed: off plan", why: "The agent edited files outside the plan's allowed list." },
  loop: { call: "Disallowed: repeat attempt", why: "The agent produced the same change Kedge had already rolled back." },
  verify_failed: { call: "Disallowed: not stable", why: "Tests passed once but failed or lost tests when Kedge ran them again." },
  over_budget: { call: "Stopped: out of budget", why: "The run hit its spend cap, so Kedge stopped calling the agent." },
};
const STATUS = {
  green: { cls: "green", text: "Green", cell: "green" },
  already_green: { cls: "neutral", text: "Already green", cell: "green" },
  gave_up: { cls: "open", text: "Gave up", cell: "struck" },
  running: { cls: "running", text: "Under review", cell: "live" },
};

let runs = [];
let selected = null;
let compare = false;
let picks = [];
let lastFingerprint = "";

const score = (r) => {
  const last = [...(r.steps || [])].reverse().find((s) => s.tests_total >= 0 && !s.rolled_back);
  return last ? `${last.tests_passed}/${last.tests_total}` : "–";
};
const prRef = (url) => {
  const m = /github\.com\/([^/]+\/[^/]+)\/pull\/(\d+)/.exec(url || "");
  return m ? `${m[1]}#${m[2]}` : url || "";
};
const lost = (r) => {
  const last = [...(r.steps || [])].reverse().find((s) => s.tests_total >= 0 && !s.rolled_back);
  return last && r.base_total > 0 && last.tests_total < r.base_total ? r.base_total - last.tests_total : 0;
};
const lostNote = (r) => (lost(r) ? `<span class="lost">${lost(r)} of ${r.base_total} tests missing vs base branch</span>` : "");
const st = (r) => STATUS[r.status] || { cls: "open", text: r.status, cell: "open" };
const traceId = (t) => (t && t !== "unavailable" ? t : null);

/* ---------- replay strip: one drawing, three scales ---------- */
function miniStrip(r) {
  const steps = (r.steps || []).filter((s) => s.action !== "replan");
  const w = 260, h = 14, n = Math.max(steps.length, 1), gap = 3, cw = (w - gap * (n - 1)) / n;
  const cells = steps.map((s, i) => {
    const x = i * (cw + gap);
    const fill = s.drift && s.drift !== "over_budget" ? "url(#hatch)" : s.false_claim ? "var(--yellow)" : "var(--green)";
    const op = s.drift ? 1 : s.tests_total > 0 ? 0.35 + 0.65 * (s.tests_passed / s.tests_total) : 0.35;
    return `<rect x="${x}" y="2" width="${cw}" height="${h - 4}" rx="2" fill="${fill}" opacity="${op}"/>`;
  });
  if (!steps.length) cells.push(`<rect x="0" y="6" width="${w}" height="2" fill="var(--line)"/>`);
  return `<svg class="run-strip" viewBox="0 0 ${w} ${h}" width="100%" height="${h}" preserveAspectRatio="none" aria-hidden="true">${cells.join("")}</svg>`;
}

function frames(r) {
  const out = [];
  const plan = r.plan || {};
  out.push(`<li class="frame plan"><div class="f-no">Kick-off</div><div class="f-score">Plan</div>
    <div class="f-act">${esc((plan.steps || [])[0] || plan.hypothesis || "Read the failing tests")}</div></li>`);
  let lastGood = 0;
  (r.steps || []).forEach((s, i) => {
    if (s.action === "replan") {
      out.push(`<li class="frame plan"><div class="f-no">Step ${s.step}</div><div class="f-score">Replan</div>
        <div class="f-act">Two drifts in a row, so Kedge asked for a different approach.</div></li>`);
      return;
    }
    const drift = s.drift && s.drift !== "over_budget";
    const pct = s.tests_total > 0 ? Math.round((100 * s.tests_passed) / s.tests_total) : 0;
    const files = (s.files_changed || []).length;
    const act = s.action === "worker_error" ? "Agent call failed or timed out" :
      files ? `Edited ${files} file${files > 1 ? "s" : ""}: ${esc(s.files_changed.slice(0, 2).join(", "))}` : "No files changed";
    const back = drift && s.rolled_back
      ? `<svg class="haul" viewBox="0 0 200 30" preserveAspectRatio="none" aria-hidden="true">
           <path d="M196 2 C 196 26, 6 26, 6 4" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="5 4"/>
           <path d="M1 10 6 2l5 8" fill="none" stroke="currentColor" stroke-width="2"/></svg>
         <div class="haul-label">Hauled back to ${esc((s.checkpoint_sha || "").slice(0, 7))}</div>`
      : "";
    out.push(`<li class="frame${drift ? " drift" : ""}" style="--i:${i}">
      ${drift ? `<div class="check">${icon("monitor")}Check: ${esc(DRIFT[s.drift]?.call.split(": ")[1] || s.drift)}</div>` : ""}
      ${s.false_claim ? `<div class="check lie">${icon("monitor")}Claim rejected</div>` : ""}
      <div class="f-no">Step ${s.step}</div>
      <div class="f-score">${s.tests_total >= 0 ? `${s.tests_passed}/${s.tests_total}` : "?"}</div>
      <div class="f-act">${act}</div>
      <div class="f-bar"><i style="width:${drift ? 100 : pct}%"></i></div>
      ${back}</li>`);
    if (!drift) lastGood = s.step;
  });
  if (r.status === "green") {
    out.push(`<li class="frame whistle"><div class="f-no">Full time</div><div class="f-score">Green</div>
      <div class="f-act">${r.draft_pr ? "Draft PR opened" : "All tests pass"}</div></li>`);
  } else if (r.status === "running") {
    out.push(`<li class="frame plan"><div class="f-no">Live</div><div class="f-score">…</div><div class="f-act">Kedge is reviewing the next step</div></li>`);
  }
  return `<ol class="replay" aria-label="Run replay">${out.join("")}</ol>`;
}

function rulings(r) {
  const items = [];
  (r.steps || []).forEach((s) => {
    if (s.drift) {
      const d = DRIFT[s.drift] || { call: s.drift, why: "" };
      items.push(`<li class="ruling"><h3><span class="cell struck"></span>Step ${s.step} · ${esc(d.call)}</h3>
        <p>${esc(d.why)} Files: ${(s.files_changed || []).map((f) => `<code>${esc(f)}</code>`).join(" ") || "none"} · tests ${s.tests_passed}/${s.tests_total}.
        ${s.rolled_back ? `Kedge rolled back to <code>${esc((s.checkpoint_sha || "").slice(0, 7))}</code> and retried with a recovery note.` : ""}</p></li>`);
    }
    if (s.false_claim) {
      items.push(`<li class="ruling"><h3><span class="cell live"></span>Step ${s.step} · Claim rejected</h3>
        <p>The agent said “${esc(s.claim)}”. Tests said ${s.tests_passed}/${s.tests_total}. Kedge believed the tests.</p></li>`);
    }
  });
  return items.length ? `<ul class="rulings">${items.join("")}</ul>`
    : `<p class="clean">No checks in this run. Every step kept the tests and stayed on the plan.</p>`;
}

function planPanel(r) {
  const p = r.plan || {};
  return `<section class="plan" aria-label="Plan">
    <p>${esc(p.hypothesis || "No plan recorded.")}</p>
    <h3>Allowed files</h3><div class="files">${(p.allowed_files || []).map((f) => `<code>${esc(f)}</code>`).join("")}</div>
    ${(p.steps || []).length ? `<h3>Steps</h3><ol>${p.steps.map((x) => `<li>${esc(x)}</li>`).join("")}</ol>` : ""}
  </section>`;
}

function actions(r) {
  const t = traceId(r.trace);
  return `<div class="actions">
    ${r.draft_pr ? `<a class="btn primary" href="${esc(r.draft_pr)}" target="_blank" rel="noopener">${icon("pr")}Open draft PR</a>` : ""}
    ${t ? `<button class="btn ghost" type="button" data-copy="${esc(t)}">${icon("trace")}Trace ${esc(t.slice(0, 8))}</button>` : ""}
    <a class="btn ghost" href="${esc(r.pr_url)}" target="_blank" rel="noopener">${icon("flag")}Source PR</a>
  </div>`;
}

function stageRun(r) {
  const s = st(r);
  const facts = [
    `<b>${r.steps.filter((x) => x.action !== "replan").length}</b> steps`,
    `<b>${r.drifts}</b> checks`,
    `<b>${r.rollbacks}</b> rollbacks`,
    r.false_claims ? `<b>${r.false_claims}</b> false claims` : "",
    `<b>$${Number(r.cost_usd_total || 0).toFixed(2)}</b>`,
    r.ci_status ? `CI <b>${esc(r.ci_status)}</b>` : "",
  ].filter(Boolean).join(" · ");
  $("#stage").innerHTML = `<article class="match">
    <header class="match-head">
      <div class="match-no" aria-hidden="true">${String(r.no).padStart(2, "0")}</div>
      <div class="match-title">
        <h1>${esc(r.title || prRef(r.pr_url))}</h1>
        <p><a href="${esc(r.pr_url)}" target="_blank" rel="noopener">${esc(prRef(r.pr_url))}</a>
          ${r.guard === false ? '<span class="tag warn">No guard</span>' : ""}
          ${r.storm ? `<span class="tag storm">Storm: ${esc(r.storm)}</span>` : ""}</p>
      </div>
      <div class="scoreline"><span class="num">${score(r)}</span><span class="lbl">Tests passing</span>${lostNote(r)}</div>
    </header>
    <div class="ruling-bar"><span class="verdict ${s.cls}">${s.text}</span><span class="facts">${facts}</span>${actions(r)}</div>
    <section class="replay-wrap" aria-label="Replay">
      <div class="section-h"><h2>Replay</h2><span>Every step Kedge checked, left to right</span></div>
      ${frames(r)}
    </section>
    <div class="two">
      <section><div class="section-h"><h2>Rulings</h2></div>${rulings(r)}</section>
      <section><div class="section-h"><h2>Plan</h2></div>${planPanel(r)}</section>
    </div>
    ${r.entire_explain && !r.entire_explain.startsWith("(no") ? `<details class="checkpoint"><summary>Entire checkpoint</summary><pre>${esc(r.entire_explain)}</pre></details>` : ""}
  </article>`;
}

function stageCompare() {
  if (picks.length < 2) {
    $("#stage").innerHTML = `<p class="hint">Pick two runs from the fixtures to put them side by side, for example the same PR with <b>--no-guard</b> and with Kedge.</p>`;
    return;
  }
  const side = (r, label) => {
    const s = st(r);
    return `<section class="side"><h2>${label}</h2>
      <div class="sub">No. ${String(r.no).padStart(2, "0")} · ${esc(prRef(r.pr_url))}${r.storm ? ` · storm ${esc(r.storm)}` : ""}</div>
      <div class="big">${score(r)}</div>${lostNote(r)}<span class="verdict ${s.cls}">${s.text}</span>
      <div class="stats"><span><b>${r.drifts}</b> checks caught · <b>${r.rollbacks}</b> rollbacks</span>
        <span><b>${r.false_claims}</b> false claims</span><span><b>$${Number(r.cost_usd_total || 0).toFixed(2)}</b> spent</span></div>
      ${miniStrip(r)}</section>`;
  };
  const [a, b] = picks.map((id) => runs.find((r) => r.run_id === id)).filter(Boolean);
  if (!a || !b) return;
  const label = (r) => (r.guard === false ? "No guard" : "Kedge");
  $("#stage").innerHTML = `<div class="versus">${side(a, label(a))}<div class="vs">vs</div>${side(b, label(b))}</div>
    <div class="replay-wrap"><div class="section-h"><h2>${label(a)}</h2></div>${frames(a)}</div>
    <div class="replay-wrap"><div class="section-h"><h2>${label(b)}</h2></div>${frames(b)}</div>`;
}

function renderTally() {
  const done = runs.filter((r) => r.status !== "running");
  const green = runs.filter((r) => r.status === "green").length;
  const checks = runs.reduce((n, r) => n + r.drifts, 0);
  const lies = runs.reduce((n, r) => n + r.false_claims, 0);
  const spend = runs.reduce((n, r) => n + Number(r.cost_usd_total || 0), 0);
  $("#tally").innerHTML = `
    <div><dt>Green</dt><dd class="g">${green}/${done.length}</dd></div>
    <div><dt>Checks</dt><dd class="r">${checks}</dd></div>
    <div><dt>False claims</dt><dd>${lies}</dd></div>
    <div><dt>Spend</dt><dd>$${spend.toFixed(2)}</dd></div>`;
}

function renderList() {
  const f = $("#filter").value;
  const shown = runs.filter((r) => f === "all" || (f === "checks" && (r.drifts || r.false_claims)) ||
    (f === "green" && r.status === "green") || (f === "open" && r.status !== "green"));
  $("#runList").innerHTML = shown.map((r) => {
    const s = st(r);
    const pick = picks.indexOf(r.run_id);
    return `<li><button class="run" type="button" data-id="${esc(r.run_id)}"
        aria-current="${!compare && r.run_id === selected}" ${compare && pick >= 0 ? `data-pick="${"ab"[pick]}"` : ""}>
      <span class="run-no">${String(r.no).padStart(2, "0")}</span>
      <span class="run-body"><span class="run-title">${esc(r.title || prRef(r.pr_url))}</span>
        <span class="run-sub"><span class="cell ${s.cell}"></span>${esc(s.text)} · ${esc(prRef(r.pr_url))}
          ${r.guard === false ? '<span class="tag warn">No guard</span>' : ""}${r.storm ? `<span class="tag storm">${esc(r.storm)}</span>` : ""}</span></span>
      <span class="run-score">${score(r)}</span>
      ${miniStrip(r)}
    </button></li>`;
  }).join("") || `<li class="clean">No runs match this filter.</li>`;
}

function render() {
  renderTally();
  renderList();
  if (!runs.length) { $("#stage").replaceChildren($("#emptyTpl").content.cloneNode(true)); return; }
  if (compare) return stageCompare();
  const r = runs.find((x) => x.run_id === selected) || runs[0];
  selected = r.run_id;
  stageRun(r);
}

async function load() {
  try {
    const res = await fetch("/api/runs", { cache: "no-store" });
    const data = await res.json();
    const ordered = [...data].sort((a, b) => a.run_id.localeCompare(b.run_id));
    ordered.forEach((r, i) => (r.no = i + 1));
    const fp = JSON.stringify(data.map((r) => [r.run_id, r.status, r.steps.length]));
    if (fp === lastFingerprint) return;  // keep the replay animation from restarting
    lastFingerprint = fp;
    runs = data;
    render();
  } catch {
    $("#stage").innerHTML = `<p class="hint">Can't reach the Kedge server. Is <code>kedge ui</code> still running?</p>`;
  }
}

$("#runList").addEventListener("click", (e) => {
  const b = e.target.closest(".run");
  if (!b) return;
  const id = b.dataset.id;
  if (compare) {
    picks = picks.includes(id) ? picks.filter((x) => x !== id) : [...picks, id].slice(-2);
  } else {
    selected = id;
    history.replaceState(null, "", `#${id}`);
  }
  render();
  $("#stage").focus({ preventScroll: true });
});
$("#filter").addEventListener("change", renderList);
$("#compareBtn").addEventListener("click", (e) => {
  compare = !compare;
  e.currentTarget.setAttribute("aria-pressed", String(compare));
  render();
});
$("#stage").addEventListener("click", async (e) => {
  const b = e.target.closest("[data-copy]");
  if (!b) return;
  try { await navigator.clipboard.writeText(b.dataset.copy); b.lastChild.textContent = "Trace ID copied"; } catch { /* clipboard blocked */ }
});

selected = location.hash.slice(1) || null;
load();
setInterval(load, 4000);
