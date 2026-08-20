---
skill_name: thumbnail-brief
version: 1.0.0
last_updated: 2026-08-20
owner: content-team
runtime: hermes
---

# Thumbnail Brief

## 1. Objective

Produce a designer-ready brief for one thumbnail. This skill outputs a written brief,
never an image and never a generated mockup. The brief must be executable by a designer
who has not seen the video and cannot ask follow-up questions.

## 2. Execution Steps

### Step 1 — Read the approved title

Take the title the human approved in `title-generation`. The thumbnail must complement
that exact title, not an earlier variant.

*Error handling:* if no approved title is supplied, stop and ask for it. Do not brief
against a candidate title.

### Step 2 — Define the single focal emotion

Name one emotion the thumbnail must transmit at a glance (e.g. relief, disbelief,
anticipation). One only.

*Error handling:* if the video supports two competing emotions, present both to the user
and ask which one leads. Do not brief a thumbnail that carries two.

### Step 3 — Specify the frame

Write each of these as a separate labelled line:

- **Subject:** who or what occupies the frame, and roughly how much of it.
- **Expression / state:** the face or object state that carries the focal emotion.
- **Composition:** subject placement, eyeline, depth, safe margins, where the duration
  stamp will sit (bottom-right).
- **Text overlay:** 3 words maximum, or none. Must not repeat words already in the title.
- **Color & contrast:** dominant color, the contrasting accent, and a note on legibility
  at 168×94 px against both light and dark YouTube themes.

*Error handling:* if the required text overlay can only be written using title words,
drop the overlay and say why. A thumbnail with no text beats a thumbnail that repeats
the title.

### Step 4 — List three reference styles

Name three existing, describable reference styles or channels and state in one line what
to take from each. References are directional, not to be copied.

*Error handling:* if fewer than three genuinely relevant references exist, give the ones
that do and describe the missing one in words rather than padding with a weak match.

### Step 5 — Self-check for executability

Reread the brief as the designer: is any decision left undefined? Fill every gap before
handing off.

*Error handling:* if a gap cannot be filled without information only the user has, list
the open questions at the top of the brief instead of burying them.

## 3. Constraints & Preferences

- Deliverable is a brief. Never produce or attempt to produce the image itself.
- Text overlay: 3 words maximum, and no word already used in the approved title.
- The brief must be executable without follow-up questions; unresolved items are listed
  explicitly, not implied.
- Legibility at 168×94 px is a hard requirement, not a preference.
- 16:9, 1280×720 minimum, safe margins clear of the duration stamp.
- No promise in the thumbnail that the title and video do not both keep.
- Describe, do not decorate: every line is a decision a designer can act on.

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
