---
name: Kedge
description: VAR Review Room. Broadcast match graphics for an agent supervisor that checks instead of trusting.
colors:
  ground: "#0e1621"
  rail: "#111b27"
  panel: "#16212e"
  panel-2: "#1d2a3a"
  line: "#2a3a4e"
  ink: "#ffffff"
  ink-2: "#c3cedb"
  ink-3: "#93a3b6"
  green: "#00e0a4"
  green-bright: "#4fffcc"
  green-ink: "#062b22"
  green-pitch: "#10322b"
  yellow: "#ffd400"
  yellow-ink: "#2b2400"
  red: "#ff3b30"
  red-soft: "#ff8a82"
  red-pitch: "#2a1618"
typography:
  sequence:
    fontFamily: "Barlow Condensed, Arial Narrow, sans-serif"
    fontSize: "88px"
    fontWeight: 800
    lineHeight: 0.8
    letterSpacing: "-0.01em"
  scoreline:
    fontFamily: "Barlow Condensed, Arial Narrow, sans-serif"
    fontSize: "72px"
    fontWeight: 800
    lineHeight: 0.85
  headline:
    fontFamily: "Barlow Condensed, Arial Narrow, sans-serif"
    fontSize: "34px"
    fontWeight: 700
    lineHeight: 1.05
  frame-score:
    fontFamily: "Barlow Condensed, Arial Narrow, sans-serif"
    fontSize: "40px"
    fontWeight: 800
    lineHeight: 1
  title:
    fontFamily: "Barlow Condensed, Arial Narrow, sans-serif"
    fontSize: "22px"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "0.05em"
  label:
    fontFamily: "Barlow Condensed, Arial Narrow, sans-serif"
    fontSize: "14px"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "0.06em"
  body:
    fontFamily: "Barlow, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 500
    lineHeight: 1.45
    fontFeature: "tnum"
  body-sm:
    fontFamily: "Barlow, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 500
    lineHeight: 1.35
  label-ui:
    fontFamily: "Barlow, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "0.06em"
  mono:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace"
    fontSize: "13px"
    fontWeight: 500
    lineHeight: 1.4
rounded:
  chip: "2px"
  control: "3px"
  panel: "4px"
  cell: "50%"
spacing:
  2xs: "4px"
  xs: "6px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
  2xl: "28px"
  3xl: "36px"
components:
  button-primary:
    backgroundColor: "{colors.green}"
    textColor: "{colors.green-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "0 16px"
    height: "38px"
  button-primary-hover:
    backgroundColor: "{colors.green-bright}"
    textColor: "{colors.green-ink}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "0 16px"
    height: "38px"
  button-pressed:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.ground}"
  verdict-green:
    backgroundColor: "{colors.green}"
    textColor: "{colors.green-ink}"
    rounded: "{rounded.chip}"
    padding: "7px 12px 6px"
  verdict-disallowed:
    backgroundColor: "{colors.red}"
    textColor: "{colors.ink}"
    rounded: "{rounded.chip}"
    padding: "7px 12px 6px"
  verdict-live:
    backgroundColor: "{colors.yellow}"
    textColor: "{colors.yellow-ink}"
    rounded: "{rounded.chip}"
    padding: "7px 12px 6px"
  verdict-neutral:
    backgroundColor: "{colors.panel-2}"
    textColor: "{colors.ink}"
    rounded: "{rounded.chip}"
    padding: "7px 12px 6px"
  panel:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.panel}"
    padding: "14px 16px"
  frame:
    backgroundColor: "{colors.panel-2}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "14px 14px 12px"
    width: "168px"
  frame-whistle:
    backgroundColor: "{colors.green-pitch}"
    textColor: "{colors.green}"
  frame-short:
    backgroundColor: "{colors.red-pitch}"
    textColor: "{colors.red-soft}"
  check-banner:
    backgroundColor: "{colors.red}"
    textColor: "{colors.ink}"
    rounded: "{rounded.chip}"
    height: "26px"
    padding: "0 8px"
  check-banner-claim:
    backgroundColor: "{colors.yellow}"
    textColor: "{colors.yellow-ink}"
  tag-storm:
    backgroundColor: "transparent"
    textColor: "{colors.yellow}"
    rounded: "{rounded.chip}"
    padding: "3px 6px 2px"
  select:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    height: "32px"
    padding: "0 10px"
---

# Design System: Kedge

## Overview

**Creative North Star: "VAR Review Room"**

Kedge looks like the graphics package of a football broadcast on match night: navy pitch-night ground, white condensed type, scorelines set huge, and a referee's review laid out frame by frame. Every agent claim goes to the monitor. A run is a fixture with a sequence number and a scoreline (tests passed over tests that should exist). Each drift is a VAR check that ends in a ruling. The viewer should grasp at demo speed that Kedge checks rather than trusts.

