---
skill_name: 06-refactor
version: 1.0.0
last_updated: 2026-08-20
owner: eng-team
runtime: hermes
---

# Phase 06 — Refactor

## 1. Objective

Clean up the code the surgery touched — inside the surgical field only. Behavior does not
change in this phase. Output is `refactor-notes.md` plus the cleanup commits. No
drive-bys.

## 2. Execution Steps

### Step 1 — Re-read the field boundary

Take the surgical field from `plan.md` and the incisions from `incision-points.md`. Those
define what may be cleaned. Everything else is out of bounds, however tempting.

*Error handling:* if the boundary is ambiguous for a specific file, treat it as outside
the field and record it as a follow-up.

### Step 2 — Confirm the suite is green

Run the full suite. Refactoring on red is not refactoring.

*Error handling:* if red, stop and return to phase 05.

### Step 3 — List candidate cleanups

Duplication introduced by the change, names that no longer describe what they do, dead
branches the change orphaned, comments the change falsified.

*Error handling:* if a candidate sits outside the field, move it to the follow-up list
immediately — do not keep it under consideration.

### Step 4 — Apply cleanups one at a time

One cleanup, one commit, suite green after each. Behavior-preserving transformations only.

*Error handling:* if a cleanup turns a test red, revert that cleanup. A red test means the
transformation was not behavior-preserving, whatever it looked like.

### Step 5 — Record follow-ups

Write everything worth fixing that was left alone, and where it lives, into
`refactor-notes.md`.

*Error handling:* never fix a follow-up "since it is only one line". Record it.

### Step 6 — Write `refactor-notes.md` and HALT

Record what was cleaned, what was left, and confirmation that behavior is unchanged.
Commit and stop for human approval.

*Error handling:* if any cleanup changed observable behavior, it was not a refactor —
revert it and raise it at the gate.

## 3. Constraints & Preferences

- **Inside the surgical field only. No drive-bys.** A one-line fix outside the field is
  still outside the field.
- Behavior-preserving changes only. Any behavior change belongs to a new surgery.
- One cleanup per commit; suite green after each.
- Formatting-only churn across untouched files is forbidden — it hides the real diff from
  the phase 07 reviewer.
- Leave the follow-up list; do not work it.

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
