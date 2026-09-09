---
name: martini-project-setup
description: >-
  Use when the user is starting a new Martini project and wants to structure it
  before generation begins — planning scenes and canvases, deciding how to organize
  shots, references, and subjects across a large project, or asking how to set up
  a project with many shots or multiple sequences. Also use when the user asks
  "how should I structure everything before I start?" or has a film project with
  50+ shots and needs a plan. Do NOT use for generating shots or writing scripts.
---

# martini-project-setup — Structuring a project before you build it

## What this skill does

Helps the user plan and set up a Martini project structure before generation
begins — deciding how to organize scenes, canvases, references, and Subjects so
the project stays navigable as it grows.

## What this skill does NOT do

- Writing the script or story → use **martini-script**
- Planning the shot list → use **martini-storyboard**
- Uploading reference files → use **martini-upload**
- Generating shots → use **martini-shot-generation**
- Organizing an already-messy board → use **martini-organization**

## Common user requests

- "I have a film project with 100 shots — how should I structure everything?"
- "How should I set up my project before I start generating?"
- "How do I organize a project with multiple scenes?"
- "What should I do first before I start making shots?"
- "How do I structure references, subjects, and shots?"

## Key constraints to know upfront

- **Projects must be created in the Martini app** — no `create_project` over MCP.
  If `get_projects` is empty, tell the user to create a project in the app first.
- **One project = one film/board.** Everything lives under a `projectId`.
- **Subjects can be shared across canvases within one project** — a character
  Subject created in one scene is accessible in another scene of the same project.
- **Cross-project reuse is not supported** — Subjects, assets, and boards are
  scoped to a single project. For a new film, create a new project.
- **Scenes are canvases**, not chapters. Use scenes to separate genuinely distinct
  sequences, not to create one scene per shot.

## Recommended project structure

For most projects, start with this layout and adapt:

```
Project: "Film Title"
│
├── Scene: "References & Subjects"   ← dedicated canvas for all reference material
│   ├── Collection: "Cast"           ← character Subjects
│   ├── Collection: "Locations"      ← location Subjects
│   ├── Collection: "Props"          ← prop Subjects
│   └── Collection: "Style Refs"     ← mood boards, color palette images
│
└── Scene: "Main Board"              ← all shot nodes live here
    ├── Bin: "Act 1 — [description]"
    ├── Bin: "Act 2 — [description]"
    └── Bin: "Act 3 — [description]"
```

For very large projects (100+ shots), consider splitting into multiple scenes by
act — but only if the acts are genuinely independent:

```
├── Scene: "References & Subjects"
├── Scene: "Act 1 — Setup"
├── Scene: "Act 2 — Conflict"
└── Scene: "Act 3 — Resolution"
```

## Setup workflow (step by step)

**1. Create the project in the app**
Open Martini, create the project. Then come back to MCP.

**2. Confirm the project exists**
```
get_projects() → confirm the project is there, note the projectId
```

**3. Create reference scene first**
```
create_scene({ projectId, name: "References & Subjects" })
```
This is where all Subjects and reference images will live, separate from shots.

**4. Create Subjects for recurring elements**
For each character, location, and prop that will appear more than once:
```
create_subject({ projectId, sceneId: <refs-scene-id>, name, type })
```
Upload reference images via **martini-upload** and attach them.
Group into Collections: "Cast", "Locations", "Props".

**5. Create the main board scene**
```
create_scene({ projectId, name: "Main Board" })
```

**6. Scaffold the shot structure**
Create bins per act/sequence before any generation:
```
create_bin({ projectId, sceneId: <main-scene-id>, name: "Act 1 — The Arrival" })
create_bin({ projectId, sceneId: <main-scene-id>, name: "Act 2 — The Conflict" })
create_bin({ projectId, sceneId: <main-scene-id>, name: "Act 3 — Resolution" })
```
Add text note labels for each section.

**7. Choose scaffold-only or generate-now**
- **Scaffold-only first** — create empty nodes in story order, then generate later
  once structure is confirmed. Spends no olives.
- **Generate-now** — scaffold and generate immediately. Use when the user is ready.

## Sizing guide

| Project size | Recommended structure |
|---|---|
| 1–10 shots | Single scene, no bins needed |
| 10–30 shots | Single scene, 1 bin per sequence |
| 30–100 shots | 2 scenes (refs + main), bins per act |
| 100+ shots | 1 refs scene + 1 scene per act, bins per sequence within each |

## What to do before the first olive is spent

In order:
1. ✅ Project created in app
2. ✅ Reference scene created
3. ✅ Subjects created (even if empty — images added later)
4. ✅ Collections organized
5. ✅ Main board scene created with bins
6. ✅ Shot structure scaffolded (empty nodes in story order)
7. ✅ User has reviewed and confirmed structure
8. → Now generate

## See also

- **martini-upload** — uploading reference images for Subjects.
- **martini-subjects** — creating and managing Subjects.
- **martini-organization** — reorganizing an existing board.
- **martini-script** — developing the narrative before structuring the board.
- **martini-storyboard** — planning the shot list before scaffolding nodes.
