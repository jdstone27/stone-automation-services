#!/usr/bin/env python3
"""
Alfred morning briefing automation.
Collects local context (date, weather, recent notes, tasks) and generates a brief.
Runs daily via cron. Outputs to file, notification, or Obsidian vault.
"""

import os
import sys
import json
import subprocess
import requests
from datetime import datetime, timedelta
from pathlib import Path
from textwrap import wrap

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'interface'))
from alfred_conf import AlfredConfig

# Configuration
ALFRED_HOME = Path.home() / 'Alfred'
CONFIG_PATH = ALFRED_HOME / 'config' / 'alfred.conf'
VAULT_ROOT = ALFRED_HOME / 'vault'
LOGS_DIR = ALFRED_HOME / 'logs'
OLLAMA_API = os.getenv('OLLAMA_API', 'http://localhost:11434')

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)

conf = AlfredConfig(str(CONFIG_PATH))


def log_msg(msg: str, level: str = 'INFO'):
    """Log to alfred.log."""
    log_file = LOGS_DIR / 'alfred.log'
    timestamp = datetime.now().isoformat()
    with open(log_file, 'a') as f:
        f.write(f"[{timestamp}] [{level}] {msg}\n")


def get_weather() -> str:
    """Fetch weather from wttr.in (no API key required)."""
    try:
        response = requests.get('https://wttr.in/?format=3', timeout=5)
        response.raise_for_status()
        return response.text.strip()
    except Exception as e:
        log_msg(f"Failed to fetch weather: {e}", 'WARN')
        return "Weather unavailable"


def get_recent_notes() -> str:
    """Get files modified in the last 24 hours from the watch folder."""
    watch_folder = Path(conf.get('watch_folder', '~/Documents/Alfred/notes')).expanduser()
    watch_folder.mkdir(parents=True, exist_ok=True)

    recent_files = []
    cutoff_time = datetime.now() - timedelta(hours=24)

    try:
        for file_path in watch_folder.glob('*'):
            if file_path.is_file():
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime > cutoff_time:
                    # Read file content (max 200 chars per file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read(200)
                            recent_files.append(f"- {file_path.name}: {content[:100]}")
                    except Exception as e:
                        log_msg(f"Failed to read {file_path.name}: {e}", 'WARN')

        return '\n'.join(recent_files) if recent_files else "No recent notes"
    except Exception as e:
        log_msg(f"Failed to scan watch folder: {e}", 'WARN')
        return "Could not access notes"


def get_tasks() -> str:
    """Get contents of tasks.txt if it exists."""
    tasks_file = (ALFRED_HOME / 'notes' / 'tasks.txt') if not conf.get('watch_folder') else \
                 Path(conf.get('watch_folder')).expanduser() / 'tasks.txt'

    if tasks_file.exists():
        try:
            with open(tasks_file, 'r') as f:
                content = f.read(500)
                return content.strip() if content.strip() else "No tasks"
        except Exception as e:
            log_msg(f"Failed to read tasks: {e}", 'WARN')
            return "Could not access tasks"

    return "No tasks file found"


def call_ollama(prompt: str) -> str:
    """Call local Ollama to generate the briefing."""
    model = conf.get('model_name', 'smollm2:1.7b')

    try:
        url = f"{OLLAMA_API}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.7,
        }

        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result.get('response', '').strip()

    except Exception as e:
        log_msg(f"Failed to call Ollama: {e}", 'ERROR')
        return "Could not generate briefing. Please check that Ollama is running on localhost:11434."


def send_desktop_notification(briefing: str):
    """Send desktop notification (Linux/macOS/Windows)."""
    user_name = conf.get('user_name', 'friend')

    try:
        if os.name == 'nt':  # Windows
            # Use PowerShell toast notification
            ps_script = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null

$APP_ID = "Alfred"
$template = @"
<toast>
    <visual>
        <binding template="ToastText02">
            <text id="1">Alfred</text>
            <text id="2">{briefing[:80]}</text>
        </binding>
    </visual>
</toast>
"@
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)
$toast = New-Object Windows.UI.Notifications.ToastNotification $xml
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($APP_ID).Show($toast)
"""
            subprocess.run(['powershell', '-Command', ps_script], check=False)

        else:  # Linux/macOS
            # Try notify-send first (Linux)
            try:
                subprocess.run(['notify-send', f'Good morning, {user_name}', briefing[:80]], check=False, timeout=5)
            except FileNotFoundError:
                # Fall back to osascript (macOS)
                apple_script = f'display notification "{briefing[:80]}" with title "Good morning, {user_name}"'
                subprocess.run(['osascript', '-e', apple_script], check=False, timeout=5)

    except Exception as e:
        log_msg(f"Failed to send notification: {e}", 'WARN')


def write_briefing_file(briefing: str):
    """Write briefing to a file."""
    briefings_dir = ALFRED_HOME / 'briefings'
    briefings_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y-%m-%d')
    output_file = briefings_dir / f'briefing_{timestamp}.txt'

    try:
        with open(output_file, 'w') as f:
            f.write(f"Alfred Morning Briefing - {timestamp}\n")
            f.write("=" * 40 + "\n\n")
            f.write(briefing)
        log_msg(f"Briefing written to {output_file}")
    except Exception as e:
        log_msg(f"Failed to write briefing file: {e}", 'ERROR')


def write_to_vault(briefing: str):
    """Write briefing to Obsidian vault as raw source."""
    raw_dir = VAULT_ROOT / 'raw'
    raw_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    raw_file = raw_dir / f'briefing_{timestamp}.md'

    try:
        with open(raw_file, 'w') as f:
            f.write(f"# Morning Briefing - {datetime.now().strftime('%Y-%m-%d')}\n\n")
            f.write(briefing)
        log_msg(f"Briefing written to vault: {raw_file}")
    except Exception as e:
        log_msg(f"Failed to write to vault: {e}", 'ERROR')


def main():
    """Main entry point for morning briefing."""
    log_msg("Morning briefing automation started")

    try:
        user_name = conf.get('user_name', 'friend')
        now = datetime.now()
        date_str = now.strftime('%A, %B %d, %Y')
        time_str = now.strftime('%I:%M %p')

        # Collect context
        weather = get_weather()
        recent_notes = get_recent_notes()
        tasks = get_tasks()

        # Build prompt for Ollama
        prompt = f"""You are Alfred. Generate a brief morning briefing for {user_name}.
It is {date_str}, {time_str}.
Weather: {weather}

Recent notes from the last 24 hours:
{recent_notes}

Today's tasks:
{tasks}

Write in second person. Be direct. No preamble. Lead with the most important thing. Maximum 150 words."""

        # Generate briefing
        briefing = call_ollama(prompt)
        log_msg(f"Briefing generated ({len(briefing)} chars)")

        # Output based on config
        output_method = conf.get('output_method', 'file')

        if output_method == 'notification':
            send_desktop_notification(briefing)
        elif output_method == 'obsidian':
            write_to_vault(briefing)
        else:  # default: file
            write_briefing_file(briefing)

        log_msg("Morning briefing completed successfully")

    except Exception as e:
        log_msg(f"Unexpected error: {e}", 'ERROR')
        sys.exit(1)


if __name__ == '__main__':
    main()
