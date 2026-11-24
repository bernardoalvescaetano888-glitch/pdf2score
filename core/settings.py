"""Persistência das configurações do aplicativo."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .installer import installed_audiveris_path
from .paths import app_data_dir, detect_executable

DEFAULTS: dict[str, Any] = {
    "theme": "Escuro",
    "audiveris": "",
    "musescore": "",
    "output_dir": "",
    "keep_mxl": True,
    "generate_mp3": True,
    "open_in_musescore": False,
    "audiveris_timeout": 900,
    "musescore_timeout": 300,
}


class Settings:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (app_data_dir() / "settings.json")
        self.data: dict[str, Any] = dict(DEFAULTS)
        self.load()

    def load(self) -> None:
        if self.path.is_file():
            try:
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    for key in DEFAULTS:
                        if key in loaded:
                            self.data[key] = loaded[key]
            except (OSError, json.JSONDecodeError):
                pass

        # Preenche os executáveis ausentes com a detecção automática.
        if not self.data.get("audiveris"):
            self.data["audiveris"] = detect_executable("audiveris") or (
                str(installed_audiveris_path() or "")
            )
        if not self.data.get("musescore"):
            self.data["musescore"] = detect_executable("musescore")

    def save(self) -> None:
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        tmp.replace(self.path)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, DEFAULTS.get(key, default))

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def update(self, values: dict[str, Any]) -> None:
        self.data.update(values)


def positive_int(value: object, fallback: int) -> int:
    """Converte um valor de spinbox em inteiro positivo."""
    try:
        number = int(str(value).strip())
    except (ValueError, TypeError):
        return fallback
    return number if number > 0 else fallback
