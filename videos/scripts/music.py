"""Kedge film soundtrack and UI sounds, synthesized from src/kedge/cues.json.

The picture reads the same cues.json (bpm, sections, events), so every hit lands on its frame.
Run: uv run --with numpy python3 scripts/music.py  ->  public/audio/kedge.wav
"""
import json
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
CUES = json.loads((ROOT / "src/kedge/cues.json").read_text())
SR = 48000
BPM, BPB, BARS = CUES["bpm"], CUES["beatsPerBar"], CUES["bars"]
BEAT = 60 / BPM
DUR = BARS * BPB * BEAT
N = int(DUR * SR) + SR  # one second of tail, trimmed at the end
rng = np.random.default_rng(7)  # fixed seed: the same file every run


def b(bar, beat=1, frac=0.0):
    return ((bar - 1) * BPB + (beat - 1) + frac) * BEAT


def ev(name):
    return b(*CUES["events"][name])


def bar_range(sec_id):
    s = next(s for s in CUES["sections"] if s["id"] == sec_id)
    return s["from"], s["to"]


def lp(x, cutoff):
    """One-pole lowpass. Cutoff may be a scalar or a per-sample array."""
    a = np.exp(-2 * np.pi * np.broadcast_to(cutoff, x.shape) / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):  # ponytail: python loop, fine for short notes; whole-track filters use lp_fast
        acc = (1 - a[i]) * x[i] + a[i] * acc
        y[i] = acc
    return y


def lp_fast(x, cutoff):
    """Fixed-cutoff one-pole lowpass via an FFT of its impulse response."""
    a = np.exp(-2 * np.pi * cutoff / SR)
    n = min(len(x), int(SR * 0.5))
    h = (1 - a) * a ** np.arange(n)
    return conv(x, h)[: len(x)]


def conv(x, h):
    m = len(x) + len(h) - 1
    f = 1 << (m - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, f) * np.fft.rfft(h, f), f)[:m]


def hp(x, cutoff):
    return x - lp_fast(x, cutoff)


def add(buf, t, sig, gain=1.0):
    i = int(round(t * SR))
    if i < 0:
        sig, i = sig[-i:], 0
    j = min(len(buf), i + len(sig))
    if j > i:
        buf[i:j] += sig[: j - i] * gain


def env(n, a=0.005, d=0.2, s=0.0, r=0.0):
    """Attack then exponential decay toward s."""
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * (s + (1 - s) * np.exp(-np.maximum(0, t - a) / max(d, 1e-4)))
    if r:
        rn = min(n, int(r * SR))
        e[-rn:] *= np.linspace(1, 0, rn)
    return e


def saw(f, n, detune=0.0):
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(1, 14):
        if f * k > SR / 2.5:
            break
        out += np.sin(2 * np.pi * f * (1 + detune) * k * t) / k
    return out * 0.6


def tri(f, n):
    t = np.arange(n) / SR
    return 2 / np.pi * np.arcsin(np.sin(2 * np.pi * f * t))


def midi(m):
    return 440 * 2 ** ((m - 69) / 12)


# ---------------------------------------------------------------- arrangement
# A minor, i - VI - III - VII, one chord per bar. Sections switch parts on bar lines.
CHORDS = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G
ROOTS = [45, 41, 36, 43]


def chord(bar):
    return CHORDS[(bar - 1) % 4], ROOTS[(bar - 1) % 4]


def section_of(bar):
    for s in CUES["sections"]:
        if s["from"] <= bar < s["to"]:
            return s["id"]
    return "end"


