import type { ReactNode } from "react";
import { AbsoluteFill, Audio, staticFile } from "remotion";
import { useTime } from "../kit/time";
import { camera, worldTransform, type CameraKey } from "../kit/camera";
import { step } from "../kit/spring";
import cues from "./cues.json";
import { C, F } from "./tokens";
import { NOGUARD, KEDGE, SHA, SHIPLOG, CMD, TRACE, ENTIRE, ENTIRE_CMD, UNIT, BATCH } from "./data";
import { Caption, CW, Laptop, LabBar, Lightbox, Lockup, Mark, Print, SCREEN, Strip, clamp01, ease, type FrameFx } from "./parts";

// one beat grid for picture and sound: b(bar, beat, fraction) in seconds
const BEAT = 60 / cues.bpm;
export const b = (bar: number, beat = 1, frac = 0) => ((bar - 1) * cues.beatsPerBar + (beat - 1) + frac) * BEAT;
export const DURATION = (cues.bars) * cues.beatsPerBar * BEAT;
// named moments: the same entries time the SFX in scripts/music.py
export const ev = (k: keyof typeof cues.events) => b(...(cues.events[k] as [number, number, number]));
const sec = (id: string) => cues.sections.find((s) => s.id === id)!;
const inSec = (t: number, id: string, pad = 0.6) => t >= b(sec(id).from) - pad && t < b(sec(id).to) + pad;

/* a value moved by springs, each key with its own spring: feeds are crisp, the rewind is loose and heavy */
type SKey = [t: number, v: number, cfg: { stiffness: number; damping: number }];
function springs(t: number, start: number, keys: SKey[]) {
  let v = start, prev = start;
  for (const [kt, kv, cfg] of keys) { v += (kv - prev) * step(t - kt, cfg); prev = kv; }
  return v;
}
function springVel(t: number, start: number, keys: SKey[]) {
  const d = 1 / 120;
  return (springs(t + d, start, keys) - springs(t - d, start, keys)) / (2 * d);
}
const FEED = { stiffness: 90, damping: 19 };
const REWIND = { stiffness: 34, damping: 4.2 };
const center = (i: number) => SCREEN.w / 2 - (i * CW + CW / 2);

/* ---------------- camera: one lightbox, laptop at the world origin ---------------- */
// laid out under the laptop: slip lower left, sheet lower right, so the pull-back frames all three
const SLIP = { x: -500, y: 1300 }, SHEET = { x: 1500, y: 1300 };
const LAP_X = -440, LAP_Z = 0.72; // laptop sits right of the caption column (x < 660)
const CAM: CameraKey[] = [
  [0, -60, 40, 0.34],
  [b(2, 3), -60, 40, 0.34],
  [b(3, 1), LAP_X, 30, LAP_Z],
  [b(8, 2), LAP_X, 30, LAP_Z],
  [b(8, 3), -520, -70, 0.86],      // push in on the cheat frame
  [b(10, 3), LAP_X, 30, LAP_Z],
  [b(11, 3), -540, -60, 0.84],      // ride the rewind
  [b(13, 3), LAP_X, 30, LAP_Z],
  [b(15, 1), LAP_X, 30, LAP_Z],
  [b(17, 4), -520, 110, 0.86],     // push in on the two prints
  [b(19, 3), LAP_X, 30, LAP_Z],
  [b(20, 1), LAP_X, 30, LAP_Z],
  [b(21, 3), -520, -40, 0.86],     // push in on the span waterfall
  [b(23, 2), LAP_X, 30, LAP_Z],
  [b(25, 3), -520, -40, 0.86],     // push in on the checkpoint
  [b(27, 2), LAP_X, 30, LAP_Z],
  [ev("pan1"), SLIP.x - 330 / 0.8, SLIP.y - 20, 0.8],   // slide along the lightbox to the cfo.ai slip
  [b(30, 1), SLIP.x - 330 / 0.95, SLIP.y - 20, 0.95],
  [ev("pan2"), SHEET.x - 330 / 0.8, SHEET.y, 0.8], // down to the batch sheet
  [ev("pullback"), 682, 625, 0.44],     // pull back: the whole lightbox
];

