---
skill_name: surgery-orchestrator
version: 1.0.0
last_updated: 2026-08-20
owner: eng-team
runtime: hermes
---

# Surgery Orchestrator

## 1. Objective

Run a change to a legacy system through seven gated phases, in order, with a human
approval between each. Every phase writes an artifact to the branch; the next phase reads
that artifact and never re-derives it. This skill sequences and enforces gates. The work
of each phase lives in that phase's SOP.

Adapted from the brownfield-code-surgeon workflow
(github.com/vivganes/brownfield-code-surgeon).

## 2. Execution Steps

### Step 1 — Confirm the surgical intent and open the branch

Restate the requested change in one sentence. Create `surgery/<date>` from the current
default branch. All artifacts and code land here.

*Error handling:* if the working tree is dirty or the current branch is `main`, stop and
ask the user to resolve before anything is written.

### Step 2 — Phase 01 `01-plan`

Invoke `01-plan`. Artifact: `surgery/<date>/plan.md`. HALT for human approval.

*Error handling:* no approval, no phase 02. An ambiguous approval is not an approval —
ask again.

### Step 3 — Phase 02 `02-map`

Invoke `02-map`, which reads `plan.md`. Artifact: `seam-map.md`. HALT for approval.

*Error handling:* if `02-map` reports it cannot trace a path, halt and surface that gap.
Do not let phase 03 guess at the missing seam.

### Step 4 — Phase 03 `03-break`

Invoke `03-break`, which reads `seam-map.md` only. Artifact: `incision-points.md`.
HALT for approval.

*Error handling:* if a proposed incision point has no corresponding seam in the map,
reject it and send phase 02 back for another pass.

### Step 5 — Phase 04 `04-cover`

Invoke `04-cover`, which reads `incision-points.md`. Artifact: `coverage-before.md` plus
committed characterization tests. GATE: coverage at the incision points must measurably
improve. HALT for approval.

*Error handling:* if coverage does not improve, stop the surgery. Report why. Do not
advance to phase 05 on an unimproved gate.

### Step 6 — Phase 05 `05-implement`

Invoke `05-implement`, which reads `plan.md` and `incision-points.md`. Artifact: the
change itself plus `change-log.md`. HALT for approval.

*Error handling:* if characterization tests fail unexpectedly, stop and report the
behavioral delta rather than updating the tests to match the new behavior.

### Step 7 — Phase 06 `06-refactor`

Invoke `06-refactor`, scoped to the surgical field only. Artifact: `refactor-notes.md`.
HALT for approval.

*Error handling:* any proposed cleanup outside the field is recorded as a follow-up, not
performed.

### Step 8 — Phase 07 `07-finish`

Invoke `07-finish`. Artifact: a PR carrying before/after coverage, test results, and a
change summary. A human merges. The orchestrator never merges.

*Error handling:* if evidence is incomplete, do not open the PR — collect the missing
evidence first.

## 3. Constraints & Preferences

- Phases run strictly in order. No skipping, no reordering, no running two phases in one
  turn.
- Every phase ends at a human gate. Silence is not approval.
- Each phase reads the prior artifact from the branch. Re-deriving a prior phase's
  conclusion is a defect, not a shortcut.
- A phase failure halts the workflow and flags that phase's SOP, not this one — unless
  the failure was in sequencing or gating, which is this SOP's responsibility.
- This SOP holds no engineering technique. Technique belongs in the phase SOPs.

### Forbidden Moves

These apply to every phase of this workflow, without exception:

- **No commits to `main`.** All work lands on `surgery/<date>`; `main` changes only by
  human merge of the phase 07 PR.
- **No edits outside the surgical field** defined in phase 01. Anything found outside it
  is written down as a follow-up, not fixed here.
- **No deleting, skipping, or weakening tests to pass a gate.** A gate that will not pass
  is a signal to stop and report, never a test to loosen.

## 4. Self-Improvement Loop

Run this loop at the end of every invocation, without exception.

1. Did any step fail? Which, why, and was it an SOP gap?
2. Was output consistent with Section 3?
3. Should this SOP be updated? If yes: commit to branch `proposal/<skill>-<date>` and open a PR. **NEVER push to `main`** — cron auto-propagates `main` to all rigs. If no repo write access: append to `MEMORY.md` under `## Skill Proposals`.
4. If nothing to change, say so explicitly.

## Changelog

| Version | Date | Change |
| --- | --- | --- |
| 1.0.0 | 2026-08-20 | Initial SOP. |