# which parts play in each section
PARTS = {
    "cover": {"pad", "arp"},
    "start": {"pad", "arp", "kick", "hat", "bass"},
    "catch": {"pad", "arp", "kick", "hat", "bass", "clap"},
    "rewind": {"pad", "arp", "kick", "hat", "bass", "clap"},
    "race": {"pad", "arp", "kick", "hat", "bass", "clap", "lead", "open"},
    "proof": {"pad", "arp", "kick", "hat", "bass", "clap"},
    "neatlogs": {"pad", "arp", "kick", "hat", "bass", "clap"},
    "entire": {"pad", "arp", "kick", "hat", "bass", "clap"},
    "cfo": {"pad", "arp", "kick", "hat", "bass", "clap", "open"},
    "batch": {"pad", "arp", "kick", "hat", "bass", "clap", "lead", "open"},
    "end": {"pad", "arp", "kick", "hat", "bass", "clap"},
}
END_DRUMS_OUT = 42  # drums and bass leave as the logo draws; pad rings out


def parts(bar):
    p = set(PARTS[section_of(bar)])
    if bar >= END_DRUMS_OUT:
        p -= {"kick", "hat", "bass", "clap", "lead", "open", "arp"}
    return p


drums = np.zeros(N)
bass = np.zeros(N)
music = np.zeros(N)
kick_env = np.zeros(N)  # for sidechain ducking

# the rewind: the band stops for the tape to spool back, two beats of silence then the groove returns on bar 12
REW_FROM, REW_TO = ev("rewind"), b(11, 3)


def muted(t):
    return REW_FROM <= t < REW_TO


def kick():
    n = int(0.42 * SR)
    t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t / 0.035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * env(n, 0.001, 0.22) + 0.2 * np.sin(ph * 2) * env(n, 0.001, 0.03)


def clap():
    n = int(0.3 * SR)
    x = hp(rng.standard_normal(n), 900)
    e = sum(env(n, 0.001, 0.012) * (np.arange(n) >= int(k * SR)) for k in (0, 0.011, 0.022))
    return x * (e + 0.6 * env(n, 0.02, 0.12)) * 0.5


def hat(open_=False):
    n = int((0.25 if open_ else 0.06) * SR)
    return hp(rng.standard_normal(n), 7000) * env(n, 0.001, 0.09 if open_ else 0.018) * 0.35


K, CL, H, HO = kick(), clap(), hat(), hat(True)

for bar in range(1, BARS + 1):
    p = parts(bar)
    notes, root = chord(bar)
    for beat in range(BPB):
        t = b(bar, beat + 1)
        if "kick" in p and not muted(t):
            add(drums, t, K, 0.9)
            add(kick_env, t, env(int(0.3 * SR), 0.001, 0.12))
        if "clap" in p and beat in (1, 3) and not muted(t):
            add(drums, t, CL, 0.55)
        for half in (0, 0.5):
            th = t + half * BEAT
            if "hat" in p and not muted(th):
                add(drums, th, H, 0.5 if half else 0.25)
        if "open" in p and not muted(t + 0.5 * BEAT):
            add(drums, t + 0.5 * BEAT, HO, 0.25)
    # bass: root on eighths, octave jump on the last eighth of the bar
    if "bass" in p:
        for k in range(8):
            t = b(bar) + k * BEAT / 2
            if muted(t):
                continue
            m = root + (12 if k == 7 else 0)
            n = int(BEAT / 2 * SR * 0.9)
            sig = saw(midi(m), n) * env(n, 0.004, 0.16, 0.25, 0.02)
            add(bass, t, lp(sig, 380 + 900 * env(n, 0.001, 0.05)), 0.55)
    # pad: whole-bar chord, detuned pair, soft attack
    if "pad" in p:
        n = int(BPB * BEAT * SR * 1.15)
        sig = sum(saw(midi(m), n, d) for m in notes for d in (-0.004, 0.004)) / 6
        sig *= env(n, 0.35, 3.0, 0.7, 0.4)
        add(music, b(bar), sig, 0.22)
    # arp: sixteenths over the chord, upper octave
    if "arp" in p:
        seq = [notes[0] + 12, notes[1] + 12, notes[2] + 12, notes[1] + 12]
        for k in range(16):
            t = b(bar) + k * BEAT / 4
            if muted(t):
                continue
            n = int(0.22 * SR)
            add(music, t, tri(midi(seq[k % 4]), n) * env(n, 0.002, 0.08), 0.09 if k % 4 else 0.13)

