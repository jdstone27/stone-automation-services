---
skill_name: 05-implement
version: 1.0.0
last_updated: 2026-08-20
owner: eng-team
runtime: hermes
---

# Phase 05 — Implement

## 1. Objective

Make the change — the smallest change that satisfies `plan.md`, at the incision points
phase 03 chose, on branch `surgery/<date>`, with the characterization tests from phase 04
holding the line. Output is the code change plus `change-log.md`.

## 2. Execution Steps

### Step 1 — Confirm the branch and the green baseline

Verify the working branch is `surgery/<date>` and that the phase 04 suite is green before
the first edit.

*Error handling:* if the branch is wrong, switch before editing. If the suite is red,
stop — implementing on a red baseline makes every later signal meaningless.

### Step 2 — Read `plan.md` and `incision-points.md`

Take the target, the invariants, and the incisions as given.

*Error handling:* if the plan and the incisions now appear to conflict, halt and raise it
at the gate. Do not resolve the conflict by choosing one.

### Step 3 — Implement at the incision points

Change only what the incisions cover. Work in small commits, each with the suite green.

*Error handling:* if the change cannot be made within the incisions, stop and return to
phase 03 for another pass. Widening the incision mid-implementation is not permitted.

### Step 4 — Run the suite after every commit

Characterization tests must stay green, except where `plan.md` explicitly says the
behavior changes.

*Error handling:* if a characterization test fails and `plan.md` does not sanction that
change, the implementation is wrong — fix the code. Update a characterization test only
when `plan.md` names that exact behavior as changing, and record the update in
`change-log.md`.

### Step 5 — Add tests for the new behavior

Cover the behavior the change introduces, alongside the characterization tests, not
replacing them.

*Error handling:* if the new behavior is hard to test at the chosen incision, say so at
the gate — that is evidence the incision was wrong.

### Step 6 — Write `change-log.md` and HALT

Record what changed, why, which invariants were verified intact, and any characterization
test that was legitimately updated. Commit and stop for human approval.

*Error handling:* if any invariant from `plan.md` could not be verified, list it as
unverified at the gate rather than implying it holds.

## 3. Constraints & Preferences

- All work on `surgery/<date>`. Never on `main`.
- Only the incision points from phase 03 are touched.
- Smallest change that satisfies the plan. No opportunistic improvements — those are
  phase 06's, and only inside the field.
- Green suite before and after every commit.
- Invariants from `plan.md` are verified, not assumed.

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
