---
name: Kedge
description: A run is a strip of film on a lightbox; Kedge is the editor with the red china marker.
colors:
  glass: "#f4f6f8"
  glass-hot: "#ffffff"
  glass-falloff: "#e9edf1"
  glass-edge: "#dfe4ea"
  rebate: "#0b0b0c"
  frame: "#1b1d21"
  frame-2: "#24272d"
  frame-type: "#f2f3f5"
  frame-caption: "#ccd1d8"
  print: "#fbfbfa"
  code-wash: "#e8ecf0"
  ink: "#111214"
  ink-2: "#4a4f57"
  ink-3: "#6b717a"
  marker: "#e3241b"
  marker-ink: "#b0170f"
  marker-hover: "#c41c13"
  catch-positive: "#ff9a92"
  grease: "#f2b705"
  grease-ink: "#7d5c00"
  keep: "#0b7346"
  keep-positive: "#7cf0bd"
  edge: "#d26a1b"
  edge-ink: "#9a4a0e"
typography:
  verdict-score:
    fontFamily: "Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "112px"
    fontWeight: 900
    lineHeight: 0.82
    letterSpacing: "-0.04em"
    fontFeature: "\"tnum\""
  display:
    fontFamily: "Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "64px"
    fontWeight: 900
    lineHeight: 0.8
    letterSpacing: "-0.02em"
  frame-score:
    fontFamily: "Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "52px"
    fontWeight: 900
    lineHeight: 0.9
    letterSpacing: "-0.02em"
  verdict-word:
    fontFamily: "Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "30px"
    fontWeight: 900
    lineHeight: 1
    letterSpacing: "0.14em"
  headline:
    fontFamily: "Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "30px"
    fontWeight: 800
    lineHeight: 1.1
  title:
    fontFamily: "Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "26px"
    fontWeight: 800
    lineHeight: 1.1
  wordmark:
    fontFamily: "Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "26px"
    fontWeight: 900
    lineHeight: 1
    letterSpacing: "0.06em"
  body:
    fontFamily: "Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.45
    fontFeature: "\"tnum\""
  action:
    fontFamily: "Archivo, Helvetica Neue, Arial, sans-serif"
    fontSize: "17px"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "0.1em"
  hand:
    fontFamily: "Permanent Marker, Marker Felt, cursive"
    fontSize: "22px"
    fontWeight: 400
    lineHeight: 1.15
  hand-big:
    fontFamily: "Permanent Marker, Marker Felt, cursive"
    fontSize: "34px"
    fontWeight: 400
    lineHeight: 1.2
  edge-print:
    fontFamily: "JetBrains Mono, ui-monospace, Menlo, monospace"
    fontSize: "11px"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "0.14em"
  mono:
    fontFamily: "JetBrains Mono, ui-monospace, Menlo, monospace"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.6
rounded:
  paper: "0px"
  sprocket: "2px"
  stamp: "3px"
  pill: "999px"
spacing:
  gutter: "40px"
  gutter-mobile: "16px"
  frame-width: "236px"
  frame-gap: "22px"
  frame-width-mobile: "190px"
  frame-gap-mobile: "14px"
  paper-pad: "22px"
  section-gap: "50px"