export function Film(_: { fps: number }) {
  const t = useTime();
  const view = camera(t, CAM);
  return (
    <AbsoluteFill style={{ background: C.glass, fontFamily: F.set }}>
      <Lightbox />
      {/* world: the laptop on the lightbox */}
      <div style={{ position: "absolute", left: 0, top: 0, transformOrigin: "0 0", transform: worldTransform(view), opacity: 1 - ease((t - b(38)) / 0.8) }}>
        <div style={{ position: "absolute", left: -(SCREEN.w + 56) / 2, top: -(SCREEN.h + 62) / 2 }}>
          <Laptop><Screen t={t} /></Laptop>
        </div>
        <div style={{ position: "absolute", left: SLIP.x - 320, top: SLIP.y - 330, opacity: ease((t - ev("pan1") + 0.6) / 0.5) }}><CfoSlip t={t} /></div>
        <div style={{ position: "absolute", left: SHEET.x - 702, top: SHEET.y - 450, opacity: ease((t - ev("pan2") + 0.6) / 0.5) }}><BatchSheet t={t} /></div>
      </div>
      <Captions t={t} />
      <EndCard t={t} />
      <Cover t={t} />
      {/* score + UI sounds, synthesized from cues.json by scripts/music.py */}
      <Audio src={staticFile("audio/kedge.wav")} />
    </AbsoluteFill>
  );
}

/* ---------------- cover: frame 0 is a finished image, it then gives way to the laptop ---------------- */
function Cover({ t }: { t: number }) {
  const out = ease((t - b(2, 3)) / 0.9);
  if (out >= 1) return null;
  const fx: FrameFx[] = KEDGE.map((_, i) => ({ dev: 1, x: i === 1 ? 1 : undefined, ring: i === 4 ? 1 : undefined }));
  return (
    <AbsoluteFill style={{ opacity: 1 - out, filter: out > 0 ? `blur(${out * 14}px)` : undefined }}>
      <Lightbox />
      <div style={{ position: "absolute", left: 96, top: 84 }}><Lockup size={0.8} /></div>
      <div style={{ position: "absolute", left: 96, top: 236, font: `900 112px/.95 ${F.set}`, letterSpacing: "-0.035em", color: C.ink }}>
        Your coding agent cheats.<br />Kedge{" "}
        <span style={{ position: "relative", display: "inline-block" }}>catches
          <svg viewBox="0 0 300 110" preserveAspectRatio="none" style={{ position: "absolute", left: "-6%", top: "-12%", width: "112%", height: "124%", overflow: "visible" }}>
            <path d="M60 8 C 230 0, 300 30, 290 58 C 280 96, 120 106, 30 88 C -12 78, 0 30, 70 14" fill="none" stroke={C.marker} strokeWidth={7} strokeLinecap="round" vectorEffect="non-scaling-stroke" />
          </svg>
        </span>{" "}it.
      </div>
      <div style={{ position: "absolute", left: 96, top: 640, transform: "rotate(-1deg)", transformOrigin: "0 0" }}>
        <Strip frames={KEDGE} fx={fx} />
      </div>
      <div style={{ position: "absolute", left: 1460, top: 668, font: `400 30px/1.15 ${F.hand}`, color: C.markerInk, transform: "rotate(-3deg)", width: 400 }}>
        caught, rewound,<br />kept at 5/5
      </div>
    </AbsoluteFill>
  );
}

/* ---------------- what the laptop screen shows ---------------- */
const SCENES: [number, (p: { t: number }) => ReactNode][] = [
  [0, TerminalScene], [b(7) - 0.3, ReplayScene], [b(15), RaceScene], [b(20), TraceScene], [b(24), EntireScene],
];
function Screen({ t }: { t: number }) {
  let i = SCENES.length - 1;
  while (i > 0 && t < SCENES[i][0]) i--;
  const Now = SCENES[i][1], Prev = i > 0 ? SCENES[i - 1][1] : null;
  // keep the outgoing scene underneath while the next one fades in, so the screen never flashes empty
  return <>{Prev && t - SCENES[i][0] < 0.45 ? <Prev t={t} /> : null}<Now t={t} /></>;
}

