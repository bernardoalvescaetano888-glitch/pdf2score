"""Instalação direta do Audiveris caso não esteja presente no sistema."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable

from .paths import app_data_dir

API_LATEST = "https://api.github.com/repos/Audiveris/audiveris/releases/latest"
ProgressFn = Callable[[str], None]

# A partir da versão 5.11 o pacote do Windows é um MSI com runtime Java embutido.
MSI_PATTERNS = ("windows-x86_64.msi", "windowsConsole-x86_64.msi")


class InstallError(RuntimeError):
    pass


def java_available() -> bool:
    """Verifica se existe Java no PATH ou em JAVA_HOME."""
    if shutil.which("java"):
        return True
    java_home = os.environ.get("JAVA_HOME", "")
    return bool(java_home) and (Path(java_home) / "bin" / "java.exe").is_file()


def _find_launcher(root: Path) -> Path | None:
    """Localiza o executável do Audiveris dentro de uma pasta."""
    if not root.is_dir():
        return None
    for name in ("audiveris.bat", "Audiveris.exe", "audiveris.exe"):
        for candidate in root.rglob(name):
            if candidate.is_file():
                return candidate
    return None


def installed_audiveris_path() -> Path | None:
    """Retorna o Audiveris baixado pelo próprio aplicativo, se existir."""
    return _find_launcher(app_data_dir() / "tools" / "audiveris")


def _fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "Pdf2Score/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - erro de rede é sempre amigável
        raise InstallError(f"Não foi possível consultar o GitHub: {exc}") from exc


def _pick_asset(release: dict) -> tuple[str, str, str]:
    """Escolhe o pacote correto do Windows (não a documentação)."""
    assets = release.get("assets", [])

    for pattern in MSI_PATTERNS:
        for asset in assets:
            if asset.get("name", "").lower().endswith(pattern):
                return asset["browser_download_url"], asset["name"], "msi"

    # Compatibilidade com versões antigas que distribuíam um ZIP.
    for asset in assets:
        name = asset.get("name", "").lower()
        if (
            name.endswith(".zip")
            and name.startswith("audiveris-")
            and not any(word in name for word in ("schema", "doc", "source", "jre"))
        ):
            return asset["browser_download_url"], asset["name"], "zip"

    raise InstallError(
        "Nenhum instalador do Audiveris para Windows foi encontrado na última versão."
    )


def _download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "Pdf2Score/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=600) as response, destination.open("wb") as out:
            while True:
                chunk = response.read(1024 * 256)
                if not chunk:
                    break
                out.write(chunk)
    except Exception as exc:  # noqa: BLE001
        raise InstallError(f"Falha no download: {exc}") from exc


def _clean_target(target_dir: Path) -> None:
    """Remove resíduos de instalações anteriores sem apagar a própria pasta."""
    if not target_dir.is_dir():
        return
    for child in target_dir.iterdir():
        if child.is_dir():
            shutil.rmtree(child, ignore_errors=True)
        else:
            try:
                child.unlink()
            except OSError:
                pass


def _extract_msi(msi: Path, output_dir: Path, progress: ProgressFn) -> None:
    """Extrai o MSI com msiexec /a (não instala no sistema)."""
    progress("Extraindo o pacote MSI do Audiveris...")
    try:
        result = subprocess.run(
            [
                "msiexec",
                "/a",
                str(msi),
                "/qn",
                f"TARGETDIR={output_dir}",
            ],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=900,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise InstallError(f"Falha ao extrair o MSI: {exc}") from exc
    if result.returncode != 0:
        raise InstallError(
            f"O msiexec falhou (código {result.returncode}). "
            "Tente executar o aplicativo como administrador."
        )


def download_and_install_audiveris(
    progress: ProgressFn | None = None,
    target_dir: Path | None = None,
) -> Path:
    """Baixa e extrai a última versão do Audiveris.

    Retorna o caminho do executável (Audiveris.exe ou audiveris.bat).
    """
    progress = progress or (lambda _message: None)
    existing = installed_audiveris_path()
    if existing:
        return existing

    target_dir = Path(target_dir or (app_data_dir() / "tools" / "audiveris"))
    target_dir.mkdir(parents=True, exist_ok=True)

    progress("Consultando a última versão do Audiveris...")
    release = _fetch_json(API_LATEST)
    url, name, kind = _pick_asset(release)

    # O msiexec falha com caminhos longos, então tudo é feito num temp curto.
    with tempfile.TemporaryDirectory(prefix="pdf2score_") as temporary:
        temp_root = Path(temporary)
        package = temp_root / name
        extracted = temp_root / "out"

        progress(f"Baixando {name}...")
        _download(url, package)

        if kind == "msi":
            _extract_msi(package, extracted, progress)
        else:
            if not java_available():
                raise InstallError(
                    "Java não foi encontrado. Instale o Java 17+ antes do Audiveris."
                )
            progress("Extraindo arquivos...")
            try:
                with zipfile.ZipFile(package) as archive:
                    archive.extractall(extracted)
            except (zipfile.BadZipFile, OSError) as exc:
                raise InstallError(f"Falha ao extrair o pacote: {exc}") from exc

        if not _find_launcher(extracted):
            raise InstallError("O pacote foi baixado, mas o Audiveris não foi encontrado.")

        progress("Copiando arquivos para a pasta do aplicativo...")
        _clean_target(target_dir)
        shutil.copytree(extracted, target_dir, dirs_exist_ok=True)

    found = installed_audiveris_path()
    if not found:
        raise InstallError("O Audiveris foi instalado, mas o executável não foi localizado.")
    progress(f"Audiveris instalado: {found}")
    return found
