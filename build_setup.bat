@echo off
setlocal
cd /d "%~dp0"

set "ISCC="
for %%P in (
  "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
  "%LOCALAPPDATA%\Programs\Inno Setup 7\ISCC.exe"
  "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
  "C:\Program Files (x86)\Inno Setup 7\ISCC.exe"
  "C:\Program Files\Inno Setup 6\ISCC.exe"
  "C:\Program Files\Inno Setup 7\ISCC.exe"
) do if exist %%P set "ISCC=%%~P"

if not defined ISCC (
  echo Inno Setup nao encontrado. Instale com:
  echo   winget install --id JRSoftware.InnoSetup --exact
  exit /b 1
)

echo Compilando instaladores com: %ISCC%
"%ISCC%" "installer\Pdf2Score.iss"
if errorlevel 1 exit /b 1
"%ISCC%" "installer\Pdf2Score-Completo.iss"
if errorlevel 1 exit /b 1

echo.
echo Instalador gerado em: %CD%\setup
endlocal
