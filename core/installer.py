"""Instalação direta do Audiveris caso não esteja presente no sistema."""

from __future__ import annotations

import json
import os
import shutil
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable

from .paths import app_data_dir

API_LATEST = "https://api.github.com/repos/Audiveris/audiveris/releases/latest"
ProgressFn = Callable[[str], None]


class InstallError(RuntimeError):
    pass


def java_available() -> bool:
    """Verifica se existe Java no PATH ou em JAVA_HOME."""
    if shutil.which("java"):
        return True
    java_home = os.environ.get("JAVA_HOME", "")
    return bool(java_home) and (Path(java_home) / "bin" / "java.exe").is_file()


def installed_audiveris_path() -> Path | None:
    """Retorna o audiveris.bat baixado pelo próprio aplicativo, se existir."""
    root = app_data_dir() / "tools" / "audiveris"
    if not root.is_dir():
        return None
    for candidate in root.rglob("audiveris.bat"):
        return candidate
    return None


def _fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "Pdf2Score/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - erro de rede é sempre amigável
        raise InstallError(f"Não foi possível consultar o GitHub: {exc}") from exc


def _pick_asset(release: dict) -> tuple[str, str]:
    assets = release.get("assets", [])
    candidates = [
        asset
        for asset in assets
        if asset.get("name", "").lower().endswith(".zip")
        and "source" not in asset.get("name", "").lower()
        and "jre" not in asset.get("name", "").lower()
    ]
    if not candidates:
        raise InstallError("Nenhum pacote ZIP foi encontrado na última versão do Audiveris.")
    asset = candidates[0]
    return asset["browser_download_url"], asset["name"]


def download_and_install_audiveris(
    progress: ProgressFn | None = None,
    target_dir: Path | None = None,
) -> Path:
    """Baixa e extrai a última versão do Audiveris.

    Retorna o caminho para ``audiveris.bat``.
    """
    progress = progress or (lambda _message: None)
    existing = installed_audiveris_path()
    if existing:
        return existing

    if not java_available():
        raise InstallError(
            "Java não foi encontrado. Instale o Java 17+ (Temurin/JDK) antes do Audiveris."
        )

    target_dir = target_dir or (app_data_dir() / "tools" / "audiveris")
    target_dir.mkdir(parents=True, exist_ok=True)

    progress("Consultando a última versão do Audiveris...")
    release = _fetch_json(API_LATEST)
    url, name = _pick_asset(release)
    version = release.get("tag_name", "")
    progress(f"Baixando {name} ({version})...")

    zip_path = target_dir / name
    request = urllib.request.Request(url, headers={"User-Agent": "Pdf2Score/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=300) as response, zip_path.open("wb") as out:
            while True:
                chunk = response.read(1024 * 256)
                if not chunk:
                    break
                out.write(chunk)
    except Exception as exc:  # noqa: BLE001
        raise InstallError(f"Falha no download: {exc}") from exc

    progress("Extraindo arquivos...")
    try:
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(target_dir)
    except (zipfile.BadZipFile, OSError) as exc:
        raise InstallError(f"Falha ao extrair o pacote: {exc}") from exc
    finally:
        zip_path.unlink(missing_ok=True)

    found = installed_audiveris_path()
    if not found:
        raise InstallError("O pacote foi baixado, mas o audiveris.bat não foi encontrado.")
    progress(f"Audiveris instalado: {found}")
    return found
