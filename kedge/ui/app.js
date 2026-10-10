const $ = (s, el = document) => el.querySelector(s);
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const inline = (t) => esc(t).replace(/`([^`]+)`/g, "<code>$1</code>");
const plural = (n, w) => `${n} ${w}${n === 1 ? "" : "s"}`;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms / speed));
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;

const DRIFT = {
  tests_regressed: ["tests lost", "The agent's change dropped passing or total tests."],
  out_of_plan: ["off the plan", "The agent touched files outside the plan."],
  loop: ["same mistake again", "The agent repeated a change Kedge already threw out."],
  verify_failed: ["didn't hold", "Tests passed once, then failed on the re-run."],
  over_budget: ["out of budget", "The run hit its spend cap."],
};

let runs = [];
let current = null;
let race = false;
let picks = [];
let speed = 1;
let playToken = 0;
let fingerprint = "";

/* ---------- facts from a run ---------- */
const lastGood = (r) => [...(r.steps || [])].reverse().find((s) => s.tests_total >= 0 && !s.rolled_back);
const denom = (r, total) => Math.max(total, r.base_total || 0);
const lost = (r) => {
  const l = lastGood(r);
  return l && r.base_total > l.tests_total ? r.base_total - l.tests_total : 0;
};
const verdict = (r) => {
  if (r.status === "green" && lost(r)) return { key: "short", word: "Shipped short", cls: "v-short" };
  if (r.status === "green") return { key: "keep", word: "Kept", cls: "v-keep" };
  if (r.status === "already_green") return { key: "flat", word: "Already green", cls: "v-flat" };
  if (r.status === "running") return { key: "live", word: "Developing", cls: "v-live" };
  return { key: "out", word: "Gave up", cls: "v-out" };
};
const score = (r) => {
  const l = lastGood(r);
  return l ? `${l.tests_passed}/${denom(r, l.tests_total)}` : "–";
};
const prRef = (u) => { const m = /github\.com\/([^/]+\/[^/]+)\/pull\/(\d+)/.exec(u || ""); return m ? `${m[1]}#${m[2]}` : u || ""; };
const checkpointId = (r) => [...(r.steps || [])].reverse().map((s) => s.entire_checkpoint).find(Boolean) || null;
const traceId = (r) => (r.trace && r.trace !== "unavailable" ? r.trace : null);
const no = (r) => String(r.no).padStart(2, "0");

function framesOf(r) {
  const f = [{ kind: "plan" }];
  (r.steps || []).forEach((s) => f.push({ kind: s.action === "replan" ? "replan" : "step", s }));
  const v = verdict(r);
  if (v.key !== "live") f.push({ kind: "final", v });
  return f;
}

/* ---------- frame + mark drawing ---------- */
function frameHTML(r, f, i) {
  if (f.kind === "plan") {
    const p = r.plan || {};
    return `<button class="frame plan" data-i="${i}" type="button"><span class="fk">Kick-off · plan</span>
      <span class="fs">Plan</span><span class="fa">${esc((p.steps || [])[0] || p.hypothesis || "Read the failing tests")}</span></button>`;
  }
  if (f.kind === "replan") {
    return `<button class="frame plan" data-i="${i}" type="button"><span class="fk">Step ${f.s.step} · replan</span>
      <span class="fs">Replan</span><span class="fa">Two strikes, so Kedge asked for a new approach.</span></button>`;
  }
  if (f.kind === "final") {
    const L = lost(r);
    const [fs, fa, cls] = {
      keep: ["Green", r.draft_pr ? "All tests pass. Draft PR opened." : "All tests pass.", ""],
      short: ["Shipped", `PR opened without ${plural(L, "test")}. Nobody checked.`, " lost"],
      flat: ["Green", "Tests already passed on arrival.", ""],
      out: ["Gave up", "No safe fix found inside the budget.", " lost"],
    }[f.v.key];
    return `<button class="frame final${cls}" data-i="${i}" type="button"><span class="fk">Full time</span>
      <span class="fs">${fs}</span><span class="fa">${esc(fa)}</span></button>`;
  }
  const s = f.s;
  const d = denom(r, s.tests_total);
  const files = s.files_changed || [];
  const pct = d > 0 && s.tests_total >= 0 ? Math.round((100 * s.tests_passed) / d) : 0;
  const act = s.action === "worker_error" ? "The agent didn't answer in time."
    : files.length ? `Edited ${files.slice(0, 2).join(", ")}${files.length > 2 ? ` +${files.length - 2}` : ""}` : "Changed nothing.";
  const isLost = s.tests_total >= 0 && d > s.tests_total && s.tests_passed > 0;
  return `<button class="frame${isLost ? " lost" : ""}" data-i="${i}" type="button"><span class="fk">Step ${s.step}</span>
    <span class="fs">${s.tests_total >= 0 ? `${s.tests_passed}/${d}` : "?"}</span><span class="fa">${esc(act)}</span>
    <span class="fb"><i style="width:${pct}%"></i></span></button>`;
}

