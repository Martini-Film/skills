---
name: martini-shot-generation
description: >-
  Use when the user is ready to generate an image or video in Martini — writing
  generation-ready prompts, selecting a model, setting format (aspect ratio,
  duration, resolution), submitting the generation job, and polling for results.
  Covers first-frame prompts, camera movement instructions, visual style, and
  converting storyboard entries into generation prompts. Do NOT use for narrative
  writing, storyboard planning, or export.
---

# martini-shot-generation — Generating images and videos

## What this skill does

Takes a prepared shot idea (from a storyboard or the user's description) and turns
it into a generated image or video in Martini: writing the prompt, picking the
model, setting the format, submitting the job, and reviewing the result.

## What this skill does NOT do

- Story or script writing → use **martini-script**
- Shot list planning → use **martini-storyboard**
- Subject creation or consistency setup → use **martini-subjects**
- Fixing a result after generation → use **martini-iteration**
- Export → use **martini-export**

## Common user requests

- "Generate a prompt for this shot."
- "Write an image prompt for the opening frame."
- "Write a video prompt where the character walks down the stairwell."
- "Make this shot ready for Martini generation."
- "Generate this shot."

## Before generating

1. **Find the project and scene** — `get_projects`, `get_board_scenes`.
2. **Check for Subjects** — `get_board_subjects`. If the shot involves a recurring
   character or location, confirm the Subject match before writing the prompt.
   See **martini-subjects** for the `@Element` convention.
3. **Pick a model** — default to current **Seedance** for video, **GPT Image** for
   stills. Resolve exact IDs with `list_models` — never hardcode. Then `get_model`
   for constraints (aspect ratios, duration limits, prompt length cap, image budget).
4. **Settle the format** — for video aim for **15s at 720p**. Ask portrait (9:16)
   vs. landscape (16:9) if unspecified — hard to change after generation.
5. **Confirm before spending** — olives are real money. For anything beyond a
   single explicit shot (multiple shots, ambiguous intent, batch), state the full
   plan — model, prompts, count, rough cost — and get a clear yes first.

## Writing a generation-ready prompt

### Structure
A strong prompt has three parts in order:
1. **Subject** — who/what is in frame (use `@Element1` if a Subject exists, prose if not)
2. **Action** — what happens during the shot, with pacing
3. **Camera and style** — lens, framing, movement, light, grade

```
@Element1 stands at the edge of the platform, scanning the crowd —
slow push-in as she spots someone. Medium shot, 35mm, shallow depth of field,
overcast natural light, desaturated grade.
```

### Timeline prompting (Seedance — for longer clips)
For shots over ~5s, break the action into timed beats so the model paces it
deliberately:

```
@Element1, rain-soaked neon alley, 35mm, shallow depth of field, teal-orange grade.
0-4s:  she steps out of a doorway, scanning left — slow dolly-in.
4-10s: she lights a cigarette, smoke catching the light — hold, slight push.
10-15s: she turns sharply at an off-screen sound — snap to tight close-up.
Handheld, naturalistic motion.
```

### Consistency block (for a sequence)
When generating multiple shots in sequence, lock one fixed block of
subject/style/camera language and change only the action:

```
# Consistency block — paste identically into every shot in this sequence:
@Element1, morning kitchen, 50mm, soft window light, warm muted grade, handheld.

# Per-shot — change only this part:
Shot 1: she pours coffee, glancing at her phone — static medium.
Shot 2: she sets the cup down and stares out the window — slow push-in.
```

### First-frame / image prompt
For an opening frame or standalone image, describe the exact moment as a still:

```
@Element1 standing at a rain-soaked train platform, looking left,
medium shot, 35mm, overcast light, desaturated grade. Photorealistic.
```

## Submitting the generation

```
create_node_and_generate({
  projectId, sceneId,
  nodeType: "video",           // or "image"
  modelId: "<resolved-id>",
  aspectRatio: "16:9",
  duration: 15,                // video only
  resolution: "720p",
  elements: [{ subjectId: "..." }],
  prompt: "..."
})  → returns jobId
```

Report the `jobId`, say it'll take a moment, then poll `get_job_status` until
complete. Then `view_asset` — assess honestly (on prompt? consistent? artifacts?).
If something's off, hand off to **martini-iteration**.

## Rules

- **Never hardcode model IDs** — always resolve via `list_models` + `get_model`.
- **Generation is async** — don't report a shot done until you've seen it.
- **Confirm before batches** — state count and cost, get a clear yes.
- **Stay under `maxPromptLength`** — check via `get_model`.
- **Image budget** — on Seedance, up to 4 elements within 9 total images.
  `@Image` tokens for reference images count against the same budget.

## Handoff

If the result needs fixing → **martini-iteration**.
When all shots are done → **martini-export**.