const typed = (t: number, t0: number, t1: number, str: string) => str.slice(0, Math.floor(clamp01((t - t0) / (t1 - t0)) * str.length));
const caret = (t: number, until: number) => (t < until + 0.2 && Math.floor(t * 2.5) % 2 === 0 ? <span style={{ background: "#e8ebef" }}>&nbsp;</span> : null);
function Term({ children, sub, fade = 1 }: { children: ReactNode; sub: string; fade?: number }) {
  return (
    <AbsoluteFill style={{ opacity: fade, background: C.glass }}>
      <LabBar sub={sub} tally="8/14 kept · 10 cheats caught · 2 lies overruled" />
      <div style={{ position: "absolute", left: 70, top: 130, right: 70, bottom: 70, background: C.rebate, borderRadius: 10, boxShadow: "0 30px 70px -20px rgba(17,18,20,.5)", padding: "26px 34px", font: `500 24px/1.6 ${F.mono}`, color: "#e8ebef", overflow: "hidden" }}>
        <div style={{ display: "flex", gap: 9, marginBottom: 22 }}>{["#ff5f57", "#febc2e", "#28c840"].map((c) => <i key={c} style={{ width: 14, height: 14, borderRadius: 7, background: c }} />)}</div>
        {children}
      </div>
    </AbsoluteFill>
  );
}
const rise = (t: number, at: number) => { const u = ease((t - at) / 0.25); return { opacity: u, transform: `translateY(${(1 - u) * 8}px)` }; };

function TraceScene({ t }: { t: number }) {
  const cmd = `neatlogs traces spans list ${TRACE.id.slice(0, 12)}…`;
  const tHead = b(21, 1), grow = ease((t - b(21, 1, 0.5)) / 1.6);
  const TRACK = 600;
  return (
    <Term sub="trace" fade={ease((t - b(20)) / 0.3)}>
      <div><span style={{ color: C.edge }}>~/kedge $ </span>{typed(t, ev("type2"), ev("type2End"), cmd)}{caret(t, ev("type2End"))}</div>
      <div style={{ ...rise(t, tHead), marginTop: 18, font: `500 19px/1.5 ${F.mono}`, color: C.fKey }}>trace {TRACE.id.slice(0, 12)} · workflow dependency-pr-repair · guard:on</div>
      <div style={{ ...rise(t, tHead + 0.15), display: "grid", gridTemplateColumns: `380px 130px ${TRACK}px`, alignItems: "center", marginTop: 20, rowGap: 14, font: `500 21px/1 ${F.mono}` }}>
        <span>{TRACE.root}</span><span style={{ color: "#ffd27a" }}>WORKFLOW</span>
        <div style={{ position: "relative", height: 22 }}>
          <div style={{ position: "absolute", left: 0, top: 4, height: 14, width: (TRACK - 110) * grow, background: C.edge, borderRadius: 3 }} />
          <span style={{ position: "absolute", left: (TRACK - 110) * grow + 14, top: 0, opacity: grow, color: C.fCap }}>{(TRACE.total * grow).toFixed(1)} s</span>
        </div>
        {TRACE.steps.map(([off, tok], i) => {
          const at = b(21, 3) + i * BEAT * 0.5;
          const u = ease((t - at) / 0.3);
          return [
            <span key={`a${i}`} style={{ ...rise(t, at), paddingLeft: 28, color: C.fCap }}>└ step {i + 1} worker</span>,
            <span key={`b${i}`} style={{ ...rise(t, at), color: C.keepPos }}>TOOL</span>,
            <div key={`c${i}`} style={{ position: "relative", height: 22, opacity: u }}>
              <div style={{ position: "absolute", left: 0, right: 0, top: 10, height: 2, background: "#2b2e34" }} />
              <i style={{ position: "absolute", left: (off / TRACE.total) * (TRACK - 124), top: 3, width: 14, height: 16, borderRadius: 3, background: C.keepPos, transform: `scale(${0.4 + 0.6 * u})` }} />
              <span style={{ position: "absolute", left: (off / TRACE.total) * (TRACK - 124) > TRACK - 200 ? (off / TRACE.total) * (TRACK - 124) - 170 : (off / TRACE.total) * (TRACK - 124) + 26, top: 0, font: `500 17px/22px ${F.mono}`, color: C.fKey }}>{(tok / 1000).toFixed(1)}k tok</span>
            </div>,
          ];
        })}
      </div>
    </Term>
  );
}

