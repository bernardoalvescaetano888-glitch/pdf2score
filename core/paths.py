"""Caminhos da aplicação e detecção automática dos executáveis."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

APP_NAME = "Pdf2Score"

AUDIVERIS_ENV = "AUDIVERIS_HOME"
MUSESCORE_ENV = "MUSESCORE_PATH"

AUDIVERIS_CANDIDATES = (
    r"C:\Program Files\Audiveris\audiveris.bat",
    r"C:\Program Files (x86)\Audiveris\audiveris.bat",
    r"C:\Program Files\Audiveris\bin\audiveris.bat",
    r"C:\Audiveris\audiveris.bat",
)

MUSESCORE_CANDIDATES = (
    r"C:\Program Files\MuseScore 4\bin\mscore.exe",
    r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe",
    r"C:\Program Files\MuseScore 3\bin\mscore.exe",
    r"C:\Program Files\MuseScore Studio 4\bin\mscore.exe",
)


def app_data_dir() -> Path:
    """Pasta onde configurações e histórico são salvos."""
    base = os.environ.get("APPDATA") if os.name == "nt" else None
    path = Path(base) / APP_NAME if base else Path.home() / ".pdf2score"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _from_env(name: str) -> str:
    """Lê uma variável de ambiente aceitando arquivo ou pasta."""
    raw = os.environ.get(name, "").strip().strip('"')
    if not raw:
        return ""
    p = Path(raw)
    if p.is_dir():
        for filename in ("audiveris.bat", "audiveris", "mscore.exe", "musescore.exe"):
            child = p / filename
            if child.is_file():
                return str(child)
    if p.is_file():
        return str(p)
    return ""


def detect_executable(kind: str) -> str:
    """Tenta encontrar Audiveris ou MuseScore no sistema."""
    kind = kind.lower()
    if kind == "audiveris":
        env = _from_env(AUDIVERIS_ENV)
        candidates = AUDIVERIS_CANDIDATES
        commands = ("audiveris",)
    elif kind == "musescore":
        env = _from_env(MUSESCORE_ENV)
        candidates = MUSESCORE_CANDIDATES
        commands = ("mscore", "musescore", "musescore4")
    else:
        raise ValueError(f"Tipo desconhecido: {kind}")

    if env:
        return env
    for command in commands:
        found = shutil.which(command)
        if found:
            return found
    for candidate in candidates:
        if Path(candidate).is_file():
            return candidate
    return ""


def open_path(path: str | Path) -> None:
    """Abre um arquivo ou pasta com o aplicativo padrão do sistema."""
    value = str(path)
    if os.name == "nt":
        os.startfile(value)  # noqa: S606 - intencional: abrir com o app padrão
    elif sys.platform == "darwin":
        subprocess.Popen(["open", value])
    else:
        subprocess.Popen(["xdg-open", value])
