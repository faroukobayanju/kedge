# How to rebuild the landing page and the demo video

Regenerate `site/` from two real runs, and re-render the 80-second demo film with its soundtrack.

## Prerequisites

- For the site: the two run folders in `runs/`
- For the video: [Bun](https://bun.sh), Node, `uv`, about 30 minutes for the final render

## Landing page

1. Pick a `--no-guard` run and a guarded run of the same PR, then build:

   ```bash
   uv run python scripts/build_site.py 20261010-2209-75ad 20261010-2211-58eb
   ```

2. Open `site/index.html` in a browser. The race at the top replays those two runs.

The script writes only public fields to `site/data.js` and strips local paths and the username from the Entire text. Check before publishing:

```bash
grep -ciE "/Users/|gmail" site/data.js   # expect 0
```

## Demo video

The film lives in `videos/` (Remotion 4.0.534). Every frame is a function of time, and picture and sound both read their timing from `videos/src/kedge/cues.json`.

1. Install:

   ```bash
   cd videos && bun install
   ```

2. Regenerate the soundtrack and UI sounds after any timing change. They are synthesized in code, at 120 BPM over 40 bars:

   ```bash
   uv run --with numpy python3 scripts/music.py     # writes public/audio/kedge.wav
   ```

3. Preview frames (frame numbers at 60 fps):

   ```bash
   bun scripts/stills.ts out/check 0 2160 4560 --composition Kedge
   ```

   Or open the editor with `bun run studio`.

4. Render the final film. This renders a 240 fps master, blends it to 60 fps with motion blur, then encodes:

   ```bash
   bun scripts/render.ts Kedge kedge --duration 80 --poster 0.5
   uv run --with numpy --with imageio-ffmpeg python3 scripts/verify.py out/kedge --duration 80 --bg 244,246,248
   ```

   Output: `out/kedge/kedge-1080p60-audio.mp4` (with sound), `kedge-1080p60.mp4` (muted), `kedge-1080p60.webm` and `poster.jpg`.

All numbers in the film come from `videos/src/kedge/data.ts`, which holds real run data with no keys, emails or owner accounts.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `RangeError: Frame NaN is not finite` from `stills.ts` | In zsh, pass frames as separate arguments (`"${F[@]}"`), not one quoted string. |
| `verify.py` reports `seam … JUMPS` | Expected: the film is not a loop. Only the duration and colour checks matter. |
| Sound and picture drift apart | You changed a time in `Film.tsx` without `cues.json`. Name the moment in `cues.json` `events` and use `ev("name")`. |

## Related

- [Dashboard reference: landing page](../reference/dashboard.md#the-landing-page-site)