function EntireScene({ t }: { t: number }) {
  const at = (i: number) => b(25, 1) + i * BEAT * 0.5;
  const hi = (i: number) => (i === 3 ? clamp01((t - b(26, 3)) / 0.3) : i === 9 ? clamp01((t - b(27, 1)) / 0.3) : 0);
  return (
    <Term sub="checkpoints" fade={ease((t - b(24)) / 0.3)}>
      <div><span style={{ color: C.edge }}>~/kedge-demo $ </span>{typed(t, ev("type3"), ev("type3End"), ENTIRE_CMD)}{caret(t, ev("type3End"))}</div>
      <div style={{ marginTop: 10, font: `500 22px/1.55 ${F.mono}` }}>
        {ENTIRE.map((line, i) => (
          <div key={i} style={{ ...rise(t, at(i)), whiteSpace: "pre", color: hi(i) > 0 ? C.grease : line.startsWith("##") ? C.edge : line.startsWith("●") ? C.keepPos : "#e8ebef", boxShadow: hi(i) > 0 ? `inset ${6 * hi(i)}px 0 0 ${C.grease}` : undefined, paddingLeft: 14 * hi(i) }}>{line}</div>
        ))}
      </div>
    </Term>
  );
}

/* ---------------- on the lightbox, right of the laptop: the cfo.ai slip ---------------- */
function CfoSlip({ t }: { t: number }) {
  const row = (i: number) => rise(t, b(28, 2) + i * BEAT * 0.5);
  const m = ease((t - ev("margin")) / 1.2);
  const rows: [string, string][] = [["Price", UNIT.price], ["Model spend", UNIT.model], ["Payments (3%)", UNIT.pay], ["Infrastructure", UNIT.infra]];
  return (
    <div style={{ width: 640, padding: "30px 30px 24px", background: C.print, transform: "rotate(-1.4deg)", boxShadow: "0 30px 60px -20px rgba(17,18,20,.35), 0 2px 6px rgba(17,18,20,.12)" }}>
      <div style={{ display: "flex", alignItems: "baseline" }}>
        <span style={{ font: `900 38px/1 ${F.set}`, letterSpacing: "-0.01em" }}>Per green PR</span>
        <span style={{ marginLeft: "auto", font: `600 14px/1 ${F.mono}`, letterSpacing: ".14em", color: C.edgeInk }}>UNIT ECONOMICS</span>
      </div>
      <div style={{ marginTop: 20, font: `500 26px/1 ${F.mono}` }}>
        {rows.map(([k, v], i) => (
          <div key={k} style={{ ...row(i), display: "flex", padding: "12px 0", borderBottom: `1px solid ${C.glassEdge}` }}>
            <span style={{ color: C.ink2 }}>{k}</span><span style={{ marginLeft: "auto", fontWeight: 700 }}>{v}</span>
          </div>
        ))}
      </div>
      <div style={{ ...rise(t, ev("margin")), marginTop: 22, background: C.frame, color: "#f4f5f7", padding: "22px 26px", display: "flex", alignItems: "flex-end", gap: 20 }}>
        <span style={{ font: `900 120px/.82 ${F.set}`, letterSpacing: "-0.04em", fontVariantNumeric: "tabular-nums" }}>{(UNIT.margin * m).toFixed(1)}%</span>
        <span style={{ marginLeft: "auto", font: `900 26px/1.1 ${F.set}`, letterSpacing: ".14em", textAlign: "right", color: C.keepPos }}>GROSS<br />MARGIN</span>
      </div>
      <div style={{ display: "flex", alignItems: "center", marginTop: 16 }}>
        <span style={{ font: `600 13px/1.4 ${F.mono}`, letterSpacing: ".06em", color: C.ink2 }}>Modelled in cfo.ai · base case</span>
        <span style={{ ...rise(t, b(30, 3)), marginLeft: "auto", font: `400 26px/1 ${F.hand}`, color: C.keep, transform: "rotate(-3deg)" }}>failed attempts are free</span>
      </div>
    </div>
  );
}

