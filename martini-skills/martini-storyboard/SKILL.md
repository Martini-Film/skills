---
name: martini-storyboard
description: >-
  Use when the user wants to convert a script or story beats into a visual plan —
  turning scenes into shot lists, deciding what happens in each shot, defining
  opening and closing frames, planning shot order, or organizing a sequence before
  generation. Do NOT use for actual prompt writing, subject management, generation,
  or export.
---

# martini-storyboard — Visual planning before generation

## What this skill does

Converts a narrative (script, beat list, or rough idea) into a concrete visual
plan: what each shot shows, in what order, with what camera approach. Output is a
shot list or storyboard — not generation-ready prompts (those come next, in
**martini-shot-generation**).

## What this skill does NOT do

- Narrative writing from scratch → use **martini-script**
- Detailed prompt polishing or generation-ready syntax → use **martini-shot-generation**
- Subject/character consistency management → use **martini-subjects**
- Export or delivery → use **martini-export**

## Common user requests

- "Turn this script into a storyboard."
- "Break this scene into shots."
- "What should each frame show?"
- "Plan a 4-shot sequence for this story."
- "What's the best shot order for this story?"
- "Define the opening and closing frame."

## How to approach it

### Script → shot list
Read the script or beats. For each beat, define one shot:
- **What's in frame** — who, what, where
- **What happens** — the action or movement within the shot
- **Opening frame** — what the shot starts on
- **Closing frame** — what the shot ends on (especially important for video continuity)
- **Camera approach** — angle, distance, movement (keep it simple: wide/medium/close, static/pan/push)
- **Duration** — approximate (short: ~5s, medium: ~10s, long: ~15s)

### Shot list format
Present as a numbered table or list. Keep it scannable:

```
Shot 1 — Platform, wide
Opening: Empty rain-soaked platform, train not yet visible.
Action: Woman walks into frame from left, stops, checks her phone.
Closing: She looks up — train appears in background, out of focus.
Camera: Static wide, slight push-in as she stops.
Duration: ~10s

Shot 2 — Phone screen, close
Opening: Fingers hovering over keyboard.
Action: She types, pauses, selects all, deletes.
Closing: Blank message field.
Camera: Extreme close-up, static.
Duration: ~6s
```

### Keyframe / first-frame planning
For each shot, define the opening frame precisely — this becomes the first-frame
prompt in generation. Ask the user if they have a specific visual in mind for
any shot; if not, propose one.

### Shot order logic
Consider: Does each shot connect visually to the next? Does the cut make sense?
Flag any jarring transitions and propose alternatives. Match cut, action cut, and
geography cut are the most reliable.

### Organizing a multi-scene project
Group shots into sequences (scenes). Label each group. Recommend one scene in
Martini per narrative sequence, not one scene per shot — see **martini-export**
for how this affects delivery.

## Expected output

- A numbered shot list with framing, action, opening/closing frame, and duration
- No generation prompts, no `@Element` syntax, no model parameters

## Handoff

When the shot list is approved, move to **martini-subjects** (if recurring
characters or locations need to be set up) and then **martini-shot-generation**
(to write generation-ready prompts for each shot).