# lead: a short motif that climbs on the race and the batch, two bars call, two bars answer
MOTIF = [(0, 76, 1.5), (1.5, 74, 0.5), (2, 72, 1), (3, 71, 1), (4, 72, 1.5), (5.5, 74, 0.5), (6, 76, 2)]
for bar in range(1, BARS + 1, 2):
    if "lead" not in parts(bar):
        continue
    for off, m, ln in MOTIF:
        t = b(bar) + off * BEAT
        n = int(ln * BEAT * SR)
        sig = (saw(midi(m), n, 0.003) * 0.5 + tri(midi(m), n)) * env(n, 0.01, 0.5, 0.5, 0.06)
        add(music, t, lp(sig, 2400), 0.07)

# the rewind: a tape spool, falling pitch, under the pause
n = int((REW_TO - REW_FROM + 0.2) * SR)
tt = np.arange(n) / SR
f = 900 * np.exp(-tt * 2.2) + 80
spool = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 + hp(rng.standard_normal(n), 2000) * 0.25
add(music, REW_FROM, spool * env(n, 0.01, 0.6, 0.2, 0.1), 0.18)

# sidechain: pad, arp and bass breathe under the kick
duck = 1 - 0.55 * np.clip(kick_env, 0, 1)
# energy per section: the race and the batch are the peaks, the tool scenes sit back
ENERGY = {"cover": 1.0, "start": 0.55, "catch": 0.7, "rewind": 0.7, "race": 1.0, "proof": 0.6, "neatlogs": 0.6,
          "entire": 0.62, "cfo": 0.8, "batch": 1.0, "end": 0.75}
groove = np.ones(N)
for bar in range(1, BARS + 1):
    groove[int(b(bar) * SR): int(b(bar + 1) * SR)] = ENERGY[section_of(bar)]
groove = lp_fast(groove, 3.0)  # ease between sections over ~50 ms
mix = (drums + bass * duck) * groove + music * duck * (0.7 + 0.3 * groove)

# master fade-out over the last bar and a half
fade = np.ones(N)
fs, fe = int(b(BARS - 1, 3) * SR), int(DUR * SR)
fade[fs:fe] = np.linspace(1, 0, fe - fs) ** 2
fade[fe:] = 0
mix *= fade

# ---------------------------------------------------------------- UI sounds
sfx = np.zeros(N)


def s_click():
    n = int(0.05 * SR)
    return (np.sin(2 * np.pi * 1800 * np.arange(n) / SR) * env(n, 0.0005, 0.006) + hp(rng.standard_normal(n), 3000) * env(n, 0.0003, 0.003) * 0.6)


def s_tick():
    n = int(0.03 * SR)
    return hp(rng.standard_normal(n), 2500) * env(n, 0.0003, 0.004) + np.sin(2 * np.pi * (900 + 400 * rng.random()) * np.arange(n) / SR) * env(n, 0.0005, 0.005) * 0.4


def s_strike():
    # china marker dragged across glass: filtered noise with a rising squeak
    n = int(0.55 * SR)
    t = np.arange(n) / SR
    scratch = lp(hp(rng.standard_normal(n), 1200), 5000) * (env(n, 0.01, 0.12) + 0.8 * env(n, 0.01, 0.12) * (t > 0.27))
    squeak = np.sin(2 * np.pi * np.cumsum(1200 + 500 * t) / SR) * env(n, 0.02, 0.08) * 0.15
    return (scratch + squeak) * 0.8


def s_ring():
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    return lp(hp(rng.standard_normal(n), 1500), 4000) * np.sin(np.pi * np.clip(t / 0.55, 0, 1)) * 0.5


def s_whoosh(length=0.9):
    n = int(length * SR)
    t = np.arange(n) / SR
    cut = 300 + 3500 * np.sin(np.pi * np.clip(t / length, 0, 1)) ** 2
    return lp(rng.standard_normal(n), cut) * np.sin(np.pi * np.clip(t / length, 0, 1)) ** 1.5 * 0.9


