# Lesson 01: Meet Alfred

## What Just Happened

You plugged in Alfred, answered three questions, and now you have a fully functioning personal AI assistant running on your machine.

Alfred is not running in the cloud. It's not sending your data anywhere. Every conversation, every note, every briefing happens right here on your computer, using a small language model called SmolLM2 that lives in Ollama.

## What's Running on Your Machine

- **Ollama**: An AI engine that serves language models locally. Think of it as the "brain" that powers Alfred.
- **SmolLM2 1.7B**: A lightweight AI model trained to be helpful, harmless, and honest. It's small enough to run on modest hardware (1.1GB), fast enough to feel snappy (3-5 tokens per second), and capable enough to handle real work.
- **Obsidian**: A beautiful, open-source notebook that stores your knowledge base as plain-text markdown files. No vendor lock-in. No cloud sync unless you choose it.
- **Alfred (this interface)**: A Flask web app that manages your settings, runs automations, and maintains your personal vault.

## What Alfred Cannot Do

- Alfred cannot browse the internet in real-time
- Alfred cannot send emails or post to social media on your behalf
- Alfred cannot access files outside of the watch folder you configure
- Alfred cannot store data in the cloud (by design — everything is local)

## What Alfred Can Do (Right Now)

1. **Generate your morning briefing** — reads your notes, your tasks, and local weather, then gives you a personalized summary every morning
2. **Remember things you write** — stores everything you add to your notes in a searchable, organized vault
3. **Learn your preferences** — over time, Alfred learns what you care about and shapes its briefings accordingly

## Your First Action

Tomorrow morning at 6:00 AM (or whenever you set it), Alfred will generate your first morning briefing automatically. You don't have to do anything. Just wake up, and it will be waiting in your briefings folder or as a notification on your desktop.

## Let's Try It Now

To see how this works, you can manually trigger the morning briefing right now:

```bash
python3 ~/Alfred/automations/morning_briefing.py
```

Or, if you prefer to wait until tomorrow morning, just go about your day. Check back tomorrow morning and you'll see what Alfred created for you.

## Next Steps

1. **Lesson 02** — Teach Alfred about you (how the vault works)
2. **Lesson 03** — Understand your first automation (morning briefing explained)
3. **Lesson 04** — Add a second automation (file organizer or daily checklist)
4. **Lesson 05** — Growing Alfred (add models, update automations)

---

**Ready to continue?** [Go to Lesson 02](../lesson_02/lesson.md)