const W = () => parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--fw")) || 236;
const H = 178;

function svgFor(frameEl) {
  let svg = frameEl.querySelector("svg.marks");
  if (!svg) {
    svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("class", "marks");
    svg.setAttribute("viewBox", `0 0 ${W() + 36} ${H + 36}`);
    svg.setAttribute("aria-hidden", "true");
    frameEl.append(svg);
  }
  return svg;
}
function stroke(frameEl, d, cls, dur, instant) {
  const svg = svgFor(frameEl);
  const p = document.createElementNS("http://www.w3.org/2000/svg", "path");
  p.setAttribute("d", d);
  p.setAttribute("class", `${cls} draw`);
  svg.append(p);
  const len = p.getTotalLength();
  p.style.setProperty("--len", len);
  p.style.setProperty("--dur", `${instant ? 1 : dur / speed}ms`);
  requestAnimationFrame(() => p.classList.add("on"));
}
// hand-drawn marks: a little wobble so they read as a person's stroke, not a vector
function xMark(el, instant) {
  const w = W() + 36, h = H + 36;
  stroke(el, `M ${w * .14} ${h * .16} Q ${w * .48} ${h * .52} ${w * .88} ${h * .86}`, "red", 420, instant);
  setTimeout(() => stroke(el, `M ${w * .86} ${h * .14} Q ${w * .55} ${h * .45} ${w * .12} ${h * .88}`, "red", 420, instant), instant ? 0 : 380 / speed);
}
function ring(el, cls = "red", instant) {
  const w = W() + 36, h = H + 36, cx = w / 2, cy = h / 2, rx = w * .5, ry = h * .5;
  stroke(el, `M ${cx - rx * .2} ${cy - ry * .98}
    C ${cx + rx * .7} ${cy - ry * 1.08}, ${cx + rx * 1.05} ${cy - ry * .2}, ${cx + rx * .96} ${cy + ry * .3}
    C ${cx + rx * .86} ${cy + ry * .98}, ${cx - rx * .5} ${cy + ry * 1.06}, ${cx - rx * .95} ${cy + ry * .4}
    C ${cx - rx * 1.08} ${cy - ry * .3}, ${cx - rx * .6} ${cy - ry * 1.02}, ${cx + rx * .15} ${cy - ry * .9}`, cls, 700, instant);
}
function underline(el, cls = "yel", instant) {
  const w = W() + 36, h = H + 36;
  stroke(el, `M ${w * .12} ${h * .48} Q ${w * .45} ${h * .44} ${w * .78} ${h * .5}`, cls, 380, instant);
}
function note(el, text, where, cls = "", instant) {
  const n = document.createElement("span");
  n.className = `note ${where} ${cls}`;
  n.innerHTML = text;
  el.append(n);
  if (instant) n.classList.add("on");
  else requestAnimationFrame(() => n.classList.add("on"));
}

/* ---------- the reel: one strip moving with spring physics ---------- */
class Reel {
  constructor(lane) {
    this.lane = lane;
    this.vp = $(".viewport", lane);
    this.strip = $(".strip", lane);
    this.x = 0; this.v = 0; this.target = 0; this.raf = 0; this.done = null;
  }
  // lay the whole sheet down: centered when it fits, otherwise ending on the last frame
  whole(n) {
    const sw = this.strip.scrollWidth, vw = this.vp.clientWidth;
    return sw <= vw - 40 ? (vw - sw) / 2 : this.center(n - 1);
  }
  toX(x, opts) { const i = this; i.target = x; return this._run(opts); }
  center(i) {
    const fw = W(), gap = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--fgap")) || 22;
    return this.vp.clientWidth / 2 - (gap + i * (fw + gap) + fw / 2);
  }
  set(x) { this.x = x; this.v = 0; this.paint(); }
  paint() {
    const blur = Math.min(Math.abs(this.v) / 700, 5);
    this.strip.style.transform = `translate3d(${this.x}px,0,0)`;
    this.strip.style.filter = blur > .3 ? `blur(${blur.toFixed(2)}px)` : "";
  }
  // a reel has mass: stiff spring, light damping, so a rewind overshoots and settles
  to(i, opts) { this.target = this.center(i); return this._run(opts); }
  _run({ stiff = 70, damp = 11 } = {}) {
    if (reduce) { this.set(this.target); return Promise.resolve(); }
    cancelAnimationFrame(this.raf);
    return new Promise((res) => {
      let last = performance.now();
      const tick = (now) => {
        const dt = Math.min((now - last) / 1000, 0.032) * speed; last = now;
        const a = stiff * (this.target - this.x) - damp * this.v;
        this.v += a * dt; this.x += this.v * dt;
        this.paint();
        if (Math.abs(this.v) < 4 && Math.abs(this.target - this.x) < .5) { this.set(this.target); res(); return; }
        this.raf = requestAnimationFrame(tick);
      };
      this.raf = requestAnimationFrame(tick);
    });
  }
}

