"""Gera o executável único Pdf2Score.exe na pasta dist/.

Uso:
    python build_exe.py
"""

from __future__ import annotations

import PyInstaller.__main__

OPTIONS = [
    "main.py",
    "--name=Pdf2Score",
    "--onefile",
    "--windowed",
    "--clean",
    "--noconfirm",
]


if __name__ == "__main__":
    PyInstaller.__main__.run(OPTIONS)
