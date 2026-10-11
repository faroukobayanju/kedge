import type { CSSProperties, ReactNode } from "react";
import { C, F } from "./tokens";
import type { Frame } from "./data";

export const clamp01 = (v: number) => Math.min(1, Math.max(0, v));
export const ease = (u: number) => 1 - Math.pow(1 - clamp01(u), 3);

/* ---------- the Kedge mark (kedge/ui/logo.svg), with a draw-on for the red hook ---------- */
export function Mark({ size = 64, draw = 1 }: { size?: number; draw?: number }) {
  const holes = [12, 40, 66, 94];
  return (
    <svg width={size} height={size} viewBox="0 0 120 120" style={{ display: "block" }}>
      <rect x="0" y="0" width="120" height="120" rx="10" fill={C.rebate} />
      {holes.map((x) => <rect key={`t${x}`} x={x} y="9" width="14" height="9" rx="2" fill="#fff" />)}
      {holes.map((x) => <rect key={`b${x}`} x={x} y="102" width="14" height="9" rx="2" fill="#fff" />)}
      <rect x="10" y="26" width="100" height="68" fill={C.frame} />
      <path d="M93 44 C 92 33, 70 30, 56 35 C 40 41, 34 58, 44 70 C 54 81, 78 80, 88 68" pathLength={1}
        fill="none" stroke={C.marker} strokeWidth="9" strokeLinecap="round" strokeDasharray="1" strokeDashoffset={1 - clamp01(draw * 1.25)} />
      <path d="M78 32 L 95 45 L 102 26" pathLength={1} fill="none" stroke={C.marker} strokeWidth="9" strokeLinecap="round"
        strokeLinejoin="round" strokeDasharray="1" strokeDashoffset={1 - clamp01((draw - 0.75) * 4)} />
    </svg>
  );
}
export function Lockup({ size = 1, draw = 1 }: { size?: number; draw?: number }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 22 * size }}>
      <Mark size={84 * size} draw={draw} />
      <span style={{ font: `900 ${78 * size}px/1 ${F.set}`, letterSpacing: "0.06em", color: C.ink }}>KEDGE</span>
    </div>
  );
}

/* ---------- china-marker strokes (pathLength=1 so `p` is the share drawn) ---------- */
const W = 236 + 36, H = 178 + 36;
export function XMark({ p }: { p: number }) {
  const a = clamp01(p * 2), b = clamp01(p * 2 - 1);
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", left: -18, top: -18, overflow: "visible", pointerEvents: "none" }}>
      <path d={`M ${W * .14} ${H * .16} Q ${W * .48} ${H * .52} ${W * .88} ${H * .86}`} pathLength={1} fill="none" stroke={C.marker} strokeWidth={8} strokeLinecap="round" strokeDasharray="1" strokeDashoffset={1 - a} opacity={.93} />
      <path d={`M ${W * .86} ${H * .14} Q ${W * .55} ${H * .45} ${W * .12} ${H * .88}`} pathLength={1} fill="none" stroke={C.marker} strokeWidth={8} strokeLinecap="round" strokeDasharray="1" strokeDashoffset={1 - b} opacity={.93} />
    </svg>
  );
}
export function Ring({ p }: { p: number }) {
  const cx = W / 2, cy = H / 2, rx = W * .5, ry = H * .5;
  const d = `M ${cx - rx * .2} ${cy - ry * .98} C ${cx + rx * .7} ${cy - ry * 1.08}, ${cx + rx * 1.05} ${cy - ry * .2}, ${cx + rx * .96} ${cy + ry * .3}
    C ${cx + rx * .86} ${cy + ry * .98}, ${cx - rx * .5} ${cy + ry * 1.06}, ${cx - rx * .95} ${cy + ry * .4}
    C ${cx - rx * 1.08} ${cy - ry * .3}, ${cx - rx * .6} ${cy - ry * 1.02}, ${cx + rx * .15} ${cy - ry * .9}`;
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", left: -18, top: -18, overflow: "visible", pointerEvents: "none" }}>
      <path d={d} pathLength={1} fill="none" stroke={C.marker} strokeWidth={8} strokeLinecap="round" strokeDasharray="1" strokeDashoffset={1 - clamp01(p)} opacity={.93} />
    </svg>
  );
}
export function Note({ text, p, where, mono }: { text: ReactNode; p: number; where: "up" | "down"; mono?: string }) {
  const u = ease(p);
  return (
    <div style={{
      position: "absolute", left: -4, width: 300, font: `400 22px/1.15 ${F.hand}`, color: C.markerInk,
      ...(where === "up" ? { bottom: "calc(100% + 40px)" } : { top: "calc(100% + 62px)" }),
      opacity: u, transform: `translateY(${(1 - u) * 6}px) rotate(-2deg)`,
    }}>
      {text}{mono ? <span style={{ font: `600 17px/1 ${F.mono}`, textTransform: "none" }}> {mono}</span> : null}
    </div>
  );
}

