"""Interface gráfica principal do Pdf2Score."""

from __future__ import annotations

import os
import queue
import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import tkinter as tk
import tkinter.scrolledtext as scrolledtext

from core.converters import (
    ConversionError,
    musicxml_to_mp3,
    open_in_musescore,
    pdf_to_musicxml,
)
from core.history import History
from core.installer import InstallError, download_and_install_audiveris, java_available
from core.paths import app_data_dir, detect_executable, open_path
from core.settings import Settings, positive_int
from ui.themes import THEMES, apply_theme


def _fmt_date(value: str | None) -> str:
    if not value:
        return "-"
    try:
        return datetime.fromisoformat(value).strftime("%d/%m/%Y %H:%M")
    except (ValueError, TypeError):
        return value


def _filename(value: str | None) -> str:
    if not value:
        return "-"
    return Path(value).name


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.settings = Settings()
        self.history = History()
        self.events: queue.Queue = queue.Queue()
        self.running = False

        self.style = ttk.Style()
        self.theme_var = tk.StringVar(value=self.settings.get("theme"))
        self.pdf_var = tk.StringVar()
        self.out_var = tk.StringVar(value=self.settings.get("output_dir") or "")
        self.audiveris_var = tk.StringVar(value=self.settings.get("audiveris") or "")
        self.musescore_var = tk.StringVar(value=self.settings.get("musescore") or "")
        self.keep_var = tk.BooleanVar(value=bool(self.settings.get("keep_mxl")))
        self.mp3_var = tk.BooleanVar(value=bool(self.settings.get("generate_mp3")))
        self.open_var = tk.BooleanVar(value=bool(self.settings.get("open_in_musescore")))
        self.timeout_a_var = tk.StringVar(value=str(self.settings.get("audiveris_timeout")))
        self.timeout_m_var = tk.StringVar(value=str(self.settings.get("musescore_timeout")))
        self.status_var = tk.StringVar(value="Pronto para converter.")

        self.root.title("Pdf2Score — partituras para MuseScore e MP3")
        self.root.geometry("1000x700")
        self.root.minsize(880, 620)

        self._build()
        self.apply_theme()
        self.theme_var.trace_add("write", self._on_theme_change)
        self._refresh_history()
        self.root.after(120, self._pump)

    # ------------------------------------------------------------------ build
    def _build(self) -> None:
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        header = ttk.Frame(main)
        header.pack(fill="x", pady=(0, 10))
        ttk.Label(header, text="PDF  →  MusicXML  →  MP3", style="Title.TLabel").pack(side="left")
        ttk.Label(header, text="Audiveris + MuseScore", style="Muted.TLabel").pack(
            side="left", padx=14
        )

        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill="both", expand=True)

        self.tab_convert = ttk.Frame(self.notebook, padding=14)
        self.tab_history = ttk.Frame(self.notebook, padding=14)
        self.tab_settings = ttk.Frame(self.notebook, padding=14)
        self.notebook.add(self.tab_convert, text=" Converter ")
        self.notebook.add(self.tab_history, text=" Histórico ")
        self.notebook.add(self.tab_settings, text=" Configurações ")

        self._build_convert_tab(self.tab_convert)
        self._build_history_tab(self.tab_history)
        self._build_settings_tab(self.tab_settings)

    def _build_convert_tab(self, parent: ttk.Frame) -> None:
        file_box = ttk.LabelFrame(parent, text=" Arquivos ", padding=10)
        file_box.pack(fill="x")

        ttk.Label(file_box, text="PDF:").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(file_box, textvariable=self.pdf_var, width=68).grid(
            row=0, column=1, sticky="ew", padx=8
        )
        ttk.Button(file_box, text="Escolher...", command=self._choose_pdf).grid(
            row=0, column=2
        )

        ttk.Label(file_box, text="Salvar em:").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(file_box, textvariable=self.out_var, width=68).grid(
            row=1, column=1, sticky="ew", padx=8
        )
        ttk.Button(file_box, text="Pasta...", command=self._choose_output).grid(
            row=1, column=2
        )
        ttk.Button(file_box, text="Abrir", command=self._open_output).grid(
            row=1, column=3, padx=(6, 0)
        )
        file_box.columnconfigure(1, weight=1)

        options = ttk.LabelFrame(parent, text=" Opções de saída ", padding=10)
        options.pack(fill="x", pady=(10, 0))
        ttk.Checkbutton(
            options, text="Manter MusicXML (.mxl)", variable=self.keep_var,
            command=self._save_settings,
        ).pack(side="left", padx=(0, 20))
        ttk.Checkbutton(
            options, text="Gerar MP3", variable=self.mp3_var,
            command=self._save_settings,
        ).pack(side="left", padx=(0, 20))
        ttk.Checkbutton(
            options, text="Abrir no MuseScore ao concluir", variable=self.open_var,
            command=self._save_settings,
        ).pack(side="left")

        action = ttk.Frame(parent)
        action.pack(fill="x", pady=(14, 8))
        self.convert_btn = ttk.Button(
            action, text="Converter", style="Accent.TButton", command=self._start
        )
        self.convert_btn.pack(side="left")
        self.progress = ttk.Progressbar(action, mode="indeterminate", length=220)
        self.progress.pack(side="left", padx=14)
        ttk.Label(action, textvariable=self.status_var, style="Muted.TLabel").pack(
            side="left", fill="x", expand=True
        )

        log_box = ttk.LabelFrame(parent, text=" Log de conversão ", padding=8)
        log_box.pack(fill="both", expand=True)
        self.log = scrolledtext.ScrolledText(
            log_box, height=14, wrap="word", font=("Consolas", 9), state="disabled"
        )
        self.log.pack(fill="both", expand=True)

    def _build_history_tab(self, parent: ttk.Frame) -> None:
        columns = ("date", "pdf", "status", "mxl", "mp3")
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", height=15
        )
        headings = {
            "date": ("Data", 150),
            "pdf": ("PDF", 210),
            "status": ("Status", 80),
            "mxl": ("MusicXML", 210),
            "mp3": ("MP3", 210),
        }
        for key, (label, width) in headings.items():
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width, anchor="w")
        scrollbar = ttk.Scrollbar(
            tree_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", lambda _event: self._open_entry("mp3"))

        buttons = ttk.Frame(parent)
        buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(buttons, text="Abrir MP3", command=lambda: self._open_entry("mp3")).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(
            buttons, text="Abrir MusicXML", command=lambda: self._open_entry("mxl")
        ).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Abrir PDF", command=lambda: self._open_entry("pdf")).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(buttons, text="Remover", command=self._remove_entry).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(buttons, text="Limpar histórico", command=self._clear_history).pack(
            side="left"
        )

    def _build_settings_tab(self, parent: ttk.Frame) -> None:
        exe_box = ttk.LabelFrame(parent, text=" Executáveis ", padding=10)
        exe_box.pack(fill="x")

        ttk.Label(exe_box, text="Audiveris:").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(exe_box, textvariable=self.audiveris_var, width=62).grid(
            row=0, column=1, sticky="ew", padx=8
        )
        ttk.Button(exe_box, text="Procurar...", command=self._choose_audiveris).grid(
            row=0, column=2
        )

        ttk.Label(exe_box, text="MuseScore:").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(exe_box, textvariable=self.musescore_var, width=62).grid(
            row=1, column=1, sticky="ew", padx=8
        )
        ttk.Button(exe_box, text="Procurar...", command=self._choose_musescore).grid(
            row=1, column=2
        )

        ttk.Button(
            exe_box,
            text="Detectar automaticamente",
            command=self._detect_executables,
        ).grid(row=2, column=1, sticky="w", pady=(8, 0))
        ttk.Button(
            exe_box,
            text="Instalar Audiveris agora",
            command=self._install_audiveris,
        ).grid(row=2, column=2, sticky="w", pady=(8, 0))
        exe_box.columnconfigure(1, weight=1)

        look_box = ttk.LabelFrame(parent, text=" Aparência ", padding=10)
        look_box.pack(fill="x", pady=(10, 0))
        ttk.Label(look_box, text="Tema:").pack(side="left")
        ttk.Combobox(
            look_box,
            textvariable=self.theme_var,
            values=list(THEMES),
            state="readonly",
            width=20,
        ).pack(side="left", padx=10)

        time_box = ttk.LabelFrame(parent, text=" Tempos limite (segundos) ", padding=10)
        time_box.pack(fill="x", pady=(10, 0))
        ttk.Label(time_box, text="Audiveris:").pack(side="left")
        ttk.Spinbox(
            time_box, from_=60, to=7200, textvariable=self.timeout_a_var, width=8
        ).pack(side="left", padx=(6, 20))
        ttk.Label(time_box, text="MuseScore:").pack(side="left")
        ttk.Spinbox(
            time_box, from_=30, to=3600, textvariable=self.timeout_m_var, width=8
        ).pack(side="left", padx=6)

        ttk.Button(
            parent, text="Salvar configurações", command=self._save_settings
        ).pack(anchor="w", pady=(14, 0))
        ttk.Label(
            parent,
            text=f"Configurações e histórico: {app_data_dir()}",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(8, 0))

    # ------------------------------------------------------------------ theme
    def apply_theme(self) -> None:
        name = self.theme_var.get()
        if name not in THEMES:
            name = next(iter(THEMES))
        palette = apply_theme(self.root, self.style, name)

        self.log.configure(
            bg=palette["text_bg"],
            fg=palette["text_fg"],
            insertbackground=palette["fg"],
            selectbackground=palette["sel_bg"],
            selectforeground=palette["sel_fg"],
            highlightbackground=palette["border"],
            highlightthickness=1,
            borderwidth=1,
            relief="flat",
        )
        for tag, color in (
            ("info", palette["muted"]),
            ("ok", palette["ok"]),
            ("erro", palette["erro"]),
            ("cmd", palette["accent"]),
        ):
            self.log.tag_configure(tag, foreground=color)
        self.tree.tag_configure("ok", foreground=palette["ok"])
        self.tree.tag_configure("erro", foreground=palette["erro"])

    def _on_theme_change(self, *_args: object) -> None:
        self.apply_theme()
        self._save_settings()

    # ------------------------------------------------------------------ files
    def _choose_pdf(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecione a partitura em PDF",
            filetypes=[("PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
        )
        if not path:
            return
        self.pdf_var.set(path)
        if not self.out_var.get().strip():
            self.out_var.set(str(Path(path).parent))
        self._save_settings()
        self._log(f"PDF selecionado: {path}", "info")

    def _choose_output(self) -> None:
        path = filedialog.askdirectory(title="Pasta onde salvar os arquivos")
        if not path:
            return
        self.out_var.set(path)
        self._save_settings()

    def _open_output(self) -> None:
        target = self.out_var.get().strip()
        if not target and self.pdf_var.get().strip():
            target = str(Path(self.pdf_var.get()).parent)
        if not target:
            messagebox.showinfo("Pasta", "Escolha um PDF ou uma pasta de saída.")
            return
        Path(target).mkdir(parents=True, exist_ok=True)
        try:
            open_path(target)
        except OSError as exc:
            messagebox.showerror("Abrir pasta", str(exc))

    def _choose_audiveris(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecione o executável do Audiveris",
            filetypes=[("Audiveris", "audiveris.bat;audiveris"), ("Todos", "*.*")],
        )
        if path:
            self.audiveris_var.set(path)
            self._save_settings()

    def _choose_musescore(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecione o executável do MuseScore",
            filetypes=[("Executável", "*.exe"), ("Todos", "*.*")],
        )
        if path:
            self.musescore_var.set(path)
            self._save_settings()

    def _detect_executables(self) -> None:
        for kind, variable in (
            ("audiveris", self.audiveris_var),
            ("musescore", self.musescore_var),
        ):
            found = detect_executable(kind)
            if found:
                variable.set(found)
                self._log(f"{kind.title()} detectado: {found}", "ok")
        self._save_settings()

    def _install_audiveris(self) -> None:
        if not java_available():
            messagebox.showerror(
                "Java necessário",
                "Instale o Java 17 ou superior antes de instalar o Audiveris.",
            )
            return
        self.notebook.select(self.tab_convert)
        self._log("Instalando Audiveris...", "info")
        self.status_var.set("Instalando Audiveris...")
        threading.Thread(target=self._install_worker, daemon=True).start()

    def _install_worker(self) -> None:
        try:
            path = download_and_install_audiveris(
                progress=lambda message: self.events.put(("log", message, "info"))
            )
            self.events.put(("audiveris", str(path)))
            self.events.put(("status", "Audiveris instalado."))
        except InstallError as exc:
            self.events.put(("log", f"ERRO: {exc}", "erro"))
            self.events.put(("status", "Falha na instalação."))

    # --------------------------------------------------------------- settings
    def _save_settings(self) -> None:
        timeout_a = positive_int(self.timeout_a_var.get(), 900)
        timeout_m = positive_int(self.timeout_m_var.get(), 300)
        self.settings.update(
            {
                "theme": self.theme_var.get(),
                "audiveris": self.audiveris_var.get().strip(),
                "musescore": self.musescore_var.get().strip(),
                "output_dir": self.out_var.get().strip(),
                "keep_mxl": self.keep_var.get(),
                "generate_mp3": self.mp3_var.get(),
                "open_in_musescore": self.open_var.get(),
                "audiveris_timeout": timeout_a,
                "musescore_timeout": timeout_m,
            }
        )
        self.settings.save()

    # -------------------------------------------------------------- conversion
    def _start(self) -> None:
        if self.running:
            return
        pdf_text = self.pdf_var.get().strip()
        if not pdf_text or not Path(pdf_text).is_file():
            messagebox.showwarning("PDF", "Escolha um arquivo PDF válido.")
            return
        if not self.keep_var.get() and not self.mp3_var.get():
            messagebox.showwarning(
                "Opções", "Marque ao menos uma saída: MusicXML ou MP3."
            )
            return

        pdf = Path(pdf_text)
        output_dir = Path(self.out_var.get().strip() or pdf.parent)
        audiveris = self.audiveris_var.get().strip()
        musescore = self.musescore_var.get().strip()

        if not audiveris or not Path(audiveris).is_file():
            messagebox.showerror(
                "Audiveris",
                "Caminho do Audiveris inválido. Configure na aba Configurações "
                "ou use 'Instalar Audiveris agora'.",
            )
            self.notebook.select(self.tab_settings)
            return
        if self.mp3_var.get() and (not musescore or not Path(musescore).is_file()):
            messagebox.showerror(
                "MuseScore",
                "Caminho do MuseScore inválido. Configure na aba Configurações.",
            )
            self.notebook.select(self.tab_settings)
            return

        self._save_settings()
        self.running = True
        self.convert_btn.configure(state="disabled")
        self.progress.start(12)
        self.status_var.set("Reconhecendo a partitura...")
        self._clear_log()
        self._log(f"Iniciando conversão: {pdf.name}", "ok")

        args = (
            pdf,
            output_dir,
            audiveris,
            musescore,
            positive_int(self.timeout_a_var.get(), 900),
            positive_int(self.timeout_m_var.get(), 300),
        )
        threading.Thread(target=self._worker, args=args, daemon=True).start()

    def _worker(
        self,
        pdf: Path,
        output_dir: Path,
        audiveris: str,
        musescore: str,
        timeout_a: int,
        timeout_m: int,
    ) -> None:
        entry = {
            "id": datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + os.urandom(2).hex(),
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "pdf": str(pdf),
            "mxl": "",
            "mp3": "",
            "status": "erro",
            "message": "",
        }
        try:
            mxl = pdf_to_musicxml(
                pdf,
                output_dir,
                audiveris,
                timeout_a,
                log=lambda message: self._emit("log", message, "info"),
            )
            entry["mxl"] = str(mxl)
            self._emit("log", f"MusicXML: {mxl}", "ok")
            self._emit("status", "Gerando MP3..." if self.mp3_var.get() else "Finalizando...")

            if self.mp3_var.get():
                mp3 = output_dir / f"{mxl.stem}.mp3"
                musicxml_to_mp3(
                    mxl,
                    mp3,
                    musescore,
                    timeout_m,
                    log=lambda message: self._emit("log", message, "info"),
                )
                entry["mp3"] = str(mp3)
                self._emit("log", f"MP3: {mp3}", "ok")

            if self.open_var.get():
                open_in_musescore(mxl, musescore)

            entry["status"] = "ok"
            entry["message"] = "Concluído"
            self._emit("log", "Conversão concluída com sucesso.", "ok")
            self._emit("status", "Concluído.")
        except (ConversionError, OSError) as exc:
            entry["message"] = str(exc)
            self._emit("log", f"ERRO: {exc}", "erro")
            self._emit("status", "Erro na conversão.")
        finally:
            self.history.add(entry)
            self.events.put(("history",))
            self.events.put(("done",))

    # ------------------------------------------------------------------ events
    def _emit(self, kind: str, *payload: object) -> None:
        self.events.put((kind, *payload))

    def _pump(self) -> None:
        while True:
            try:
                event = self.events.get_nowait()
            except queue.Empty:
                break
            kind, *payload = event
            if kind == "log":
                self._log(str(payload[0]), str(payload[1]) if len(payload) > 1 else "info")
            elif kind == "status":
                self.status_var.set(str(payload[0]))
            elif kind == "history":
                self._refresh_history()
            elif kind == "done":
                self.progress.stop()
                self.convert_btn.configure(state="normal")
                self.running = False
            elif kind == "audiveris":
                self.audiveris_var.set(str(payload[0]))
                self._save_settings()
        self.root.after(120, self._pump)

    # --------------------------------------------------------------------- log
    def _clear_log(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _log(self, text: str, tag: str = "info") -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n", tag)
        self.log.see("end")
        self.log.configure(state="disabled")

    # ----------------------------------------------------------------- history
    def _refresh_history(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for item in self.history.entries:
            status = item.get("status", "erro")
            tag = "ok" if status == "ok" else "erro"
            self.tree.insert(
                "",
                "end",
                iid=str(item.get("id")),
                values=(
                    _fmt_date(item.get("created_at")),
                    _filename(item.get("pdf")),
                    "OK" if tag == "ok" else "ERRO",
                    _filename(item.get("mxl")),
                    _filename(item.get("mp3")),
                ),
                tags=(tag,),
            )

    def _selected_entry(self) -> dict | None:
        selected = self.tree.selection()
        if not selected:
            return None
        for item in self.history.entries:
            if str(item.get("id")) == selected[0]:
                return item
        return None

    def _open_entry(self, key: str) -> None:
        item = self._selected_entry()
        if not item or not item.get(key):
            messagebox.showinfo("Histórico", "Selecione uma conversão com esse arquivo.")
            return
        path = Path(str(item[key]))
        if not path.is_file():
            messagebox.showerror("Arquivo", f"Arquivo não encontrado:\n{path}")
            return
        try:
            open_path(path)
        except OSError as exc:
            messagebox.showerror("Abrir arquivo", str(exc))

    def _remove_entry(self) -> None:
        item = self._selected_entry()
        if not item:
            return
        self.history.remove(str(item["id"]))
        self._refresh_history()

    def _clear_history(self) -> None:
        if not self.history.entries:
            return
        if messagebox.askyesno("Histórico", "Apagar todo o histórico?"):
            self.history.clear()
            self._refresh_history()