The world is dense and flat: tonal navy panels separated by one hairline colour, no shadows, small radii, and three signal colours with fixed meanings. Numbers carry the story, so they are the biggest things on the screen and always tabular. Motion is limited to broadcast cues: a live pulse on things under review and a yellow-to-red wipe when a check becomes a ruling.

The nautical brand (the anchor mark, "hauled back to", storm) lives inside this world as vocabulary and the inline SVG anchor, not as a second visual system.

**Key Characteristics:**
- Pitch-night navy ground with tonal panels and 1px hairline borders; no shadows.
- Three signal colours with one meaning each: green confirmed, yellow under review, red disallowed.
- Barlow Condensed for every number, heading and label; Barlow for running text; tabular numerals everywhere.
- The replay strip: one drawing of a run, used at thumbnail and full width.
- Drift always reads without colour: diagonal hatch plus stop bar.
- Scores use the base-branch denominator, so a run that lost tests never looks perfect.

## Colors

A night-match broadcast palette: cold navy neutrals and three saturated signal colours that work like referee decisions.

### Primary
- **Confirmed Green** (`green`): the colour of a held result. Green verdicts, a winning scoreline, filled state cells, the final-whistle frame, the progress fill in a replay frame, the primary action (open draft PR), the anchor mark, and the "Green" tally. Dark text (`green-ink`) always sits on a green fill.
- **Floodlit Green** (`green-bright`): hover state of the primary button only.
- **Final-Whistle Pitch** (`green-pitch`): background tint of the final-whistle frame.

### Secondary
- **Check Yellow** (`yellow`): under review, attention and live. The running verdict ("Under review"), live state cells with their pulse, the "Claim rejected" banner, the storm tag, the opening frame of the check wipe, the empty-state monitor, plus the focus ring and text selection. Dark text (`yellow-ink`) always sits on a yellow fill.

### Tertiary
- **Disallowed Red** (`red`): drift, disallowed, gave up, shipped short. Check banners after the ruling lands, drift frame borders, the hatch, struck cells, the "No guard" tag, and the unguarded side of a compare.
- **Ruling Red Soft** (`red-soft`): red as text on navy. Short scorelines, the missing-tests note, the checks tally, failed CI links. Use it wherever red is foreground text; `red` is for fills, borders and marks.
- **Short Pitch** (`red-pitch`): background tint of the "Shipped" frame for a run that shipped short.

### Neutral
- **Pitch Night** (`ground`): the page ground and inline code background.
- **Dugout** (`rail`): the fixtures rail and its sticky header, one step lifted from the ground.
- **Gantry** (`panel`): top bar, ruling bar, ruling cards, plan, replay track, compare sides, select.
- **Monitor** (`panel-2`): replay frames, current fixture, neutral verdict. The highest tonal step.
- **Touchline** (`line`): every border and divider, the empty progress track, the scrollbar thumb.
- **Floodlight White** (`ink`): headings, numbers, primary text. Also white text on red fills.
- **Commentary** (`ink-2`): running text, frame actions, secondary facts.
- **Caption** (`ink-3`): labels, sub-lines, idle sequence numbers, hollow cell rings, quiet borders on hover.

### Named Rules
**The Three Decisions Rule.** Green means confirmed, yellow means under review or needing attention, red means disallowed. Each colour keeps that one meaning on every surface. Never use green or red as decoration, and never use yellow for success.

**The Ink-On-Signal Rule.** Green and yellow fills carry their dark ink (`green-ink`, `yellow-ink`). Red fills carry white. White on `red` measures about 3.5:1, so it only passes as large or bold display text. Set red labels at title size or larger, or use `red-soft` text on navy.

**The No-Fourth-Signal Rule.** There is no brand accent apart from the three decisions. Emphasis that isn't a decision uses white over `ink-2`/`ink-3`, or size.

## Typography

**Display Font:** Barlow Condensed 600/700/800 (with Arial Narrow, sans-serif), self-hosted woff2
**Body Font:** Barlow 400/500/600 (with system-ui, sans-serif), self-hosted woff2
**Label/Mono Font:** system monospace (ui-monospace, SFMono-Regular, Menlo) for file paths, SHAs and code only

**Character:** A sports-broadcast condensed grotesk for everything that is a number, a call or a heading, and its regular-width sibling for the sentences. They are the same family, so the pairing reads as one graphics package.

