# Alfred — Private, Local AI Assistant

Alfred is a personal AI assistant that lives entirely on your machine. No cloud, no telemetry, no accounts. Just a Raspberry Pi or mini PC that boots, discovers your computer, installs itself, and starts automating your daily work.

## What Alfred Does

**In the first 5 minutes:**
1. Plug in the device
2. Answer three questions: where you work, what wastes your time, your name
3. Alfred learns your automation preferences

**Every morning after:**
- Alfred generates a personalized briefing based on your notes, tasks, and local weather
- Optional: automatically organize files, maintain checklists, or draft emails
- All data stays local; all processing happens on your machine

## Directory Structure

```
alfred/
├── bootstrap/              # Installation and setup scripts
│   ├── install.sh         # Main Linux installer
│   ├── build_vault.sh     # Creates Obsidian vault structure
│   └── lib/
│       └── conf.sh        # Bash config helper
├── interface/              # Web onboarding interface
│   ├── server.py          # Flask application (localhost:4242)
│   ├── alfred_conf.py     # Python config helper
│   ├── q1.html, q2.html, q3.html, completion.html
│   └── style.css
├── automations/            # Automation templates
│   └── morning_briefing.py # Morning briefing generator
├── vault/                  # Obsidian vault structure
│   ├── raw/               # Append-only source files
│   ├── wiki/              # LLM-maintained knowledge base
│   ├── _templates/        # Note templates
│   ├── ALFRED.md          # Operating schema
│   └── index.md           # Master index
├── curriculum/            # Five-lesson onboarding curriculum
├── config/                # Configuration files
├── logs/                  # Operational logs
└── README.md
```

## Installation

### Quick Start (Linux)

```bash
cd alfred/bootstrap
./install.sh
```

This will:
1. Install Ollama (local AI engine)
2. Download SmolLM2 1.7B model
3. Install Obsidian (vault editor)
4. Create vault structure
5. Launch the onboarding interface at `http://localhost:4242`

### Manual Setup

If you prefer step-by-step:

```bash
# 1. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull smollm2:1.7b

# 2. Install Obsidian
# Download from https://obsidian.md

# 3. Create directories
mkdir -p ~/Alfred/{vault,config,logs,automations,briefings}

# 4. Install Python dependencies
pip3 install flask requests

# 5. Initialize vault
./bootstrap/build_vault.sh ~/Alfred/vault

# 6. Start the interface
cd interface
python3 server.py
```

Then open `http://localhost:4242` in your browser.

## Configuration

All settings are stored in `~/Alfred/config/alfred.conf`:

```
user_name="Your Name"
context_type="home"              # 'home' or 'work'
automation_type="morning_briefing"
briefing_time="06:00"            # 24-hour format
watch_folder="~/Documents/Alfred/notes"
output_method="file"             # 'file', 'notification', or 'obsidian'
model_name="smollm2:1.7b"
```

## Using Alfred

### Onboarding (First Time)
1. Start the installer: `./bootstrap/install.sh`
2. Answer three questions
3. Alfred initializes your vault and schedules your first automation

### Daily Use
- **Morning briefing runs automatically** at the configured time (default 6:00 AM)
- **Add notes** to `~/Documents/Alfred/notes/` and Alfred learns from them
- **Manage tasks** in `~/Documents/Alfred/notes/tasks.txt`
- **View results** in `~/Alfred/briefings/` or Obsidian vault

### The Vault
Your personal knowledge base is stored in Obsidian. Alfred maintains it automatically:
- `raw/` — your source material (append-only)
- `wiki/` — organized, linked articles (maintained by Alfred)
- `ALFRED.md` — Alfred's operating schema

Open the vault in Obsidian: File → Open Vault → `~/Alfred/vault`

## Logging

All operations are logged to `~/Alfred/logs/alfred.log`:

```
[2025-08-09T06:00:15.234567] [INFO] Morning briefing automation started
[2025-08-09T06:00:16.123456] [INFO] Briefing written to /home/user/Alfred/briefings/briefing_2025-08-09.txt
[2025-08-09T06:00:17.987654] [INFO] Morning briefing completed successfully
```

## Troubleshooting

### Ollama not running
```bash
ollama serve
```

### Flask interface won't start
```bash
pip3 install flask requests
python3 ~/Alfred/interface/server.py
```

### Morning briefing not running
Check crontab:
```bash
crontab -l
```

Should see something like:
```
00 06 * * * /usr/bin/python3 /home/user/Alfred/automations/morning_briefing.py
```

### Full logs
```bash
cat ~/Alfred/logs/alfred.log
```

## Privacy & Data

- **All inference local**: Models run on your machine, not in the cloud
- **No telemetry**: Alfred never phones home
- **No accounts**: No registration, no passwords, no "save to cloud"
- **Your data stays yours**: Everything in `~/Alfred/` is yours to keep or delete

## Architecture Notes

**Why Ollama?** Lightweight, local-first inference engine with support for many models.

**Why SmolLM2 1.7B?** Runs in ~1GB RAM with acceptable speed (~3-5 tokens/sec on consumer CPU). Smaller models are faster but less capable.

**Why Obsidian?** Beautiful, open-source vault editor. Works offline. Syncs via your own storage (iCloud, Dropbox, etc.) if you choose.

**Why separate interface from vault?** The three-question onboarding only runs once. The vault grows with every interaction. Keeping them separate means you can change/update vault structure without breaking onboarding.

## Model Selection

The installer defaults to **SmolLM2 1.7B**, which works well on most hardware:

| Hardware | Recommended Model | Speed |
|----------|-------------------|-------|
| CPU-only (8GB+ RAM) | SmolLM2 1.7B | 3-5 tok/sec |
| Laptop GPU (NVIDIA) | Phi-4 Mini 3.8B | 10-15 tok/sec |
| Mac Apple Silicon | Gemma 3 4B | 20+ tok/sec |

To switch models, edit `~/Alfred/config/alfred.conf`:
```
model_name="phi:3.8b"
```

Then restart Ollama and re-pull:
```bash
ollama pull phi:3.8b
```

## License

MIT. Use, modify, share freely.

---

**Made with ⚙️ for people who value privacy and autonomy.**