components:
  button-replay:
    backgroundColor: "{colors.marker-ink}"
    textColor: "{colors.glass-hot}"
    typography: "{typography.action}"
    rounded: "{rounded.pill}"
    padding: "0 24px 0 20px"
    height: "52px"
  button-replay-hover:
    backgroundColor: "{colors.marker-hover}"
  button-pill:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    padding: "0 16px"
    height: "40px"
  button-pill-pressed:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.glass-hot}"
  button-open-pr:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.glass-hot}"
    rounded: "{rounded.pill}"
    padding: "0 16px"
    height: "40px"
  film-cell:
    backgroundColor: "{colors.rebate}"
    padding: "30px 11px 34px"
    width: "258px"
  frame:
    backgroundColor: "{colors.frame}"
    textColor: "{colors.frame-type}"
    rounded: "{rounded.paper}"
    padding: "18px 16px 16px"
    height: "178px"
  frame-plan:
    backgroundColor: "{colors.frame-2}"
  print:
    backgroundColor: "{colors.print}"
    textColor: "{colors.ink}"
    rounded: "{rounded.paper}"
    padding: "22px 22px 18px"
    width: "560px"
  print-image:
    backgroundColor: "{colors.frame}"
    textColor: "{colors.frame-type}"
    typography: "{typography.verdict-score}"
    padding: "22px 26px 20px"
  slip:
    backgroundColor: "{colors.print}"
    textColor: "{colors.ink}"
    rounded: "{rounded.paper}"
    padding: "20px 22px 18px"
    width: "420px"
  plan-slip:
    backgroundColor: "{colors.print}"
    textColor: "{colors.ink-2}"
    typography: "{typography.mono}"
    padding: "20px 22px"
  sheet:
    backgroundColor: "{colors.print}"
    textColor: "{colors.ink}"
    rounded: "{rounded.paper}"
    padding: "14px 14px 12px"
  stamp:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.edge-print}"
    rounded: "{rounded.stamp}"
    padding: "9px 12px 8px"
  lab-label:
    backgroundColor: "{colors.print}"
    textColor: "{colors.ink}"
    typography: "{typography.wordmark}"
    rounded: "{rounded.paper}"
    padding: "8px 14px 7px"
---

# Design System: Kedge

## Overview

**Creative North Star: "Contact Sheet on the Lightbox"**

A run is a strip of film laid on a backlit lightbox, and Kedge is the editor leaning over it with a red china marker. Every surface is a physical object on that glass: black film rebate with real sprocket cutouts the light shines through, dark frame positives carrying white set type, cream paper (prints, slips, sheets, stamps) tilted where a hand dropped it, and marker strokes drawn on top as if by a person. Nothing is a dashboard widget. Structure is the ornament: sprockets count frames, edge print numbers them, the circle and the X are the data.

The system is an Experience-mode world: it performs. Frames develop out of black as they feed through the gate, the X stroke-draws over a cheat, the strip rewinds with reel inertia and motion blur to the circled checkpoint, then the strip is cut into contact rows and the keeper lifts off the sheet as one enlarged print with one huge score and one huge word. Density is low on the glass and high on paper: the lightbox stays bright and open; evidence lives on typed slips.

Color is disciplined by meaning, not decoration. The glass and film are neutral; red belongs to the editor's hand, yellow belongs only to the agent's lie, green belongs only to what was kept, orange belongs only to the film's own edge print. The world rejects the dashboard: no cards, no sidebar table, no section kickers.

**Key Characteristics:**
- Backlit glass ground, brightest under the film, falling off toward the edges.
- Film rebate cells with four sprocket cutouts top and bottom per frame, showing the backlight.
- Orange mono edge print under every frame, numbering it like stock.
- Red china-marker strokes and Permanent Marker notes as the only hand on the page.
- Paper objects (print, slip, plan slip, sheet stack, stamps) instead of cards.
- Spring physics with intent: crisp feed, loose heavy rewind, needle-settling score.

## Colors

A cool, near-white lightbox and near-black film carry everything; four meaning-locked inks do the talking.

### Primary
- **China-Marker Red** (marker): the editor's stroke. X over drift and over a shipped-short final frame, the ring around the checkpoint and the keeper, the focus ring. Stroke use only (7px, ~93% opacity); never body text.
- **Marker Ink** (marker-ink): the readable red. Handwritten notes ("hauled back to", "off the plan", "keeper"), the Replay button fill, the unguarded lane name, shipped-short and gave-up verdicts on paper, the Entire checkpoint stamp. Hover deepens to Marker Hover (marker-hover) on the Replay button only.
- **Catch Positive** (catch-positive): red as it reads on a dark positive. Lost step scores on frames ("2/5") and the SHIPPED SHORT / GAVE UP word on the print image.

### Secondary
- **Grease Pencil Yellow** (grease): the agent's false claim. The underline stroke on a false-claim frame and the false-claim tick on a sheet's mini film. Also the text selection highlight, the one sanctioned non-claim use.
- **Grease Ink** (grease-ink): readable yellow-brown for the false-claim note ("agent: ... tests: 2/5") and the "claim overruled" log heading.

