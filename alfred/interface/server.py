#!/usr/bin/env python3
"""
Alfred onboarding interface. Three-question flow on localhost:4242.
Questions: environment (home/work), pain point, name.
Flow: collect answers → call local Ollama to select automation → initialize vault + config.
"""

import os
import sys
import json
import subprocess
import requests
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from alfred_conf import AlfredConfig

app = Flask(__name__, template_folder='.', static_folder='.')
app.config['JSON_SORT_KEYS'] = False

# Configuration
ALFRED_HOME = Path.home() / 'Alfred'
CONFIG_PATH = ALFRED_HOME / 'config' / 'alfred.conf'
VAULT_ROOT = ALFRED_HOME / 'vault'
OLLAMA_API = os.getenv('OLLAMA_API', 'http://localhost:11434')
MODEL = os.getenv('ALFRED_MODEL', 'smollm2:1.7b')

# Ensure directories exist
ALFRED_HOME.mkdir(parents=True, exist_ok=True)
(ALFRED_HOME / 'config').mkdir(parents=True, exist_ok=True)
(ALFRED_HOME / 'logs').mkdir(parents=True, exist_ok=True)

conf = AlfredConfig(str(CONFIG_PATH))


def log_msg(msg: str):
    """Log to alfred.log"""
    log_file = ALFRED_HOME / 'logs' / 'alfred.log'
    timestamp = datetime.now().isoformat()
    with open(log_file, 'a') as f:
        f.write(f"[{timestamp}] {msg}\n")


def call_ollama_for_automation(pain_point: str) -> dict:
    """
    Call local Ollama to determine which automation to recommend.
    Returns: {automation_type, automation_description, first_action}
    """
    prompt = f"""The user has described their primary daily frustration as: {pain_point}

Identify the single most automatable element of this frustration. Return a JSON object with three fields:
- automation_type (one of: morning_briefing, file_organizer, daily_checklist, email_draft, reminder_system)
- automation_description (one plain English sentence describing what Alfred will do)
- first_action (the specific first thing Alfred will do tomorrow morning)

Return ONLY valid JSON, no other text."""

    try:
        # Try /api/generate endpoint first (older Ollama versions)
        url = f"{OLLAMA_API}/api/generate"
        payload = {
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.7,
        }

        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        response_text = result.get('response', '').strip()

        # Try to parse JSON from response
        try:
            automation = json.loads(response_text)
            required_keys = {'automation_type', 'automation_description', 'first_action'}
            if all(k in automation for k in required_keys):
                return automation
        except json.JSONDecodeError:
            pass

        # Fallback: default to morning_briefing
        log_msg(f"Ollama response was not valid JSON. Response: {response_text[:200]}")
        return {
            "automation_type": "morning_briefing",
            "automation_description": "Provide you with a brief morning summary of your day",
            "first_action": "Send you a morning briefing at 6:00 AM"
        }

    except Exception as e:
        log_msg(f"Error calling Ollama: {e}")
        return {
            "automation_type": "morning_briefing",
            "automation_description": "Provide you with a brief morning summary of your day",
            "first_action": "Send you a morning briefing at 6:00 AM"
        }


@app.route('/')
def index():
    """Start the onboarding flow."""
    return redirect(url_for('question_one'))


@app.route('/q1')
def question_one():
    """Question 1: Home or Work?"""
    return render_template('q1.html')


@app.route('/q2', methods=['POST'])
def question_two():
    """Question 2: What's your pain point?"""
    data = request.get_json()
    context_type = data.get('context_type', '').strip()

    if context_type not in ['home', 'work']:
        return jsonify({'error': 'Invalid context type'}), 400

    conf.set('context_type', context_type)
    return render_template('q2.html', context_type=context_type)


@app.route('/q3', methods=['POST'])
def question_three():
    """Question 3: What's your name?"""
    data = request.get_json()
    pain_point = data.get('pain_point', '').strip()

    if len(pain_point.split()) < 3:
        return jsonify({'error': 'Tell me a little more.'}), 400

    conf.set('primary_pain_point', pain_point)

    # Call Ollama to determine automation
    automation = call_ollama_for_automation(pain_point)
    conf.update(
        automation_type=automation.get('automation_type', 'morning_briefing'),
        automation_description=automation.get('automation_description', ''),
        first_action=automation.get('first_action', '')
    )

    return render_template('q3.html', pain_point=pain_point)


@app.route('/finalize', methods=['POST'])
def finalize():
    """Process the name and finalize onboarding."""
    data = request.get_json()
    user_name = data.get('user_name', '').strip()

    if not user_name:
        return jsonify({'error': 'Please enter your name'}), 400

    conf.set('user_name', user_name)
    conf.set('install_date', datetime.now().strftime('%Y-%m-%d'))

    # Initialize vault with user profile and first automation
    bootstrap_dir = Path(__file__).parent.parent / 'bootstrap'
    build_vault_script = bootstrap_dir / 'build_vault.sh'

    try:
        subprocess.run(
            ['bash', str(build_vault_script), '--init-user', str(VAULT_ROOT)],
            check=True,
            capture_output=True,
            text=True
        )
        log_msg(f"Vault initialized for {user_name}")
    except subprocess.CalledProcessError as e:
        log_msg(f"Error initializing vault: {e.stderr}")
        return jsonify({'error': 'Failed to initialize vault'}), 500

    # Schedule the morning briefing automation
    automation_type = conf.get('automation_type')
    try:
        schedule_automation(automation_type)
        log_msg(f"Scheduled automation: {automation_type}")
    except Exception as e:
        log_msg(f"Warning: Failed to schedule automation: {e}")

    return jsonify({
        'success': True,
        'user_name': user_name,
        'first_action': conf.get('first_action')
    })


def schedule_automation(automation_type: str):
    """Schedule the selected automation to run daily."""
    briefing_time = conf.get('briefing_time', '06:00')
    automations_dir = Path(__file__).parent.parent / 'automations'

    if automation_type == 'morning_briefing':
        script = automations_dir / 'morning_briefing.py'
        if not script.exists():
            log_msg(f"Warning: {script} not found")
            return

        # For Linux: use cron
        # For macOS/Windows: would need launchd/Task Scheduler (future)
        hour, minute = briefing_time.split(':')
        cron_schedule = f"{minute} {hour} * * *"

        # Add to crontab if not already present
        try:
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            existing_crontab = result.stdout if result.returncode == 0 else ''

            if str(script) not in existing_crontab:
                new_crontab = existing_crontab + f"{cron_schedule} {sys.executable} {script}\n"
                subprocess.run(['crontab'], input=new_crontab, text=True, check=True)
                log_msg(f"Added morning_briefing to crontab: {cron_schedule}")
        except Exception as e:
            log_msg(f"Warning: Could not add to crontab: {e}")


@app.route('/completion')
def completion():
    """Completion screen."""
    user_name = conf.get('user_name')
    first_action = conf.get('first_action')
    return render_template('completion.html', user_name=user_name, first_action=first_action)


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    log_msg(f"Server error: {e}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    log_msg("Alfred onboarding interface starting on localhost:4242")
    app.run(host='localhost', port=4242, debug=False)
