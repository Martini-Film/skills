# Martini Skills

Agent skills for [Martini](https://martini.film) — the AI video production tool.
Each skill is a self-contained set of instructions (and any supporting files) that
teaches an AI agent how to do something with Martini through its MCP connector.

Skills here are harness-neutral: a `SKILL.md` works as a `/name` command in Claude
Code, a `$name` skill in Codex, or anywhere else that reads the skill format.

## Skills

| Skill | What it does |
|---|---|
| [`martini-skills`](martini-skills/) | The core filmmaking guide — generate shots and images, keep characters consistent across shots with Subjects, build a board from a script, batch-produce, and iterate. Covers the Subject/@Element prompt convention, model selection, async generation jobs, and credit (olive) cost. Reads `playbook.md` for larger build-outs. |
| [`blender-to-martini`](blender-to-martini/) | Take a Blender viewport shot (blockout + keyframed camera) into Martini as an editable, camera-faithful draft — entirely through the Blender MCP + Martini MCP, with no Blender addon and no credentials in Blender. Ships `export_take.py`, the Blender-side render script the skill runs. |

## Layout

Each skill lives in its own top-level directory:

```
<skill-name>/
  SKILL.md         # the skill: YAML frontmatter (name, description) + instructions
  <supporting>     # optional bundled files the skill reads or runs
```

`SKILL.md` frontmatter must include at least `name` and `description` — the
`description` is what an agent reads to decide when the skill applies, so keep it
specific about *when to use it*.

## Releases

Every push to `main` publishes a [GitHub Release](../../releases) tagged with the
commit's short SHA. Each skill is zipped on its own and attached as a release
asset (e.g. `martini-skills.zip`, `blender-to-martini.zip`) — the zips are flat,
holding just the skill's files. See [`.github/workflows/release.yml`](.github/workflows/release.yml).

When you add a new skill, add a matching `zip` line and entry to the release
workflow so it ships too.

## Editing a skill

Edit the files under the skill's directory and open a PR. Merging to `main` cuts a
new release automatically, so review before merge.