function laneHTML(r, label) {
  const fr = framesOf(r);
  const fw = W(), gap = 22;
  const edges = fr.map((_, i) => `<span class="edge" style="left:${gap + i * (fw + gap)}px">KEDGE ${no(r)} ▸ ${i + 1}${i === fr.length - 1 ? "A" : ""}</span>`).join("");
  return `<div class="lane" data-run="${esc(r.run_id)}">
    ${label ? `<div class="lane-tag"><b>${label}</b> · No. ${no(r)}</div>` : ""}
    <div class="viewport"><div class="gate"></div>
      <div class="strip">${fr.map((f, i) => frameHTML(r, f, i)).join("")}${edges}</div>
    </div></div>`;
}

function printHTML(r, label) {
  const v = verdict(r);
  const l = lastGood(r);
  const big = l ? `${l.tests_passed}/${denom(r, l.tests_total)}` : "–";
  const L = lost(r);
  const why = {
    keep: `${plural(r.drifts, "cheat")} caught, ${plural(r.rollbacks, "rewind")}, every test kept.`,
    short: `${plural(L, "test")} vanished and the PR shipped anyway. No one was checking.`,
    flat: "Nothing to fix: the tests already passed.",
    out: `Kedge refused every unsafe change: ${plural(r.drifts, "cheat")} caught.`,
    live: "Still developing.",
  }[v.key];
  const sign = { keep: "Kedge ✓", short: "unchecked", out: "Kedge: no safe fix", flat: "", live: "" }[v.key];
  return `<article class="print ${v.key}" data-run="${esc(r.run_id)}">
    <div class="img"><span class="big" data-to="${l ? l.tests_passed : 0}" data-of="${l ? denom(r, l.tests_total) : 0}">${big}</span>
      <span class="word">${esc(v.word)}</span><span class="why">${esc(why)}</span></div>
    <div class="cap"><span class="who">${label ? esc(label) + " · " : ""}No. ${no(r)} · ${esc(prRef(r.pr_url))}</span>
      ${r.draft_pr ? `<a class="open" href="${esc(r.draft_pr)}" target="_blank" rel="noopener"><svg aria-hidden="true"><use href="#i-pr"/></svg>Open PR</a>` : ""}
      ${sign ? `<span class="sign${v.key === "keep" ? " ok" : ""}">${esc(sign)}</span>` : ""}</div>
  </article>`;
}

