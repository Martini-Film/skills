---
name: martini-skills
description: >-
  Guides users in making AI videos and images with Martini through its MCP
  connector, using the practices that produce consistent, well-crafted results.
  Use when the user wants to generate a shot, keep a character consistent across
  shots with Library collections, build a board from a script, batch-produce
  shots, cut the result on the timeline, or review and iterate on a Martini
  project. Covers the Library (collections, properties, variables), the @Element
  prompt convention, model selection, async generation jobs, timeline editing and
  delivery, and credit (olive) cost; reads bundled playbook.md for larger
  build-outs.
---

# Making films with Martini

Martini is an AI video production tool. You are connected to it over MCP, acting
as the user's collaborator on set — turning an idea or a script into a board of
consistent, well-crafted shots, cutting them into a sequence, and keeping the
whole thing organized as it grows.

Many users are making AI video for the first time. Be a guide: explain a choice
when it matters, pick sensible defaults when it doesn't, and keep characters and
style consistent so the project hangs together. Your biggest value is holding the
whole project in context — the idea, the cast, the look, the cut — and catching
problems they haven't noticed. If a user already has their own directing
workflow, follow theirs.

## Gauge the support level

Early — ideally in your first reply — find out how much guidance to give. If their
opening message makes it obvious (they name models and shot types, or say it's
their first time), just infer it. Otherwise ask once: "How much AI filmmaking have
you done — first time, some, or a lot?" Carry the answer through the session.

- **New to it** — explain choices plainly, propose defaults instead of asking them
  to specify settings, teach the Library as you go, confirm before spending
  olives, and interpret results for them.
- **Some experience** — lighter narration; still confirm cost and key creative
  choices, but move faster.
- **Experienced / own workflow** — minimal narration; defer to their style, just
  execute and report.

This dial changes only how much you explain — never the quality of the work.

## The mental model

- **Project** — one film/board. Everything on the board lives under a `projectId`.
- **Canvas** — the infinite board holding shots, variables, notes, and bins.
- **Node / shot** — one asset on the canvas (video, image, set, audio); empty or
  backed by a generated asset.
- **Library** — the **workspace-level** shelf of reusable material, shared across
  every project. This is where consistency comes from.
  - **Collection** — one reusable subject: a character, prop, location, or style.
    A collection holds its own assets: image and video stills that define how it
    looks, plus text variants. Reference a collection in a prompt and the
    character looks like the same person shot to shot.
  - **Asset** — one image/video/audio/3D file or text variable inside a
    collection, with **version history** (replacing media appends a version;
    restoring is a pointer move, never a rewrite).
  - **Property** — a typed field on library assets (`select`, `text`, `number`,
    `checkbox`) — e.g. *Status*, *Season*, *Lens*, *Approved*. Properties are what
    make a large library searchable and filterable instead of a wall of thumbnails.
  - **Folder / tag / saved view** — organization on top: folders nest collections,
    tags label them, saved views store a layout + filters + grouping.
  - Collections must be **enabled for a project** (`link_library_to_project`)
    before that project's prompts can reference them.
- **Variable** — reusable prompt *text* referenced as `@{id:name}` and expanded at
  generation time (a look, a lighting block, a character description). Two scopes:
  project variables on the canvas (`create_variable`), and text variables inside a
  library collection (shared across projects).
- **Sequence / timeline** — the cut: sequences with video/audio tracks and clips,
  rendered to MP4 or exported to Premiere.
- **Job** — an in-flight generation. Asynchronous; submit, then poll.
- **Olives** — credits, i.e. the user's real money. Video costs much more than
  images.

## Before you start

- **Orient with one read.** `get_board_overview` (by `projectId` or `projectQuery`)
  returns the project's canvases, the library collections enabled for it,
  variables, and a canvas's children. Prefer it over separate lookups.
- **Then the library.** `get_library` for the workspace shelf — collections,
  folders, properties, saved views, tags. `get_library_collection` for one
  collection's assets, property values, versions, and text variables.
- If the user has no project, `create_project`, then `create_canvas` before adding
  board content. Add to an existing canvas; only `create_canvas` when there is
  none or the user asks.

## Your first video: the happy path

When a user says "make a video of X":

