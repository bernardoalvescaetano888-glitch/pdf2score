"""Ponto de entrada do Pdf2Score.

Uso:
    python main.py
"""

from __future__ import annotations

import tkinter as tk

from ui.app import App


def main() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
