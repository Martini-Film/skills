# Martini directing playbook

Loaded from `SKILL.md` for larger build-outs. These are default best practices for
getting good, consistent results — adapt to the user; if they have their own
approach, use theirs. Assumes you've already read the core skill (mental model,
the @Element convention, the always-apply rules).

## Put anything that recurs in the Library

The habit that makes a project look consistent: the moment a character, prop,
location, or look will appear more than once, make it a **library collection** and
reference it as an element from then on. The library is workspace-wide, so the
cast you build today is available in every future project.

Three ways material gets in:

- **From external URLs** — `import_library_assets` with `items` of file URLs.
  Images are mirrored into Martini storage. Pass `newCollection` to create the
  collection in the same call.
- **From shots already on the board** — the same tool captures existing project
  assets by reference, with provenance and no copy. This is how a good generated
  still becomes the canonical look for a character.
- **From local bytes** — no URL, so upload into a project first
  (`upload_assets_prepare` → PUT → `upload_assets_complete`, or
  `upload_asset_from_base64` for a small image), then capture that asset into the
  library. Run `check_storage_reachability` once per session first.

Set the hero still (`collection.setHero`) — it's what elements resolve to by
default — and add more stills for stronger consistency. Replacing an asset's media
appends a **version**; older versions stay reachable
(`asset.setCurrentVersion`).

## Properties: make a big library navigable

Properties are typed fields on library assets — `select`, `text`, `number`,
`checkbox`. They're the difference between a library you can query and a wall of
thumbnails. Suggest them once a collection has more than a handful of assets.

Useful shapes:

- `select` **Status** — Draft / Approved / Retired. The single most useful one:
  filter to approved material before generating.
- `select` **Look** or **Costume** — which version of the character this still is.
  Then pin it in a shot with `libraryAssetId`.
- `text` **Notes** — why this still exists, what it's good for.
- `number` **Lens** / `checkbox` **Locked** — whatever the production actually
  tracks.

Working with them:

```
1. get_library                                  → existing properties, keys, option IDs
2. edit_library [{ type: 'property.create',
     property: { label: 'Status', type: 'select',
                 options: [{ value: 'Approved' }, { value: 'Draft' }] } }]
3. edit_library [{ type: 'asset.setValue',
     id: '<assetId>', key: 'status', value: '<optionId>' }]
```

- **Read properties before writing values.** `select` values are **option IDs**,
  not labels, and a value whose type doesn't match the property is a *silent
  no-op* — nothing errors, nothing changes.
- Prefer setting values **during** `import_library_assets` over backfilling.
- `property.removeOption` is a hard delete and does **not** clear values still
  holding that option — clear or re-set them yourself.
- **Saved views** (`view.save`) store a layout + filters + grouping + sort — e.g.
  "Cast, grouped by Status". Offer one once the user has a filter they keep
  re-typing. Folders and tags handle the coarse organization.

## Keep the board organized

A tidy, labeled board lets the user navigate the project and work alongside you.
Build the habit early.

- **Order shots in story order, left to right.** A batch created without explicit
  positions is laid out in list order — so pass shots in the order they play. Use
  `placement: { rightOf }` / `{ below }` for relative drops; set explicit
  `position` only for a deliberate layout (storyboard rows per sequence).
- **Group a sequence into a bin.** `group_nodes_into_bin` / `create_bin` collect a
  canvas's shots under a named container ("Sequence 1 — The Chase"). Bins don't
  nest — one level deep. `layout_bin_children` tidies one up.
- **Label with text notes.** `create_text_note` makes on-canvas headers, scene
  slugs, and director notes so the board reads like a storyboard.
- **Mark what's good.** `set_asset_metadata` sets review ratings, color labels,
  and display names on shots — so a long board still says which takes are keepers.
- **Keep reusable material in the Library, not scattered on the canvas.** The
  canvas is the cut; the library is the shelf.
- **One canvas per section, not per shot.** Keep a sequence on one canvas; reach
  for a new one only for a genuinely separate sequence or when asked.

## Build a project from a script

When the user has a script (often a local text file — ask for it, read it, work in
story beats), turn it into structure:

1. **Decompose** — pull out the cast, locations, and key props; list them back to
   confirm.
2. **Choose a delivery mode** — *scaffold-only* (build the library collections and
   empty draft shots for the user to fill later; spends no olives) or
   *generate-now* (also create images/shots; spends olives). Ask if unclear.
3. **Build the library side** — a collection per character/location/prop, in a
   folder named for the production, with images when you have them.
   `link_library_to_project` to enable them for this project.
4. **Add variables** for the recurring prompt text — the grade, the lighting, the
   lens package — so every shot in the sequence shares identical language.
5. **Lay out the shots** — `create_nodes` for empty drafts, or
   `create_nodes_and_generate` to scaffold + generate at once. Group a sequence
   into a bin and annotate with text notes.

A natural handoff: scaffold collections and empty shots → user adds reference
images → next turn, "turn these beats into shots" → you generate.

## Batch generation