/* ---------- the performance ---------- */
async function perform(reel, r, token, instant) {
  const fr = framesOf(r);
  const els = [...reel.strip.querySelectorAll(".frame")];
  const alive = () => token === playToken;
  const dev = (i) => els[i].classList.add("dev");
  if (instant) {
    els.forEach((e) => e.classList.add("dev"));
  } else {
    reel.set(reel.vp.clientWidth + 60);
    await reel.to(0, { stiff: 40, damp: 10 }); if (!alive()) return;
    dev(0); await sleep(650);
  }
  for (let i = 1; i < fr.length; i++) {
    const f = fr[i];
    if (!instant) { await reel.to(i); if (!alive()) return; dev(i); await sleep(420); }
    if (f.kind === "step") {
      const s = f.s;
      if (s.false_claim) {
        underline(els[i], "yel", instant);
        note(els[i], `agent: “${esc(s.claim)}”<br>tests: ${s.tests_passed}/${denom(r, s.tests_total)}`, "up", "yel", instant);
        if (!instant) await sleep(1100);
      }
      if (s.drift && s.drift !== "over_budget") {
        xMark(els[i], instant);
        const [what] = DRIFT[s.drift] || [s.drift];
        note(els[i], `✗ ${what}<br><small>${esc((s.files_changed || []).slice(0, 2).join(", "))}</small>`, "down", "", instant);
        if (!instant) await sleep(1300);
        if (s.rolled_back) {
          let cp = 0;
          for (let j = i - 1; j > 0; j--) if (fr[j].kind === "step" && !fr[j].s.drift) { cp = j; break; }
          if (!instant) {
            await reel.to(cp, { stiff: 34, damp: 7 }); if (!alive()) return;   // the rewind
          }
          if (!els[cp].querySelector(".note.up")) {
            ring(els[cp], "red", instant);
            note(els[cp], `↺ hauled back to <span class="sha">${esc((s.checkpoint_sha || "").slice(0, 7))}</span>`, "up", "", instant);
          }
          if (!instant) await sleep(1200);
        }
      }
    }
    if (f.kind === "final") {
      if (f.v.key === "keep" || f.v.key === "flat") { ring(els[i], "red", instant); note(els[i], "keeper", "up", "", instant); }
      if (f.v.key === "short") { xMark(els[i], instant); note(els[i], `✗ ${plural(lost(r), "test")} missing, shipped anyway`, "down", "", instant); }
      if (!instant) await sleep(900);
    }
  }
  if (instant) reel.set(reel.whole(fr.length));
  else if (alive()) await reel.toX(reel.whole(fr.length), { stiff: 26, damp: 9 });
}

