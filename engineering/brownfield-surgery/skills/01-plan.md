---
skill_name: 01-plan
version: 1.0.0
last_updated: 2026-08-20
owner: eng-team
runtime: hermes
---

# Phase 01 — Plan

## 1. Objective

Define the surgical target before anyone touches the system: what changes, what must
**not** change, and how success is measured. Output is `plan.md` on the surgery branch.
This phase halts for human approval.

## 2. Execution Steps

### Step 1 — State the surgical target

One paragraph: the behavior to change, in terms of observable system behavior rather than
files or functions.

*Error handling:* if the request is stated as a solution ("refactor X"), ask what behavior
must change. A plan written against a solution cannot be verified.

### Step 2 — Define the surgical field

List the modules, files, and boundaries that may be touched. Everything else is out of
bounds for the whole workflow.

*Error handling:* if the field cannot be bounded without reading code, note the open
question and leave the boundary explicitly provisional — phase 02 will close it. Do not
default to "wherever needed".

### Step 3 — State what must NOT change

Enumerate the invariants: public APIs, data formats, side effects, performance envelopes,
downstream consumers, and any behavior other systems depend on — including bug-compatible
behavior that callers may rely on.

*Error handling:* if an invariant's current behavior is unknown, list it as an open
question for phase 02 rather than asserting it.

### Step 4 — Write success criteria

Each criterion must be checkable by a person reading the phase 07 PR: a test that passes,
a metric that moves, an output that matches.

*Error handling:* if a criterion cannot be checked from the PR, rewrite it until it can,
or drop it and say why.

### Step 5 — List known risks and the rollback path

Name what could go wrong and how the change is reverted.

*Error handling:* if there is no clean rollback, say so explicitly — that is a fact the
approver needs before the gate.

### Step 6 — Write `plan.md` and HALT

Commit `plan.md` to `surgery/<date>` and stop for human approval.

*Error handling:* do not proceed to phase 02 without explicit approval. If the approver
amends the plan, update `plan.md` and re-present it.

## 3. Constraints & Preferences

- Zero code edits in this phase.
- "What must NOT change" is mandatory and never empty.
- Success criteria are observable, not aspirational.
- Unknowns are recorded as open questions, never resolved by assumption.
- HALT is unconditional: this phase ends at a human gate.

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
