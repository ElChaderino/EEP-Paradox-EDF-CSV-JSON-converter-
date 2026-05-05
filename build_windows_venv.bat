@echo off
REM Build EEGParadox_EDF_Tool.exe using an isolated venv (avoids PyInstaller scanning global Torch/PyQt6/etc.).
set "TOOL=%~dp0"
set "ROOT=%TOOL%.."
cd /d "%ROOT%"
if exist .venv_edf_build rmdir /s /q .venv_edf_build
python -m venv .venv_edf_build
call .venv_edf_build\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r EEG_EDF_Standalone_Tool/requirements-build.txt
python -m PyInstaller EEG_EDF_Standalone_Tool/build_exe.spec --noconfirm
echo.
echo Output: %ROOT%\dist\EEGParadox_EDF_Tool\EEGParadox_EDF_Tool.exe
pause