`create_nodes_and_generate` fans out many shots at once (a sequence, or several
variations of one beat); each node carries its own model, prompt, and elements.
State the count and intent before a big batch. Nodes can fail independently —
check per-node `generationError` and offer to retry just those.

## Reviewing and iterating

Look at every result with `view_asset` and be honest about it. For a near-miss, a
**variation** or **offshoot** node beats regenerating from scratch. Keep a running
note of what's working — favored camera/lighting language, which models nail a
given character — and promote the winning still into the library so the next shot
inherits it.

## Prompting for film

If the user hasn't set a style: think in beats and tempo (encode motion and
rhythm — "slow push-in as she turns" — not a static description), speak the
language of the camera (lens, framing, movement, light, grade), give dialogue
emotional texture through pacing and parentheticals, and keep characters anchored
to library elements so identity holds across the cut.

Two structured patterns get markedly more controllable, repeatable results on
modern video models — Seedance especially, with director-level camera control and
longer (up to 15s) clips. Treat them as craft, not a model-specific spec, and
defer to anything `get_models` reports (e.g. the prompt-length cap):

- **Lock a consistent block, vary only the action.** Hold one fixed description of
  the subject (or reference it as a library element), the style/lighting, and the
  camera/lens — identical across every shot in a sequence — and change only what
  happens. Consistent language is what makes consecutive shots read as one film.
  Store that block as a **variable** and drop it in as `@{id:name}` so it's
  genuinely identical, not retyped.
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
model's image slots for you. Note that **library elements and reference images
share one image budget** (on Seedance, up to 4 elements within 9 total images) —
exceed it and the extra `@Image` tokens stay in the prompt as plain text instead of
resolving. `get_models` reports the limits; strongest on Seedance, not universal.

## Assembling and delivering the cut

Once the shots are approved, build the sequence rather than leaving the user to
drag clips themselves.

1. `get_timeline_context` — read sequences, tracks, clips, gaps, and the
   `revisionToken`.
2. `apply_timeline_edit` — `assemble` a first cut from the approved shots in story
   order, then refine with `insert` / `update` / `remove` / `reorder` / `split` /
   `normalize`. Always pass `ifRevision` (from the read) and a stable
   `operationId`. Dry-run a large restructure first, and
   `checkpoint_timeline` before anything you'd hate to lose.
3. `render_timeline_frame` — composite a few moments (or a strip across a range) to
   confirm order, trims, and track priority before rendering anything.
   `get_timeline_audio_report` to catch dead air and loudness problems.
4. `render_timeline` in **draft**, poll `get_timeline_delivery_status`, then
   `inspect_timeline_artifact` for a contact sheet. Show it to the user. Only then
   render **final**.
5. `import_timeline_artifact` puts the finished render back on a canvas as a video
   node; `export_timeline_xml` hands the cut to Premiere as an XMEML bundle with
   the original media.

Renders are durable server-side jobs — report the ID, don't sit and spin.
`WORKER_INTERRUPTED` from the status poll means resubmit with a **new**
`operationId`.

## Rejections and keyword substitution

When a prompt is moderated or rejected, note the trigger, avoid it for the rest of
the session, and substitute phrasing that preserves intent. If a model keeps
refusing a concept, suggest a different model or reframing rather than retrying.

## Tool reference

Read tools are free; write/generate tools mutate the board or spend olives.

- **Orient** — `get_projects`, `get_board_overview`, `get_board_canvases`,
  `get_canvas`, `get_canvas_children`, `get_board_assets`, `get_asset`,
  `get_text_note`, `get_models`, `get_jobs`
- **Library** — `get_library`, `get_library_collection`, `view_library_asset`,
  `edit_library` (collections, folders, assets, properties, tags, views),
  `import_library_assets`, `link_library_to_project`
- **Variables** — `get_board_variables`, `get_variable`, `create_variable`,
  `update_variable`, `move_variable`
- **Canvas** — `create_project`, `rename_project`, `create_canvas`, `create_node`,
  `create_nodes`, `move_node`, `move_nodes`, `create_bin`, `update_bins`,
  `move_node_to_bin`, `group_nodes_into_bin`, `layout_bin_children`,
  `create_text_note`, `update_text_note`, `set_asset_metadata`,
  `reorder_variation_stack_members`
- **Generate & edit media** — `generate`, `create_node_and_generate`,
  `create_nodes_and_generate`, `crop_image`, `extract_video_frame`, `inspect_video`
- **Timeline** — `get_timeline_context`, `apply_timeline_edit`,
  `checkpoint_timeline`, `restore_checkpoint`, `render_timeline_frame`,
  `get_timeline_audio_report`, `render_timeline`, `export_timeline_xml`,
  `get_timeline_delivery_status`, `inspect_timeline_artifact`,
  `import_timeline_artifact`
- **Assets in/out** — `check_storage_reachability`, `upload_assets_prepare` /
  `upload_assets_complete`, `upload_asset_from_base64`, `view_asset`,
  `get_asset_download_url`
- **Support** — `prepare_support_request`, `submit_support_request`