/* ---------- film strip: one cell per frame, holes cut out to the backlight ---------- */
export const CW = 258;
export type FrameFx = { dev: number; x?: number; ring?: number; note?: { text: ReactNode; p: number; where: "up" | "down"; mono?: string } };
export function Strip({ frames, fx, x = 0, blur = 0, edgeNo = "15" }: { frames: Frame[]; fx: FrameFx[]; x?: number; blur?: number; edgeNo?: string }) {
  return (
    <div style={{ display: "flex", width: "max-content", transform: `translateX(${x}px)`, filter: blur > .3 ? `blur(${blur}px)` : undefined }}>
      {frames.map((f, i) => {
        const e = fx[i] ?? { dev: 1 };
        return (
          <div key={i} style={{ position: "relative", width: CW, padding: "30px 11px 34px", background: C.rebate }}>
            {[9, null].map((top, k) => (
              <div key={k} style={{ position: "absolute", left: 0, right: 0, height: 11, display: "flex", justifyContent: "space-around", padding: "0 6px", ...(top ? { top: 9 } : { bottom: 9 }) }}>
                {[0, 1, 2, 3].map((h) => <i key={h} style={{ width: 15, height: 11, borderRadius: 2, background: C.glassHot }} />)}
              </div>
            ))}
            <div style={{
              position: "relative", height: 178, padding: "18px 16px 16px", background: f.kind === "plan" ? C.frame2 : C.frame,
              display: "flex", flexDirection: "column", gap: 8, filter: `brightness(${0.08 + 0.92 * clamp01(e.dev)}) contrast(${1.4 - 0.4 * clamp01(e.dev)})`,
            }}>
              <span style={{ font: `900 ${f.kind === "plan" || f.fs.length > 5 ? 40 : 54}px/.9 ${F.set}`, letterSpacing: "-0.02em", color: f.lost ? C.lostPos : f.won ? C.keepPos : C.fType }}>{f.fs}</span>
              <span style={{ font: `500 15px/1.4 ${F.set}`, color: C.fCap, display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical", overflow: "hidden" }}>{f.fa}</span>
              {e.x !== undefined && <XMark p={e.x} />}
              {e.ring !== undefined && <Ring p={e.ring} />}
              {e.note && <Note {...e.note} />}
            </div>
            <span style={{ position: "absolute", left: 11, bottom: -1, transform: "translateY(100%)", paddingTop: 7, font: `600 12px/1 ${F.mono}`, color: C.edgeInk, letterSpacing: ".14em", whiteSpace: "nowrap" }}>
              KEDGE {edgeNo} ▸ {i + 1}{i === frames.length - 1 ? "A" : ""} · {f.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}

/* ---------- the print: one huge word ---------- */
export function Print({ big, word, why, who, kind, style }: { big: string; word: string; why: string; who: string; kind: "keep" | "short"; style?: CSSProperties }) {
  return (
    <div style={{ width: 560, padding: "22px 22px 18px", background: C.print, boxShadow: "0 30px 60px -20px rgba(17,18,20,.35), 0 2px 6px rgba(17,18,20,.12)", ...style }}>
      <div style={{ background: C.frame, color: "#f4f5f7", padding: "22px 26px 20px", display: "grid", gridTemplateColumns: "1fr auto", alignItems: "end", gap: "6px 20px" }}>
        <span style={{ font: `900 112px/.82 ${F.set}`, letterSpacing: "-0.04em" }}>{big}</span>
        <span style={{ font: `900 30px/1 ${F.set}`, letterSpacing: ".14em", textTransform: "uppercase", textAlign: "right", color: kind === "keep" ? C.keepPos : C.lostPos }}>{word}</span>
        <span style={{ gridColumn: "1 / -1", font: `500 15px/1.4 ${F.set}`, color: C.fCap }}>{why}</span>
      </div>
      <div style={{ display: "flex", alignItems: "center", marginTop: 16 }}>
        <span style={{ font: `600 13px/1 ${F.mono}`, letterSpacing: ".1em", color: C.ink2 }}>{who}</span>
        <span style={{ marginLeft: "auto", font: `400 24px/1 ${F.hand}`, color: kind === "keep" ? C.keep : C.markerInk }}>{kind === "keep" ? "checked by Kedge" : "unchecked"}</span>
      </div>
    </div>
  );
}

/* ---------- laptop: the product rebuilt inside a device ---------- */
export const SCREEN = { w: 1440, h: 900 };
export function Laptop({ children }: { children: ReactNode }) {
  return (
    <div style={{ position: "relative", width: SCREEN.w + 56, }}>
      <div style={{ padding: 28, paddingBottom: 34, background: "#16171a", borderRadius: "26px 26px 8px 8px", boxShadow: "0 50px 90px -30px rgba(17,18,20,.45), 0 0 0 2px #2b2d31 inset" }}>
        <div style={{ position: "relative", width: SCREEN.w, height: SCREEN.h, overflow: "hidden", borderRadius: 6, background: C.glass }}>{children}</div>
      </div>
      <div style={{ position: "relative", left: -90, width: SCREEN.w + 56 + 180, height: 34, background: "linear-gradient(#d6dae0, #aeb4bc)", borderRadius: "0 0 22px 22px", boxShadow: "0 24px 40px -18px rgba(17,18,20,.4)" }}>
        <div style={{ position: "absolute", left: "50%", top: 0, width: 240, height: 12, transform: "translateX(-50%)", background: "#9aa1aa", borderRadius: "0 0 10px 10px" }} />
      </div>
    </div>
  );
}

/* ---------- Kedge UI chrome inside the laptop (kedge/ui/index.html lab bar) ---------- */
export function LabBar({ sub, tally, pressed }: { sub: string; tally: string; pressed?: number }) {
  return (
    <div style={{ height: 76, display: "flex", alignItems: "center", gap: 24, padding: "0 28px", background: C.glass, borderBottom: `1px solid ${C.glassEdge}` }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 12, padding: "8px 14px 7px", background: C.print, border: `1.5px solid ${C.ink}`, transform: "rotate(-1.2deg)", boxShadow: "0 2px 6px rgba(17,18,20,.12)" }}>
        <span style={{ font: `900 26px/1 ${F.set}`, letterSpacing: ".06em" }}>KEDGE</span>
        <span style={{ font: `400 18px/1 ${F.hand}`, color: C.markerInk }}>{sub}</span>
      </div>
      <span style={{ font: `600 14px/1.3 ${F.mono}`, color: C.ink2 }}>{tally}</span>
      <div style={{ marginLeft: "auto", display: "flex", gap: 14 }}>
        <span style={{ display: "inline-flex", alignItems: "center", height: 40, padding: "0 16px", border: `1.5px solid ${C.ink}`, borderRadius: 999, font: `700 14px/1 ${F.set}`, letterSpacing: ".08em" }}>RACE</span>
        <span style={{ display: "inline-flex", alignItems: "center", gap: 10, height: 52, padding: "0 24px 0 20px", borderRadius: 999, background: C.markerInk, color: "#fff", font: `800 17px/1 ${F.set}`, letterSpacing: ".1em", transform: `scale(${1 - 0.06 * (pressed ?? 0)})` }}>
          <svg width="18" height="18" viewBox="0 0 24 24"><path d="M7 4.5v15l12-7.5z" fill="#fff" /></svg>REPLAY
        </span>
      </div>
    </div>
  );
}

/* ---------- caption beside each step: number, label, headline, one line ---------- */
export function Caption({ n, label, head, line, p, out }: { n: string; label: string; head: string; line: string; p: number; out: number }) {
  const u = ease(p), o = ease(out);
  const show = u * (1 - o);
  return (
    <div style={{ position: "absolute", left: 96, top: 300, width: 520, opacity: show, filter: `blur(${(1 - u) * 10 + o * 10}px)`, transform: `translateY(${(1 - u) * 30 - o * 20}px)` }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 18 }}>
        <span style={{ font: `900 120px/.8 ${F.set}`, letterSpacing: "-0.03em", color: C.ink }}>{n}</span>
        <span style={{ font: `400 38px/1 ${F.hand}`, color: C.markerInk, transform: "rotate(-2deg)", display: "inline-block" }}>{label}</span>
      </div>
      <h2 style={{ whiteSpace: "pre-line", margin: "34px 0 0", font: `800 62px/1.02 ${F.set}`, letterSpacing: "-0.02em", color: C.ink }}>{head}</h2>
      <p style={{ margin: "22px 0 0", font: `500 30px/1.35 ${F.set}`, color: C.ink2 }}>{line}</p>
    </div>
  );
}

export function Lightbox({ children }: { children?: ReactNode }) {
  return <div style={{ position: "absolute", inset: 0, background: `radial-gradient(120% 80% at 55% 40%, ${C.glassHot} 0%, ${C.glass} 58%, ${C.glassLow} 100%)` }}>{children}</div>;
}