function countUp(el) {
  const to = +el.dataset.to, of = +el.dataset.of;
  if (reduce || !of) return;
  const t0 = performance.now(), dur = 900 / speed;
  const tick = (now) => {
    const k = Math.min((now - t0) / dur, 1), e = 1 - Math.pow(1 - k, 3);
    el.textContent = `${Math.round(to * e)}/${of}`;
    if (k < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

async function play(instant = false) {
  const token = ++playToken;
  const chosen = race ? picks.map((id) => runs.find((r) => r.run_id === id)).filter(Boolean) : [current].filter(Boolean);
  if (!chosen.length) return;
  $$(".print").forEach((p) => p.classList.remove("on"));
  const reels = [...document.querySelectorAll(".lane")].map((l) => new Reel(l));
  await Promise.all(reels.map((reel, k) => perform(reel, chosen[k], token, instant || reduce)));
  if (token !== playToken) return;
  document.querySelectorAll(".print").forEach((p, k) => setTimeout(() => {
    p.classList.add("on"); countUp($(".big", p));
  }, instant ? 0 : k * 450));
}
const $$ = (s) => [...document.querySelectorAll(s)];

/* ---------- layout ---------- */
function renderBench() {
  const bench = $("#bench");
  if (!runs.length) { bench.replaceChildren($("#emptyTpl").content.cloneNode(true)); $("#envelope").innerHTML = ""; return; }
  if (race) {
    const [a, b] = picks.map((id) => runs.find((r) => r.run_id === id));
    if (!a || !b) {
      bench.innerHTML = `<div class="empty"><p class="mark-note big">Pick two sheets to race.</p>
        <p>The same PR with <code>--no-guard</code> and with Kedge makes the point.</p></div>`;
      $("#envelope").innerHTML = "";
      return;
    }
    const lbl = (r) => (r.guard === false ? "No guard" : "Kedge");
    bench.innerHTML = `<div class="reel-title"><span class="no">vs</span><h1>${esc(a.title || prRef(a.pr_url))}</h1>
      <span class="src">${esc(prRef(a.pr_url))}${a.storm ? `<span class="storm">sabotage: ${esc(a.storm)}</span>` : ""}</span></div>
      ${laneHTML(a, lbl(a))}${laneHTML(b, lbl(b))}<div class="prints">${printHTML(a, lbl(a))}${printHTML(b, lbl(b))}</div>`;
    $("#envelope").innerHTML = "";
    return;
  }
  const r = current;
  bench.innerHTML = `<div class="reel-title"><span class="no">${no(r)}</span><h1>${esc(r.title || prRef(r.pr_url))}</h1>
    <span class="src"><a href="${esc(r.pr_url)}" target="_blank" rel="noopener">${esc(prRef(r.pr_url))}</a>
      ${r.guard === false ? '<span class="storm">no guard</span>' : ""}${r.storm ? `<span class="storm">sabotage: ${esc(r.storm)}</span>` : ""}</span></div>
    ${laneHTML(r)}<div class="prints">${printHTML(r)}</div>`;
  renderEnvelope(r);
}

function renderEnvelope(r) {
  const items = [];
  (r.steps || []).forEach((s) => {
    if (s.drift) {
      const [what, why] = DRIFT[s.drift] || [s.drift, ""];
      items.push(`<li><h3>Step ${s.step}: ${esc(what)}</h3><p>${esc(why)} Files ${(s.files_changed || []).map((f) => `<code>${esc(f)}</code>`).join(" ") || "none"},
        tests ${s.tests_passed}/${denom(r, s.tests_total)}.${s.rolled_back ? ` Rolled back to <code>${esc((s.checkpoint_sha || "").slice(0, 7))}</code> and retried with a recovery note.` : ""}</p></li>`);
    }
    if (s.false_claim) items.push(`<li><h3 class="yel">Step ${s.step}: claim overruled</h3><p>The agent said “${esc(s.claim)}”. The tests said ${s.tests_passed}/${denom(r, s.tests_total)}.</p></li>`);
  });
  if (!items.length) items.push(`<li><h3 class="ok">No cheats on this sheet</h3><p>Every step kept the tests and stayed on the plan.</p></li>`);
  const p = r.plan || {};
  const t = traceId(r), cp = checkpointId(r);
  const ci = r.ci_status && r.ci_status !== "not run" ? r.ci_status : null;
  $("#envelope").innerHTML = `<section><h2>Editor's notes</h2><ul class="log">${items.join("")}</ul>
      <div class="stamps">
        ${r.draft_pr ? `<a class="stamp pr" href="${esc(r.draft_pr)}" target="_blank" rel="noopener">Draft PR<b>${esc(prRef(r.draft_pr))}</b></a>` : ""}
        ${t ? `<button class="stamp trace" type="button" data-copy="${esc(t)}">neatlogs trace<b>${esc(t.slice(0, 12))}</b></button>` : `<span class="stamp trace" aria-disabled="true">neatlogs trace<b>not recorded</b></span>`}
        ${cp ? `<button class="stamp entire" type="button" data-copy="${esc(cp)}">Entire checkpoint<b>${esc(cp.slice(0, 12))}</b></button>` : `<span class="stamp entire" aria-disabled="true">Entire checkpoint<b>none</b></span>`}
        ${ci ? `<a class="stamp ci${ci === "passed" ? " pass" : ""}" href="${esc((r.draft_pr || r.pr_url) + "/checks")}" target="_blank" rel="noopener" title="Kedge's verdict comes from running the tests itself">GitHub CI<b>${esc(ci)}</b></a>` : ""}
      </div>
      ${cp && r.entire_explain && !r.entire_explain.startsWith("(no") ? `<details class="cp"><summary>Read the agent's session behind the final commit</summary><pre>${esc(r.entire_explain)}</pre></details>` : ""}
    </section>
    <section><h2>The plan</h2><div class="plan-note"><p>${p.hypothesis ? inline(p.hypothesis) : "No plan recorded."}</p>
      ${(p.steps || []).length ? `<ol>${p.steps.map((x) => `<li>${inline(x)}</li>`).join("")}</ol>` : ""}
      <p style="margin-top:12px">Allowed: ${(p.allowed_files || []).map((f) => `<code>${esc(f)}</code>`).join(" ")}</p></div></section>`;
}

function renderSheets() {
  $("#sheetList").innerHTML = runs.map((r) => {
    const v = verdict(r);
    const pick = picks.indexOf(r.run_id);
    return `<li><button class="sheet" type="button" data-id="${esc(r.run_id)}"
      aria-current="${!race && current && r.run_id === current.run_id}" ${race && pick >= 0 ? `data-pick="${pick}"` : ""}>
      <span class="sheet-no">${no(r)}</span><span class="sheet-title">${esc(r.title || prRef(r.pr_url))}</span>
      <span class="sheet-sub">${esc(prRef(r.pr_url))} · ${score(r)}${r.guard === false ? " · no guard" : ""}${r.storm ? ` · ${esc(r.storm)}` : ""}</span>
      <span class="sheet-verdict ${v.cls}">${esc(v.word)}</span></button></li>`;
  }).join("");
}

function renderTally() {
  const done = runs.filter((r) => r.status !== "running");
  const kept = runs.filter((r) => verdict(r).key === "keep").length;
  const cheats = runs.reduce((n, r) => n + r.drifts, 0);
  const lies = runs.reduce((n, r) => n + r.false_claims, 0);
  $("#tally").innerHTML = `<b>${kept}/${done.length}</b> kept · <b>${cheats}</b> cheats caught · <b>${lies}</b> lies overruled`;
  if (current && !race) $("#labelSub").textContent = `sheet No. ${no(current)}`;
  else $("#labelSub").textContent = race ? "race" : "contact sheet";
}

function show(autoplay) {
  renderTally(); renderSheets(); renderBench();
  if (runs.length) play(!autoplay);
}

async function load(first) {
  try {
    const data = await (await fetch("/api/runs", { cache: "no-store" })).json();
    [...data].sort((a, b) => a.run_id.localeCompare(b.run_id)).forEach((r, i) => (r.no = i + 1));
    const fp = JSON.stringify(data.map((r) => [r.run_id, r.status, r.steps.length]));
    if (fp === fingerprint) return;
    fingerprint = fp;
    runs = data;
    const want = current?.run_id || location.hash.slice(1);
    current = runs.find((r) => r.run_id === want) || runs[0] || null;
    if (first) show(true); else { renderTally(); renderSheets(); }
  } catch {
    $("#bench").innerHTML = `<div class="empty"><p class="mark-note big">Lost the light.</p><p>Is <code>kedge ui</code> still running?</p></div>`;
  }
}

/* ---------- interaction ---------- */
$("#playBtn").addEventListener("click", () => { renderBench(); play(false); });
$("#sheetsBtn").addEventListener("click", () => {
  const open = $("#sheets").hidden;
  $("#sheets").hidden = !open;
  $("#sheetsBtn").setAttribute("aria-expanded", String(open));
});
$("#raceBtn").addEventListener("click", (e) => {
  race = !race;
  e.currentTarget.setAttribute("aria-pressed", String(race));
  $("#raceHint").hidden = !race;
  if (race && picks.length < 2) { $("#sheets").hidden = false; $("#sheetsBtn").setAttribute("aria-expanded", "true"); }
  show(true);
});
$("#sheetList").addEventListener("click", (e) => {
  const b = e.target.closest(".sheet");
  if (!b) return;
  const id = b.dataset.id;
  if (race) {
    picks = picks.includes(id) ? picks.filter((x) => x !== id) : [...picks, id].slice(-2);
    if (picks.length === 2) { $("#sheets").hidden = true; $("#sheetsBtn").setAttribute("aria-expanded", "false"); }
  } else {
    current = runs.find((r) => r.run_id === id);
    history.replaceState(null, "", `#${id}`);
    $("#sheets").hidden = true; $("#sheetsBtn").setAttribute("aria-expanded", "false");
  }
  show(true);
});
document.addEventListener("click", async (e) => {
  const b = e.target.closest("[data-copy]");
  if (!b) return;
  try { await navigator.clipboard.writeText(b.dataset.copy); $("b", b).textContent = "copied"; } catch { /* clipboard blocked */ }
});
document.addEventListener("keydown", (e) => {
  if (e.target.closest("input, select, textarea")) return;
  if (e.key === " " || e.key === "Enter" && e.target === document.body) { e.preventDefault(); renderBench(); play(false); }
  if (e.key === "Escape") { $("#sheets").hidden = true; $("#sheetsBtn").setAttribute("aria-expanded", "false"); }
  if (e.key === "s") speed = speed === 1 ? 0.55 : 1;  // slow-motion for the video
});

/* the loupe: a magnified copy of the frame under the cursor */
const loupe = $("#loupe"), loupeIn = $("#loupeIn");
let loupeFrame = null;
document.addEventListener("pointermove", (e) => {
  const fr = e.target.closest?.(".frame");
  if (!fr || e.pointerType !== "mouse") { loupe.classList.remove("on"); loupeFrame = null; return; }
  if (fr !== loupeFrame) {
    loupeFrame = fr;
    const clone = fr.cloneNode(true);
    clone.style.width = `${fr.offsetWidth}px`;
    clone.querySelectorAll(".note").forEach((n) => n.remove());
    loupeIn.replaceChildren(clone);
  }
  const rect = fr.getBoundingClientRect(), z = 2.1, R = 110;
  loupe.style.left = `${e.clientX - R}px`;
  loupe.style.top = `${e.clientY - R}px`;
  loupeIn.style.transform = `translate(${R - (e.clientX - rect.left) * z}px, ${R - (e.clientY - rect.top) * z}px) scale(${z})`;
  loupe.classList.add("on");
});

load(true);
setInterval(() => load(false), 5000);
