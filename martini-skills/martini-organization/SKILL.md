---
name: martini-organization
description: >-
  Use when the user wants to organize their Martini board — tidying a messy canvas,
  grouping shots into bins, labeling sequences with text notes, arranging shots in
  story order, organizing reference images and Subjects into Collections, or
  structuring a project with many shots so it stays navigable. Also use when the
  user says "my canvas is a mess" or asks how to manage a large number of generated
  shots or references. Do NOT use for generating new shots or exporting.
---

# martini-organization — Keeping the board navigable

## What this skill does

Helps the user structure and tidy their Martini canvas — grouping shots into
sequences, labeling sections, arranging references, and keeping a large project
from becoming unmanageable.

## What this skill does NOT do

- Generating new shots → use **martini-shot-generation**
- Creating Subjects from scratch → use **martini-subjects**
- Uploading new files → use **martini-upload**
- Exporting or delivering → use **martini-export**

## Common user requests

- "My canvas is a mess."
- "I have 300 generated shots — how do I organize them?"
- "How should I organize my references?"
- "Group these shots into scenes."
- "Label my sequences."
- "How do I keep characters separate from shots?"

## Core principles

- **Story order, left to right.** Shots should read like a timeline — left is
  earlier, right is later. A batch created without explicit positions is laid out
  in list order; pass shots in the order they play.
- **One scene per sequence, not per shot.** Keep a scene for a narrative sequence;
  create a new scene only for a genuinely separate sequence or when the user asks.
- **Group sequences into bins.** A bin is a named container for a set of shots.
  Bins don't nest — one level deep only.
- **Label everything.** Text notes create on-canvas headers, scene slugs, and
  director annotations. A board should read like a storyboard.
- **Separate references from shots.** Characters, props, and locations live in
  Collections; shot nodes live in bins. Don't mix them.

## Bins — grouping a sequence

```
# Create a bin then add nodes:
create_bin({ projectId, sceneId, name: "Act 1 — The Arrival" })
move_node_to_bin({ nodeId, binId })

# Or group existing nodes in one step:
group_nodes_into_bin({ nodeIds: [...], name: "Act 1 — The Arrival" })

# Rename or reposition:
update_bin({ binId, name: "Act 1 — Revised" })
move_bin({ binId, position: { x, y } })
```

Good bin naming: `"Scene 3 — The Chase"`, `"Opening titles"`, `"Alt takes — rooftop"`.

## Text notes — labeling the canvas

```
create_text_note({ projectId, sceneId, text: "ACT 1", position: { x, y } })
update_text_note({ noteId, text: "ACT 1 — REVISED" })
```

Use text notes for: act labels, scene slugs, TODO markers, style notes
("using teal-orange grade from here"), and director annotations.

## Collections — organizing Subjects

Collections group Subjects (not shot nodes). Keep references separate from
editorial content:

```
create_subject_collection({ projectId, sceneId, name: "Cast" })
add_subjects_to_collection({ collectionId, subjectIds: [...] })
remove_subjects_from_collection({ collectionId, subjectIds: [...] })
```

Suggested Collections for any project:
- **Cast** — human characters
- **Locations** — recurring environments
- **Props** — recurring objects
- **Style refs** — mood boards, color palette images (as reference assets)

Members must share one scene. Removing all members dissolves the collection.

## Moving nodes

```
move_node({ nodeId, position: { x, y } })
```

After a batch creation, nudge nodes into the right layout. Use explicit positions
for deliberate storyboard-style layouts (e.g. rows per sequence).

## Reading the board before reorganizing

Always read before writing — these tools are free:

```
get_board_scenes()          → list all scenes
get_scene({ sceneId })      → scene details
get_scene_layout({ sceneId }) → node positions
get_bin_contents({ binId }) → what's in a bin
get_board_assets({ projectId }) → all assets in the project
get_board_subjects({ projectId }) → all Subjects
get_text_note({ noteId })   → read a note
```

## Suggested layout for a typical project

```
Scene: "Main Board"
├── [Text note] "CAST & REFERENCES"
│   └── Collections: Cast / Locations / Props
├── [Text note] "ACT 1 — SETUP"
│   └── Bin: "Act 1 shots" → shot nodes in order
├── [Text note] "ACT 2 — CONFLICT"
│   └── Bin: "Act 2 shots" → shot nodes in order
└── [Text note] "ACT 3 — RESOLUTION"
    └── Bin: "Act 3 shots" → shot nodes in order
```

## Handling 100+ shots

When a project grows large:
1. **Read the board first** — `get_scene_layout` to understand current state.
2. **Group by sequence** — identify natural scene breaks, create one bin per sequence.
3. **Name bins descriptively** — include act number and scene description.
4. **Move loose nodes into bins** — `move_node_to_bin` for each ungrouped node.
5. **Add text note headers** — label each act/section so the canvas scans quickly.
6. **Separate alt takes** — create an "Alts" bin for rejected-but-kept variations.

If a board read fails with an over-limit error, try `get_board_scenes` (lighter).
If that also fails, have the user contact support@martini.film with the project ID.

## See also

- **martini-subjects** — creating and managing Subjects and Collections.
- **martini-upload** — bringing reference images in before organizing them.
- **martini-project-setup** — structuring a project from the start before any work begins.
