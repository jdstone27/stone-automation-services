---
skill_name: 02-map
version: 1.0.0
last_updated: 2026-08-20
owner: eng-team
runtime: hermes
---

# Phase 02 — Map

## 1. Objective

Trace how the system actually works around the surgical target: inputs, processes,
outputs, and the seams where behavior can be observed or intercepted without changing it.
Output is `seam-map.md`. Zero code edits.

## 2. Execution Steps

### Step 1 — Read `plan.md`

Take the target, the field, the invariants, and the open questions from phase 01. Do not
re-derive them.

*Error handling:* if `plan.md` is missing or unapproved, stop and return to phase 01.

### Step 2 — Trace inputs

Every way data enters the field: callers, entry points, config, environment, database
reads, message consumers, clock and randomness.

*Error handling:* if a caller cannot be identified statically, mark it "unknown callers"
in the map. Do not assume there are none.

### Step 3 — Trace processes

The transformation path from input to output, including branches, error paths, and any
global or shared state read or written along the way.

*Error handling:* if a path is too tangled to state confidently, record it as a
low-confidence region rather than a clean description.

### Step 4 — Trace outputs

Return values, writes, emitted events, logs other systems parse, and every observable
side effect.

*Error handling:* if a side effect's consumers are unknown, list it as an unresolved
dependency — phase 04 will need it for characterization.

### Step 5 — Identify seams

A seam is a place where behavior can be observed or altered without editing the code that
runs there: interfaces, injection points, boundaries, parameters. For each, record
location, type, what it exposes, and how hard it is to exercise in a test.

*Error handling:* if the field has no usable seam, say so plainly. That is a finding for
phase 03, not a reason to create one here.

### Step 6 — Answer phase 01's open questions

Resolve what the trace resolved; carry the rest forward as still-open.

*Error handling:* never close an open question with a guess. Unresolved is a valid state.

### Step 7 — Write `seam-map.md` and HALT

Commit to the surgery branch and stop for human approval.

*Error handling:* if the map contradicts `plan.md` (an invariant is already broken, the
field is wrong), surface the contradiction at the gate rather than silently adjusting.

## 3. Constraints & Preferences

- **Zero code edits.** Reading, tracing, and writing the map only — including no
  "harmless" formatting or import changes.
- Confidence is labelled: state what was traced versus what was inferred.
- The map describes the system as it is, not as it should be.
- No solutions in this phase. Incision points are phase 03's output.

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
