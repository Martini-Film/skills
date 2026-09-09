---
name: martini-subjects
description: >-
  Use when the user needs to keep a character, person, prop, animal, or location
  visually consistent across multiple shots — creating Subject descriptions,
  managing reference images, using the @Element convention in prompts, or deciding
  when and how to reference a recurring visual identity. Do NOT use for narrative
  writing, full storyboard planning, or export.
---

# martini-subjects — Character and visual consistency

## What this skill does

Manages the visual identity of anything that recurs across shots: characters,
props, animals, locations, costumes. Output is either a Subject setup in Martini
(via MCP tools) or guidance on how to describe and reference a recurring element
consistently.

The golden rule: the moment something appears in more than one shot, it gets a
Subject. A character described in words comes out different every time; a Subject
keeps them consistent.

## What this skill does NOT do

- Writing the script or story → use **martini-script**
- Planning the shot list → use **martini-storyboard**
- Writing the full generation prompt → use **martini-shot-generation**
- Export → use **martini-export**

## Common user requests

- "Keep this character consistent across shots."
- "Create a subject description for this carrot character."
- "How should I define this recurring location?"
- "Make sure Helen looks the same in every scene."
- "I have a reference image — how do I use it?"

## Creating a Subject

**Without a reference image:**
```
create_subject({ projectId, sceneId, name: "Helen", type: "character" })
```
Add a description in the Subject notes. Images can be added later via
`update_subject_images`.

**With the user's own image:**
1. `check_storage_reachability` — once per session before the first upload.
   If it fails, print its `suggestion.message` verbatim and stop.
2. `upload_asset_init` → PUT bytes to the presigned URL → `upload_asset_complete`.
   Images only: JPEG/PNG/WebP, 25 MB cap.
3. `create_subject` with the CDN URL as `mainImageUrl`. Add more angles via
   `referenceImageUrls` or `update_subject_images`.

More reference angles = stronger consistency. Ask if the user has a front view,
side view, or close-up in addition to the main image.

## The @Element convention

This is how a Subject enters a generation prompt.

- `elements` is an **ordered array** of `{ subjectId, costumeId? }`.
- In the prompt, reference each by 1-based position: `@Element1`, `@Element2`, …
- The backend resolves each token to that Subject's images — do **not** describe
  the character in prose when using elements.
- Every `@ElementN` must have a matching array entry — off-by-one is rejected.
- `costumeId` selects one look for a multi-look character.

```
elements: [{ subjectId: "<helen-id>" }, { subjectId: "<kitchen-id>" }]
prompt: "@Element1 stands at the counter in @Element2, morning light,
         medium shot, static camera."
```

## Reference images vs. Subjects

A one-off style or mood image (not a named subject) goes in `referenceImages`
and is tagged `@Image1`, `@Image2` — numbered separately from `@Element`:

```
referenceImages: ["<jacket-url>"]
prompt: "@Element1 wearing @Image1 as the jacket reference, walking down the street."
```

**Shared image budget (Seedance):** up to 4 elements within 9 total images.
Exceed it and extra `@Image` tokens stay as plain text. Always check `get_model`
for the actual limits.

## Organizing Subjects with Collections

Group related Subjects into Collections so the board stays navigable:

```
create_subject_collection({ projectId, sceneId, name: "Cast" })
add_subjects_to_collection({ collectionId, subjectIds: [...] })
```

Suggested groups: "Cast", "Locations", "Props". Members must share one scene.
Removing all members dissolves the collection.

## When to create a Subject vs. just describe in prompt

| Situation | Recommendation |
|---|---|
| Character appears in 2+ shots | Always create a Subject |
| Location appears in 2+ shots | Create a Subject |
| One-off background / mood image | Use `referenceImages` + `@Image` |
| Generic unnamed extra | Describe in prose — no Subject needed |

## Handoff

Once Subjects are set up, move to **martini-shot-generation** to write prompts
that reference them correctly via `@Element`.
