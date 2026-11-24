"""Temas visuais da interface (ttk)."""

from __future__ import annotations

from tkinter import ttk

THEMES: dict[str, dict[str, str]] = {
    "Escuro": {
        "bg": "#1e1e26",
        "panel": "#282833",
        "fg": "#e5e7eb",
        "muted": "#9ca3af",
        "accent": "#60a5fa",
        "accent_fg": "#0b1020",
        "button_bg": "#343442",
        "button_fg": "#e5e7eb",
        "border": "#454552",
        "entry_bg": "#20202a",
        "entry_fg": "#f3f4f6",
        "text_bg": "#20202a",
        "text_fg": "#d1d5db",
        "sel_bg": "#3b82f6",
        "sel_fg": "#ffffff",
        "tree_bg": "#23232d",
        "tree_fg": "#e5e7eb",
        "ok": "#4ade80",
        "erro": "#f87171",
    },
    "Claro": {
        "bg": "#f2f4f7",
        "panel": "#ffffff",
        "fg": "#1f2937",
        "muted": "#6b7280",
        "accent": "#2563eb",
        "accent_fg": "#ffffff",
        "button_bg": "#e5e7eb",
        "button_fg": "#111827",
        "border": "#d1d5db",
        "entry_bg": "#ffffff",
        "entry_fg": "#111827",
        "text_bg": "#ffffff",
        "text_fg": "#111827",
        "sel_bg": "#2563eb",
        "sel_fg": "#ffffff",
        "tree_bg": "#ffffff",
        "tree_fg": "#1f2937",
        "ok": "#15803d",
        "erro": "#b91c1c",
    },
    "Azul": {
        "bg": "#0f172a",
        "panel": "#1e293b",
        "fg": "#e2e8f0",
        "muted": "#94a3b8",
        "accent": "#38bdf8",
        "accent_fg": "#082f49",
        "button_bg": "#334155",
        "button_fg": "#e2e8f0",
        "border": "#475569",
        "entry_bg": "#0b1220",
        "entry_fg": "#e2e8f0",
        "text_bg": "#0b1220",
        "text_fg": "#cbd5e1",
        "sel_bg": "#0284c7",
        "sel_fg": "#ffffff",
        "tree_bg": "#131f35",
        "tree_fg": "#e2e8f0",
        "ok": "#4ade80",
        "erro": "#fb7185",
    },
    "Verde": {
        "bg": "#10231c",
        "panel": "#17332a",
        "fg": "#e8f5ee",
        "muted": "#9db9ab",
        "accent": "#34d399",
        "accent_fg": "#052e1b",
        "button_bg": "#214438",
        "button_fg": "#e8f5ee",
        "border": "#2f5c4b",
        "entry_bg": "#0c1c16",
        "entry_fg": "#e8f5ee",
        "text_bg": "#0c1c16",
        "text_fg": "#d1e8dc",
        "sel_bg": "#059669",
        "sel_fg": "#ffffff",
        "tree_bg": "#122820",
        "tree_fg": "#e8f5ee",
        "ok": "#6ee7b7",
        "erro": "#fca5a5",
    },
}


def _lighten(color: str, ratio: float = 0.16) -> str:
    value = color.lstrip("#")
    red, green, blue = (int(value[i : i + 2], 16) for i in (0, 2, 4))
    mix = lambda channel: round(channel + (255 - channel) * ratio)  # noqa: E731
    return f"#{mix(red):02x}{mix(green):02x}{mix(blue):02x}"


def apply_theme(root, style: ttk.Style, name: str) -> dict[str, str]:
    """Aplica um tema ao root e aos estilos ttk. Retorna a paleta usada."""
    palette = THEMES.get(name, THEMES["Escuro"])
    p = palette
    root.configure(bg=p["bg"])

    style.theme_use("clam")
    style.configure(".", background=p["bg"], foreground=p["fg"])

    style.configure("TFrame", background=p["bg"])
    style.configure("TLabel", background=p["bg"], foreground=p["fg"])
    style.configure("Muted.TLabel", foreground=p["muted"])
    style.configure("Title.TLabel", foreground=p["accent"], font=("Segoe UI", 17, "bold"))

    style.configure(
        "TLabelframe",
        background=p["bg"],
        foreground=p["fg"],
        bordercolor=p["border"],
    )
    style.configure(
        "TLabelframe.Label", background=p["bg"], foreground=p["muted"]
    )

    style.configure(
        "TButton",
        background=p["button_bg"],
        foreground=p["button_fg"],
        bordercolor=p["border"],
        padding=6,
    )
    style.map(
        "TButton",
        background=[("active", _lighten(p["button_bg"])), ("disabled", p["panel"])],
        foreground=[("active", p["fg"]), ("disabled", p["muted"])],
    )
    style.configure(
        "Accent.TButton",
        background=p["accent"],
        foreground=p["accent_fg"],
        bordercolor=p["accent"],
        font=("Segoe UI", 10, "bold"),
        padding=8,
    )
    style.map(
        "Accent.TButton",
        background=[("active", _lighten(p["accent"])), ("disabled", p["panel"])],
        foreground=[("active", p["accent_fg"]), ("disabled", p["muted"])],
    )

    style.configure(
        "TEntry",
        fieldbackground=p["entry_bg"],
        foreground=p["entry_fg"],
        insertcolor=p["fg"],
        bordercolor=p["border"],
    )
    style.configure(
        "TCombobox",
        fieldbackground=p["entry_bg"],
        foreground=p["entry_fg"],
        background=p["button_bg"],
        arrowcolor=p["fg"],
        bordercolor=p["border"],
    )
    style.configure(
        "TCheckbutton",
        background=p["bg"],
        foreground=p["fg"],
        indicatorcolor=p["entry_bg"],
        bordercolor=p["border"],
    )
    style.map(
        "TCheckbutton",
        background=[("active", p["bg"])],
        indicatorcolor=[("selected", p["accent"])],
    )

    style.configure("TNotebook", background=p["bg"], bordercolor=p["border"])
    style.configure(
        "TNotebook.Tab",
        background=p["panel"],
        foreground=p["muted"],
        bordercolor=p["border"],
        padding=(14, 7),
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", p["accent"])],
        foreground=[("selected", p["accent_fg"])],
    )

    style.configure(
        "Horizontal.TProgressbar",
        background=p["accent"],
        troughcolor=p["panel"],
        bordercolor=p["border"],
    )
    style.configure(
        "Treeview",
        fieldbackground=p["tree_bg"],
        background=p["tree_bg"],
        foreground=p["tree_fg"],
        bordercolor=p["border"],
        rowheight=26,
    )
    style.configure(
        "Treeview.Heading",
        background=p["panel"],
        foreground=p["fg"],
        bordercolor=p["border"],
        relief="flat",
    )
    style.map(
        "Treeview",
        background=[("selected", p["sel_bg"])],
        foreground=[("selected", p["sel_fg"])],
    )
    style.configure(
        "TScrollbar",
        background=p["panel"],
        troughcolor=p["bg"],
        arrowcolor=p["fg"],
        bordercolor=p["border"],
    )

    return palette
