"""Histórico persistente das conversões."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .paths import app_data_dir

MAX_ENTRIES = 100


class History:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (app_data_dir() / "history.json")
        self.entries: list[dict[str, Any]] = []
        self.load()

    def load(self) -> None:
        if not self.path.is_file():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                self.entries = [item for item in data if isinstance(item, dict)]
                self.entries = self.entries[:MAX_ENTRIES]
        except (OSError, json.JSONDecodeError):
            self.entries = []

    def add(self, entry: dict[str, Any]) -> None:
        self.entries.insert(0, entry)
        self.entries = self.entries[:MAX_ENTRIES]
        self.save()

    def remove(self, entry_id: str) -> None:
        self.entries = [item for item in self.entries if item.get("id") != entry_id]
        self.save()

    def clear(self) -> None:
        self.entries = []
        self.save()

    def save(self) -> None:
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(self.entries, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        tmp.replace(self.path)
