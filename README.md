# company-skills-library

One skill set, proven end to end: repo → plugin → skill → Hermes sync. Task logic
lives in versioned Markdown SOPs; agents stay generic. Change how work gets done by
editing a file and merging a PR — not by rewriting an agent.

v1 ships **one plugin**: `brownfield-surgery`. Everything else waits until the
pipeline is validated on a live rig.

## Layout

```
company-skills-library/
├── .claude-plugin/marketplace.json
├── README.md
└── engineering/brownfield-surgery/
    ├── .claude-plugin/plugin.json
    └── skills/{surgery-orchestrator, 01-plan, 02-map, 03-break, 04-cover, 05-implement, 06-refactor, 07-finish}.md
```

## brownfield-surgery

Modifying a legacy system through seven phases, in order, each ending at a human
gate, each writing an artifact the next phase reads instead of re-deriving.

| Phase | Does | Artifact |
| --- | --- | --- |
| `01-plan` | Surgical target, what must NOT change, success criteria | `plan.md` |
| `02-map` | Trace inputs/processes/outputs/seams. Zero code edits | `seam-map.md` |
| `03-break` | Pick incision points, from the seam map only | `incision-points.md` |
| `04-cover` | Characterization tests **before** touching code | `coverage-before.md` + tests |
| `05-implement` | The change, on `surgery/<date>` | `change-log.md` |
| `06-refactor` | Cleanup inside the surgical field only | `refactor-notes.md` |
| `07-finish` | PR with before/after coverage, results, summary | the PR |

`surgery-orchestrator` sequences the phases and enforces the gates. It holds no
engineering technique — that lives in the phase SOPs.

Two hard gates: **04** stops the surgery outright if coverage at the incision points
does not measurably improve, and **07** never merges — a human does.

Forbidden in every phase: no commits to `main`, no edits outside the surgical field,
no deleting or weakening tests to pass a gate.

Adapted from [brownfield-code-surgeon](https://github.com/vivganes/brownfield-code-surgeon).

## Install

In Claude Code: `/plugin` → Marketplace → add this repository → install
`brownfield-surgery`. Enable auto-update so rigs pick up merged SOP changes.

## Hermes rig setup

```bash
cd ~/.hermes
git clone git@github.com:your-org/company-skills-library.git skills
crontab -l | { cat; echo '*/15 * * * * cd ~/.hermes/skills && git pull --ff-only'; } | crontab -
```

- `--ff-only` is mandatory. Divergence on a live rig fails loudly instead of silently
  merging.
- Rollback is `git revert` on the repo; cron propagates the revert within 15 minutes.
- Keep volatile data — run counts, dates, session state — in `MEMORY.md`, never in
  skill files. Skills live in the cached prompt tier and must stay stable.

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

## Acceptance checklist

- [ ] Repo matches the tree above; plugin installs via `/plugin` → Marketplace
- [ ] A real surgery runs end to end on Hermes and produces a PR with coverage evidence
- [ ] Cron pulls a test commit within 15 min
- [ ] Self-improvement loop produces a `proposal/` branch, never a commit on `main`

## Note on skill file layout

Skills are flat `.md` files under `skills/`. Claude Code's own loader discovers skills
as `skills/<skill-name>/SKILL.md` with `name` and `description` frontmatter. If these
need to be auto-discovered rather than read as SOP documents, move each
`skills/<name>.md` to `skills/<name>/SKILL.md` and add `name` and `description` keys;
no body content changes.

## Deferred to v1.1

`youtube-publish` and its skills (dropped from v1 — not in use), CODEOWNERS,
usage-tracking hooks.
