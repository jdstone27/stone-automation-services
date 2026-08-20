---
name: 07-finish
description: 'Phase 07 of brownfield surgery: open the pull request carrying before/after coverage, full test results, invariants verified and outstanding follow-ups. A human merges.'
skill_name: 07-finish
version: 1.0.0
last_updated: 2026-08-20
owner: eng-team
runtime: hermes
---

# Phase 07 — Finish

## 1. Objective

Close the surgery: open a pull request from `surgery/<date>` carrying the evidence a
reviewer needs — before/after coverage, test results, and a change summary tied back to
`plan.md`. A human merges. This skill never does.

## 2. Execution Steps

### Step 1 — Gather the artifacts

Collect `plan.md`, `seam-map.md`, `incision-points.md`, `coverage-before.md`,
`change-log.md`, and `refactor-notes.md` from the branch.

*Error handling:* if any artifact is missing, stop. A missing artifact means a phase was
skipped — return to it rather than reconstructing it here.

### Step 2 — Measure coverage after

Re-run coverage with the same command recorded in `coverage-before.md`. Record after
numbers alongside the before numbers.

*Error handling:* if the command or configuration changed since the baseline, say so — a
comparison across different measurements is not evidence.

### Step 3 — Run the full suite and capture results

Full suite, clean checkout of the branch. Capture pass/fail counts and the runtime.

*Error handling:* if anything is red, do not open the PR. Report the failure and return to
the owning phase.

### Step 4 — Write the change summary

Per success criterion in `plan.md`: what was done, and the evidence it is met. Then the
invariants: each one, and how it was verified intact. Then the follow-ups from
`refactor-notes.md`.

*Error handling:* if a success criterion is not met, state it as not met. Do not reword
the criterion to fit the outcome.

### Step 5 — Open the PR

Title names the surgical target. Body carries: change summary, before/after coverage
table, test results, invariants verified, follow-ups not done, and rollback instructions.
Link the artifacts.

*Error handling:* if PR creation fails, report the error and leave the branch pushed —
never merge locally as a workaround.

### Step 6 — Hand off and stop

Request review. Stop. The surgery ends at a human merge decision.

*Error handling:* if a reviewer requests changes, route each one to the owning phase and
re-run from there. Do not patch review feedback directly in this phase.

## 3. Constraints & Preferences

- The human merges. This skill never merges, never force-merges, never enables auto-merge.
- Evidence over assertion: coverage numbers, test output, criterion-by-criterion mapping.
- Before/after coverage must come from the same command and configuration.
- Unmet criteria and undone follow-ups are stated in the PR, not omitted.
- No new code changes in this phase — only assembling and reporting.

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
