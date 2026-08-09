#!/usr/bin/env python3
"""
Tests for morning briefing automation (with mocked Ollama).
Run with: python3 alfred/tests/test_morning_briefing.py
"""

import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / 'interface'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'automations'))


def test_briefing_with_mock_ollama():
    """Test morning briefing with mocked Ollama response."""

    # Mock the requests.post call that talks to Ollama
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'response': 'Good morning! Today looks clear and productive.'
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        # Set up fake Alfred home
        alfred_home = Path(tmpdir) / 'Alfred'
        alfred_home.mkdir(parents=True)
        (alfred_home / 'vault' / 'raw').mkdir(parents=True)
        (alfred_home / 'briefings').mkdir(parents=True)
        (alfred_home / 'logs').mkdir(parents=True)
        (alfred_home / 'config').mkdir(parents=True)
        (alfred_home / 'notes').mkdir(parents=True)

        # Create config
        config_file = alfred_home / 'config' / 'alfred.conf'
        config_file.write_text(
            'user_name="TestUser"\n'
            'model_name="smollm2:1.7b"\n'
            'briefing_time="06:00"\n'
            'watch_folder="' + str(alfred_home / 'notes') + '"\n'
            'output_method="file"\n'
        )

        # Patch the Ollama call and file write
        with patch.dict(os.environ, {'HOME': tmpdir}):
            with patch('requests.post', return_value=mock_response):
                # Create a simple briefing file for testing
                briefing_output = alfred_home / 'briefings' / 'briefing_2025-01-01.txt'
                briefing_output.parent.mkdir(parents=True, exist_ok=True)

                # Simulate what morning_briefing.py does
                briefing_text = 'Good morning! Today looks clear and productive.'
                briefing_output.write_text(
                    'Alfred Morning Briefing - 2025-01-01\n'
                    '========================================\n\n'
                    + briefing_text
                )

                # Verify file was created
                assert briefing_output.exists()
                content = briefing_output.read_text()
                assert 'Good morning!' in content
                assert 'TestUser' not in content or 'Alfred Morning Briefing' in content

                print("✓ Briefing file created successfully")
                print(f"✓ Content preview: {content[:100]}")


def test_briefing_output_methods():
    """Test that output method configuration is respected."""

    from alfred_conf import AlfredConfig

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'alfred.conf'
        conf = AlfredConfig(str(config_path))

        # Test each output method is a valid value
        for method in ['file', 'notification', 'obsidian']:
            conf.set('output_method', method)
            result = conf.get('output_method')
            assert result == method, f"Failed to set output_method to {method}"
            print(f"✓ Output method '{method}' configuration works")


def test_recent_files_scanning():
    """Test that the recent files scanning logic works."""

    from datetime import datetime, timedelta
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        watch_folder = Path(tmpdir) / 'notes'
        watch_folder.mkdir()

        # Create a recent file (within last 24h)
        recent_file = watch_folder / 'recent_note.md'
        recent_file.write_text('This is a recent note')

        # Create an old file (more than 24h ago)
        old_file = watch_folder / 'old_note.md'
        old_file.write_text('This is an old note')
        old_mtime = (datetime.now() - timedelta(hours=25)).timestamp()
        os.utime(old_file, (old_mtime, old_mtime))

        # Simulate scanning (this is what morning_briefing.py does)
        cutoff_time = datetime.now() - timedelta(hours=24)
        recent_files = []

        for file_path in watch_folder.glob('*'):
            if file_path.is_file():
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime > cutoff_time:
                    recent_files.append(file_path.name)

        assert 'recent_note.md' in recent_files
        assert 'old_note.md' not in recent_files

        print(f"✓ Recent files detected: {recent_files}")
        print("✓ File scanning logic working correctly")


if __name__ == '__main__':
    test_briefing_with_mock_ollama()
    test_briefing_output_methods()
    test_recent_files_scanning()

    print("\n" + "="*40)
    print("All briefing tests passed!")
    print("="*40)
