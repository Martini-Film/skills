---
name: blender-to-martini
description: Take a Blender viewport shot (blockout + keyframed camera) into Martini as an editable, camera-faithful draft — entirely through Blender MCP + Martini MCP, no Blender addon.
category: Generation
tags: [blender, mcp, camera, seedance, handoff]
---

You bring a shot a user has authored in **Blender** into **Martini**, where it
becomes an editable draft whose AI render **faithfully follows the camera move
the user keyframed**. This runs entirely through two MCP servers the user
already has connected — **Blender MCP** (to read the scene + render) and
**Martini MCP** (to import) — so there is **no Blender addon to install, and no
credentials ever enter Blender**.

The thesis (do not violate it): **Blender authors the camera; Martini renders it
and must never re-invent the motion.** Blender renders a clean flythrough along
the authored camera (the "guide"); Martini hands that guide to Seedance with a
"follow the guide's exact trajectory" instruction.

## Prerequisites

- **Blender MCP** connected, able to run Python (`execute_blender_code` or
  equivalent). If the connected Blender MCP cannot execute code, stop and tell
  the user — this skill needs it to render the guide.
- **Martini MCP** connected (the `render_blender_take` tool must be available).
- An open Blender scene with a **blockout/greybox**, an **active camera**, and
  the camera **keyframed** across a frame range.

## Interaction principles (read before acting)

