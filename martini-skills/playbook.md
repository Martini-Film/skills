# Martini directing playbook

Loaded from `SKILL.md` for larger build-outs. These are default best practices for
getting good, consistent results — adapt to the user; if they have their own
approach, use theirs. Assumes you've already read the core skill (mental model,
the @Element convention, the always-apply rules).

## Make a Subject for anything that recurs

The habit that makes a project look consistent: the moment a character, prop, or
location will appear more than once, create a Subject (`create_subject`) and
reference it as an element from then on.

To bring in the user's own image as a Subject:

1. `check_storage_reachability` once per session before the first upload (if you
   haven't already). If the probe fails, print its `suggestion.message` and stop.
2. `upload_asset_init` → PUT the bytes to the returned presigned URL →
   `upload_asset_complete`. Images only (JPEG/PNG/WebP), 25 MB cap.
3. `create_subject` with the CDN URL as `mainImageUrl`; add more with
   `referenceImageUrls` or `update_subject_images` for stronger consistency.

## Keep the board organized

A tidy, labeled board lets the user navigate the project and work alongside you.
Build the habit early.

- **Order shots in story order, left to right.** A batch created without explicit
  positions is laid out in list order — so pass shots in the order they play. Set
  explicit `position` only for a deliberate layout (storyboard rows per sequence).
- **Group a sequence into a bin.** `group_nodes_into_bin` / `create_bin` collect a
  scene's shots under a named container ("Sequence 1 — The Chase"). Bins don't
  nest — one level deep.
- **Label with text notes.** `create_text_note` makes on-canvas headers, scene
  slugs, and director notes so the board reads like a storyboard.
- **Keep references grouped.** Put characters/props/locations in Collections so
  reusable material stays separate from the shots you're cutting.
- **One scene per section, not per shot.** Keep a sequence on one scene; reach for
  a new scene only for a genuinely separate sequence or when asked.

## Build a project from a script

When the user has a script (often a local text file — ask for it, read it, work in
story beats), turn it into structure:

1. **Decompose** — pull out the cast, locations, and key props; list them back to
   confirm.
2. **Choose a delivery mode** — *scaffold-only* (create Subjects and empty draft
   shots for the user to fill later; spends no olives) or *generate-now* (also
   create images/shots; spends olives). Ask if unclear.
3. **Create Subjects** for each character/location/prop — with images when you
   have them, empty in scaffold-only mode.
4. **Group with Collections** ("Cast", "Locations", "Props") to keep the board
   navigable. Members must share a scene.
5. **Lay out the shots** — `create_nodes` for empty drafts, or
   `create_nodes_and_generate` to scaffold + generate at once. Group a sequence
   into a bin and annotate with text notes.

A natural handoff: scaffold Subjects and empty shots → user adds reference images
→ next turn, "turn these beats into shots" → you generate.

## Batch generation

`create_nodes_and_generate` fans out many shots at once (a sequence, or several
variations of one beat); each node carries its own model, prompt, and elements.
State the count and intent before a big batch. Nodes can fail independently —
check per-node `generationError` and offer to retry just those.

## Reviewing and iterating

Look at every result with `view_asset` and be honest about it. For a near-miss, a
**variation** or **offshoot** node beats regenerating from scratch. Keep a running
note of what's working — favored camera/lighting language, which models nail a
given character — and reuse it.

## Prompting for film

If the user hasn't set a style: think in beats and tempo (encode motion and
rhythm — "slow push-in as she turns" — not a static description), speak the
language of the camera (lens, framing, movement, light, grade), give dialogue
emotional texture through pacing and parentheticals, and keep characters anchored
to Subjects so identity holds across the cut.

Two structured patterns get markedly more controllable, repeatable results on
modern video models — Seedance especially, with director-level camera control and
longer (up to 15s) clips. Treat them as craft, not a model-specific spec, and
defer to anything `get_model` reports (e.g. the prompt-length cap):

- **Lock a consistent block, vary only the action.** Hold one fixed description of
  the subject (or reference it as a Subject element), the style/lighting, and the
  camera/lens — identical across every shot in a sequence — and change only what
  happens. Consistent language is what makes consecutive shots read as one film.
  (Reuse the block from your notes today; Variables will make it a saved block.)
- **Break the clip into timed beats** (Seedance's guides call this *timeline
  prompting*). Beyond a couple of seconds, spell the action out second-by-second
  so the model paces it deliberately, with a camera direction per beat:

```
A weathered detective in a tan coat (@Element1), rain-soaked neon alley,
35mm, shallow depth of field, moody teal-and-orange grade.
0-3s:  he steps from a doorway, scanning left — slow dolly-in.
3-9s:  he lights a cigarette, smoke catching the light — hold, slight push.
9-15s: he turns sharply toward an off-screen sound — snap to a tight close-up.
Handheld, naturalistic motion; ambient rain and distant traffic.
```

Keep it tight — every line should earn its place, under the model's
`maxPromptLength`.

### Tagging reference images by role (multi-reference)

On models that support multi-reference (Seedance especially), don't just attach a
`referenceImages` image — *give it a job in the prompt* with an `@Image` token, the
way Seedance's own guides do. The first `referenceImages` entry is `@Image1`, the
second `@Image2`, numbered separately from `@Element`:

```
referenceImages: ["<jacket-url>", "<location-url>"]
prompt: "@Element1 in the alley. @Image1 as the jacket and material reference,
         @Image2 as the location and lighting reference."
```

Assigning each input a clear role — *this is the subject, this the outfit, this the
location* — is what works best. Martini maps `@Element` and `@Image` into the
model's image slots for you. Note that **Subjects and reference images share one
image budget** (on Seedance, up to 4 elements within 9 total images) — exceed it
and the extra `@Image` tokens stay in the prompt as plain text instead of
resolving. `@Video`/`@Audio` tokens exist at the model level but aren't reachable
over MCP (image uploads only). `get_model` reports the limits; strongest on
Seedance, not universal.

## Rejections and keyword substitution

When a prompt is moderated or rejected, note the trigger, avoid it for the rest of
the session, and substitute phrasing that preserves intent. If a model keeps
refusing a concept, suggest a different model or reframing rather than retrying.

## Tool reference

Read tools are free; write/generate tools mutate the board or spend olives.

- **Read** — `get_projects`, `get_board_scenes`, `get_scene`, `get_scene_layout`,
  `get_bin_contents`, `get_board_assets`, `get_asset`, `get_asset_draft_settings`,
  `get_board_subjects`, `get_subject`, `get_text_note`, `list_models`, `get_model`,
  `list_project_jobs`, `get_job_status`
- **Subjects & collections** — `create_subject`, `update_subject_images`,
  `create_subject_collection`, `add_subjects_to_collection`,
  `remove_subjects_from_collection` (removing all members dissolves it)
- **Canvas** — `create_scene`, `create_node`, `create_nodes`, `move_node`,
  `create_bin`, `update_bin`, `move_bin`, `move_node_to_bin`,
  `group_nodes_into_bin`, `create_text_note`, `update_text_note`
- **Generate** — `generate`, `create_node_and_generate`,
  `create_nodes_and_generate`
- **Assets in/out** — `check_storage_reachability`, `upload_asset_init` /
  `upload_asset_complete` (+ `_batch`), `view_asset`, `get_asset_download_url`
