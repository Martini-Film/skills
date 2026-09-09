---
name: martini-export
description: >-
  Use when the user wants to export, deliver, or organize their final Martini
  project — downloading generated assets, getting an XML timeline export for
  Premiere Pro or DaVinci Resolve, organizing shots into a final sequence,
  preparing files for client or team delivery, or understanding what to package
  and send. Do NOT use for script writing, shot generation, or subject setup.
---

# martini-export — Delivery and export

## What this skill does

Handles the final phase: getting generated shots out of Martini, organized, and
ready for delivery — whether that's downloading clips, exporting an XML timeline
to an NLE, or preparing a handoff package for a client or team.

## What this skill does NOT do

- Script or narrative writing → use **martini-script**
- Shot planning → use **martini-storyboard**
- Generating new shots → use **martini-shot-generation** (unless filling a gap)
- Fixing prompts or iterating on results → use **martini-iteration**

## Common user requests

- "How should I export this?"
- "Prepare this project for delivery."
- "How do I organize the final clips?"
- "What should I send to the client / team?"
- "Get the XML for Premiere."
- "Download all the shots from this scene."

## Before any transfer

Call `check_storage_reachability` once per session before the first upload or
download. If it fails, print its `suggestion.message` verbatim and stop — do not
proceed until resolved.

## Downloading a single asset

1. Identify the node — `get_scene_layout` or `get_scene` to find it.
2. Get asset details — `get_asset`.
3. **Ask where to save** before downloading.
4. Get the download URL — `get_asset_download_url` returns a time-limited
   presigned URL. Download to the user's specified path promptly.

```
get_asset({ projectId, assetId })              → confirm it's the right shot
get_asset_download_url({ projectId, assetId }) → presigned URL (time-limited)
# Save to user's chosen path
```

## Downloading a full sequence

1. `get_bin_contents` — list nodes in the bin/sequence.
2. `get_asset` per node — collect asset IDs.
3. `get_asset_download_url` per asset.
4. Download each to the user's chosen folder.

State the count, confirm the destination folder, then proceed. Name files in shot
order (e.g. `shot_01.mp4`, `shot_02.mp4`) so they import cleanly.

## XML export for Premiere Pro / DaVinci Resolve

The XML carries the timeline assembly — shot order, cut points, durations. Media
files must be downloaded separately and relinked in the NLE.

Steps:
1. Confirm the user's NLE (Premiere Pro or DaVinci Resolve).
2. Export the XML from the Martini timeline.
3. Ask where to save the XML before writing it.
4. Remind the user:
   - **Premiere Pro:** File → Import → select the XML.
   - **DaVinci Resolve:** File → Import Timeline → Import AAF, EDL, XML.
5. After import, relink media to the downloaded clip files if prompted.

## Organizing for delivery

Before downloading, review the board with the user:
- Are all shots approved? Any still needing a retry?
- Are shots in the right order in their bins?
- Are there any placeholder/empty nodes to remove?

Suggest a clean folder structure for the handoff package:
```
project-name/
  finals/
    shot_01.mp4
    shot_02.mp4
    ...
  timeline/
    project-name-export.xml
  ref/
    (any reference images or subject sheets)
```

## What can and can't be exported

| Can export | Cannot |
|---|---|
| Generated images (JPEG/PNG/WebP) | Audio (not supported over MCP) |
| Generated video clips | Video uploads (images only via MCP) |
| Timeline XML | Project settings / metadata |

## Quick gotchas

- Download URLs are time-limited — use them promptly after calling
  `get_asset_download_url`.
- Always ask where to save before writing any file to disk.
- `view_asset` is for inline preview only (images, 10 MB cap) — not a download.
- `check_storage_reachability` must pass before any transfer.