### Hierarchy
- **Sequence** (800, 88px, 0.8): the run's two-digit fixture number beside the match header, in `ink-3`. Hidden below 900px.
- **Scoreline** (800, 72px, 0.85; 52px below 900px): the final tests-passing score, right-aligned. Green when won, `red-soft` when short.
- **Frame score** (800, 40px): the score inside each replay frame. Compare sides use 64px.
- **Headline** (700, 34px, 1.05, balanced wrap): the PR title. Mixed case.
- **Title** (800, 20–24px, uppercase, 0.03–0.05em): section heads (Replay, Rulings, Plan), ruling-card heads, verdict pills, fixtures head.
- **Label** (700, 12–15px, uppercase, 0.06–0.08em): buttons, frame step labels, check banners, tags, haul label.
- **Body** (500, 15px, 1.45): running text in `ink-2`; ruling copy capped at 70ch.
- **Body small** (500, 13px, 1.35): fixture sub-lines and frame actions.
- **UI label** (Barlow 600, 13px, uppercase, 0.06em): tally names and the "Tests passing" caption under a scoreline.

### Named Rules
**The Numbers Are Headlines Rule.** Scores, counts and sequence numbers are set in Barlow Condensed 800 at the largest size in their container, always with tabular numerals (`font-variant-numeric: tabular-nums` on body). A number is never smaller than the words that describe it.

**The Condensed Calls Rule.** Every call (verdict, check, tag, button, section head) is Barlow Condensed in uppercase with positive tracking. Sentences are never uppercase and never condensed.

## Layout

The dashboard uses a broadcast shell: a sticky 64px top bar with the wordmark and batch tally, a fixed 360px fixtures rail on the left, and a scrolling stage on the right (padding 28px 36px 48px, content max 1180px). The match header is a three-column grid: sequence number, title block, scoreline. Under it come the ruling bar (verdict, facts, actions), the full-width replay strip, then a 1.4fr/1fr pair of Rulings and Plan. Compare mode puts two sides in a 1fr / auto / 1fr grid around a "vs" and then stacks the two replay strips.

Spacing follows a tight 4–36px rhythm. 6–8px gaps sit inside clusters, 12–16px is panel padding, and 24–28px separates sections. Lists of cards use 6–10px gaps.

Below 900px the shell becomes one column. The rail turns into a top block capped at 42vh, the tally keeps only Green with its label dropped, the "Review room" lockup and compare label hide, the sequence number hides, the scoreline drops to 52px, two-column areas stack, and ruling-bar actions become a 2-up grid with the primary action spanning both columns. The replay strip scrolls horizontally rather than wrapping.

## Elevation & Depth

The system is flat. Depth comes from tonal steps only: `ground` < `rail` < `panel` < `panel-2`, each edged with a 1px `line` border. There are no drop shadows. The one glow is the live pulse, a 5px yellow ring at 18% opacity (`box-shadow: 0 0 0 5px rgba(255,212,0,.18)`) that animates on live state cells. It is a state signal, not elevation.

### Named Rules
**The Gantry Rule.** A surface is lifted by moving one tonal step up and drawing a `line` hairline, never by adding a shadow.

## Shapes

The shapes are squared broadcast plates. Radii are small and tiered: 2px for chips, verdicts, tags and check banners; 3px for buttons, inputs, frames and code chips; 4px for panels and the replay track. The only round element is the state cell. Borders are 1px solid by default. A dashed border means "not a played step" (plan and replan frames, the empty "clean" note, the compare hint). A 4px top rule in red or green marks the two sides of a compare.

## Components

### Buttons
Squared and loud, like broadcast lower-third plates.
- **Shape:** 3px corners, 38px tall, 16px horizontal padding, 18px inline SVG icon with an 8px gap.
- **Primary:** Confirmed Green fill with green-ink text in condensed uppercase label type. One per view: open the draft PR.
- **Hover / Focus:** primary brightens to Floodlit Green; ghost border lifts from `line` to `ink-3`. Transitions are 0.2s on the house ease. Focus is a 2px yellow outline offset 2px.
- **Ghost:** transparent with a `line` border, used for evidence actions (trace, checkpoint) and the Compare toggle.
- **Pressed toggle:** inverts to a white fill with ground-colour text.
- **Unavailable:** stays in place at 45% opacity with a label that says what is missing ("Trace not recorded"). It is not removed.

### Chips / Tags
- **No guard:** red fill, white condensed 12px uppercase.
- **Storm:** transparent with a 1px yellow border and yellow text (attention, not a verdict).
- **CI link:** 1px `line` border with a state cell. Text turns `red-soft` when CI failed.

### Cards / Containers
- **Corner Style:** 4px.
- **Background:** Gantry (`panel`) on the ground.
- **Shadow Strategy:** none (see Elevation).
- **Border:** 1px `line`.
- **Internal Padding:** 14px 16px. Compare sides use 18px.

