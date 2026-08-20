# company-skills-library

A "thin agent, thick skill" library. Task logic lives in versioned Markdown SOPs;
agents stay generic. Change how work gets done by editing a skill file and merging a
PR — not by rewriting an agent.

## Layout

```
company-skills-library/
├── .claude-plugin/marketplace.json
├── CODEOWNERS
├── README.md
├── content/youtube-publish/
│   ├── .claude-plugin/plugin.json
│   ├── skills/{title-generation, thumbnail-brief, description-writing, youtube-orchestrator}.md
│   └── hooks/{hooks.json, track-usage.sh}
└── engineering/brownfield-surgery/
    ├── .claude-plugin/plugin.json
    └── skills/{surgery-orchestrator, 01-plan, 02-map, 03-break, 04-cover, 05-implement, 06-refactor, 07-finish}.md
```

## Plugins in v1

| Plugin | Path | What it does |
| --- | --- | --- |
| `youtube-publish` | `content/youtube-publish` | Title options → thumbnail brief → description, assembled into one human review package. |
| `brownfield-surgery` | `engineering/brownfield-surgery` | Seven human-gated phases for modifying a legacy system. Template: [brownfield-code-surgeon](https://github.com/vivganes/brownfield-code-surgeon). |

## Install

In Claude Code: `/plugin` → Marketplace → add this repository → install
`youtube-publish` and/or `brownfield-surgery`. Enable auto-update so rigs pick up
merged SOP changes.

## Skill conventions

Every skill file carries YAML frontmatter (`skill_name`, `version`, `last_updated`,
`owner`, `runtime: hermes`) and these sections in order:

1. Objective
2. Execution Steps — each step carries its own error handling
3. Constraints & Preferences
4. Self-Improvement Loop
5. Changelog

The Self-Improvement Loop is byte-identical in every skill. Its rule matters most:
a skill that wants to change itself commits to `proposal/<skill>-<date>` and opens a
PR. **Nothing pushes to `main`** — cron propagates `main` to every rig within 15
minutes, so an unreviewed push is a fleet-wide change.

## Hermes rig setup

```bash
cd ~/.hermes
git clone git@github.com:your-org/company-skills-library.git skills
crontab -l | { cat; echo '*/15 * * * * cd ~/.hermes/skills && git pull --ff-only'; } | crontab -
```

- `--ff-only` is mandatory. Divergence on a production rig fails loudly instead of
  silently merging.
- Rollback is `git revert` on the repo; cron propagates the revert within 15 minutes.
- Keep volatile data — run counts, dates, session state — in `MEMORY.md`, never in
  skill files. Skills live in the cached prompt tier and must stay stable.

## Ownership

`CODEOWNERS` routes `/content/` to `@content-team` and `/engineering/` to `@eng-team`.
Proposal PRs land on the owning team.

## Usage tracking

`youtube-publish` registers a `PreToolUse` hook on `Skill` that appends one JSON line
per invocation to `usage-log.jsonl` inside the plugin root. The log is generated at
runtime and is not committed.

## Note on skill file layout

This repo follows the build spec's flat layout: one `.md` file per skill directly under
each plugin's `skills/` directory. Claude Code's own skill loader discovers skills as
`skills/<skill-name>/SKILL.md` with `name` and `description` frontmatter. If these
skills need to be auto-discovered by Claude Code rather than read as SOP documents,
move each `skills/<name>.md` to `skills/<name>/SKILL.md` and add `name` and
`description` keys to the frontmatter; no body content changes.