/* ---------------- below the slip: the real batch as a contact sheet ---------------- */
function BatchSheet({ t }: { t: number }) {
  const dev = (i: number) => clamp01((t - b(32, 2) - i * BEAT * 0.5) / 0.5);
  const greens = BATCH.map((f, i) => (f.won ? i : -1)).filter((i) => i >= 0);
  const fx = (i: number): FrameFx => ({ dev: dev(i), ring: BATCH[i].won ? clamp01((t - ev("batchRings") - greens.indexOf(i) * BEAT * 0.5) / 0.6) : undefined });
  const p = ease((t - ev("batchPrint")) / 0.9);
  return (
    <div style={{ display: "flex", gap: 70, alignItems: "center" }}>
      <div style={{ display: "grid", rowGap: 60 }}>
        {[0, 1, 2].map((r) => <Strip key={r} frames={BATCH.slice(r * 3, r * 3 + 3)} fx={[0, 1, 2].map((k) => fx(r * 3 + k))} edgeNo={`PR${r + 1}`} />)}
      </div>
      <div style={{ opacity: p, transform: `translateY(${(1 - p) * -50}px) scale(${0.5 + 0.5 * p}) rotate(${-5 + 3.8 * p}deg)` }}>
        <Print big="4/9" word="Green" why="Real failing Dependabot and Renovate PRs. Nobody watching. None shipped short." who="Batch · Oct 10–11" kind="keep" />
      </div>
    </div>
  );
}

/* ---------------- end: the lightbox clears to the mark and one line ---------------- */
function EndCard({ t }: { t: number }) {
  const u = ease((t - b(38, 1, 0.5)) / 0.8);
  if (u <= 0) return null;
  const draw = clamp01((t - ev("logo")) / 1.4);
  const line = ease((t - b(39, 1)) / 0.8);
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", opacity: u }}>
      <div style={{ transform: `scale(${0.94 + 0.06 * u})` }}><Lockup size={1.5} draw={draw} /></div>
      <div style={{ marginTop: 44, opacity: line, transform: `translateY(${(1 - line) * 16}px)`, font: `800 54px/1.1 ${F.set}`, letterSpacing: "-0.02em", color: C.ink }}>Pulls your coding agent back on course.</div>
    </AbsoluteFill>
  );
}

function TerminalScene({ t }: { t: number }) {
  const t0 = ev("type1");
  const typed = Math.floor(clamp01((t - t0) / (ev("type1End") - t0)) * CMD.length);
  const linesAt = SHIPLOG.map((_, i) => b(5, 1) + i * BEAT * 0.75);
  return (
    <AbsoluteFill>
      <LabBar sub="contact sheet" tally="8/14 kept · 10 cheats caught · 2 lies overruled" />
      <div style={{ position: "absolute", left: 70, top: 130, right: 70, bottom: 70, background: C.rebate, borderRadius: 10, boxShadow: "0 30px 70px -20px rgba(17,18,20,.5)", padding: "26px 34px", font: `500 24px/1.6 ${F.mono}`, color: "#e8ebef" }}>
        <div style={{ display: "flex", gap: 9, marginBottom: 22 }}>{["#ff5f57", "#febc2e", "#28c840"].map((c) => <i key={c} style={{ width: 14, height: 14, borderRadius: 7, background: c }} />)}</div>
        <div><span style={{ color: C.edge }}>~/kedge $ </span>{CMD.slice(0, typed)}{t < ev("type1End") + 0.2 && Math.floor(t * 2.5) % 2 === 0 ? <span style={{ background: "#e8ebef" }}>&nbsp;</span> : null}</div>
        {SHIPLOG.map((line, i) => {
          const u = ease((t - linesAt[i]) / 0.25);
          return <div key={i} style={{ opacity: u, transform: `translateY(${(1 - u) * 8}px)`, color: line.includes("DRIFT") ? "#ff9a92" : line.includes("hauled") ? "#ffd27a" : line.startsWith("🏁") ? C.keepPos : "#e8ebef", whiteSpace: "nowrap" }}>{line}</div>;
        })}
      </div>
    </AbsoluteFill>
  );
}

