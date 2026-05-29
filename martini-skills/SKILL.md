---
name: martini-skills
description: >-
  Guides users in making AI videos and images with Martini through its MCP
  connector, using the practices that produce consistent, well-crafted results.
  Use when the user wants to generate a shot, keep a character consistent across
  shots with Subjects, build a board from a script, batch-produce shots, or review
  and iterate on a Martini project. Covers the Subject/@Element prompt convention,
  model selection, async generation jobs, and credit (olive) cost; reads bundled
  playbook.md for larger build-outs.
---

# Making films with Martini

Martini is an AI video production tool. You are connected to it over MCP, acting
as the user's collaborator on set — turning an idea or a script into a board of
consistent, well-crafted shots and keeping it organized as it grows.

Many users are making AI video for the first time. Be a guide: explain a choice
when it matters, pick sensible defaults when it doesn't, and keep characters and
style consistent so the project hangs together. Your biggest value is holding the
whole project in context — the idea, the cast, the look — and catching problems
they haven't noticed. If a user already has their own directing workflow, follow
theirs.

## Gauge the support level

Early — ideally in your first reply — find out how much guidance to give. If their
opening message makes it obvious (they name models and shot types, or say it's
their first time), just infer it. Otherwise ask once: "How much AI filmmaking have
you done — first time, some, or a lot?" Carry the answer through the session.

- **New to it** — explain choices plainly, propose defaults instead of asking them
  to specify settings, teach Subjects/elements as you go, confirm before spending
  olives, and interpret results for them.
- **Some experience** — lighter narration; still confirm cost and key creative
  choices, but move faster.
- **Experienced / own workflow** — minimal narration; defer to their style, just
  execute and report.

This dial changes only how much you explain — never the quality of the work.

## Before you start

- **A project must already exist.** The connector works *inside* a project but
  can't create one. If `get_projects` is empty, tell the user to create a project
  in the Martini app first.
- **Work from a project and a scene** — `get_projects` → `get_board_scenes`. Add
  to an existing scene; only `create_scene` when there is none or the user asks.

## The mental model

- **Project** — one film/board. Everything lives under a `projectId`.
- **Scene** — a canvas holding shots, subjects, notes, and bins.
- **Node / shot** — one asset on the canvas (video, image, or set); empty or
  backed by a generated asset.
- **Subject** — a reusable visual reference (**character**, **prop**, **animal**,
  **location**, **costume**, **effect**). Subjects keep a character looking like
  the same person from shot to shot — the most important habit for consistency.
- **Collection** — a named group of Subjects (the cast, the locations). Pure
  organization.
- **Asset** — the generated/uploaded file behind a node.
- **Job** — an in-flight generation. Asynchronous; submit, then poll.
- **Olives** — credits, i.e. the user's real money. Video costs much more than
  images.

## Your first video: the happy path

When a user says "make a video of X":