### Inputs / Fields
- **Select:** Gantry fill, 1px `line` border, 3px corners, 32px tall, Barlow 600 14px.
- **Focus:** the global yellow 2px outline.

### Navigation
- **Fixture list:** each run is a full-width button on a 54px / 1fr / auto grid. It holds the 30px condensed sequence number in `ink-3`, the title (Barlow 600 15px, single-line ellipsis), a sub-line with state cell, status text and repo#n, a right-aligned 24px scoreline, and the thumbnail replay strip underneath. Hover lifts to `panel`. The current run lifts to `panel-2` with a `line` border and its number turns white. In compare, picks A and B carry `ink-3` and `ink` borders.

### State Cell (signature)
A fixed 12px circle with a 2px ring that carries state by fill and mark, so it reads without colour:
- **Held:** filled green.
- **Not held:** hollow `ink-3` ring.
- **Disallowed:** red ring struck through with a diagonal red bar.
- **Live:** yellow ring with a 1.4s pulse.

### Verdict
A condensed 800 22px uppercase plate with 2px corners that states the ruling: Green (green), Gave up / Shipped short (red), Under review (yellow), Already green (`panel-2`).

### Replay Strip (signature move)
One drawing of a run, used at two scales.
- **Full width:** a horizontally scrolling `panel` track. It holds a row of 168px frames, each with a step label, a 40px score, an action line and a 6px progress bar. The opening "Kick-off / Plan" frame and any replan frame are dashed and transparent. A drift frame has a red border, a hatched bar and the stop-bar overlay. A CHECK banner (red, 26px, monitor icon) sits above it. A dashed curved "haul" arrow and an "Hauled back to <sha>" label run underneath, back to the last good frame. A false claim adds a yellow "Claim rejected" banner below the frame. A green run ends on a "Full time / Green" frame on Final-Whistle Pitch with a green border. A run that shipped short ends on a "Full time / Shipped" drift frame on Short Pitch.
- **Thumbnail:** a 260x14 SVG row of rounded bars, one per step. Drift steps use the red hatch pattern, false claims use yellow, steps use green only if the run ended truly green, and everything else uses `ink-3`. Bar opacity scales from 0.35 to 1 with the share of tests passing.
- **Motion:** the drift CHECK banner wipes in yellow from left to right, holds, then turns red (1.6s, house ease). This is the review becoming a ruling. Reduced-motion removes it.

### Drift Mark
Drift never relies on red alone. The disallowed segment carries a 45° diagonal hatch (red with translucent ground stripes in the thumbnail, red stripes on the progress bar) and a stop bar: a full-frame overlay of 135° stripes in red at 14% opacity, 10px apart. A drift frame's bar is always drawn full, so its length doesn't suggest progress.

### Scoreline
Score = tests passed over the larger of the step's test total and the base branch's test total. A run that deleted tests shows 2/5, never a flattering 2/2. When tests are missing, the scoreline turns `red-soft`, a condensed uppercase note states "N of M tests missing vs base branch", and a "green" status is reported as "Shipped short" with a struck cell and red verdict. A run with no scored step shows an en dash.

## Do's and Don'ts

### Do:
- **Do** keep green, yellow and red to their one decision each: confirmed, under review/attention, disallowed.
- **Do** set every score, count and sequence number in Barlow Condensed 800 with tabular numerals, larger than its label.
- **Do** compute scores against the base branch's test total whenever tests went missing, and say how many are missing.
- **Do** mark drift with hatch and stop bar as well as colour, so it survives greyscale and colour-blind viewing.
- **Do** draw a run as the replay strip (frames left to right, CHECK above, haul arrow below), reusing the same drawing at thumbnail scale.
- **Do** show state with the fixed cell (filled, hollow, struck, live) beside status text.
- **Do** lift surfaces by tonal step plus a 1px `line` hairline.
- **Do** use dashed borders only for things that were not played: plans, replans, empty notes.
- **Do** keep unavailable evidence actions visible at 45% opacity with a label that says what is missing.

### Don't:
- **Don't** use yellow for success or green for decoration; a fourth accent colour breaks the decision language.
- **Don't** put white text on a red fill below title size; use `red-soft` text on navy for small red copy.
- **Don't** add drop shadows or glows apart from the live pulse.
- **Don't** show a score with a shrunken denominator, or call a run green when it lost tests.
- **Don't** render the nautical glyphs (anchor, sailboat, wave, compass, money bag, chequered flag, lying face) as emoji in the UI; icons are inline 2px-stroke SVG symbols that use `currentColor`.
- **Don't** set sentences in uppercase or in the condensed face.