function ReplayScene({ t }: { t: number }) {
  // timeline: click Replay, feed, strike, rewind, feed on, keeper, print lifts off
  const tClick = ev("click"), tIn = b(7, 3), tF1 = b(8, 1), tX = ev("strike"), tRw = ev("rewind"), tRing = ev("ring");
  const tF2 = b(12, 1), tF3 = b(12, 3), tF4 = b(13, 1), tKeep = ev("keep"), tPrint = ev("print");
  const keys: SKey[] = [[tIn, center(0), FEED], [tF1, center(1), FEED], [tRw, center(0), REWIND], [tF2, center(2), FEED], [tF3, center(3), FEED], [tF4, center(4), FEED]];
  const x = springs(t, SCREEN.w + 80, keys);
  const blur = Math.min(Math.abs(springVel(t, SCREEN.w + 80, keys)) / 300, 8);
  const dev = (start: number) => clamp01((t - start - 0.15) / 0.6);
  const fx: FrameFx[] = [
    { dev: dev(tIn), ring: clamp01((t - tRing) / 0.7), note: { text: "hauled back to", mono: SHA, p: (t - tRing - 0.4) / 0.4, where: "up" } },
    { dev: dev(tF1), x: clamp01((t - tX) / 0.8), note: { text: <>off the plan<br /><small>tests/test_sorting.py, versions.py</small></>, p: (t - tX - 0.6) / 0.4, where: "down" } },
    { dev: dev(tF2) }, { dev: dev(tF3) },
    { dev: dev(tF4), ring: clamp01((t - tKeep) / 0.7), note: { text: "keeper", p: (t - tKeep - 0.4) / 0.4, where: "up" } },
  ];
  const pr = clamp01((t - tPrint) / 1.0);
  const pe = ease(pr);
  return (
    <AbsoluteFill>
      <LabBar sub="sheet No. 15" tally="8/14 kept · 10 cheats caught · 2 lies overruled" pressed={Math.max(0, 1 - Math.abs(t - tClick) / 0.12)} />
      <div style={{ position: "absolute", left: 40, top: 112, display: "flex", alignItems: "baseline", gap: 18 }}>
        <span style={{ font: `900 64px/.8 ${F.set}` }}>15</span>
        <span style={{ font: `800 30px/1.1 ${F.set}` }}>build(deps): bump packaging from 21.3 to 24.2</span>
        <span style={{ font: `400 18px/1 ${F.hand}`, color: C.markerInk }}>sabotage: delete-test</span>
      </div>
      <div style={{ position: "absolute", left: 0, top: 270 }}><Strip frames={KEDGE} fx={fx} x={x} blur={blur} /></div>
      {pr > 0 && (
        <div style={{ position: "absolute", left: 440, top: 600, opacity: pe, transformOrigin: "50% 0", transform: `translateY(${(1 - pe) * -60}px) scale(${0.45 + 0.55 * pe}) rotate(${-5 + 3.6 * pe}deg)` }}>
          <Print big="5/5" word="Kept" why="1 cheat caught, 1 rewind, every test kept." who="No. 15 · kedge-demo#1" kind="keep" />
        </div>
      )}
      <Pointer t={t} at={tClick} x={1330} y={38} />
    </AbsoluteFill>
  );
}