### Tertiary
- **Keep Green** (keep): verified-good outcomes on paper and glass: the Kept verdict on a sheet, "checked by Kedge" on the print, the guarded "Kedge" lane name in a race, a passing CI stamp, and "No cheats on this sheet".
- **Keep Positive** (keep-positive): green on a dark positive: the "Green" final frame, the KEPT word on the print, the keeper tick on a sheet's mini film.
- **Edge-Print Orange** (edge): the film stock's own colour. Frame hover / open outline (2px, 3px offset).
- **Edge Ink** (edge-ink): edge-print numerals under the rebate, the "Developing" verdict, the neatlogs trace stamp.

### Neutral
- **Backlit Glass** (glass): page and lab bar ground. **Hot Glass** (glass-hot) is the centre of the backlight radial (120% x 70% at 50% 34%) and the colour of every sprocket cutout; **Glass Falloff** (glass-falloff) is the radial's edge. **Glass Edge** (glass-edge) is the lab bar's 1px bottom rule.
- **Film Rebate** (rebate): the strip, mini film on sheets, the loupe's interior.
- **Frame Positive** (frame) and **Plan Positive** (frame-2): step / final frames and the print image; plan and replan frames sit one step lighter. **Frame Type** (frame-type) and **Frame Caption** (frame-caption) are the white set type and grey caption on positives.
- **Print Stock** (print): every paper object. **Code Wash** (code-wash): inline code on glass; on paper, code drops the wash and goes 600 weight.
- **Ink** (ink), **Ink 2** (ink-2), **Ink 3** (ink-3): text, secondary text, labels and dt terms.

