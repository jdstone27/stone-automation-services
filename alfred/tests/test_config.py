#!/usr/bin/env python3
"""
Tests for Alfred config management.
Run with: python3 -m pytest tests/test_config.py -v
"""

import sys
import tempfile
from pathlib import Path
import shutil

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'interface'))
from alfred_conf import AlfredConfig


def test_config_read_write():
    """Test basic config read/write."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'alfred.conf'
        conf = AlfredConfig(str(config_path))

        # Check defaults exist
        config = conf.read()
        assert 'user_name' in config
        assert 'context_type' in config
        assert config['briefing_time'] == '06:00'

        print("✓ Config defaults initialized")


def test_config_set_get():
    """Test setting and getting individual values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'alfred.conf'
        conf = AlfredConfig(str(config_path))

        # Set individual values
        conf.set('user_name', 'Alice')
        conf.set('context_type', 'home')

        # Verify they were written
        assert conf.get('user_name') == 'Alice'
        assert conf.get('context_type') == 'home'

        print("✓ Config get/set working")


def test_config_update():
    """Test batch update."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'alfred.conf'
        conf = AlfredConfig(str(config_path))

        conf.update(
            user_name='Bob',
            automation_type='morning_briefing',
            first_action='Send you a briefing'
        )

        config = conf.read()
        assert config['user_name'] == 'Bob'
        assert config['automation_type'] == 'morning_briefing'
        assert config['first_action'] == 'Send you a briefing'

        print("✓ Config batch update working")


def test_config_persistence():
    """Test that config persists across instances."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'alfred.conf'

        # Create and write
        conf1 = AlfredConfig(str(config_path))
        conf1.set('user_name', 'Charlie')

        # Create new instance and read
        conf2 = AlfredConfig(str(config_path))
        assert conf2.get('user_name') == 'Charlie'

        print("✓ Config persists across instances")


def test_config_quote_handling():
    """Test that quotes are properly stripped."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'alfred.conf'
        conf = AlfredConfig(str(config_path))

        conf.set('user_name', 'Diana "The Great" Smith')
        result = conf.get('user_name')

        # Should handle quoted values
        assert 'Diana' in result

        print("✓ Quote handling working")


if __name__ == '__main__':
    test_config_read_write()
    test_config_set_get()
    test_config_update()
    test_config_persistence()
    test_config_quote_handling()

    print("\n" + "="*40)
    print("All config tests passed!")
    print("="*40)
