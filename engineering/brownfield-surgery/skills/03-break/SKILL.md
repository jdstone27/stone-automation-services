---
name: 03-break
description: 'Phase 03 of brownfield surgery: select and rank the incision points where the change will enter the system, derived from the seam map only. No production-code edits.'
skill_name: 03-break
version: 1.0.0
last_updated: 2026-08-20
owner: eng-team
runtime: hermes
---

# Phase 03 — Break

## 1. Objective

Choose the incision points: the specific places the change will enter the system, derived
from `seam-map.md` and nothing else. Output is `incision-points.md`. Still zero
production-code edits.

## 2. Execution Steps

### Step 1 — Read `seam-map.md`

Load the seams, the low-confidence regions, and the unresolved dependencies. This map is
the only permitted source of incision points.

*Error handling:* if `seam-map.md` is missing or unapproved, stop and return to phase 02.
Do not read the codebase to fill the gap yourself.

### Step 2 — Select candidate incisions

For each seam that could carry the change, record: seam reference, why it is a candidate,
what it exposes for testing, and the blast radius if it is wrong.

*Error handling:* if a candidate has no seam reference in the map, discard it and note
that phase 02 may need another pass.

### Step 3 — Score and rank

Score each candidate on testability, blast radius, reversibility, and distance from the
invariants in `plan.md`. Prefer the smallest incision that can carry the change.

*Error handling:* if the top two candidates score equally, present both at the gate with
the tradeoff stated. Do not break the tie silently.

### Step 4 — Name the incisions that will NOT be made

Record the seams deliberately left alone and why. This bounds the change for phases 05
and 06.

*Error handling:* if a rejected seam is rejected only because it is hard, say that
plainly rather than dressing it as a design decision.

### Step 5 — State what phase 04 must characterize

For each selected incision, list the behaviors that must be pinned by characterization
tests before any code is touched.

*Error handling:* if a behavior at an incision point cannot be observed from any seam,
flag it — phase 04's gate cannot pass on an unobservable behavior.

### Step 6 — Write `incision-points.md` and HALT

Commit to the surgery branch and stop for human approval.

*Error handling:* do not begin writing tests. Phase 04 owns that, after this gate.

## 3. Constraints & Preferences

- Incision points come from `seam-map.md` only. No fresh code-reading, no intuition, no
  "while I was in there".
- Every incision carries a seam reference; an unreferenced incision is invalid.
- Smallest viable incision wins over the most elegant one.
- No production-code edits in this phase.
- Ties and doubts go to the human gate, not to a coin flip.

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