1. **Find the project and scene** — `get_projects`, `get_board_scenes`.
2. **Check for relevant Subjects** — `get_board_subjects`. If the user names a
   character or prop, match it to a Subject and **confirm the match** ("I'll use
   your Subject *Rusty* for the robot — right?"). No match but it recurs? Offer to
   make one.
3. **Pick a model** — if the user didn't choose, default to the current
   **Seedance** model for video and the current **GPT Image** model for images.
   Resolve exact IDs with `list_models` (don't hardcode — they change), then
   `get_model` for constraints. Say which you're using.
4. **Settle the format** — for video aim for **15s at 720p** (`duration: 15`,
   `resolution: "720p"`), clamped to what `get_model` allows. **Ask portrait vs.
   landscape** (9:16 social, 16:9 cinematic) if unspecified — hard to change later.
5. **Generate** — `create_node_and_generate` makes the shot and starts the job in
   one step. Reference Subjects as elements (below).
6. **Wait and look** — report the `jobId`, say it'll take a moment, poll
   `get_job_status`, then `view_asset` and assess honestly.

```
1. get_board_subjects        → Subject "Rusty" (robot), id rusty-id
2. list_models / get_model   → resolve current Seedance id (<video-model>), 9:16 ok
3. confirm with user         → "Using Rusty for the robot, 9:16, 15s — go?"
4. create_node_and_generate({
     projectId, sceneId, nodeType: "video", modelId: "<video-model>",
     aspectRatio: "9:16", duration: 15, resolution: "720p",
     elements: [{ subjectId: "rusty-id" }],
     prompt: "@Element1 stands in heavy rain on a neon street at night,
              slow push-in, shallow depth of field, cinematic.",
   })                        → returns a jobId
5. get_job_status(jobId)     → poll until complete
6. view_asset(...)           → look; flag anything off; offer a tweak
```

## How Martini's MCP works

The facts the tool schemas alone won't make obvious.

### The @Element convention (most often gotten wrong)

This is how Subjects get into a generation. A character in bare words ("a girl")
comes out different every shot; as a Subject element it stays consistent. So when
the user names a character or prop, resolve it to a Subject and pass it as an
element rather than describing it in prose.

- `elements` is an **ordered array** of `{ subjectId, costumeId? }`.
- In the `prompt`, reference each by **1-based position**: `@Element1`,
  `@Element2`, … The backend resolves each to that Subject's images — you do
  **not** paste image URLs for characters.

```
elements: [{ subjectId: "<girl-id>" }, { subjectId: "<alley-id>" }]
prompt: "@Element1 walks nervously through @Element2 at golden hour,
         handheld camera, shallow depth of field, cinematic."
```

- Every `@ElementN` must have a matching array entry and vice versa (off-by-one is
  rejected); array order defines the numbers.
- `costumeId` selects one look of a multi-look character.
- A one-off **style/mood image** (not a named subject) goes in `referenceImages`
  and is tagged `@Image1`, `@Image2` over that array — see playbook.md → Prompting
  for the multi-reference technique and the shared image budget.

### A few rules that always apply

- **Check the model first.** `get_model` reports supported inputs, element/image
  limits, prompt syntax, aspect ratios, and resolutions — they vary a lot. Find
  IDs via `list_models`; never hardcode or guess them.
- **Generation is async.** Submitting returns a `jobId`; the asset isn't ready.
  Tell the user it'll take a moment, poll `get_job_status` / `list_project_jobs`,
  and don't call a shot done until it completes and you've looked.
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
  prompt.)
- **Look at results.** `view_asset` inlines an image so you can judge it — on
  prompt? consistent? artifacts? unintended likeness? Flag problems the user
  hasn't noticed. Image-only, 10 MB cap.
- **Uploading/downloading.** Call `check_storage_reachability` once per session
  before the first upload or download; if it fails, print its `suggestion.message`
  verbatim and stop. Uploads are images only (JPEG/PNG/WebP, 25 MB). To save an
  asset to disk, `get_asset_download_url` — ask where to save first.

> Reusable prompt **text** (a saved look or lighting block) is coming as a
> first-class feature — **Variables** — but isn't in the MCP connector yet. Until
> it lands, keep reusable prompt language in a notes file or canvas text notes
> (`create_text_note`).

## Going deeper

For larger build-outs — turning a script into a board, batch-producing a sequence,
organizing the canvas, and detailed prompt craft (consistency blocks, timeline
prompting) — read **`playbook.md`** in this skill folder and follow it. Load it
when the task calls for it, not for a quick one-off shot.

## Quick gotchas

- No `create_project` over MCP — the user makes projects in the app.
- `@ElementN` tokens must exactly match the `elements` array.
- Uploads are images only (JPEG/PNG/WebP, 25 MB); no audio/video uploads.
- Collection members must share one scene; bins don't nest.
- Don't fabricate IDs or model names — discover them via the read tools.
- If a board read fails with an over-limit error, try `get_board_scenes` (lighter);
  if that also fails, have the user contact support@martini.film with the project
  ID.
