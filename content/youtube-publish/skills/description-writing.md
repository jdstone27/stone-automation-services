---
skill_name: description-writing
version: 1.0.0
last_updated: 2026-08-20
owner: content-team
runtime: hermes
---

# Description Writing

## 1. Objective

Produce a publish-ready YouTube description that:

- leads with a hook inside the first 150 characters (the only part shown before "…more"),
- is discoverable, carrying the primary keyword in natural language,
- contains exactly one call to action,
- carries chapter timestamps when a transcript exists,
- carries every disclosure the video legally requires.

Output is a single block of plain text, ready to paste into the YouTube description
field without edits.

## 2. Execution Steps

### Step 1 — Gather inputs

Collect: video title (approved), transcript or detailed outline, primary keyword,
2–4 secondary keywords, the single CTA, any links to include, sponsor/affiliate
information, target audience.

*Error handling:* if any input is missing, ask the user for it. Never guess a keyword,
a link, or sponsor terms. If the user says an input does not apply, record that and
continue.

### Step 2 — Extract the hook

Read the transcript and identify the single strongest promise, tension, or result the
video delivers. State it in one sentence in the viewer's language, not the creator's.

*Error handling:* if the transcript is absent or too thin to locate a promise, ask the
user for the video's one-sentence promise before continuing. Do not invent one.

### Step 3 — Write the first 150 characters

The first 150 characters must stand alone as a complete thought: hook + primary
keyword. Count the characters. If over 150, cut adjectives first, then qualifiers,
then restructure. Do not cut the keyword.

*Error handling:* if the line cannot reach ≤150 characters with the keyword intact
after three tightening passes, present the two closest options to the user and ask
which promise to drop.

### Step 4 — Write the body

Three moves, in order:

1. expand the hook into 2–4 sentences of what the video actually covers;
2. state the concrete takeaway the viewer leaves with;
3. give the single CTA, phrased as one action.

*Error handling:* if more than one CTA is supplied, ask the user to pick one. Do not
stack CTAs.

### Step 5 — Timestamps

Build a `Chapters:` block. One chapter per line, format `00:00 Title`, first entry
always `00:00`, times strictly ascending, titles ≤5 words drawn from what the
transcript actually says.

*Error handling:* if no transcript is available, insert the literal line
`<!-- TIMESTAMPS NEEDED -->` where the chapter block belongs and tell the user
timestamps are outstanding. Never fabricate a timestamp.

### Step 6 — Links and disclosures

Add supplied links, each on its own line, full `https://` form. Add FTC disclosures
whenever sponsor or affiliate information was supplied: a plain-language paid-promotion
line for sponsored content, and an affiliate-commission line above affiliate links.

*Error handling:* if sponsor information is ambiguous about whether the placement is
paid, ask. Do not decide on the user's behalf whether a disclosure is required.

### Step 7 — Validate

Walk the Validation Checklist in Section 3 item by item. Fix each failure and re-run
the whole checklist.

*Error handling:* if the same checklist rule fails twice, stop. Report which rule is
failing and ask the user how to resolve it rather than attempting a third rewrite.

## 3. Constraints & Preferences

- Plain text only. YouTube does not render Markdown — no `**bold**`, no `#` headings,
  no `-` bullet syntax carried over from drafting.
- Blank line between paragraphs; YouTube collapses single newlines unpredictably.
- Full `https://` URLs, each on its own line. No shorteners, no bare domains.
- Target ≤1,000 characters. Hard cap 5,000 characters (YouTube's limit).
- Maximum 2 emojis in the whole description, never inside the first 150 characters.
- Second person ("you"), present tense, active voice.
- No clickbait: every claim in the description must be one the video delivers.
- Keyword placement must read naturally. Never stuff, never list keywords as tags.

### Validation Checklist

- [ ] Primary keyword appears in the first sentence.
- [ ] First 150 characters read as a standalone, complete hook.
- [ ] Exactly one CTA.
- [ ] Every link came from user input; none invented.
- [ ] Disclosures present whenever sponsor or affiliate information was supplied.
- [ ] Timestamps present and ascending, or `<!-- TIMESTAMPS NEEDED -->` inserted.
- [ ] Character count within target/cap; emoji count within limit.
- [ ] Plain text, no Markdown syntax remaining.

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
