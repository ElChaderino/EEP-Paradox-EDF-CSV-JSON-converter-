@echo off
setlocal EnableExtensions EnableDelayedExpansion
title EEG Paradox EDF Tool — one-click setup

REM ------------------------------------------------------------------------------
REM  Installs Python (if needed), creates a dedicated venv, and pip-installs the
REM  app dependencies so users can run from source — double-click Run_EDF_Studio.bat
REM  Requires: Windows 10/11, internet access for pip (and winget if Python missing).
REM ------------------------------------------------------------------------------

REM Support two layouts:
REM   Monorepo: this .bat lives in .../<repo>/EEG_EDF_Standalone_Tool/
REM   Flat GH repo: this .bat lives next to main.py and requirements-standalone.txt

pushd "%~dp0" || (
  echo Could not open script folder.
  pause
  exit /b 1
)
set "TOOL_DIR=%CD%"
for %%I in ("%CD%") do set "TOOL_LEAF=%%~nxI"
if /I "%TOOL_LEAF%"=="EEG_EDF_Standalone_Tool" (
  pushd ".." || (
    echo Could not open parent repository folder.
    pause
    exit /b 1
  )
  set "REPO_ROOT=%CD%"
  popd
) else (
  set "REPO_ROOT=%TOOL_DIR%"
)
popd

set "VENV_DIR=%REPO_ROOT%\.venv_edf_app"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "REQ_FILE=%TOOL_DIR%\requirements-standalone.txt"

echo.
echo  EEG Paradox EDF Tool — setup
echo  Folder: "%REPO_ROOT%"
echo.

if not exist "%REQ_FILE%" (
  echo ERROR: Requirements file not found:
  echo   "%REQ_FILE%"
  pause
  exit /b 1
)

call :ResolvePython
if defined FOUND_PYTHON goto :PythonOk

echo  Python 3.10 or newer was not found on this PC.
echo  Trying to install Python 3.12 using winget ^(Internet required^)...
where winget >nul 2>&1
if errorlevel 1 goto :NoWinget

winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements --silent
echo.

REM Same-session PATH: common per-user install locations
set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"
set "PATH=%ProgramFiles%\Python312;%ProgramFiles%\Python312\Scripts;%PATH%"

echo Waiting a few seconds for the installer to finish registering...
timeout /t 10 /nobreak >nul

call :ResolvePython
if defined FOUND_PYTHON goto :PythonOk

echo winget ran, but Python is still not visible in this window.
echo Close this window, open a NEW Command Prompt, and run One_Click_Setup.bat again.
echo Or install Python manually ^(see message below^).
goto :ManualPython

:NoWinget
echo winget is not available on this system.

:ManualPython
echo.
echo Please install Python 3.10+ from:
echo   https://www.python.org/downloads/windows/
echo.
echo Important: enable **Add python.exe to PATH** ^or install the **py launcher**,
echo then run **One_Click_Setup.bat** again.
start "" "https://www.python.org/downloads/windows/"
pause
exit /b 1

:PythonOk
echo  Using Python:
echo    %FOUND_PYTHON%
echo.

if not exist "%VENV_PY%" (
  echo Creating virtual environment ^(only once^)...
  "%FOUND_PYTHON%" -m venv "%VENV_DIR%"
)
if not exist "%VENV_PY%" (
  echo ERROR: Could not create venv at:
  echo   "%VENV_DIR%"
  pause
  exit /b 1
)

echo Upgrading pip and installing packages ^(numpy, scipy, mne, PyQt5 — may take several minutes^)...
"%VENV_PY%" -m pip install --upgrade pip wheel setuptools
if errorlevel 1 (
  echo pip upgrade failed.
  pause
  exit /b 1
)

"%VENV_PY%" -m pip install -r "%REQ_FILE%"
if errorlevel 1 (
  echo Package install failed. Check your internet connection and try again.
  pause
  exit /b 1
)

echo.
echo ------------------------------------------------------------------------------
echo  Setup finished successfully.
echo.
echo  Start the program anytime by double-clicking:
echo    "%TOOL_DIR%\Run_EDF_Studio.bat"
echo.
echo  ^(Optional^) You can still use the frozen EXE in dist\ if you prefer.
echo ------------------------------------------------------------------------------
echo.

choice /C YN /M "Launch the EDF Tool now"
if errorlevel 2 goto :Done
call "%TOOL_DIR%\Run_EDF_Studio.bat"
goto :Done

:Done
pause
exit /b 0

REM ============================================================================
REM  Resolve Python 3.10+ ; sets FOUND_PYTHON to python.exe path
REM ============================================================================
:ResolvePython
set "FOUND_PYTHON="
py -3 -c "import sys; sys.exit(0 if sys.version_info[:2]>=(3,10) else 1)" 2>nul
if errorlevel 1 goto :TryPlainPython
for /f "delims=" %%I in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do set "FOUND_PYTHON=%%I"
if defined FOUND_PYTHON exit /b 0

:TryPlainPython
python -c "import sys; sys.exit(0 if sys.version_info[:2]>=(3,10) else 1)" 2>nul
if errorlevel 1 goto :TryWellKnown
for /f "delims=" %%I in ('python -c "import sys; print(sys.executable)" 2^>nul') do set "FOUND_PYTHON=%%I"
if defined FOUND_PYTHON exit /b 0

:TryWellKnown
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "FOUND_PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe" & exit /b 0
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set "FOUND_PYTHON=%LOCALAPPDATA%\Programs\Python\Python311\python.exe" & exit /b 0
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" set "FOUND_PYTHON=%LOCALAPPDATA%\Programs\Python\Python310\python.exe" & exit /b 0
if exist "%ProgramFiles%\Python312\python.exe" set "FOUND_PYTHON=%ProgramFiles%\Python312\python.exe" & exit /b 0
if exist "%ProgramFiles%\Python311\python.exe" set "FOUND_PYTHON=%ProgramFiles%\Python311\python.exe" & exit /b 0
if exist "%ProgramFiles%\Python310\python.exe" set "FOUND_PYTHON=%ProgramFiles%\Python310\python.exe" & exit /b 0
exit /b 0
