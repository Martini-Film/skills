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

## Install

**Claude Code and Codex are the best fit** — these skills drive Martini agentically
over MCP, which is what a CLI/IDE agent is built for. Claude Desktop works too
(see below), but the agentic flows shine in a coding-agent harness.

### Claude Code / Codex (recommended)

Install with the [`skills`](https://github.com/vercel-labs/skills) CLI. This grabs
both skills and drops them into the agent's skills directory:

```bash
# Claude Code, installed globally (~/.claude/skills)
npx -y skills add github.com/Martini-Film/skills --global --agent claude-code --yes

# Codex
npx -y skills add github.com/Martini-Film/skills --global --agent codex --yes
```

Install into multiple agents at once by repeating `--agent`, or drop `--global` to
install into the current project (`.claude/skills/`) instead. To install just one
skill from the repo, add `--skill`:

```bash
npx -y skills add github.com/Martini-Film/skills --skill blender-to-martini --global --agent claude-code --yes
```

To update, re-run the same command. (`skills` supports many more agents — Cursor,
OpenCode, and others — via the same `--agent` flag.)

You'll also need the **Martini MCP** connected so the skill has tools to call —
in Claude Code: `claude mcp add --transport http --scope user martini https://www.martini.film/mcp`.

### Claude Desktop / Claude.ai

The `skills` CLI targets CLI/IDE agents, not Claude Desktop. To use a skill there,
install it manually:

1. Download the skill zip from the [latest release](../../releases/latest) —
   `martini-skills.zip` or `blender-to-martini.zip`.
2. Add it as a Skill in Claude Desktop (Settings → Capabilities/Skills → upload the zip).
3. Connect the Martini MCP connector so the skill has tools to call.

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
