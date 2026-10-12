"""Voice-over from src/kedge/voice.json with macOS `say`, one wav per line, checked against the bar grid.

Run: uv run --with imageio-ffmpeg python3 scripts/voice.py [--voice "Ava (Premium)"]
Writes public/audio/vo/<id>.wav (48 kHz mono) and fails if a line runs into the next one.
"""
import json
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import imageio_ffmpeg

ROOT = Path(__file__).resolve().parent.parent
CUES = json.loads((ROOT / "src/kedge/cues.audio.json").read_text())
VO = json.loads((ROOT / "src/kedge/voice.json").read_text())
BEAT = 60 / CUES["bpm"]
END = CUES["bars"] * CUES["beatsPerBar"] * BEAT
voice = sys.argv[sys.argv.index("--voice") + 1] if "--voice" in sys.argv else VO["voice"]
out = ROOT / "public/audio/vo"
out.mkdir(parents=True, exist_ok=True)
ff = imageio_ffmpeg.get_ffmpeg_exe()


def at(bar, beat, frac):
    return ((bar - 1) * CUES["beatsPerBar"] + (beat - 1) + frac) * BEAT


lines = VO["lines"]
bad = 0
for i, line in enumerate(lines):
    with tempfile.NamedTemporaryFile(suffix=".aiff") as tmp:
        subprocess.run(["say", "-v", voice, "-r", str(VO["rate"]), "-o", tmp.name, line["text"]], check=True)
        dst = out / f"{line['id']}.wav"
        subprocess.run([ff, "-v", "error", "-y", "-i", tmp.name, "-ar", "48000", "-ac", "1", "-sample_fmt", "s16", str(dst)], check=True)
    with wave.open(str(dst)) as w:
        dur = w.getnframes() / w.getframerate()
    start = at(*line["at"])
    nxt = at(*lines[i + 1]["at"]) if i + 1 < len(lines) else END
    room = nxt - start - 0.25
    ok = dur <= room
    bad += not ok
    print(f"{line['id']:9s} {start:5.1f}s  {dur:4.1f}s of {room:4.1f}s  {'ok' if ok else 'TOO LONG'}")
print(f"voice: {voice}")
sys.exit(1 if bad else 0)
