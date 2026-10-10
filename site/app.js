const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const inline = (t) => esc(t).replace(/`([^`]+)`/g, "<code>$1</code>");
const plural = (n, w) => `${n} ${w}${n === 1 ? "" : "s"}`;
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
let speed = 1;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms / speed));

const DRIFT = {
  tests_regressed: ["tests lost", "The agent's change dropped passing or total tests."],
  out_of_plan: ["off the plan", "The agent touched files outside the plan."],
  loop: ["same mistake again", "The agent repeated a change Kedge already threw out."],
  verify_failed: ["didn't hold", "Tests passed once, then failed on the re-run."],
  over_budget: ["out of budget", "The run hit its spend cap."],
};

const CFG = window.KEDGE || {};
let runs = [];
let current = null;
let race = !!CFG.race;
let picks = CFG.race ? [...CFG.race] : [];
let playToken = 0;
let fingerprint = "";

/* ---------- facts ---------- */
const lastGood = (r) => [...(r.steps || [])].reverse().find((s) => s.tests_total >= 0 && !s.rolled_back);
const denom = (r, total) => Math.max(total, r.base_total || 0);
const lost = (r) => { const l = lastGood(r); return l && r.base_total > l.tests_total ? r.base_total - l.tests_total : 0; };
const verdict = (r) => {
  if (r.status === "green" && lost(r)) return { key: "short", word: "Shipped short", cls: "v-short" };
  if (r.status === "green") return { key: "keep", word: "Kept", cls: "v-keep" };
  if (r.status === "already_green") return { key: "flat", word: "Already green", cls: "v-flat" };
  if (r.status === "running") return { key: "live", word: "Developing", cls: "v-live" };
  return { key: "out", word: "Gave up", cls: "v-out" };
};
const score = (r) => { const l = lastGood(r); return l ? `${l.tests_passed}/${denom(r, l.tests_total)}` : "–"; };
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

/* ---------- frames ---------- */
function frameInner(r, f) {
  if (f.kind === "plan") {
    const p = r.plan || {};
    return { cls: "plan", fs: "Plan", fa: (p.steps || [])[0] || p.hypothesis || "Read the failing tests" };
  }
  if (f.kind === "replan") return { cls: "plan", fs: "Replan", fa: "Two strikes, so Kedge asked for a new approach." };
  if (f.kind === "final") {
    const L = lost(r);
    return {
      keep: { cls: "won", fs: "Green", fa: r.draft_pr ? "All tests pass. Draft PR opened." : "All tests pass." },
      short: { cls: "lost", fs: "Shipped", fa: `PR opened without ${plural(L, "test")}. Nobody checked.` },
      flat: { cls: "won", fs: "Green", fa: "Tests already passed on arrival." },
      out: { cls: "lost", fs: "Gave up", fa: "No safe fix inside the budget." },
    }[f.v.key];
  }
  const s = f.s, d = denom(r, s.tests_total), files = s.files_changed || [];
  const fa = s.action === "worker_error" ? "The agent didn't answer in time."
    : files.length ? `Edited ${files.slice(0, 2).join(", ")}${files.length > 2 ? ` +${files.length - 2}` : ""}` : "Changed nothing.";
  const isLost = s.tests_total >= 0 && d > s.tests_total && s.tests_passed > 0;
  return { cls: isLost ? "lost" : "", fs: s.tests_total >= 0 ? `${s.tests_passed}/${d}` : "?", fa };
}
const holes = (n = 4) => `<i></i>`.repeat(n);
function cellHTML(r, f, i, last) {
  const x = frameInner(r, f);
  const label = f.kind === "step" ? `step ${f.s.step}` : f.kind === "replan" ? `step ${f.s.step}` : f.kind === "final" ? "final" : "plan";
  return `<div class="cell"><span class="holes top">${holes()}</span>
    <button class="frame ${x.cls}" data-i="${i}" type="button" aria-expanded="false" aria-label="Frame ${i + 1}: ${esc(x.fs)}. Open evidence">
      <span class="fs">${esc(x.fs)}</span><span class="fa">${esc(x.fa)}</span></button>
    <span class="holes bot">${holes()}</span>
    <span class="edge">KEDGE ${no(r)} ▸ ${i + 1}${last ? "A" : ""} · ${label}</span></div>`;
}

/* ---------- china-marker strokes ---------- */
const W = () => parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--fw")) || 236;
const H = 178;
function svgFor(el) {
  let svg = el.querySelector("svg.marks");
  if (!svg) {
    svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("class", "marks");
    svg.setAttribute("viewBox", `0 0 ${W() + 36} ${H + 36}`);
    svg.setAttribute("preserveAspectRatio", "none");
    svg.setAttribute("aria-hidden", "true");
    el.append(svg);
  }
  return svg;
}
function stroke(el, d, cls, dur, instant) {
  const p = document.createElementNS("http://www.w3.org/2000/svg", "path");
  p.setAttribute("d", d);
  p.setAttribute("class", `${cls} draw`);
  svgFor(el).append(p);
  p.style.setProperty("--len", p.getTotalLength());
  p.style.setProperty("--dur", `${instant ? 1 : dur / speed}ms`);
  requestAnimationFrame(() => p.classList.add("on"));
}
// a person's stroke, not a vector: each mark leans and bows a little
function xMark(el, instant) {
  const w = W() + 36, h = H + 36;
  stroke(el, `M ${w * .14} ${h * .16} Q ${w * .48} ${h * .52} ${w * .88} ${h * .86}`, "red", 420, instant);
  setTimeout(() => stroke(el, `M ${w * .86} ${h * .14} Q ${w * .55} ${h * .45} ${w * .12} ${h * .88}`, "red", 420, instant), instant ? 0 : 380 / speed);
}
function ring(el, instant) {
  const w = W() + 36, h = H + 36, cx = w / 2, cy = h / 2, rx = w * .5, ry = h * .5;
  stroke(el, `M ${cx - rx * .2} ${cy - ry * .98} C ${cx + rx * .7} ${cy - ry * 1.08}, ${cx + rx * 1.05} ${cy - ry * .2}, ${cx + rx * .96} ${cy + ry * .3}
    C ${cx + rx * .86} ${cy + ry * .98}, ${cx - rx * .5} ${cy + ry * 1.06}, ${cx - rx * .95} ${cy + ry * .4}
    C ${cx - rx * 1.08} ${cy - ry * .3}, ${cx - rx * .6} ${cy - ry * 1.02}, ${cx + rx * .15} ${cy - ry * .9}`, "red", 700, instant);
}
function underline(el, instant) {
  const w = W() + 36, h = H + 36;
  stroke(el, `M ${w * .12} ${h * .5} Q ${w * .45} ${h * .45} ${w * .8} ${h * .52}`, "yel", 380, instant);
}
function note(el, html, where, cls, instant) {
  const n = document.createElement("span");
  n.className = `note ${where} ${cls || ""}`;
  n.innerHTML = html;
  el.append(n);
  if (instant) n.classList.add("on"); else requestAnimationFrame(() => n.classList.add("on"));
}

/* ---------- the reel: one strip on a spring ---------- */
class Reel {
  constructor(lane) {
    this.lane = lane; this.vp = $(".viewport", lane); this.strip = $(".strip", lane);
    this.x = 0; this.v = 0; this.target = 0; this.raf = 0;
  }
  cw() { return W() + (parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--fgap")) || 22); }
  center(i) { return this.vp.clientWidth / 2 - (i * this.cw() + this.cw() / 2); }
  set(x) { this.x = x; this.v = 0; this.paint(); }
  paint() {
    const blur = Math.min(Math.abs(this.v) / 300, 7);
    this.strip.style.transform = `translate3d(${this.x}px,0,0)`;
    this.strip.style.filter = blur > .3 ? `blur(${blur.toFixed(2)}px)` : "";
  }
  // feed: critically damped, a crisp pull-down. rewind: loose and heavy, it overshoots and smears.
  to(i, { stiff = 70, damp = 17 } = {}) {
    this.target = this.center(i);
    if (reduce) { this.set(this.target); return Promise.resolve(); }
    cancelAnimationFrame(this.raf);
    return new Promise((res) => {
      let last = performance.now();
      const tick = (now) => {
        const dt = Math.min((now - last) / 1000, .032) * speed; last = now;
        this.v += (stiff * (this.target - this.x) - damp * this.v) * dt;
        this.x += this.v * dt;
        this.paint();
        if (Math.abs(this.v) < 4 && Math.abs(this.target - this.x) < .5) { this.set(this.target); res(); return; }
        this.raf = requestAnimationFrame(tick);
      };
      this.raf = requestAnimationFrame(tick);
    });
  }
  // cut the strip into contact-sheet rows so every frame, and every mark, stays on the box
  layDown(instant) {
    const cells = $$(".cell", this.strip);
    const before = cells.map((c) => c.getBoundingClientRect());
    this.lane.classList.add("laid");
    this.strip.style.transform = ""; this.strip.style.filter = "";
    if (instant || reduce) return;
    cells.forEach((c, k) => {
      const a = c.getBoundingClientRect(), b = before[k];
      c.animate([{ transform: `translate(${b.left - a.left}px, ${b.top - a.top}px)` }, { transform: "none" }],
        { duration: 900 / speed, delay: (k * 40) / speed, easing: "cubic-bezier(.16, 1, .3, 1)", fill: "backwards" });
    });
  }
}

function laneHTML(r, label) {
  const fr = framesOf(r);
  return `<div class="lane" data-run="${esc(r.run_id)}">
    ${label ? `<h2 class="lane-name ${r.guard === false ? "unguarded" : "guarded"}">${label}</h2>` : ""}
    <div class="viewport"><div class="gate"></div>
      <div class="strip">${fr.map((f, i) => cellHTML(r, f, i, i === fr.length - 1)).join("")}</div></div></div>`;
}

function printHTML(r, label) {
  const v = verdict(r), l = lastGood(r), L = lost(r);
  const why = {
    keep: `${plural(r.drifts, "cheat")} caught, ${plural(r.rollbacks, "rewind")}, every test kept.`,
    short: `${plural(L, "test")} vanished and the PR shipped anyway. No one was checking.`,
    flat: "Nothing to fix: the tests already passed.",
    out: `Kedge refused every unsafe change: ${plural(r.drifts, "cheat")} caught.`,
    live: "Still developing.",
  }[v.key];
  const sign = { keep: "checked by Kedge", short: "unchecked", out: "no safe fix", flat: "", live: "" }[v.key];
  return `<article class="print ${v.key}" data-run="${esc(r.run_id)}">
    <div class="img"><span class="big" data-to="${l ? l.tests_passed : 0}" data-of="${l ? denom(r, l.tests_total) : 0}">${score(r)}</span>
      <span class="word">${esc(v.word)}</span><span class="why">${esc(why)}</span></div>
    <div class="cap"><span class="who">${label ? esc(label) + " · " : ""}No. ${no(r)} · ${esc(prRef(r.pr_url))}</span>
      ${r.draft_pr ? `<a class="open" href="${esc(r.draft_pr)}" target="_blank" rel="noopener"><svg aria-hidden="true"><use href="#i-pr"/></svg>Open PR</a>` : ""}
      ${sign ? `<span class="sign${v.key === "keep" ? " ok" : ""}">${esc(sign)}</span>` : ""}</div></article>`;
}

/* ---------- the performance ---------- */
async function perform(reel, r, token, instant) {
  const fr = framesOf(r);
  const els = $$(".frame", reel.strip);
  const alive = () => token === playToken;
  if (instant) els.forEach((e) => e.classList.add("dev"));
  else {
    reel.set(reel.vp.clientWidth + 60);
    await reel.to(0, { stiff: 40, damp: 13 }); if (!alive()) return;
    els[0].classList.add("dev"); await sleep(600);
  }
  for (let i = 1; i < fr.length; i++) {
    const f = fr[i];
    if (!instant) { await reel.to(i); if (!alive()) return; els[i].classList.add("dev"); await sleep(420); }
    if (f.kind === "step") {
      const s = f.s;
      if (s.false_claim) {
        underline(els[i], instant);
        note(els[i], `agent: “${esc(s.claim)}”<br>tests: ${s.tests_passed}/${denom(r, s.tests_total)}`, "up", "yel", instant);
        if (!instant) await sleep(1100);
      }
      if (s.drift && s.drift !== "over_budget") {
        xMark(els[i], instant);
        note(els[i], `${(DRIFT[s.drift] || [s.drift])[0]}<br><small>${esc((s.files_changed || []).slice(0, 2).join(", "))}</small>`, "down", "", instant);
        if (!instant) await sleep(1300);
        if (s.rolled_back) {
          let cp = 0;
          for (let j = i - 1; j > 0; j--) if (fr[j].kind === "step" && !fr[j].s.drift) { cp = j; break; }
          if (!instant) { await reel.to(cp, { stiff: 34, damp: 4 }); if (!alive()) return; }   // the rewind
          if (!els[cp].querySelector(".note.up")) {
            ring(els[cp], instant);
            note(els[cp], `hauled back to <span class="sha">${esc((s.checkpoint_sha || "").slice(0, 7))}</span>`, "up", "", instant);
          }
          if (!instant) await sleep(1200);
        }
      }
    }
    if (f.kind === "final") {
      if (f.v.key === "keep" || f.v.key === "flat") { ring(els[i], instant); note(els[i], "keeper", "up", "", instant); }
      if (f.v.key === "short") { xMark(els[i], instant); note(els[i], `${plural(lost(r), "test")} missing, shipped anyway`, "down", "", instant); }
      if (!instant) await sleep(900);
    }
  }
  reel.layDown(instant);
  if (!instant) await sleep(1000);
}

// the count settles like a needle: an underdamped spring on the number itself
function settle(el, instant) {
  const to = +el.dataset.to, of = +el.dataset.of;
  if (instant || reduce || !of) return;
  let x = 0, v = 0, last = performance.now();
  const tick = (now) => {
    const dt = Math.min((now - last) / 1000, .032) * speed; last = now;
    v += (90 * (to - x) - 7 * v) * dt; x += v * dt;
    el.textContent = `${Math.max(0, Math.round(x))}/${of}`;
    if (Math.abs(v) > .05 || Math.abs(to - x) > .05) requestAnimationFrame(tick); else el.textContent = `${to}/${of}`;
  };
  requestAnimationFrame(tick);
}

// the keeper lifts off the sheet: the print grows out of the final frame's own rectangle
function lift(print, keeperEl, instant) {
  print.classList.add("on");
  if (instant || reduce || !keeperEl) return;
  const a = keeperEl.getBoundingClientRect(), b = print.getBoundingClientRect();
  print.animate([
    { transform: `translate(${a.left - b.left}px, ${a.top - b.top}px) scale(${a.width / b.width}, ${a.height / b.height})`, opacity: .4 },
    { transform: `translate(${(a.left - b.left) * .3}px, ${(a.top - b.top) * .3 - 30}px) scale(.8) rotate(-4deg)`, opacity: 1, offset: .45 },
    { transform: "rotate(-1.4deg)", opacity: 1 },
  ], { duration: 1100 / speed, easing: "cubic-bezier(.16, 1, .3, 1)", fill: "forwards" });
}

async function play(instant = false) {
  const token = ++playToken;
  closeSlip();
  const chosen = race ? picks.map((id) => runs.find((r) => r.run_id === id)).filter(Boolean) : [current].filter(Boolean);
  if (!chosen.length) return;
  const reels = $$(".lane").map((l) => new Reel(l));
  await Promise.all(reels.map((reel, k) => perform(reel, chosen[k], token, instant || reduce)));
  if (token !== playToken) return;
  $$(".print").forEach((p, k) => setTimeout(() => {
    const keeper = $$(".lane")[k] && $$(".frame", $$(".lane")[k]).pop();
    lift(p, keeper, instant || reduce);
    settle($(".big", p), instant || reduce);
  }, instant ? 0 : k * 500 / speed));
}

/* ---------- the frame slip ---------- */
function closeSlip() {
  $("#slip")?.remove();
  $$(".frame[aria-expanded='true']").forEach((f) => f.setAttribute("aria-expanded", "false"));
}
function openSlip(btn) {
  const lane = btn.closest(".lane");
  const r = runs.find((x) => x.run_id === lane.dataset.run);
  const f = framesOf(r)[+btn.dataset.i];
  closeSlip();
  btn.setAttribute("aria-expanded", "true");
  const rows = [];
  let title = "Plan", hand = "";
  if (f.kind === "plan") {
    rows.push(["Hypothesis", inline(r.plan?.hypothesis || "none")], ["Allowed", (r.plan?.allowed_files || []).map((x) => `<code>${esc(x)}</code>`).join(" ")]);
  } else if (f.kind === "final") {
    title = "Final"; hand = f.v.word;
    rows.push(["Score", score(r)], ["Draft PR", r.draft_pr ? `<a href="${esc(r.draft_pr)}" target="_blank" rel="noopener">${esc(prRef(r.draft_pr))}</a>` : "none"]);
    rows.push(["Entire", checkpointId(r) ? `<code>${esc(checkpointId(r))}</code>` : "no checkpoint"], ["neatlogs", traceId(r) ? `<code>${esc(traceId(r))}</code>` : "trace not recorded"]);
  } else {
    const s = f.s;
    title = `Step ${s.step}`;
    hand = s.drift ? (DRIFT[s.drift] || [s.drift])[0] : f.kind === "replan" ? "replan" : "";
    rows.push(["Action", s.action === "worker_error" ? "agent timed out" : s.action]);
    rows.push(["Files", (s.files_changed || []).map((x) => `<code>${esc(x)}</code>`).join(" ") || "none"]);
    if (s.tests_total >= 0) rows.push(["Tests", `${s.tests_passed}/${denom(r, s.tests_total)}`]);
    if (s.drift) rows.push(["Kedge", `${esc((DRIFT[s.drift] || ["", ""])[1])}${s.rolled_back ? " Rolled back." : ""}`]);
    if (s.claim) rows.push(["Agent said", `“${esc(s.claim)}”${s.false_claim ? " (overruled)" : ""}`]);
    rows.push(["Commit", `<code>${esc((s.checkpoint_sha || "").slice(0, 10))}</code>`]);
    if (s.entire_checkpoint) rows.push(["Entire", `<code>${esc(s.entire_checkpoint)}</code>`]);
    rows.push(["Tokens", (s.tokens || 0).toLocaleString()]);
  }
  const slip = document.createElement("aside");
  slip.id = "slip"; slip.className = "slip"; slip.setAttribute("aria-label", `${title} evidence`);
  slip.innerHTML = `<button class="close" type="button">Close</button>
    <h3>${esc(title)}${hand ? `<span class="hand">${esc(hand)}</span>` : ""}</h3>
    <dl>${rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("")}</dl>`;
  document.body.append(slip);
  $(".close", slip).focus();
}

/* ---------- layout ---------- */
function renderBench() {
  const bench = $("#bench");
  closeSlip();
  if (!runs.length) { bench.replaceChildren($("#emptyTpl").content.cloneNode(true)); if ($("#envelope")) $("#envelope").innerHTML = ""; return; }
  if (race) {
    const [a, b] = picks.map((id) => runs.find((r) => r.run_id === id));
    if ($("#envelope")) $("#envelope").innerHTML = "";
    if (!a || !b) {
      bench.innerHTML = `<div class="empty"><p class="mark-note big">Pick two sheets to race.</p>
        <p>The same PR with <code>--no-guard</code> and with Kedge makes the point.</p></div>`;
      return;
    }
    const lbl = (r) => (r.guard === false ? "No guard" : "Kedge");
    bench.innerHTML = `<div class="reel-title"><span class="no">vs</span><h1>${esc(a.title || prRef(a.pr_url))}</h1>
      <span class="src">${esc(prRef(a.pr_url))}${a.storm ? `<span class="storm">sabotage: ${esc(a.storm)}</span>` : ""}</span></div>
      ${laneHTML(a, lbl(a))}${laneHTML(b, lbl(b))}<div class="prints">${printHTML(a, lbl(a))}${printHTML(b, lbl(b))}</div>`;
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
  if (!$("#envelope")) return;
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
  const p = r.plan || {}, t = traceId(r), cp = checkpointId(r);
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
    <section><h2>The plan</h2><div class="plan-slip"><p>${p.hypothesis ? inline(p.hypothesis) : "No plan recorded."}</p>
      ${(p.steps || []).length ? `<ol>${p.steps.map((x) => `<li>${inline(x)}</li>`).join("")}</ol>` : ""}
      <p>Allowed: ${(p.allowed_files || []).map((f) => `<code>${esc(f)}</code>`).join(" ")}</p></div></section>`;
}

