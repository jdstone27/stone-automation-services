---
skill_name: youtube-orchestrator
version: 1.0.0
last_updated: 2026-08-20
owner: content-team
runtime: hermes
---

# YouTube Orchestrator

## 1. Objective

Run the YouTube publication pipeline end to end: titles, thumbnail brief, description.
This skill sequences sub-skills and carries approved artifacts forward. It does not
write titles, briefs, or descriptions itself — that logic lives in the sub-skill SOPs
and is never duplicated here.

## 2. Execution Steps

### Step 1 — Collect the pipeline inputs

Gather transcript or outline, primary keyword, secondary keywords, the CTA, links,
sponsor/affiliate information, and target audience. Hold them as the shared input set
for every sub-skill.

*Error handling:* if the transcript is missing, say which downstream steps degrade
(timestamps become `<!-- TIMESTAMPS NEEDED -->`) and ask whether to proceed.

### Step 2 — Invoke `title-generation`

Run the skill. Present its five scored options to the human.

*Error handling:* if `title-generation` fails, halt the pipeline. Report the failure and
flag `title-generation`'s SOP as the location of the gap — never this SOP, and never
work around it by writing titles here.

### Step 3 — Human picks the title

Wait for an explicit choice. Record the exact chosen string.

*Error handling:* if the human rejects all five, re-invoke `title-generation` with their
feedback. Do not proceed on an unapproved title, and do not pick one.

### Step 4 — Invoke `thumbnail-brief`

Pass the chosen title verbatim. Collect the brief.

*Error handling:* if `thumbnail-brief` fails or returns open questions, halt, surface the
questions, and flag `thumbnail-brief`'s SOP if the failure was an SOP gap.

### Step 5 — Invoke `description-writing`

Pass the chosen title and the transcript, plus keywords, CTA, links, and sponsor
information. Collect the description.

*Error handling:* if `description-writing` fails, halt and flag `description-writing`'s
SOP. Do not hand-patch its output here.

### Step 6 — Assemble the review package

Present one package containing: the chosen title, the thumbnail brief, the description,
and a list of anything outstanding (missing timestamps, open designer questions, links
awaiting the user).

*Error handling:* if any artifact is missing, say so in the package rather than
presenting a partial package as complete.

### Step 7 — Await approval

Stop. The pipeline ends at human approval of the package; publication is never
performed by this skill.

*Error handling:* if the human requests changes, route each change to the owning
sub-skill and re-run only that sub-skill and anything downstream of it.

## 3. Constraints & Preferences

- Strict order: `title-generation` → human pick → `thumbnail-brief` → `description-writing`
  → review package → approval.
- Any sub-skill failure halts the whole pipeline. No partial delivery, no substitution.
- A halt flags the failing sub-skill's SOP, not this one — unless the failure was in
  sequencing or artifact hand-off, which is this SOP's responsibility.
- Downstream skills read the approved artifact. They never re-derive the title.
- This SOP contains no content-writing rules. If a content rule is needed, it belongs in
  the sub-skill.
- Never publish, schedule, or upload. Human approval is the terminal state.

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