- **Narrate each step** in plain language ("Reading your scene… rendering a
  clean guide along your camera in Blender (~15s)… setting it up in Martini…").
  The user cannot see the MCP calls; the render briefly makes Blender busy.
- **Infer, don't interrogate.** Read camera, frame range, fps, and aspect from
  the scene. Only ask for a shot name if you can't sensibly default it, and an
  optional first-frame look. Don't quiz the user about settings.
- **Draft-first — never auto-spend.** Always import with `autoRender: false`.
  The user frames the first frame and presses Generate in Martini. State this.
- **Hand off cleanly.** End with the Martini link and the exact next step.
- **Fail gracefully.** No active camera, no keyframes, or a Blender MCP that
  can't render → say what's wrong and how to fix it; don't push a broken take.

---

## Step 1 — Inspect the scene (Blender MCP)

Run a small Python probe via Blender MCP to confirm the shot is ready and read
its parameters. Report what you found, conversationally.

```python
import bpy, json

s = bpy.context.scene
cam = s.camera

def camera_moves(scene, camera):
    """True if the camera's world transform or lens changes across the range —
    catches motion from ANY source (object keyframes, a parent empty/rig, a
    constraint, drivers, or lens/zoom keys), not just the camera's own action."""
    if not camera or scene.frame_end <= scene.frame_start:
        return False
    saved = scene.frame_current
    f0, f1, n = scene.frame_start, scene.frame_end, 6
    frames = sorted({round(f0 + (f1 - f0) * i / (n - 1)) for i in range(n)})
    samples = []
    for f in frames:
        scene.frame_set(f)
        m = camera.matrix_world
        loc, rot = m.to_translation(), m.to_quaternion()
        samples.append((loc.x, loc.y, loc.z, rot.x, rot.y, rot.z, rot.w, camera.data.lens))
    scene.frame_set(saved)
    first = samples[0]
    return any(abs(v - first[j]) > 1e-6 for row in samples for j, v in enumerate(row))

print(json.dumps({
    "has_camera": cam is not None,
    "camera": cam.name if cam else None,
    "frame_start": s.frame_start, "frame_end": s.frame_end,
    "fps": s.render.fps,
    "res_x": s.render.resolution_x, "res_y": s.render.resolution_y,
    "animated": camera_moves(s, cam),
}))
```

If `has_camera` is false or `animated` is false, stop and guide the user (set an
active camera; animate its motion across the frame range). Detecting motion by
sampling `matrix_world` — rather than checking `cam.animation_data.action` —
means a camera driven by a parent empty, a rig, a constraint, or lens/zoom
keyframes is correctly recognised as a valid shot (it would otherwise be rejected
even though `export_take.py` samples and renders it fine).

## Step 2 — Confirm intent (light touch)

Default the **shot name** from the .blend filename or the camera. Optionally ask
for a one-line **first-frame look** (e.g. "rain-slick neon alley, anamorphic") —
but it's fine to leave blank; the user sets it on the draft in Martini. Do **not**
ask about model, resolution, or guide engine — defaults are good.

## Step 3 — Ensure a Martini project + canvas (Martini MCP)

Use `get_projects` to find the target project if the user named one, else
`create_project`. Keep the `projectId`. The guide upload needs a canvas, so read
`get_board_overview` (or `get_board_canvases`) and reuse the first canvas; if the
project is empty, `create_canvas`. Keep the `canvasId`.

## Step 4 — Render the guide (Blender MCP)

Read `export_take.py` from this skill directory and run it via Blender MCP,
injecting a `CONFIG` dict (prepend it to the script source). The default op
(`render`) renders a **clean guide flythrough** to a file on the Blender host
(the first frame is grabbed server-side from frame 0 of the guide, so it's
pixel-consistent and needs no extra render), samples the full camera path, and
prints a JSON result between `===MARTINI_TAKE_BEGIN===` / `===MARTINI_TAKE_END===`.
It returns **file paths + sizes, not base64** — the bytes go straight to R2 in
Step 4b, never through you.

Prepend, then send the whole thing to `execute_blender_code`:

```python
CONFIG = {"op": "render", "mode": "follow", "guide_engine": "fast_eevee", "shot_name": "<shot name>"}
# …contents of export_take.py follow…
```

Extract the JSON. If `ok` is false, surface `error`. You get
`result.guide = {path, filename, content_type, size_bytes}` (a ~100-300 KB
480-720p clip), `result.camera_path_file = {path, filename, content_type,
size_bytes}` (the authored camera move, written to disk for upload — not inlined),
and the scene params. `first_frame` is normally `null` (frame-grab); set
`CONFIG["first_frame"] = True` for a materials-rich scene where you want a full
scene-engine first frame.

### Step 4a — Prepare the uploads (Martini MCP)

Ask Martini for a presigned R2 PUT URL for the guide, sized from the render:

```
upload_assets_prepare(
  projectId: <projectId>,
  canvasId:  <canvasId>,
  files: [{ filename: <result.guide.filename>, contentType: "video/mp4", sizeBytes: <result.guide.size_bytes> }],
)
```

Keep `assetId` (the **guideAssetId**) and `uploadUrl` from `results[0]`. Then
presign the camera path as a sidecar of that guide asset:

```
prepare_blender_camera_path_upload(
  projectId:    <projectId>,
  guideAssetId: <assetId>,
  sizeBytes:    <result.camera_path_file.size_bytes>,
)
```

Keep its `uploadUrl` (the camera-path PUT URL). If either `directUpload` is
`false` (filesystem-only local storage with no presign), fall back: re-run Step 4
with `CONFIG["inline"] = True` and pass `result.inline.guide_base64` as
`guideBase64` and `result.camera_path` as `cameraPath` to `render_blender_take`
(Steps 4b–4c are then skipped).

### Step 4b — Upload the bytes (Blender MCP, `op="put"`)

Run `export_take.py` again with the put op so Blender PUTs both files straight to
R2 in one call (no credentials — the presigned URLs carry the signature):

```python
CONFIG = {"op": "put", "puts": [
  {"path": "<result.guide.path>", "url": "<guide uploadUrl>", "content_type": "video/mp4"},
  {"path": "<result.camera_path_file.path>", "url": "<camera-path uploadUrl>", "content_type": "application/json"},
]}
# …contents of export_take.py follow…
```

Confirm every `results[*].ok` is true (HTTP 2xx). If not, surface the error.

### Step 4c — Complete the upload (Martini MCP → `upload_assets_complete`)

```
upload_assets_complete(projectId: <projectId>, assetIds: [<guideAssetId>])
```

This lands the guide as a first-class **video node** (thumbnail + proxy). The
camera-path sidecar needs no completion — it rides in the guide asset's folder.

## Step 5 — Import into Martini (Martini MCP → `render_blender_take`)

Reference the uploaded guide by id — no base64, no inline camera path.
`render_blender_take` **reuses** the existing guide asset (it won't re-land a
duplicate) and reads the camera path from the guide's sidecar by reference.
**Always `autoRender: false`** (draft-first).

```
render_blender_take(
  projectId:        <projectId>,
  canvasId:         <canvasId>,
  guideAssetId:     <guideAssetId>,         # reused, not duplicated; its camera-path.json sidecar is read automatically
  shotName:         <result.shot_name>,
  durationSeconds:  <result.duration_seconds>,
  aspectRatio:      <result.aspect_ratio>,
  mode:             "follow",
  model:            "seedance-2.0",
  skipStartingFrame: false,          # two-stage: art-direct the first frame
  startingFramePrompt: <optional look from Step 2>,
  autoRender:       false,           # land editable drafts; never auto-spend
)
```

It grabs frame 0 as the **first-frame draft**, creates the **animate shot
draft**, adds a guidance note, lays the nodes out tidily, and stamps the authored
camera move onto the shot (read from the guide's `camera-path.json` sidecar). It
returns `projectUrl`. (You can still pass `cameraPath` inline to override the
sidecar — the filesystem-storage fallback above does exactly that.)

For the `interpolate` mode (first + last frame, no camera follow), the render op
also writes both frames; upload each via the same prepare → put → complete dance
(contentType `image/jpeg`) and pass `firstFrameAssetId` + `lastFrameAssetId` with
`mode: "interpolate"`. (For tiny images the base64 inputs are also fine.)

## Step 6 — Hand off

Give the user the `projectUrl` and the next step, e.g.:

> Your Blender shot is in Martini as an editable draft → <projectUrl>
> ① Tweak the first-frame prompt and press Generate to style your blockout.
> ② Then Generate the shot — it follows the camera you keyframed in Blender.
> Nothing's been spent yet.

---

## Notes

- **Why presigned R2 (not base64):** the guide is a video and the camera path is
  a multi-KB JSON blob — both too large to push through the agent context
  reliably. `upload_assets_prepare` (guide) and `prepare_blender_camera_path_upload`
  (camera path) return presigned PUT URLs and Blender uploads the bytes directly to
  R2; the URLs carry the auth, so Blender stays credential-free. The
  `guideBase64` / `firstFrameBase64` inputs and inline `cameraPath` remain as a
  fallback for tiny clips or filesystem-only local storage (Step 4a's
  `directUpload:false` branch).
- **Camera path** is preserved on the import for provenance (the faithful render
  rides the guide video, not re-derived coordinates). It's stored as a
  `camera-path.json` sidecar in the guide asset's R2 folder and read back by
  reference (`guideAssetId`) at import — never inlined through the agent.
- **This replaces the Blender addon.** The addon was a logged-in API client whose
  auth/distribution/version drift caused most of its bugs; this skill needs none
  of that. Non-agent hand-artists (no Blender MCP) use Martini's web file-drop.