function renderSheets() {
  if (!$("#sheetList")) return;
  $("#sheetList").innerHTML = runs.map((r) => {
    const v = verdict(r), pick = picks.indexOf(r.run_id);
    const film = framesOf(r).map((f) => `<i class="${f.kind === "step" && f.s.drift ? "x" : f.kind === "step" && f.s.false_claim ? "y" : f.kind === "final" && (f.v.key === "keep") ? "k" : f.kind === "final" && f.v.key === "short" ? "x" : ""}"></i>`).join("");
    return `<li><button class="sheet" type="button" data-id="${esc(r.run_id)}"
      aria-current="${!race && current && r.run_id === current.run_id}" ${race && pick >= 0 ? `data-pick="${pick}"` : ""}>
      <span class="sheet-no">${no(r)}</span><span class="sheet-title">${esc(r.title || prRef(r.pr_url))}</span>
      <span class="sheet-film" aria-hidden="true">${film}</span>
      <span class="sheet-sub">${esc(prRef(r.pr_url))} · ${score(r)}${r.guard === false ? " · no guard" : ""}${r.storm ? ` · ${esc(r.storm)}` : ""}</span>
      <span class="sheet-verdict ${v.cls}">${esc(v.word)}</span></button></li>`;
  }).join("");
}

function renderTally() {
  const done = runs.filter((r) => r.status !== "running");
  const kept = runs.filter((r) => verdict(r).key === "keep").length;
  const cheats = runs.reduce((n, r) => n + r.drifts, 0), lies = runs.reduce((n, r) => n + r.false_claims, 0);
  if (!$("#tally")) return;
  $("#tally").innerHTML = `<b>${kept}/${done.length}</b> kept · <b>${cheats}</b> cheats caught · <b>${lies}</b> lies overruled`;
  $("#labelSub").textContent = race ? "race" : current ? `sheet No. ${no(current)}` : "contact sheet";
}

