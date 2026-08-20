---
skill_name: 04-cover
version: 1.0.0
last_updated: 2026-08-20
owner: eng-team
runtime: hermes
---

# Phase 04 — Cover

## 1. Objective

Pin the current behavior at the incision points with characterization tests, written and
passing **before** any production code is touched. Output is `coverage-before.md` plus the
committed tests. Gate: coverage at the incision points must measurably improve, or the
surgery stops.

## 2. Execution Steps

### Step 1 — Read `incision-points.md`

Take the selected incisions and the behaviors phase 03 said must be characterized.

*Error handling:* if it is missing or unapproved, stop and return to phase 03.

### Step 2 — Measure and record baseline coverage

Run the coverage tool over the surgical field. Record the numbers, the command used, and
the commit SHA in `coverage-before.md`.

*Error handling:* if no coverage tooling exists, establish it or record an explicit,
reproducible baseline measurement. An unmeasured baseline cannot satisfy this phase's
gate — say so at the gate rather than proceeding.

### Step 3 — Write characterization tests

Pin what the code **does**, not what it should do. Bugs included: if the current behavior
is wrong, the test records the wrong behavior and the test name says so.

*Error handling:* if a test fails on first run, the assertion is wrong, not the system —
correct the test to match observed behavior. If the behavior is non-deterministic, pin
the invariant instead and note the non-determinism.

### Step 4 — Cover the error paths too

Characterize failure modes at the incision points: exceptions, timeouts, empty and
malformed input.

*Error handling:* if an error path cannot be triggered through a seam, record it as
uncovered in `coverage-before.md`. Do not paper over it.

### Step 5 — Re-measure and check the gate

Run coverage again. Compare against baseline at the incision points.

*Error handling:* if coverage has not measurably improved, **stop the surgery**. Report
the before/after numbers and what blocked the improvement. Do not proceed to phase 05,
and do not adjust thresholds, exclude files, or reshape the metric to clear the gate.

### Step 6 — Commit and HALT

Commit the tests and `coverage-before.md` to the surgery branch. Stop for human approval.

*Error handling:* the whole test suite must be green at this gate. If a pre-existing
failure is unrelated to the field, record it explicitly at the gate.

## 3. Constraints & Preferences

- Tests come **before** production-code edits. No exceptions, no "small change first".
- Characterization tests describe current behavior, including bugs.
- The gate is a measurement, not a judgement: before and after numbers, both recorded.
- Coverage improvement is measured at the incision points, not repo-wide.
- Test names state what is pinned, including when what is pinned is a defect.

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
