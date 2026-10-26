# -*- coding: utf-8 -*-
""" Node ID -> name store, learned from NODEINFO packets and persisted to JSON """

import json
import logging
import os
import threading
from typing import Dict, Optional


def normalize_node_id(node: object) -> Optional[str]:
    """Return node id as '!xxxxxxxx' from int, '!hex' or 'hex'; None if invalid"""
    if node is None:
        return None
    if isinstance(node, int):
        return f"!{node & 0xFFFFFFFF:08x}"
    text = str(node).strip().lower().lstrip('!')
    try:
        return f"!{int(text, 16):08x}"
    except ValueError:
        return None


class NodeNameStore:
    """
    Thread-safe mapping of node id ('!91d4a7ac') -> {'long': ..., 'short': ...}
    persisted to a JSON file. Can be seeded from an env var (NODE_NAMES) in the
    form '!91d4a7ac=Renato,!3fd72c6c=elen', useful on hosts with ephemeral
    filesystems (e.g. Render free tier). Learned names override the seed.
    """

    def __init__(self, path: str, logger: logging.Logger, seed: str = ''):
        self.path = path
        self.logger = logger
        self.lock = threading.Lock()
        self.names: Dict[str, Dict[str, str]] = {}
        for part in (seed or '').split(','):
            if '=' not in part:
                continue
            node, name = part.split('=', 1)
            node_id = normalize_node_id(node)
            if node_id and name.strip():
                self.names[node_id] = {'long': name.strip(), 'short': ''}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
            for node, entry in data.items():
                node_id = normalize_node_id(node)
                if node_id and isinstance(entry, dict) and entry.get('long'):
                    self.names[node_id] = {'long': str(entry['long']), 'short': str(entry.get('short', ''))}
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            self.logger.error("Failed to load node names: %s", exc)

    def _save(self) -> None:
        try:
            with open(self.path, 'w', encoding='utf-8') as fh:
                json.dump(self.names, fh, ensure_ascii=False, indent=1, sort_keys=True)
        except OSError as exc:
            self.logger.error("Failed to save node names: %s", exc)

    def learn(self, node: object, long_name: Optional[str], short_name: Optional[str] = '') -> bool:
        """Store/refresh name for node; returns True if something changed"""
        node_id = normalize_node_id(node)
        long_name = (long_name or '').strip()
        if not node_id or not long_name:
            return False
        entry = {'long': long_name, 'short': (short_name or '').strip()}
        with self.lock:
            if self.names.get(node_id) == entry:
                return False
            self.names[node_id] = entry
            self._save()
        self.logger.info("Learned node name %s = %s (%s)", node_id, entry['long'], entry['short'])
        return True

    def get(self, node: object) -> Optional[str]:
        """Long name for node or None"""
        node_id = normalize_node_id(node)
        if not node_id:
            return None
        with self.lock:
            entry = self.names.get(node_id)
        return entry['long'] if entry else None

    def as_seed(self) -> str:
        """Serialize as NODE_NAMES env var value"""
        with self.lock:
            return ','.join(f"{k}={v['long']}" for k, v in sorted(self.names.items()))
