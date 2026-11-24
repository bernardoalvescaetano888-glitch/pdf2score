"""Wrappers em Python para Audiveris (PDF -> MusicXML) e MuseScore (MusicXML -> MP3)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable

LogFn = Callable[[str], None]


class ConversionError(RuntimeError):
    """Erro amigável de conversão."""


def _log_noop(_message: str) -> None:
    pass


def _run(command: list[str], timeout: int, log: LogFn) -> str:
    readable = " ".join(
        f'"{part}"' if " " in part else part for part in command
    )
    log(f"$ {readable}")
    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise ConversionError(f"Executável não encontrado: {command[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise ConversionError(
            f"Tempo limite de {timeout}s excedido ao executar {Path(command[0]).name}."
        ) from exc

    output = (process.stdout or "") + (process.stderr or "")
    for line in output.splitlines():
        if line.strip():
            log(line.strip())

    if process.returncode != 0:
        raise ConversionError(
            f"{Path(command[0]).name} terminou com código {process.returncode}."
        )
    return output


def _find_new_mxl(output_dir: Path, before: set[Path]) -> Path:
    files = sorted(
        output_dir.rglob("*.mxl"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    fresh = [item for item in files if item.resolve() not in before]
    candidates = fresh or files
    if not candidates:
        raise ConversionError(
            "O Audiveris não gerou nenhum arquivo .mxl. Confira o log acima e "
            "tente abrir o PDF manualmente no Audiveris."
        )
    return candidates[0]


def pdf_to_musicxml(
    pdf: Path,
    output_dir: Path,
    audiveris_exe: str,
    timeout: int = 900,
    log: LogFn | None = None,
) -> Path:
    """Converte um PDF em MusicXML comprimido (.mxl) usando o Audiveris."""
    log = log or _log_noop
    pdf = Path(pdf)
    output_dir = Path(output_dir)

    if not pdf.is_file():
        raise ConversionError(f"PDF não encontrado: {pdf}")
    if not Path(audiveris_exe).is_file():
        raise ConversionError(f"Audiveris não encontrado: {audiveris_exe}")

    output_dir.mkdir(parents=True, exist_ok=True)
    before = {item.resolve() for item in output_dir.rglob("*.mxl")}

    log(f"Reconhecendo partitura: {pdf.name}")
    _run(
        [
            audiveris_exe,
            "-batch",
            "-transcribe",
            "-export",
            "-output",
            str(output_dir),
            str(pdf),
        ],
        timeout,
        log,
    )
    return _find_new_mxl(output_dir, before)


def musicxml_to_mp3(
    mxl: Path,
    mp3: Path,
    musescore_exe: str,
    timeout: int = 300,
    log: LogFn | None = None,
) -> Path:
    """Exporta um MusicXML para MP3 usando o modo linha de comando do MuseScore."""
    log = log or _log_noop
    mxl = Path(mxl)
    mp3 = Path(mp3)

    if not mxl.is_file():
        raise ConversionError(f"MusicXML não encontrado: {mxl}")
    if not Path(musescore_exe).is_file():
        raise ConversionError(f"MuseScore não encontrado: {musescore_exe}")

    mp3.parent.mkdir(parents=True, exist_ok=True)
    log(f"Gerando MP3: {mp3.name}")
    _run([musescore_exe, "-o", str(mp3), str(mxl)], timeout, log)

    if not mp3.is_file():
        raise ConversionError("O MuseScore não gerou o arquivo MP3.")
    return mp3


def open_in_musescore(mxl: Path, musescore_exe: str) -> None:
    """Abre o MusicXML no MuseScore (sem bloquear a interface)."""
    musescore_exe = str(musescore_exe)
    if not Path(musescore_exe).is_file():
        raise ConversionError(f"MuseScore não encontrado: {musescore_exe}")
    subprocess.Popen([musescore_exe, str(mxl)], close_fds=True)
