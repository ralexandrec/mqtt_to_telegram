# -*- coding: utf-8 -*-
""" Telegram subscribers store (users that interacted with the bot) """

import json
import logging
import os
import threading
from typing import List, Set


class SubscriberStore:
    """
    Thread-safe set of Telegram chat IDs persisted to a JSON file.
    Can be seeded from a comma-separated env var (TELEGRAM_SUBSCRIBERS),
    useful on hosts with ephemeral filesystems (e.g. Render free tier).
    """

    def __init__(self, path: str, logger: logging.Logger, seed: str = ''):
        self.path = path
        self.logger = logger
        self.lock = threading.Lock()
        self.ids: Set[int] = set()
        self._load()
        for part in (seed or '').split(','):
            part = part.strip()
            if part.lstrip('-').isdigit():
                self.ids.add(int(part))

    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, 'r', encoding='utf-8') as fh:
                self.ids = {int(x) for x in json.load(fh)}
        except (OSError, ValueError, TypeError) as exc:
            self.logger.error("Failed to load subscribers: %s", exc)

    def _save(self) -> None:
        try:
            with open(self.path, 'w', encoding='utf-8') as fh:
                json.dump(sorted(self.ids), fh)
        except OSError as exc:
            self.logger.error("Failed to save subscribers: %s", exc)

    def add(self, chat_id: int) -> bool:
        """Add chat id; returns True if it was new"""
        with self.lock:
            if chat_id in self.ids:
                return False
            self.ids.add(chat_id)
            self._save()
        self.logger.info("New subscriber %s (all: %s)", chat_id,
                         ','.join(str(x) for x in sorted(self.ids)))
        return True

    def remove(self, chat_id: int) -> None:
        """Remove chat id (e.g. user blocked the bot)"""
        with self.lock:
            if chat_id in self.ids:
                self.ids.discard(chat_id)
                self._save()
                self.logger.info("Removed subscriber %s", chat_id)

    def all(self) -> List[int]:
        """List of chat ids"""
        with self.lock:
            return sorted(self.ids)