### Contrast notes
Measured WCAG ratios on the built pairs: ink on glass 17.3:1; ink-2 on glass 7.6:1; ink-3 on print 4.75:1 and on glass 4.54:1 (small labels only, nothing lighter). Marker-ink on glass 6.5:1, on print 6.8:1; white on marker-ink 7.1:1. Edge-ink on glass 5.8:1, grease-ink on glass 5.7:1. On positives: frame-type 15.2:1, frame-caption 11.0:1, keep-positive 12.1:1, catch-positive 8.3:1. Raw marker (4.3:1) and raw edge (3.3:1) never carry text on glass; that is why the -ink variants exist. Keep Green (#0b7346) measures 5.45:1 on glass and 5.71:1 on print, so it passes AA at every size it is set.

### Named Rules
**The One Hand Rule.** Red is the editor's hand and nothing else: catches, the rewind's checkpoint ring, the keeper ring, the primary Replay action, and annotations. Red never fills a panel or tints a background.

**The Liar's Yellow Rule.** Grease yellow appears only where the agent claimed something the tests contradict. If there is no false claim on screen, there is no yellow (text selection excepted).

**The Kept Green Rule.** Green means verified good: a kept verdict, a passing check, the guarded side. Never use it for "success" styling of controls or for running state.

**The Ink-Not-Stroke Rule.** Every mark colour exists twice: a raw stroke value for drawn marks and an -ink (or -positive) value for text. Text always takes the -ink value on light and the -positive value on frames.

## Typography

**Display Font:** Archivo (with Helvetica Neue, Arial), self-hosted 400/600/800/900
**Hand Font:** Permanent Marker (with Marker Felt, cursive), self-hosted 400
**Label/Mono Font:** JetBrains Mono (with ui-monospace, Menlo), self-hosted 400/600

**Character:** Archivo is the set type of a lab: heavy, tight, tabular, built for one huge number. Permanent Marker is the editor's hand on top of it. JetBrains Mono is what the machine printed: edge numbers, SHAs, code, slips.

### Hierarchy
- **Verdict Score** (900, 112px / 76px under 900px, 0.82, -0.04em): the score on the enlarged print. One per print.
- **Display** (900, 64px / 46px mobile, 0.8, -0.02em): the run number beside the reel title ("15", or "vs" in a race).
- **Frame Score** (900, 52px, 0.9, -0.02em; 38px on plan frames): the step score or word printed on a positive.
- **Verdict Word** (900, 30px / 22px mobile, 0.14em, uppercase): KEPT, SHIPPED SHORT, GAVE UP on the print image.
- **Headline** (800, 30px / 22px mobile, 1.1, max 34ch, balanced): the PR title on the bench.
- **Title** (800, 26-28px, 1.1): section heads on glass ("Editor's notes", "The plan", "Sheets"); 24px for race lane names; 22px for slip heads.
- **Wordmark** (900, 26px / 22px mobile, 0.06em, uppercase): KEDGE on the lab label.
- **Body** (400, 15px, 1.45, tabular nums; max 66ch in notes): running text. Frame captions are 13px/1.4, print reasons 14px/1.4.
- **Action** (800, 17px, 0.1em, uppercase): the Replay button; secondary pills and Open PR run 14px with 0.06-0.08em.
- **Hand** (400, 17-22px, 1.15; 34px for empty-state lines): marker notes, verdicts on sheets, slip and log annotations, signatures on the print.
- **Edge Print** (600, 11px, 0.14em): the frame numbering under the rebate; stamps reuse it uppercase at 0.12em with an 800 Archivo value line.
- **Mono** (400, 13px, 1.6): the plan slip; 12-14px for sheet subs, captions on prints, the tally (600), SHAs inside notes (600).

### Named Rules
**The One Huge Word Rule.** Each print carries exactly one huge score and one huge verdict word. Nothing else on the screen competes with the 112px score.

**The Hand Is Only For Marks Rule.** Permanent Marker sets only what an editor would write by hand: annotations, verdicts, signatures, hints. It never sets a heading, a button, a number to compare, or body copy.

**The Machine Print Rule.** Anything a machine stamped (edge numbers, SHAs, PR refs, code, plans as typed) is JetBrains Mono. Set type for people is Archivo.

**The Base Denominator Rule.** Every score is passed / max(step total, the run's base total): a run that deleted three of five tests reads 2/5, never 2/2. The denominator never animates; only the numerator settles. No measured step reads "–" on paper and "?" on a frame.

## Layout

The lightbox is full-bleed under a sticky 76px lab bar (28px side padding). The bench uses a 40px gutter (16px under 900px). The film strip spans the viewport inside an overflow-hidden gate (74px top, 100px bottom padding to leave room for notes above and below), translated so the active frame sits at centre; a white 110px bloom behind the centre frame is the gate's backlight and fades once the strip is laid down.

Each film cell is frame width plus gap (236 + 22px; 190 + 14px under 900px), with 30px rebate above and 34px below the 178px frame. After playback the strip "lays down": it wraps into contact rows across the full width with 110px row gaps so every frame and every mark stays visible. The print(s) centre below with a 34px gap between race prints. Notes ("editor's notes" and "the plan") sit in a two-column envelope (1.15fr / 1fr, 50px gap, max 1280px) that stacks under 900px. The sheet stack opens as a fixed near-opaque glass overlay with an auto-fill grid of 260px-min sheets (30px row, 26px column gaps). The frame slip docks fixed bottom-right (28px inset; 16px on mobile), max 420px.

Breakpoint: one, at 900px. Below it the lab bar wraps (tally on its own line), the Replay label hides to its icon, sizes step down as listed, and the loupe is disabled.

## Elevation & Depth

Depth is physical: things are either on the glass, in the film, or paper lying on top. The glass itself is lit (a radial from hot white under the film to a cooler falloff). Film is flat and shadowless; it is a transparency on the glass. Paper casts soft, offset-down, negative-spread shadows tinted from ink, deeper the more recently it was laid (sheet < plan slip < slip < print). There are no hard offset shadows and no borders on paper.

### Shadow Vocabulary
- **Label** (`box-shadow: 0 2px 6px rgba(17,18,20,.12)`): the lab label stuck to the bar.
- **Sheet rest / lifted** (`0 10px 24px -10px rgba(17,18,20,.35), 0 1px 3px rgba(17,18,20,.12)` / `0 18px 34px -12px rgba(17,18,20,.4)`): run sheets on the stack; hover lifts 4px and straightens.
- **Plan slip** (`0 16px 34px -14px rgba(17,18,20,.3), 0 1px 3px rgba(17,18,20,.1)`).
- **Frame slip** (`0 24px 50px -16px rgba(17,18,20,.4), 0 2px 6px rgba(17,18,20,.12)`).
- **Print** (`0 30px 60px -20px rgba(17,18,20,.35), 0 2px 6px rgba(17,18,20,.12)`): the keeper, highest paper on the box.
- **Marker glow** (`0 6px 18px rgba(176,23,15,.3)`): the Replay button only.
- **Loupe** (`0 18px 40px rgba(17,18,20,.35)` plus `inset 0 0 34px rgba(0,0,0,.55)` vignette).
- **Backlight bloom** (`0 0 110px 30px #fff`): the gate behind the centre frame.

### Named Rules
**The Paper Lies Down Rule.** Paper is tilted where a hand dropped it (label -1.2deg, sheets cycling -1.4 / 0.9 / -0.4deg, slip -0.8deg, plan slip 0.7deg, print resting at -1.4deg, stamps ±1.5-2deg) and straightens on hover. Film and frames are never tilted.

**The Cutout Rule.** Sprocket holes are cutouts, not decoration: they are filled with the hot backlight colour, never grey, never the ground.

## Shapes

Paper and film are square-cornered (0px); the only rounding is physical. Sprocket cutouts are 15 x 11px with 2px corners, four per frame on each rebate edge. Stamps are rubber stamps: 2px currentColor border, 3px corners. Controls are full pills (999px): Replay, Race, Open PR. The loupe is a circle with a 7px ink bezel. Marker strokes are round-capped, round-joined 7px paths drawn as a person would: the X leans and bows (two quadratic strokes), the ring is an open, overshooting loop that ends past its start, the false-claim underline wobbles.

## Components

### Buttons
Pills on the lab bar and the print, set in uppercase Archivo with tracking.
- **Shape:** full pill (999px).
- **Replay (primary):** marker-ink fill, white, 52px tall (46px mobile), play icon plus label, marker glow; hover lifts 1px and deepens to marker-hover. The only filled red control.
- **Race (toggle):** 40px, transparent with 1.5px ink outline; pressed state fills ink with hot-glass text.
- **Open PR:** 40px ink pill on the print's caption, white text, PR icon; hover lightens slightly.
- **Focus:** every focusable element takes a 3px marker outline at 3px offset.

### Film strip and frames (signature)
- **Cell:** rebate black, one per step, carrying its own top and bottom sprocket rows and its own edge print, so cells can be cut apart into contact rows.
- **Frame:** a dark positive (frame; plan and replan on frame-2), square, 178px tall, frame score over a three-line caption. Lost steps print their score in catch-positive; the green final frame in keep-positive.
- **Edge print:** below the rebate on the glass, edge-ink mono: `KEDGE 15 ▸ 3 · step 2`; the last frame takes an "A" suffix (`5A · final`).
- **States:** undeveloped frames sit at brightness .08 / contrast 1.4 and develop to full over .7s as they reach the gate. Hover or open draws a 2px edge-orange outline.
- **Marks:** SVG strokes live inside the frame (bleeding 18px past it) so they travel, rewind and magnify with it. Notes hang above (checkpoint, false claim, keeper) or below (the catch) the strip, rotated -2deg.

### The print (keeper)
- Print stock with the print shadow, max 560px, holding a dark image block (verdict score left, verdict word right, one-line reason under) and a caption row: mono provenance (`No. 15 · owner/repo#1`), the Open PR pill, and a hand signature ("checked by Kedge" in keep, "unchecked" / "no safe fix" in marker-ink). Race mode lays two prints side by side.

### Slips (frame slip, plan slip)
- **Frame slip:** a typed evidence slip for one frame, fixed bottom-right, print stock, -0.8deg; Archivo 800 head with a hand annotation, a two-column dt/dd list (ink-3 terms), mono codes, and a plain uppercase "Close" text button. Escape closes it.
- **Plan slip:** the plan as typed, mono 13/1.6 on print stock at 0.7deg; code inside it goes 600 with no wash.

### Sheet stack (run picker)
- Each run is a contact sheet: big run number, two-line title, a mini film (rebate with one tick per frame: marker ring for a catch, grease underbar for a false claim, keep-positive ring for a keeper), mono sub line with the score, and a hand verdict. Current sheet takes a 3px ink outline; race picks take a 3px marker outline.

### Stamps (evidence)
- Rubber-stamped evidence links: mono uppercase label over an Archivo 800 value, rotated, in a meaning colour (Draft PR ink, neatlogs trace edge-ink, Entire checkpoint marker-ink, GitHub CI marker-ink or keep when passed). Unavailable evidence is shown at 50% with "not recorded" rather than hidden.

### Lab label (navigation)
- The KEDGE wordmark stamped on a print-stock label with a 1.5px ink border, tilted -1.2deg, a hand sub-label ("sheet No. 15", "race"), and the sheets icon; it opens the sheet stack. Beside it, the tally in mono: `8/14 kept · 10 cheats caught · 2 lies overruled`.

### Loupe
- A 220px circular magnifier (2.1x) that follows a mouse over frames, cloning the frame with its marks. Mouse only; off under 900px.

### The Performance (signature motion)
The replay is choreographed with springs and stroke-draws; each beat below is a world rule, not a page flourish.

- **Develop:** frames come up from black (`filter: brightness(.08) contrast(1.4)` to none, .7s ease-out) as they reach the gate.
- **Feed:** a crisp, critically damped spring per frame (stiffness 70, damping 17); the strip's entry from off-screen right is slightly looser (40 / 13).
- **X stroke-draw:** two leaning strokes, 420ms each, the second starting at 380ms, ease cubic-bezier(.65,0,.35,1). Ring 700ms; false-claim underline 380ms.
- **Rewind:** a loose, heavy, underdamped spring (stiffness 34, damping 4) back to the last clean step, with horizontal motion blur proportional to velocity (|v|/300 px, capped at 7px, applied above 0.3px). The contrast with the crisp feed is the point.
- **Laydown:** the strip is cut into contact rows; each cell FLIPs from its strip position, 900ms ease-out-expo (cubic-bezier(.16,1,.3,1)), staggered 40ms.
- **Lift:** the print grows out of the final frame's own rectangle, rises and tilts to -4deg at 45%, lands at -1.4deg; 1100ms ease-out-expo. Race prints lift 500ms apart.
- **Settle:** the score's numerator counts up on an underdamped spring (stiffness 90, damping 7), overshooting like a needle; the denominator is fixed from the start.
- **Reduced motion:** all of it resolves to the final laid-down state with marks and print in place. A slow-motion key (`s`, 0.55x) exists for recording.

## Do's and Don'ts

### Do:
- **Do** give every frame its own rebate cell with four sprocket cutouts top and bottom, filled with the hot backlight colour (#ffffff), and its own mono edge print in edge-ink.
- **Do** put evidence on paper objects (print, slip, plan slip, sheet, stamp) in print stock (#fbfbfa) with a soft negative-spread ink shadow and a small hand-dropped tilt.
- **Do** draw catches as round-capped 7px marker strokes that lean and overshoot, and write their explanations in Permanent Marker in marker-ink.
- **Do** write every score as passed / max(step total, base total): 2/5, never 2/2.
- **Do** keep one huge score and one huge verdict word per print, and nothing else at that scale.
- **Do** keep the feed crisp (critically damped) and the rewind loose and blurred; resolve everything instantly under prefers-reduced-motion.
- **Do** use the -ink colour for any marker, grease or edge text on light ground, and the -positive colour on frames.

### Don't:
- **Don't** build cards, sidebar tables or dashboard panels: bordered, rounded, flat-shadowed containers have no place on the lightbox.
- **Don't** add kickers or eyebrows above headings; section heads are plain Archivo titles and annotations are hand notes placed on the object they mark.
- **Don't** use grease yellow for anything but a false claim, or keep green for anything but a verified-good outcome.
- **Don't** set headings, buttons, body copy or comparable numbers in Permanent Marker.
- **Don't** tilt film or frames, and don't fill sprocket holes with grey or the ground colour.
- **Don't** use hard offset shadows; paper shadows are soft, offset down, and ink-tinted.
- **Don't** set raw marker (#e3241b) or raw edge orange (#d26a1b) as text on glass; they are stroke and outline colours.