function show(autoplay) { renderTally(); renderSheets(); renderBench(); if (runs.length) play(!autoplay); }

async function load(first) {
  try {
    const data = CFG.data || await (await fetch("/api/runs", { cache: "no-store" })).json();
    [...data].sort((a, b) => a.run_id.localeCompare(b.run_id)).forEach((r, i) => (r.no = i + 1));
    const fp = JSON.stringify(data.map((r) => [r.run_id, r.status, r.steps.length]));
    if (fp === fingerprint) return;
    fingerprint = fp; runs = data;
    const want = current?.run_id || location.hash.slice(1);
    current = runs.find((r) => r.run_id === want) || runs[0] || null;
    if (first) show(true); else { renderTally(); renderSheets(); }
  } catch {
    $("#bench").innerHTML = `<div class="empty"><p class="mark-note big">Lost the light.</p><p>Is <code>kedge ui</code> still running?</p></div>`;
  }
}

/* ---------- interaction ---------- */
const on = (sel, ev, fn) => document.querySelectorAll(sel).forEach((el) => el.addEventListener(ev, fn));
const sheetsOpen = (open) => { if (!$("#sheets")) return; $("#sheets").hidden = !open; $("#sheetsBtn").setAttribute("aria-expanded", String(open)); };
on("#playBtn, [data-play]", "click", () => { renderBench(); play(false); });
on("#sheetsBtn", "click", () => sheetsOpen($("#sheets").hidden));
on("#raceBtn", "click", (e) => {
  race = !race;
  e.currentTarget.setAttribute("aria-pressed", String(race));
  $("#raceHint").hidden = !race;
  if (race && picks.length < 2) sheetsOpen(true);
  show(true);
});
on("#sheetList", "click", (e) => {
  const b = e.target.closest(".sheet");
  if (!b) return;
  const id = b.dataset.id;
  if (race) {
    picks = picks.includes(id) ? picks.filter((x) => x !== id) : [...picks, id].slice(-2);
    if (picks.length === 2) sheetsOpen(false); else { renderSheets(); return; }
  } else {
    current = runs.find((r) => r.run_id === id);
    history.replaceState(null, "", `#${id}`);
    sheetsOpen(false);
  }
  show(true);
});
document.addEventListener("click", async (e) => {
  const frame = e.target.closest(".frame");
  if (frame && !e.target.closest(".loupe")) { frame.getAttribute("aria-expanded") === "true" ? closeSlip() : openSlip(frame); return; }
  if (e.target.closest(".slip .close")) { closeSlip(); return; }
  const b = e.target.closest("[data-copy]");
  if (b) { try { await navigator.clipboard.writeText(b.dataset.copy); $("b", b).textContent = "copied"; } catch { /* clipboard blocked */ } }
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") { closeSlip(); sheetsOpen(false); return; }
  if (e.target !== document.body) return;               // buttons keep Space and Enter for themselves
  if (e.key === " ") { e.preventDefault(); renderBench(); play(false); }
  if (e.key === "s") speed = speed === 1 ? .55 : 1;   // slow motion for the video
});

/* the loupe: a magnified copy of the frame under the cursor */
const loupe = $("#loupe"), loupeIn = $("#loupeIn");
let loupeFrame = null;
if (loupe) document.addEventListener("pointermove", (e) => {
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

// embedded pages wait until the bench scrolls into view, so the race plays when someone is looking
if (CFG.data && "IntersectionObserver" in window) {
  const io = new IntersectionObserver((es) => { if (es.some((x) => x.isIntersecting)) { io.disconnect(); load(true); } }, { threshold: .35 });
  io.observe($("#bench"));
} else load(true);
if (!CFG.data) setInterval(() => load(false), 5000);
