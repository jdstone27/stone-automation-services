"""Folder-drop watcher.

Polls the inbox rather than using filesystem events: polling survives bind-mount
quirks on Docker for Mac, and a file dropped while the service was down is still
picked up on the next tick. Ordinary inotify-style watching misses both.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path

from app.config import Settings
from app.db import session_scope
from app.pipeline import ingest_path

logger = logging.getLogger(__name__)

# Why: a file copied into the inbox may still be being written. Only ingest once
# its size has held steady across two consecutive ticks.
_IGNORED_PREFIXES = (".", "~")


class InboxWatcher:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_sizes: dict[Path, int] = {}

    def start(self) -> None:
        if self._thread is not None:
            return
        self._settings.ensure_dirs()
        self._thread = threading.Thread(target=self._run, name="inbox-watcher", daemon=True)
        self._thread.start()
        logger.info("watching %s every %ss", self._settings.inbox_dir, self._settings.watch_interval_seconds)

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=10)
            self._thread = None

    def _run(self) -> None:
        while not self._stop.wait(self._settings.watch_interval_seconds):
            try:
                self.scan_once()
            except Exception:  # noqa: BLE001 - the watcher must never die
                logger.exception("inbox scan failed; continuing")

    def scan_once(self) -> int:
        """Process every settled file in the inbox. Returns how many were ingested."""
        inbox = self._settings.inbox_dir
        if not inbox.is_dir():
            return 0

        processed = 0
        seen: set[Path] = set()

        for path in sorted(inbox.iterdir()):
            if not path.is_file() or path.name.startswith(_IGNORED_PREFIXES):
                continue
            seen.add(path)

            try:
                size = path.stat().st_size
            except OSError:
                continue

            if self._last_sizes.get(path) != size:
                # Still growing (or seen for the first time) — wait a tick.
                self._last_sizes[path] = size
                continue

            self._last_sizes.pop(path, None)
            try:
                with session_scope() as session:
                    outcome = ingest_path(session, path, self._settings)
            except Exception:  # noqa: BLE001
                logger.exception("failed to ingest %s; leaving it in the inbox", path)
                continue

            if outcome is not None:
                processed += 1

        # Forget files that have left the inbox.
        for tracked in list(self._last_sizes):
            if tracked not in seen:
                self._last_sizes.pop(tracked, None)

        return processed