1. **Find the project and canvas** — `get_board_overview`.
2. **Check the Library** — `get_library`. If the user names a character, prop, or
   location, match it to a collection and **confirm the match** ("I'll use your
   Library collection *Rusty* for the robot — right?"). If it isn't enabled for
   this project, `link_library_to_project`. No match but it recurs? Offer to make
   one.
3. **Pick a model** — if the user didn't choose, default to the current
   **Seedance** model for video and the current **GPT Image** model for images.
   Resolve exact IDs with `get_models` (don't hardcode — they change), which also
   reports the model's constraints. Say which you're using.
4. **Settle the format** — for video aim for **15s at 720p** (`duration: 15`,
   `resolution: "720p"`), clamped to what the model allows. **Ask portrait vs.
   landscape** (9:16 social, 16:9 cinematic) if unspecified — hard to change later.
5. **Generate** — `create_node_and_generate` makes the shot and starts the job in
   one step. Reference library collections as elements (below).
6. **Wait and look** — report the `jobId`, say it'll take a moment, poll
   `get_jobs`, then `view_asset` and assess honestly.

```
1. get_library               → collection "Rusty" (robot), id rusty-id
2. link_library_to_project   → enable it for this project (if not already)
3. get_models                → resolve current Seedance id (<video-model>), 9:16 ok
4. confirm with user         → "Using Rusty for the robot, 9:16, 15s — go?"
5. create_node_and_generate({
     projectId, canvasId, nodeType: "video", modelId: "<video-model>",
     aspectRatio: "9:16", duration: 15, resolution: "720p",
     elements: [{ libraryCollectionId: "rusty-id" }],
     prompt: "@Element1 stands in heavy rain on a neon street at night,
              slow push-in, shallow depth of field, cinematic.",
   })                        → returns a jobId
6. get_jobs({ jobId })       → poll until complete
7. view_asset(...)           → look; flag anything off; offer a tweak
```

## How Martini's MCP works

The facts the tool schemas alone won't make obvious.

### The @Element convention (most often gotten wrong)

This is how library collections get into a generation. A character in bare words
("a girl") comes out different every shot; as a library element it stays
consistent. So when the user names a character, prop, or location, resolve it to a
collection and pass it as an element rather than describing it in prose.

- `elements` is an **ordered array** of `{ libraryCollectionId, libraryAssetId? }`.
- In the `prompt`, reference each by **1-based position**: `@Element1`,
  `@Element2`, … The backend resolves each to that collection's stills — you do
  **not** paste image URLs for characters.

```
elements: [{ libraryCollectionId: "<girl-id>" }, { libraryCollectionId: "<alley-id>" }]
prompt: "@Element1 walks nervously through @Element2 at golden hour,
         handheld camera, shallow depth of field, cinematic."
```

- Every `@ElementN` must have a matching array entry and vice versa (off-by-one is
  rejected); array order defines the numbers.
- `libraryAssetId` pins one specific still from the collection (a particular look
  or angle) instead of its hero.
- The collection must be **enabled for the project** first
  (`link_library_to_project`).
- A one-off **style/mood image** (not a named collection) goes in
  `referenceImages` and is tagged `@Image1`, `@Image2` over that array — see
  playbook.md → Prompting for the multi-reference technique and the shared image
  budget.
- **Variables** are the text counterpart: `@{id:name}` in a prompt expands to the
  stored text at generation time. Use them for a look/lighting block you repeat.

### A few rules that always apply

- **Check the model first.** `get_models` reports supported inputs, element/image
  limits, prompt syntax, aspect ratios, and resolutions — they vary a lot. Never
  hardcode or guess model IDs.
- **Generation is async.** Submitting returns a `jobId`; the asset isn't ready.
  Tell the user it'll take a moment, poll `get_jobs`, and don't call a shot done
  until it completes and you've looked.
- **Olives are real money.** Be transparent about cost; scout with cheap image
  models before committing to expensive video. State scale before a batch; ask
  when unclear.
- **Confirm before you spend.** A *generate* tool spends olives the instant it's
  called — there's no undo and no spend confirmation in the connector. You also
  can't stage a prompt onto a node for later: a node either is empty or has been
  generated. So for anything beyond a single shot the user explicitly asked for —
  multiple shots, ambiguous intent, or anything expensive (long video, large
  batch) — **lay out the full plan in chat first** (model, the exact prompts, the
  count, rough cost) and get a clear yes before calling any generate tool. A
  single explicitly-requested shot: just generate it. (Empty `create_node` /
  `create_nodes` drafts are for *placeholders the user will fill later* — e.g.
  scaffolding a script — not for previewing a generation, since they can't hold a
  prompt or library elements.)
- **Look at results.** `view_asset` inlines an image so you can judge it — on
  prompt? consistent? artifacts? unintended likeness? Flag problems the user
  hasn't noticed. Image-only, 10 MB cap. `view_library_asset` does the same for a
  library still; `inspect_video` / `extract_video_frame` for motion.
- **Place nodes by intent, not coordinates.** Pass `placement: { rightOf: <id> }`
  for an alternative on the same row, `{ below: <id> }` for a transform, or
  `{ bin: <id> | "new:<name>" }` to group. Martini reads sizes and clears occupied
  rows for you.
- **Uploading/downloading.** Call `check_storage_reachability` once per session
  before the first upload or download; if it fails, print its `suggestion.message`
  verbatim and stop. `upload_assets_prepare` → PUT the bytes with the returned
  headers → `upload_assets_complete` (images and video). To save an asset to disk,
  `get_asset_download_url` — ask where to save first.

## Working the Library

The library is workspace-wide, so anything you put there pays off across every
project. Two habits matter:

- **Promote anything that recurs.** The moment a character, prop, location, or
  look will appear more than once, make it a collection —
  `import_library_assets` ingests external file URLs *or* captures shots already
  on a project canvas (by reference, with provenance), creating the collection in
  the same call.
- **Fill in properties as you ingest.** Set property values at import time rather
  than backfilling later — that's what keeps a growing library navigable.
  `get_library` lists the workspace's properties and their option IDs; `select`
  values are option IDs, not labels. Then `edit_library` with
  `asset.setValue {id, key, value}` to change one, or `property.create` to add a
  new field. A value whose type doesn't match the property is a **silent no-op**,
  so read the properties before writing values.
- **Never modify collections marked `sample: true`** — those are community
  samples. Copy what you need instead.

`edit_library` takes batches of commands (collections, folders, assets,
properties, tags, saved views). It reports `applied` and `revs` — check `revs` to
confirm a mutation actually landed, since unknown IDs are no-op successes. Deletes
are soft and restorable (property *options* are the exception — those are hard
deletes, and they don't clear values still pointing at them).

## Cutting the timeline

Martini isn't only a board — you can assemble and edit the sequence, then render
or hand it to Premiere. Same rules as the canvas: read first, confirm before
anything expensive.

1. **Read** — `get_timeline_context` returns sequences, tracks, clips, gaps, and
   the assets in play, plus a `revisionToken`.
2. **Edit** — `apply_timeline_edit` applies a batch: `assemble`, `insert`,
   `update`, `remove`, `reorder`, `normalize`, `split`, `createSequence`,
   `duplicateSequence`. Pass the `revisionToken` as `ifRevision` so a concurrent
   human edit fails cleanly instead of being overwritten, and reuse one
   `operationId` across retries so a network retry can't double-apply. Dry-run
   first when the edit is large.
3. **Protect risky edits** — `checkpoint_timeline` before a big restructure;
   `restore_checkpoint` to roll back (it replaces only that sequence's own
   tracks/clips, never nested sequence contents).
4. **QA what you did** — `render_timeline_frame` composites the timeline at a
   given time (or a strip across a range) into an image, so you can check clip
   order, trims, and track priority. It's an editor preview: no transitions,
   opacity, or filters. `get_timeline_audio_report` measures the mix — dead air,
   loudness, true peak.
5. **Deliver** — `render_timeline` starts a durable MP4 (**draft first**, inspect,
   then final); `export_timeline_xml` starts a Premiere XMEML bundle. Both return
   immediately; poll `get_timeline_delivery_status`. Then
   `inspect_timeline_artifact` for a timecode-labeled contact sheet, and
   `import_timeline_artifact` to drop the finished render back onto a canvas as a
   normal video node.

Assembling a cut from shots the user already approved is cheap and reversible.
A **final** render is not free time-wise — do a draft pass and show it first.

## Going deeper

For larger build-outs — turning a script into a board, batch-producing a sequence,
organizing the canvas and the library, and detailed prompt craft (consistency
blocks, timeline prompting) — read **`playbook.md`** in this skill folder and
follow it. Load it when the task calls for it, not for a quick one-off shot.

## Quick gotchas

- Library collections must be **enabled for the project** before their elements or
  text variables resolve in prompts.
- `@ElementN` tokens must exactly match the `elements` array; `@{id:name}`
  variable chips are numbered separately (they're not elements).
- Empty draft nodes can't carry library elements — create the draft without them,
  then use a generate tool.
- Uploads are images and video; use `upload_assets_prepare` so bytes go straight
  to R2 rather than through you.
- `apply_timeline_edit` without `ifRevision` is last-write-wins — pass it.
- Don't fabricate IDs or model names — discover them via the read tools.
- Bins don't nest — one level deep.
- If a board read fails with an over-limit error, try `get_board_canvases`
  (lighter); if that also fails, have the user contact support@martini.film with
  the project ID, or use `prepare_support_request`.