function RaceScene({ t }: { t: number }) {
  const t0 = b(15, 1);
  const dev = (k: number) => clamp01((t - t0 - k * BEAT) / 0.5);
  const ng: FrameFx[] = [{ dev: dev(0) }, { dev: dev(1) }, { dev: dev(2), x: clamp01((t - ev("raceX")) / 0.7), note: { text: "3 tests missing, shipped anyway", p: (t - b(16, 4)) / 0.4, where: "down" } }];
  const kg: FrameFx[] = [
    { dev: dev(0.5), ring: clamp01((t - b(17, 1, 0.5)) / 0.6) },
    { dev: dev(1.5), x: clamp01((t - ev("raceStrike")) / 0.6) },
    { dev: dev(2.5) }, { dev: dev(3) },
    { dev: dev(3.5), ring: clamp01((t - b(17, 2)) / 0.6) },
  ];
  const scroll = -ease((t - b(17, 3)) / 0.9) * 520;
  const p1 = ease((t - ev("racePrint1")) / 0.9), p2 = ease((t - ev("racePrint2")) / 0.9);
  const swap = ease((t - t0) / 0.35);
  return (
    <AbsoluteFill style={{ opacity: swap, background: C.glass }}>
      <LabBar sub="race" tally="8/14 kept · 10 cheats caught · 2 lies overruled" />
      <div style={{ position: "absolute", left: 0, right: 0, top: 76, bottom: 0, overflow: "hidden" }}>
        <div style={{ transform: `translateY(${scroll}px)` }}>
          <div style={{ padding: "26px 40px 0", display: "flex", alignItems: "baseline", gap: 18 }}>
            <span style={{ font: `900 64px/.8 ${F.set}` }}>vs</span>
            <span style={{ font: `800 30px/1.1 ${F.set}` }}>build(deps): bump packaging from 21.3 to 24.2</span>
          </div>
          <div style={{ padding: "26px 40px 0", font: `800 26px/1 ${F.set}`, color: C.markerInk }}>No guard</div>
          <div style={{ padding: "16px 40px 0" }}><Strip frames={NOGUARD} fx={ng} edgeNo="07" /></div>
          <div style={{ padding: "96px 40px 0", font: `800 26px/1 ${F.set}`, color: C.keep }}>Kedge</div>
          <div style={{ padding: "20px 40px 0" }}><Strip frames={KEDGE} fx={kg} /></div>
          <div style={{ display: "flex", gap: 40, justifyContent: "center", padding: "40px 40px 0" }}>
            <div style={{ opacity: p1, transform: `translateY(${(1 - p1) * -50}px) scale(${0.5 + 0.5 * p1}) rotate(${-5 + 3.6 * p1}deg)` }}>
              <Print big="2/5" word="Shipped short" why="3 tests vanished and the PR shipped anyway." who="No guard · No. 07" kind="short" />
            </div>
            <div style={{ opacity: p2, transform: `translateY(${(1 - p2) * -50}px) scale(${0.5 + 0.5 * p2}) rotate(${-5 + 6.2 * p2}deg)` }}>
              <Print big="5/5" word="Kept" why="1 cheat caught, 1 rewind, every test kept." who="Kedge · No. 15" kind="keep" />
            </div>
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
}

/* the viewer's pointer: glides in, squashes on the click */
function Pointer({ t, at, x, y }: { t: number; at: number; x: number; y: number }) {
  const arrive = ease((t - (at - 0.9)) / 0.8);
  if (t < at - 0.9 || t > at + 1.2) return null;
  const px = x + (1 - arrive) * -260, py = y + (1 - arrive) * 220;
  const sq = 1 - 0.18 * Math.max(0, 1 - Math.abs(t - at) / 0.1);
  return (
    <svg width="40" height="40" viewBox="0 0 24 24" style={{ position: "absolute", left: px, top: py, transform: `scale(${sq})`, transformOrigin: "4px 3px", filter: "drop-shadow(0 2px 3px rgba(0,0,0,.35))" }}>
      <path d="M4 3l14 7.5-6.2 1.6L9 18z" fill="#111214" stroke="#fff" strokeWidth="1.6" strokeLinejoin="round" />
    </svg>
  );
}

/* ---------------- captions, screen space, left column ---------------- */
const CAPS = [
  { id: "start", n: "01", label: "start", head: "Hand it a red PR.", line: "Dependabot bumped packaging. Every test fails." },
  { id: "catch", n: "02", label: "catch", head: "It deletes a test. Kedge strikes it.", line: "Tests drop from 5 to 2. The X goes on." },
  { id: "rewind", n: "03", label: "rewind", head: "Back to the last good commit.", line: "Then the agent fixes it properly: 5/5." },
  { id: "race", n: "04", label: "the race", head: "Same sabotage. One ships short.", line: "No guard ships 2/5. Kedge keeps 5/5." },
  { id: "neatlogs", n: "05", label: "neatlogs", head: "Every step\nis a span.", line: "One trace per run, tagged with the PR and the guard." },
  { id: "entire", n: "06", label: "Entire", head: "Every agent commit is a checkpoint.", line: "Intent, files and transcript, one command away." },
  { id: "cfo", n: "07", label: "cfo.ai", head: "$10 a green PR.", line: "92.5% margin, per cfo.ai." },
  { id: "batch", n: "08", label: "real PRs", head: "4 of 9 went green.", line: "Unattended. None shipped short." },
];
function Captions({ t }: { t: number }) {
  return (
    <>
      {CAPS.map((c) => {
        const s = sec(c.id);
        if (!inSec(t, c.id)) return null;
        return <Caption key={c.id} n={c.n} label={c.label} head={c.head} line={c.line} p={(t - b(s.from) - 0.1) / 0.5} out={(t - (b(s.to) - 0.35)) / 0.3} />;
      })}
    </>
  );
}

export { Mark };
