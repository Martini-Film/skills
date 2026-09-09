---
name: martini-shot-generation
description: >-
  Use when the user is ready to generate an image or video in Martini — writing
  generation-ready prompts, selecting a model, setting format (aspect ratio,
  duration, resolution), submitting the generation job, and polling for results.
  Covers first-frame prompts, camera movement instructions, visual style, scaffold-only
  vs generate-now decisions, batch generation, and converting storyboard entries into
  generation prompts. Do NOT use for narrative writing, storyboard planning, or export.
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
- "I have a script — scaffold the shots first before we generate."

## Scaffold-only vs generate-now

Before starting any multi-shot work, choose a delivery mode — ask the user if unclear:

- **Scaffold-only** — create Subjects and empty draft nodes (`create_nodes`);
  spend no olives. Good when the user wants to review structure or add reference
  images before committing to generation.
- **Generate-now** — scaffold + generate immediately (`create_nodes_and_generate`);
  spends olives. Use when the user is ready and has confirmed.

Natural handoff: scaffold empty shots → user reviews and adds reference images →
next turn, "generate these" → call generate tools.

> Empty `create_node` / `create_nodes` drafts are placeholders only — they cannot
> hold a prompt for later generation. A node is either empty or has been generated.

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
5. **Confirm before spending** — present a plan (model, prompts, count, rough cost)
   and get a clear yes before calling any generate tool. A single explicitly-
   requested shot: just generate it.

## Writing a generation-ready prompt

### Structure
A strong prompt has three parts in order:
1. **Subject** — who/what is in frame (`@Element1` if a Subject exists, prose if not)
2. **Action** — what happens, with pacing
3. **Camera and style** — lens, framing, movement, light, grade

```
@Element1 stands at the edge of the platform, scanning the crowd —
slow push-in as she spots someone. Medium shot, 35mm, shallow depth of field,
overcast natural light, desaturated grade.
```

### Timeline prompting (Seedance — for clips over ~5s)
Break the action into timed beats so the model paces it deliberately:

```
@Element1, rain-soaked neon alley, 35mm, shallow depth of field, teal-orange grade.
0-4s:  she steps out of a doorway, scanning left — slow dolly-in.
4-10s: she lights a cigarette, smoke catching the light — hold, slight push.
10-15s: she turns sharply at an off-screen sound — snap to tight close-up.
Handheld, naturalistic motion.
```

### Consistency block (for a sequence)
Lock one fixed block of subject/style/camera language and change only the action
across every shot in the sequence:

```
# Paste this block identically into every shot:
@Element1, morning kitchen, 50mm, soft window light, warm muted grade, handheld.

# Change only the action per shot:
Shot 1: she pours coffee, glancing at her phone — static medium.
Shot 2: she sets the cup down and stares out the window — slow push-in.
```

## Submitting a single shot

```
create_node_and_generate({
  projectId, sceneId,
  nodeType: "video",        // or "image"
  modelId: "<resolved-id>",
  aspectRatio: "16:9",
  duration: 15,             // video only
  resolution: "720p",
  elements: [{ subjectId: "..." }],
  prompt: "..."
}) → returns jobId
```

Report the `jobId`, say it'll take a moment, poll `get_job_status` until complete,
then `view_asset` — assess honestly. If something's off → **martini-iteration**.

## Batch generation

`create_nodes_and_generate` fans out many shots at once. Pass shots in story order.
Each node is independent — check per-node `generationError` and offer to retry
just the failed ones individually.

```
create_nodes_and_generate([
  { nodeType: "video", modelId, prompt: "...", elements: [...], aspectRatio: "16:9", duration: 10 },
  { nodeType: "video", modelId, prompt: "...", elements: [...], aspectRatio: "16:9", duration: 8 },
])
```

State the count and cost before a big batch. Get a clear yes first.

## Rules

- **Never hardcode model IDs** — always resolve via `list_models` + `get_model`.
- **Generation is async** — don't report a shot done until you've seen it.
- **Confirm before batches** — state count and cost, get a clear yes.
- **Stay under `maxPromptLength`** — check via `get_model`.
- **Image budget** — on Seedance, up to 4 elements within 9 total images.
  `@Image` tokens for reference images count against the same budget.
- **Olives are real money** — scout with image models before committing to video.

## Tool reference

Read tools are free. Write/generate tools mutate the board or spend olives.

- **Read** — `get_projects`, `get_board_scenes`, `get_scene`, `get_scene_layout`,
  `get_bin_contents`, `get_board_assets`, `get_asset`, `get_asset_draft_settings`,
  `get_board_subjects`, `get_subject`, `get_text_note`, `list_models`, `get_model`,
  `list_project_jobs`, `get_job_status`
- **Canvas** — `create_scene`, `create_node`, `create_nodes`, `move_node`,
  `create_bin`, `update_bin`, `move_bin`, `move_node_to_bin`,
  `group_nodes_into_bin`, `create_text_note`, `update_text_note`
- **Generate** — `generate`, `create_node_and_generate`, `create_nodes_and_generate`
- **Assets in/out** — `check_storage_reachability`, `upload_asset_init`,
  `upload_asset_complete`, `upload_asset_init_batch`, `upload_asset_complete_batch`,
  `view_asset`, `get_asset_download_url`
- **Subjects** — `create_subject`, `update_subject_images`,
  `create_subject_collection`, `add_subjects_to_collection`,
  `remove_subjects_from_collection`

## Handoff

If the result needs fixing → **martini-iteration**.
When all shots are done → **martini-export**.
