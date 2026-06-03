---
name: martini-upload
description: >-
  Use when the user wants to bring their own files into Martini — uploading
  reference images, character photos, location shots, or style references, either
  one at a time or in bulk. Covers the full upload workflow (reachability check,
  presigned URL, completion), batch uploads, supported formats, size limits, and
  what to do when upload fails. Do NOT use for generating new images or videos,
  or for downloading/exporting assets.
---

# martini-upload — Bringing your own files into Martini

## What this skill does

Handles getting the user's own files (photos, reference images, character sheets,
location shots) into Martini so they can be used as Subjects or reference images
in generation. Covers single uploads, batch uploads, and troubleshooting.

## What this skill does NOT do

- Creating Subjects from uploaded images → see **martini-subjects** for that step
- Generating new images or videos → use **martini-shot-generation**
- Downloading or exporting generated assets → use **martini-export**

## Common user requests

- "How do I upload my reference images?"
- "I have 20 photos of my character — how do I bring them in?"
- "What file formats does Martini accept?"
- "My upload failed — what do I do?"
- "I have a folder of location references I want to use."
- "What's the fastest way to bring these images into Martini?"

## Supported formats and limits

| Type | Supported formats | Max size |
|---|---|---|
| Images | JPEG, PNG, WebP | 25 MB per file |
| Video | ❌ Not supported via MCP | — |
| Audio | ❌ Not supported via MCP | — |

If the user tries to upload video or audio: explain this isn't supported over MCP
and suggest they use the Martini app directly for those file types.

## Before any upload

Call `check_storage_reachability` **once per session** before the first upload.
If it fails, print its `suggestion.message` verbatim and stop — do not attempt
any upload until resolved. This catches connectivity and permission issues early.

```
check_storage_reachability() → if ok, proceed; if not, print suggestion.message
```

## Single image upload

Three steps — init, PUT, complete:

```
1. upload_asset_init({ projectId, filename: "character-front.jpg", mimeType: "image/jpeg" })
   → returns { uploadUrl, assetId }

2. PUT the file bytes to uploadUrl (presigned S3 URL — use promptly, it expires)

3. upload_asset_complete({ projectId, assetId })
   → returns the CDN URL for use in create_subject or referenceImages
```

After completion, the CDN URL is what gets passed to `create_subject` as
`mainImageUrl`. See **martini-subjects** for the next step.

## Batch upload (multiple images)

For bulk uploads use the batch variants — more efficient than looping single uploads:

```
1. upload_asset_init_batch({ projectId, files: [
     { filename: "char-front.jpg", mimeType: "image/jpeg" },
     { filename: "char-side.jpg",  mimeType: "image/jpeg" },
     { filename: "location-a.jpg", mimeType: "image/jpeg" },
   ]})
   → returns [{ uploadUrl, assetId }, { uploadUrl, assetId }, ...]

2. PUT each file to its own uploadUrl (can be done in parallel)

3. upload_asset_complete_batch({ projectId, assetIds: [...] })
   → returns CDN URLs for all files
```

State the count before starting a batch. After completion, confirm how many
succeeded and flag any that failed individually.

## Organizing uploads as they come in

Large uploads get unwieldy fast. As files come in, immediately assign them:

- **Character photos** → create a Subject, use as `mainImageUrl` + `referenceImageUrls`
- **Location shots** → create a location Subject
- **Style/mood references** → keep as `referenceImages` (not Subjects) — use
  `@Image1`, `@Image2` in prompts
- **Props** → create a prop Subject if it recurs; keep as reference image if one-off

Don't let uploads accumulate as loose assets — assign them a role right away.
See **martini-organization** for how to keep the board navigable.

## How many reference images per Subject?

More is better, up to the model's image budget:

| Images provided | Result |
|---|---|
| 1 (front only) | Basic consistency — works but may drift |
| 2–3 (front + side + close-up) | Good consistency across shots |
| 4+ | Strong consistency; check `get_model` for the budget limit |

On Seedance: up to 4 Subject elements within 9 total images shared with
`referenceImages`. `get_model` reports the actual limits.

## Troubleshooting uploads

| Problem | Fix |
|---|---|
| `check_storage_reachability` fails | Print `suggestion.message` verbatim; stop and wait for user to resolve |
| Presigned URL expired | Re-run `upload_asset_init` to get a fresh URL |
| File too large (>25 MB) | Ask user to resize/compress before uploading |
| Wrong file format | Only JPEG/PNG/WebP accepted; ask user to convert |
| Upload succeeds but Subject looks wrong | Add more reference angles via `update_subject_images` |

## See also

- **martini-subjects** — turning uploaded images into Subjects and using @Element.
- **martini-organization** — keeping uploads and references organized on the board.