def s_print():
    # a sheet of paper laid on glass: a short swish, then a soft thud
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    thud = np.sin(2 * np.pi * (90 + 60 * np.exp(-t / 0.02)) * t) * env(n, 0.002, 0.07)
    out = np.zeros(n)
    sw = s_whoosh(0.3)
    out[: len(sw)] += sw * 0.5
    i = int(0.24 * SR)
    out[i:] += thud[: n - i] * 0.9 + hp(rng.standard_normal(n - i), 1500) * env(n - i, 0.001, 0.015) * 0.3
    return out


def bell(m, length=1.4, g=1.0):
    n = int(length * SR)
    t = np.arange(n) / SR
    f = midi(m)
    return g * (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t / 0.2)) * env(n, 0.002, 0.5)


def s_rewind():
    return np.zeros(1)  # the tape spool lives in the music bed


SOUNDS = {"click": s_click, "strike": s_strike, "ring": s_ring, "whoosh": s_whoosh, "print": s_print,
          "rewind": s_rewind, "ping": lambda: bell(88, 1.2), "chime": lambda: sum(bell(m, 2.6, 0.5) for m in (69, 76, 81, 84))}

# each sound's transient: where its loudest moment sits, so it lands on the cue's frame
PEAK = {"print": 0.24, "whoosh": 0.45, "ring": 0.0, "strike": 0.0}

for cue in CUES["sfx"]:
    g = cue.get("gain", 0.4)
    if cue["sound"] == "typing":
        t0, t1, chars = ev(cue["from"]), ev(cue["to"]), cue["chars"]
        for k in range(1, chars + 1):  # one tick each time the picture adds a character
            add(sfx, t0 + k * (t1 - t0) / chars, s_tick(), g * (0.7 + 0.6 * rng.random()))
        continue
    if cue["sound"] == "pings":
        for k in range(cue["count"]):
            add(sfx, ev(cue["at"]) + k * cue["stepBeats"] * BEAT, bell(84 + [0, 3, 7, 12][k % 4], 1.0), g)
        continue
    add(sfx, ev(cue["at"]) - PEAK.get(cue["sound"], 0.0), SOUNDS[cue["sound"]](), g)

# voice-over (scripts/voice.py): placed on the bar grid from voice.json, music ducks under it
VO = json.loads((ROOT / "src/kedge/voice.json").read_text())
vo = np.zeros(N)
for line in VO["lines"]:
    path = ROOT / "public/audio/vo" / f"{line['id']}.wav"
    if not path.exists():
        continue
    with wave.open(str(path)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
    add(vo, b(*line["at"]), x / (np.max(np.abs(x)) + 1e-9) * 0.9)
speaking = lp_fast((np.abs(vo) > 0.01).astype(np.float64), 4.0)  # ~40 ms smoothing of "someone is talking"
speaking = np.clip(speaking * 3, 0, 1)
mix *= 1 - 0.6 * speaking  # music sits back while the voice talks

out = mix * 0.8 + sfx * 0.9 + vo * 0.95

# small room: a short noise-tail reverb on everything except the drums' low end
ir_n = int(1.6 * SR)
ir = rng.standard_normal(ir_n) * np.exp(-np.arange(ir_n) / SR / 0.35)
ir = lp_fast(ir, 6000)
ir /= np.sqrt(np.sum(ir ** 2))
wet = conv(hp(music * duck + sfx, 200), ir)[:N]
out += wet * 0.18

out = out[: int(DUR * SR)]
peak = np.max(np.abs(out))
out = np.tanh(out / peak * 1.3) / np.tanh(1.3) * 0.89  # gentle soft clip, about -1 dBFS

dst = ROOT / "public/audio/kedge.wav"
dst.parent.mkdir(parents=True, exist_ok=True)
pcm = (np.stack([out, out], 1) * 32767).astype(np.int16)
with wave.open(str(dst), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"{dst}  {DUR:.1f}s  {BARS} bars @ {BPM} bpm  sfx={len(CUES['sfx'])}")
