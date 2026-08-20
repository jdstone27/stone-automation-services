---
skill_name: title-generation
version: 1.0.0
last_updated: 2026-08-20
owner: content-team
runtime: hermes
---

# Title Generation

## 1. Objective

Produce five title options for one video. Each option is ≤60 characters and
front-loads the primary keyword wherever that reads naturally. The human picks;
this skill never picks.

## 2. Execution Steps

### Step 1 — Extract the core promise

From the transcript, outline, or brief, state in one sentence what the viewer gets by
watching. This sentence is the source every title must trace back to.

*Error handling:* if no transcript or outline is supplied, ask for the video's promise
in one sentence. Do not generate titles from the topic alone.

### Step 2 — Generate five variants, one per style

One title in each style, no duplicates of angle:

1. how-to ("How to …")
2. curiosity (withholds the mechanism, never the subject)
3. number-led ("7 …", "3 …")
4. direct (plain statement of the result)
5. question

Front-load the primary keyword in each where the sentence still reads like English.

*Error handling:* if a style cannot be filled honestly for this video — a number-led
title with no countable list, for example — say so explicitly and substitute a second
title in the closest workable style rather than inventing structure the video lacks.

### Step 3 — Score each variant

Score every title against the checklist in Section 3, one line of reasoning per title.
Note the character count for each.

*Error handling:* if a title exceeds 60 characters, tighten it and re-score. If it
still exceeds 60 after two passes, replace it.

### Step 4 — Present

Present all five with scores, character counts, and a one-line note on the tradeoff
each makes. Ask the user to choose. Do not recommend by default; if the user asks for
a recommendation, give one and say why.

*Error handling:* never auto-select a title, and never pass a title downstream that the
user has not explicitly approved.

## 3. Constraints & Preferences

- ≤60 characters per title, counted exactly.
- No clickbait: no promise the video does not deliver.
- No ALL CAPS words. Sentence case or title case only.
- Maximum 1 emoji across a title, and only where it adds meaning.
- Keyword accuracy beats cleverness. A clear title that matches search intent wins
  over a witty one that does not.
- No brackets/parentheses stacking ("(2026) [MUST WATCH]").
- Titles must be distinct from each other in angle, not just in wording.

### Scoring Checklist

- [ ] ≤60 characters.
- [ ] Primary keyword present, front-loaded where natural.
- [ ] Promise is one the video actually keeps.
- [ ] No ALL CAPS, ≤1 emoji.
- [ ] Reads clearly out of context, with no thumbnail to lean on.

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
